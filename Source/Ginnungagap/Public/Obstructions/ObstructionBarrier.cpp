#include "Obstructions/ObstructionBarrier.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"

#include "Activities/PlayerActivityComponent.h"
#include "Equipment/EquipmentComponent.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "Ship/ShipSystemActor.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "UI/UiSoundSubsystem.h"
#include "Stealth/NoisePerceptionSubsystem.h"
#include "Stealth/StealthTypes.h"

namespace
{
	/**
	 * How much harder cutting is on gear than simply wearing it.
	 *
	 * Equipment already degrades on a per-second rate through DegradeEquipment, so a cut is charged
	 * as that rate over the cut's duration, multiplied. Reusing the existing rate rather than
	 * inventing a second number means a change to how fast gear wears out reaches this too, instead
	 * of the two drifting apart.
	 */
	constexpr float CutWearMultiplier = 14.0f;

	/** Default sizes, so an unconfigured barrier is a corridor-width obstruction rather than a point. */
	constexpr float DefaultHalfWidth = 190.0f;
	constexpr float DefaultHalfDepth = 60.0f;
	constexpr float DefaultHalfHeight = 160.0f;
}

AObstructionBarrier::AObstructionBarrier()
{
	PrimaryActorTick.bCanEverTick = false;

	Blocker = CreateDefaultSubobject<UBoxComponent>(TEXT("Blocker"));
	Blocker->SetBoxExtent(FVector(DefaultHalfDepth, DefaultHalfWidth, DefaultHalfHeight));
	Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Blocker->SetCollisionObjectType(ECC_WorldStatic);
	Blocker->SetCollisionResponseToAllChannels(ECR_Block);
	RootComponent = Blocker;

	VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
	VisualMesh->SetupAttachment(RootComponent);
	// The blocker carries the collision. A second collider in the same place fights the first, and
	// on this map that has already pushed a player through a wall once.
	VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DisplayName = NSLOCTEXT("Obstructions", "DefaultObstruction", "Blocked passage");
}

EObstructionRefusal AObstructionBarrier::GetRefusal(EObstructionVerb Verb, const APawn* Player) const
{
	if (bCleared)
	{
		return EObstructionRefusal::AlreadyCleared;
	}

	const FObstructionVerbOption* Option = Options.Find(Verb);
	if (!Option || !Option->bAllowed)
	{
		return EObstructionRefusal::NotPossibleHere;
	}

	if (Option->MinimumEquipmentCondition > 0.0f)
	{
		// No pawn is not the same as no equipment. A caller asking "is this obstruction cuttable at
		// all" passes null, and should be told about the obstruction rather than about a player who
		// is not there.
		if (!Player)
		{
			return EObstructionRefusal::None;
		}

		const UEquipmentComponent* Equipment = Player->FindComponentByClass<UEquipmentComponent>();
		if (!Equipment || Equipment->GetWorstSlotCondition() < Option->MinimumEquipmentCondition)
		{
			return EObstructionRefusal::EquipmentTooWorn;
		}

		// Worth knowing at the design level, not just the code level: GetWorstSlotCondition()
		// returns 1.0 -- perfect -- when nothing is equipped at all, by its own explicit design
		// ("nothing worn is not the same as everything ruined"). So this check gates on the
		// *condition* of whatever gear a player happens to have, never on *possessing* a specific
		// tool. A story beat written as "find the tool, then cut" is not mechanically enforced by
		// this obstruction: a totally fresh player with nothing equipped can Cut on the first frame.
		// That is fine for the obstruction's own generic design intent, and worth a second look if a
		// specific scripted beat depends on the causality holding.
	}

	return EObstructionRefusal::None;
}

bool AObstructionBarrier::CanResolveWith(EObstructionVerb Verb, const APawn* Player) const
{
	return GetRefusal(Verb, Player) == EObstructionRefusal::None;
}

TArray<EObstructionVerb> AObstructionBarrier::GetAvailableVerbs(const APawn* Player) const
{
	TArray<EObstructionVerb> Available;
	for (const TPair<EObstructionVerb, FObstructionVerbOption>& Entry : Options)
	{
		if (GetRefusal(Entry.Key, Player) == EObstructionRefusal::None)
		{
			Available.Add(Entry.Key);
		}
	}

	// Sorted so a prompt lists the same options in the same order every time. TMap iteration order
	// is not stable across runs, and a menu whose entries move between playthroughs reads as a bug.
	Available.Sort([](EObstructionVerb A, EObstructionVerb B)
	{
		return static_cast<uint8>(A) < static_cast<uint8>(B);
	});
	return Available;
}

float AObstructionBarrier::GetCollateralAtDistance(EObstructionVerb Verb, float Distance) const
{
	const FObstructionVerbOption* Option = Options.Find(Verb);
	if (!Option || Option->CollateralRadius <= 0.0f || Option->CollateralSeverity <= 0.0f)
	{
		return 0.0f;
	}
	if (Distance >= Option->CollateralRadius)
	{
		return 0.0f;
	}

	// Linear falloff rather than inverse square. This is blast and debris in a corridor, not
	// radiated energy in open space, and a linear figure is one a player can predict from "how far
	// away is that console" -- which is the decision the whole verb exists to pose.
	const float Falloff = 1.0f - (Distance / Option->CollateralRadius);
	return Option->CollateralSeverity * Falloff;
}

void AObstructionBarrier::ApplyCollateral(const FObstructionVerbOption& Option)
{
	UWorld* World = GetWorld();
	if (!World || Option.CollateralRadius <= 0.0f || Option.CollateralSeverity <= 0.0f)
	{
		return;
	}

	const FVector At = GetActorLocation();
	for (TActorIterator<AShipSystemActor> It(World); It; ++It)
	{
		AShipSystemActor* System = *It;
		if (!IsValid(System) || !System->PowerNode)
		{
			continue;
		}

		const float Distance = FVector::Dist(At, System->GetActorLocation());
		if (Distance >= Option.CollateralRadius)
		{
			continue;
		}

		const float Damage = Option.CollateralSeverity * (1.0f - Distance / Option.CollateralRadius);
		if (Damage <= KINDA_SMALL_NUMBER)
		{
			continue;
		}

		// Added to whatever damage the system already carries rather than assigned. Blowing the
		// same bulkhead twice should not heal the console next to it, and assignment would let a
		// second, weaker blast do exactly that.
		const float Existing = System->PowerNode->DamageFraction;
		System->PowerNode->SetDamageFraction(FMath::Clamp(Existing + Damage, 0.0f, 1.0f));
	}
}

void AObstructionBarrier::ReportNoise(const FObstructionVerbOption& Option, EObstructionVerb Verb,
	AActor* NoiseSource)
{
	UWorld* World = GetWorld();
	if (!World || Option.NoiseLoudness <= 0.0f)
	{
		return;
	}

	UNoisePerceptionSubsystem* Noise = World->GetSubsystem<UNoisePerceptionSubsystem>();
	if (!Noise)
	{
		return;
	}

	// Categorised by what it actually sounds like, because the perception system weights categories
	// differently and a breach filed as footsteps would be heard as footsteps.
	ENoiseCategory Category = ENoiseCategory::Impact;
	if (Verb == EObstructionVerb::Cut)
	{
		Category = ENoiseCategory::Tool;
	}
	else if (Verb == EObstructionVerb::Squeeze)
	{
		Category = ENoiseCategory::Movement;
	}

	Noise->ReportNoise(GetActorLocation(), Option.NoiseLoudness, Category, NoiseSource);
}

void AObstructionBarrier::ApplyCutCost(const FObstructionVerbOption& Option, APawn* Player)
{
	if (!Player)
	{
		return;
	}

	UEquipmentComponent* Equipment = Player->FindComponentByClass<UEquipmentComponent>();
	if (!Equipment)
	{
		return;
	}

	// Condition is read before the cut, not after. The burn is a consequence of the state the gear
	// was in when the player chose to use it, and charging the wear first would mean a cut with
	// good gear could burn on the condition its own wear produced.
	const float ConditionBefore = Equipment->GetWorstSlotCondition();
	Equipment->DegradeEquipment(Option.DurationSeconds * CutWearMultiplier);

	if (UPlayerStatusEffectComponent* Status =
		Player->FindComponentByClass<UPlayerStatusEffectComponent>())
	{
		Status->ApplyWeldingBackfire(ConditionBefore);
	}
}

void AObstructionBarrier::ApplySqueezeCost(const FObstructionVerbOption& Option, APawn* Player)
{
	if (!Player || Option.NearEntrapmentChance <= 0.0f)
	{
		return;
	}
	if (FMath::FRand() >= Option.NearEntrapmentChance)
	{
		return;
	}

	if (UPlayerStatusEffectComponent* Status =
		Player->FindComponentByClass<UPlayerStatusEffectComponent>())
	{
		Status->ApplyStressEvent(EPlayerStressEvent::NearEntrapment);
	}
}

bool AObstructionBarrier::ResolveWith(EObstructionVerb Verb, APawn* Player)
{
	if (GetRefusal(Verb, Player) != EObstructionRefusal::None)
	{
		return false;
	}

	const FObstructionVerbOption Option = Options[Verb];

	switch (Verb)
	{
	case EObstructionVerb::Breach:
		ApplyCollateral(Option);
		break;
	case EObstructionVerb::Cut:
		ApplyCutCost(Option, Player);
		break;
	case EObstructionVerb::Squeeze:
		ApplySqueezeCost(Option, Player);
		break;
	}

	ReportNoise(Option, Verb, Player);

	bCleared = true;
	ClearedWith = Verb;

	// The way through stays open. A blockage that closes behind the player turns a route decision
	// into a one-way door, and the point of choosing between three costs is that the route is now
	// yours for the rest of the run.
	Blocker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// The thing that was in the way is still there. Cut, it lies where it fell, beside the gap
	// the tool made; squeezed past, it has not moved at all.
	if (Verb == EObstructionVerb::Cut)
	{
		VisualMesh->AddLocalOffset(CutVisualOffset);
		VisualMesh->AddLocalRotation(CutVisualRotation);
	}

	// Getting past something that was in the way is worth a sound. Confirm rather than
	// ObjectiveComplete: clearing an obstruction is progress, not an objective.
	if (UWorld* World = GetWorld())
	{
		if (UGameInstance* GameInstance = World->GetGameInstance())
		{
			if (UUiSoundSubsystem* UiSound = GameInstance->GetSubsystem<UUiSoundSubsystem>())
			{
				UiSound->PlayUiSound(EUiSoundEvent::Confirm);
			}
		}
	}

	OnObstructionCleared.Broadcast(this, Verb);
	return true;
}

void AObstructionBarrier::ApplyAuthoringPreset(FName PresetName)
{
	Options.Reset();

	if (PresetName == TEXT("CollapsedDebris"))
	{
		// Loose structure. Everything works on it, which makes it the one that teaches the choice:
		// the player meets three real options before any of them is scarce.
		FObstructionVerbOption Breach;
		Breach.bAllowed = true;
		Breach.DurationSeconds = 3.0f;
		Breach.NoiseLoudness = 0.85f;
		Breach.CollateralRadius = 900.0f;
		Breach.CollateralSeverity = 0.45f;
		Options.Add(EObstructionVerb::Breach, Breach);

		FObstructionVerbOption Cut;
		Cut.bAllowed = true;
		Cut.DurationSeconds = 11.0f;
		Cut.MinimumEquipmentCondition = 0.25f;
		Cut.NoiseLoudness = 0.35f;
		Options.Add(EObstructionVerb::Cut, Cut);

		FObstructionVerbOption Squeeze;
		Squeeze.bAllowed = true;
		Squeeze.DurationSeconds = 7.0f;
		Squeeze.NoiseLoudness = 0.15f;
		Squeeze.NearEntrapmentChance = 0.35f;
		Options.Add(EObstructionVerb::Squeeze, Squeeze);

		bBypassable = true;
		DisplayName = NSLOCTEXT("Obstructions", "CollapsedDebris", "Collapsed structure");
		return;
	}

	if (PresetName == TEXT("WeldedBulkhead"))
	{
		// Someone sealed this from the other side, and they did it properly. No gaps to squeeze
		// through: it is cut or blown, and blowing it in a compartment full of systems is expensive.
		FObstructionVerbOption Breach;
		Breach.bAllowed = true;
		Breach.DurationSeconds = 4.0f;
		Breach.NoiseLoudness = 1.0f;
		Breach.CollateralRadius = 1300.0f;
		Breach.CollateralSeverity = 0.7f;
		Options.Add(EObstructionVerb::Breach, Breach);

		FObstructionVerbOption Cut;
		Cut.bAllowed = true;
		Cut.DurationSeconds = 18.0f;
		Cut.MinimumEquipmentCondition = 0.45f;
		Cut.NoiseLoudness = 0.4f;
		Options.Add(EObstructionVerb::Cut, Cut);

		bBypassable = false;
		DisplayName = NSLOCTEXT("Obstructions", "WeldedBulkhead", "Welded bulkhead");
		return;
	}

	if (PresetName == TEXT("JammedHatch"))
	{
		// The squeeze-only case, and the nastiest. Nothing to cut and nothing worth blowing, so the
		// only way past is through a gap that might not let go -- and being forced into the verb
		// with the near-miss attached is the point of it existing.
		FObstructionVerbOption Squeeze;
		Squeeze.bAllowed = true;
		Squeeze.DurationSeconds = 9.0f;
		Squeeze.NoiseLoudness = 0.2f;
		Squeeze.NearEntrapmentChance = 0.6f;
		Options.Add(EObstructionVerb::Squeeze, Squeeze);

		bBypassable = false;
		DisplayName = NSLOCTEXT("Obstructions", "JammedHatch", "Jammed hatch");
		return;
	}

	// Unknown preset. Left with no options at all rather than given a default set: a barrier that
	// silently permits everything because its name was misspelled is worse than one that permits
	// nothing and says so.
	bBypassable = true;
	DisplayName = NSLOCTEXT("Obstructions", "UnknownPreset", "Blocked passage");
}


// --- choosing a verb ---------------------------------------------------------------------------

bool AObstructionBarrier::SelectVerb(EObstructionVerb Verb, const APawn* Player)
{
	// Refuses rather than arming a failure. A barrier set to a verb it cannot perform would show a
	// prompt that does nothing when pressed, which reads as a broken control rather than as a
	// closed option.
	if (GetRefusal(Verb, Player) != EObstructionRefusal::None)
	{
		return false;
	}
	SelectedVerb = Verb;
	return true;
}

EObstructionVerb AObstructionBarrier::CycleVerb(const APawn* Player)
{
	const TArray<EObstructionVerb> Available = GetAvailableVerbs(Player);
	if (Available.Num() == 0)
	{
		return SelectedVerb;
	}

	// Wraps through what is actually available, so a player at a welded bulkhead never lands on
	// "squeeze" and presses a key that does nothing. Starting from the current selection means
	// cycling is stable: the same press order always produces the same sequence.
	const int32 Current = Available.IndexOfByKey(SelectedVerb);
	const int32 Next = (Current == INDEX_NONE) ? 0 : (Current + 1) % Available.Num();
	SelectedVerb = Available[Next];
	return SelectedVerb;
}

// --- IInteractable -----------------------------------------------------------------------------

void AObstructionBarrier::OnInteract_Implementation(APawn* InteractingPawn)
{
	if (!HasAuthority() || !InteractingPawn || bCleared)
	{
		return;
	}

	// If the barrier is sitting on a verb this pawn cannot use -- gear worn out since it was last
	// chosen, or nothing chosen yet -- move to one they can before starting. Silently starting
	// nothing would look like a dead interaction.
	if (!CanResolveWith(SelectedVerb, InteractingPawn))
	{
		CycleVerb(InteractingPawn);
		if (!CanResolveWith(SelectedVerb, InteractingPawn))
		{
			return;
		}
	}

	if (UPlayerActivityComponent* Activity =
		InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
	{
		// Called directly rather than through IPlayerActivitySource::Execute_. Going through the
		// interface thunk from inside the class returned a default-constructed definition -- every
		// field at its struct default, so every verb would have started the same three-second
		// generic activity. A test caught it, and it would have been very hard to see in game:
		// the prompt appears, a bar fills, the obstruction clears, and only the type and the noise
		// are silently wrong.
		//
		// There is no reason to dispatch dynamically to ourselves anyway.
		Activity->StartActivity(this, GetActivityDefinition_Implementation(InteractingPawn));
	}
}

// --- IPlayerActivitySource ---------------------------------------------------------------------

FPlayerActivityDefinition AObstructionBarrier::GetActivityDefinition_Implementation(APawn* Player) const
{
	FPlayerActivityDefinition Definition;

	const FObstructionVerbOption* Option = Options.Find(SelectedVerb);
	const float Duration = Option ? Option->DurationSeconds : 6.0f;
	const float Loudness = Option ? Option->NoiseLoudness : 0.4f;

	Definition.DurationSeconds = Duration;
	Definition.WorkNoiseLoudness = Loudness;
	Definition.MaxRange = 260.0f;
	Definition.bLockMovement = true;

	switch (SelectedVerb)
	{
	case EObstructionVerb::Cut:
		// A real welding activity, and the reason this is worth routing through the activity system
		// at all. Welding is a tool-path mechanic that can be failed, and a failed welding activity
		// already spends gear condition and rolls for a burn -- so cutting through an obstruction
		// carries the same risk as any other weld, through the same code, with no special case.
		Definition.Type = EPlayerActivityType::Welding;
		Definition.Mechanic = EActivityMechanic::ToolPath;
		Definition.ToolPathTolerance = 0.22f;
		Definition.DisplayName = NSLOCTEXT("Obstructions", "CutThrough", "Cut through");
		break;

	case EObstructionVerb::Breach:
		// Setting charges: an ordered assembly, and failable. Getting the sequence wrong on
		// something you are about to detonate should not be free.
		Definition.Type = EPlayerActivityType::ComponentReplacement;
		Definition.Mechanic = EActivityMechanic::OrderedAssembly;
		Definition.PuzzleSteps = 4;
		Definition.AllowedMistakes = 2;
		Definition.DisplayName = NSLOCTEXT("Obstructions", "SetCharges", "Set charges");
		break;

	case EObstructionVerb::Squeeze:
		// Timed, and deliberately not failable. You either get through or you nearly do not, and
		// the "nearly" is rolled on completion rather than being a failure state -- a squeeze that
		// can be lost is a trap, and this is meant to be a corridor.
		Definition.Type = EPlayerActivityType::FieldProcedure;
		Definition.Mechanic = EActivityMechanic::Timed;
		Definition.DisplayName = NSLOCTEXT("Obstructions", "SqueezeThrough", "Squeeze through");
		// Seen from outside: a body working through a gap is the shot, not a visor full of wall.
		Definition.bThirdPersonView = true;
		break;
	}

	// Nothing here is Bloom-sensitive. Bloom interference models a growth fouling shipboard
	// systems; it has no bearing on whether a person can fit through a gap.
	Definition.bBloomSensitive = false;

	return Definition;
}

bool AObstructionBarrier::CanStartActivity_Implementation(APawn* Player) const
{
	return CanResolveWith(SelectedVerb, Player);
}

void AObstructionBarrier::OnActivityCompleted_Implementation(APawn* Player)
{
	// Resolution happens here rather than on interaction, so the costs land when the work finishes
	// rather than when it starts. A player who is interrupted mid-cut has spent time and nothing
	// else, which is the correct outcome and the reason the activity system is involved at all.
	ResolveWith(SelectedVerb, Player);
}


FText AObstructionBarrier::GetVerbName(EObstructionVerb Verb)
{
	switch (Verb)
	{
	case EObstructionVerb::Breach:  return NSLOCTEXT("Obstructions", "VerbBreach", "Set charges");
	case EObstructionVerb::Cut:     return NSLOCTEXT("Obstructions", "VerbCut", "Cut through");
	case EObstructionVerb::Squeeze: return NSLOCTEXT("Obstructions", "VerbSqueeze", "Squeeze through");
	}
	return FText::GetEmpty();
}

FText AObstructionBarrier::GetInteractionPrompt_Implementation(APawn* Viewer) const
{
	if (bCleared)
	{
		return FText::GetEmpty();
	}

	const TArray<EObstructionVerb> Available = GetAvailableVerbs(Viewer);
	if (Available.Num() == 0)
	{
		// Says what is wrong rather than nothing at all. A player standing at an obstruction with
		// no usable verb needs to know it is their gear and not a bug -- and this is the one case
		// where an empty prompt would be actively misleading, because the thing plainly is a door.
		return FText::Format(
			NSLOCTEXT("Obstructions", "PromptNoVerb", "{0} \u2014 no way through with what you are carrying"),
			DisplayName);
	}

	// Names the selected verb first, then what else is possible. Listing the alternatives is the
	// entire point: an obstruction with three ways past it that only ever shows one is a locked
	// door with a progress bar, and the choice between blowing, cutting and squeezing is the
	// feature.
	FString Others;
	for (EObstructionVerb Verb : Available)
	{
		if (Verb == SelectedVerb)
		{
			continue;
		}
		if (!Others.IsEmpty())
		{
			Others += TEXT(", ");
		}
		Others += GetVerbName(Verb).ToString().ToLower();
	}

	const FText Chosen = GetVerbName(
		Available.Contains(SelectedVerb) ? SelectedVerb : Available[0]);

	if (Others.IsEmpty())
	{
		return FText::Format(NSLOCTEXT("Obstructions", "PromptSingle", "{0}  \u2014  {1}"),
			Chosen, DisplayName);
	}

	return FText::Format(NSLOCTEXT("Obstructions", "PromptWithAlternatives", "{0}  \u2014  {1}  (also: {2})"),
		Chosen, DisplayName, FText::FromString(Others));
}
