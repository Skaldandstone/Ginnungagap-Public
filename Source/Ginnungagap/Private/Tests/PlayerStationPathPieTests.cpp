#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/OverlapResult.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"

#include "Activities/ActivityStation.h"
#include "Activities/PlayerActivityComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Interaction/InteractionComponent.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "Ship/BulkheadDoor.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/InventoryItemPickup.h"
#include "Obstructions/ObstructionBarrier.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "Player/SurvivalPlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

#include "Tests/GinnungagapTestMap.h"

/**
 * The demo played the way a person plays it: stand in front of each station on the objective
 * chain, look at it, press Interact, and answer the prompts the activity puts up until it
 * finishes. The walkthrough test proves the chain and the route by firing each station's
 * completion directly; this proves the keyboard path into each one -- the eye-line focus trace,
 * the Interact binding, StartActivity's range check, the input sequence or the timed fill --
 * which is what James will actually be doing with the E key. Movement between stations is a
 * teleport; the route is the walkthrough's business.
 */
namespace StationPath
{
	UWorld* FindPieWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}

	struct FStep
	{
		FString Name;
		TFunction<AActor*(UWorld*)> Find;
		FName ObjectiveActiveBefore;   // the chain's objective this station belongs to (NAME_None: no check)
		FName ObjectiveActiveAfter;    // what should be active once it completes (NAME_None: chain over)
	};

	template <typename T> AActor* First(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It) { return *It; }
		return nullptr;
	}

	TArray<FStep> Steps()
	{
		return {
			{ TEXT("suit rack"),          &First<AQuickDemoSuitStation>,       TEXT("QD_SuitUp"),        TEXT("QD_ReachWorkshop") },
			{ TEXT("workshop bench"),     &First<AQuickDemoWorkshopBench>,     TEXT("QD_ReachWorkshop"), TEXT("QD_RestorePower") },
			{ TEXT("suit repair bench"),  &First<AQuickDemoSuitRepairBench>,   NAME_None,                NAME_None },
			{ TEXT("power station"),      &First<AQuickDemoPowerStation>,      TEXT("QD_RestorePower"),  TEXT("QD_SealBreach") },
			{ TEXT("breach station"),     &First<AQuickDemoBreachStation>,     TEXT("QD_SealBreach"),    TEXT("QD_ReachCIC") },
			{ TEXT("locked CIC door"),    [](UWorld* W) -> AActor* { for (TActorIterator<ABulkheadDoor> It(W); It; ++It) { if (It->ActorHasTag(TEXT("QuickDemoCICDoor"))) return *It; } return nullptr; }, NAME_None, NAME_None },
			{ TEXT("CIC access station"), &First<AQuickDemoCICAccessStation>,  TEXT("QD_ReachCIC"),      TEXT("QD_ReachCIC") },
			{ TEXT("CIC console"),        &First<AQuickDemoCICConsole>,        TEXT("QD_ReachCIC"),      NAME_None },
		};
	}

	/** A spot 150 cm off the station on whichever side has room, facing it. */
	bool StandBefore(UWorld* World, ACoopSurvivalCharacter* Pawn, AActor* Station)
	{
		const FVector Target = Station->GetActorLocation();
		const FVector Forward = Station->GetActorForwardVector().GetSafeNormal2D();
		for (const float Distance : { 150.0f, 115.0f })
		for (const FVector& Dir : { Forward, -Forward, FVector(Forward.Y, -Forward.X, 0.0f), FVector(-Forward.Y, Forward.X, 0.0f), FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) })
		{
			const FVector Feet = Target + Dir * Distance;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(StationPath), false, Pawn);
			Params.AddIgnoredActor(Station);
			// Stand on the floor under the spot, not at the station's own height: stations sit 90 cm
			// up a wall and doors 20 cm under the deck, and a capsule sunk into the floor is "blocked".
			float FloorZ = Target.Z;
			{
				FHitResult Floor;
				// From just above the target: a barrier's origin is 160 up, and 200 above that is the
				// deck's ceiling, whose top the trace would take for a floor.
				if (World->LineTraceSingleByChannel(Floor, FVector(Feet.X, Feet.Y, Target.Z + 60.0f), FVector(Feet.X, Feet.Y, Target.Z - 400.0f), ECC_Visibility, Params))
				{
					FloorZ = Floor.ImpactPoint.Z;
				}
			}
			const FVector Spot(Feet.X, Feet.Y, FloorZ + 96.0f + 2.0f);
			TArray<FOverlapResult> Overlaps;
			World->OverlapMultiByChannel(Overlaps, Spot, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(40.0f, 94.0f), Params);
			bool bBlocked = false;
			for (const FOverlapResult& O : Overlaps)
			{
				if (O.bBlockingHit)
				{
					bBlocked = true;
					UE_LOG(LogTemp, Display, TEXT("STATIONPATH spot %s at %s blocked by %s.%s"), *Station->GetName(), *Spot.ToCompactString(),
						O.GetActor() ? *O.GetActor()->GetName() : TEXT("?"), O.GetComponent() ? *O.GetComponent()->GetName() : TEXT("?"));
					break;
				}
			}
			if (!bBlocked)
			{
				{
					const UPrimitiveComponent* OldBase = Pawn->GetMovementBase();
					UE_LOG(LogTemp, Display, TEXT("STATIONPATH before teleport to %s: pawn at %s vel %s base %s.%s"), *Station->GetName(),
						*Pawn->GetActorLocation().ToCompactString(), *Pawn->GetVelocity().ToCompactString(),
						OldBase && OldBase->GetOwner() ? *OldBase->GetOwner()->GetName() : TEXT("none"), OldBase ? *OldBase->GetName() : TEXT("-"));
				}
				// Off whatever it stood on first: a moving base (the pod's lid, the sleeper's
				// platform) imparts its velocity when the pawn leaves it, and a teleport is leaving.
				Pawn->SetBase(static_cast<UPrimitiveComponent*>(nullptr), NAME_None);
				Pawn->SetActorLocation(Spot, false, nullptr, ETeleportType::TeleportPhysics);
				if (UCharacterMovementComponent* Move = Pawn->GetCharacterMovement())
				{
					Move->StopMovementImmediately();
					Move->SetMovementMode(MOVE_Walking);
				}
				const FRotator Face = (-Dir).Rotation();
				Pawn->SetActorRotation(FRotator(0.0f, Face.Yaw, 0.0f));
				if (AController* C = Pawn->GetController())
				{
					// Down a little: the stations' interactable bodies sit below eye height.
					C->SetControlRotation(FRotator(-18.0f, Face.Yaw, 0.0f));
				}
				return true;
			}
		}
		return false;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FPlayEveryStation, FAutomationTestBase*, Test);

bool FPlayEveryStation::Update()
{
	static TArray<StationPath::FStep> Steps;
	static int32 Index = -1;
	static int32 Phase = 0;          // 0 place, 1 wait for focus, 2 press, 3 answer prompts, 4 verify
	static double PhaseAt = -1.0;
	static double StartedAt = 0.0;
	static int32 Presses = 0;
	static bool bSawLockedCICDoor = false;

	UWorld* World = StationPath::FindPieWorld();
	ASurvivalPlayerController* PC = World ? Cast<ASurvivalPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
	ACoopSurvivalCharacter* Pawn = PC ? Cast<ACoopSurvivalCharacter>(PC->GetPawn()) : nullptr;
	if (!World || !PC || !Pawn)
	{
		return false;
	}
	const double Now = World->GetTimeSeconds();
	auto Reset = [&]() { Steps.Reset(); Index = -1; Phase = 0; PhaseAt = -1.0; Presses = 0; };
	auto Fail = [&](const FString& Why) { Test->AddError(Why); Reset(); return true; };

	if (Index < 0)
	{
		for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It) { It->Skip(); }
		Steps = StationPath::Steps();
		// The ship's obstructions, worked the same way (interact starts the selected verb's
		// activity); afterwards each must be cleared. They come before the side stations so the
		// climb's barrier is met in chain order.
		for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
		{
			TWeakObjectPtr<AActor> Barrier = *It;
			Steps.Add({ FString::Printf(TEXT("barrier %s"), *It->GetName()), [Barrier](UWorld*) -> AActor* { return Barrier.Get(); }, NAME_None, NAME_None });
		}
		// One supply off the deck, taken with the same E press: a pickup is not an activity, so
		// its step ends when the actor is gone and the item is in the inventory.
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("CorvetteSupply")) || !Cast<AInventoryItemPickup>(*It)) continue;
			TWeakObjectPtr<AActor> Supply = *It;
			Steps.Add({ FString::Printf(TEXT("supply %s"), *It->GetName()), [Supply](UWorld*) -> AActor* { return Supply.Get(); }, NAME_None, NAME_None });
			break;
		}
		// The optional work off the chain (the corvette's CorvetteSideStation actors): each is
		// played the same way, with no objective expectations.
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("CorvetteSideStation"))) continue;
			TWeakObjectPtr<AActor> Side = *It;
			Steps.Add({ FString::Printf(TEXT("side station %s"), *It->GetName()), [Side](UWorld*) -> AActor* { return Side.Get(); }, NAME_None, NAME_None });
		}
		// The welded door is worked the same way (an activity source rather than a station); once
		// its weld is cut it must be passable.
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("CorvetteWeldedDoor"))) continue;
			TWeakObjectPtr<AActor> Door = *It;
			Steps.Add({ TEXT("welded door"), [Door](UWorld*) -> AActor* { return Door.Get(); }, NAME_None, NAME_None });
		}
		Index = 0; Phase = 0; PhaseAt = -1.0;
		StartedAt = Now;
		if (Pawn->GetPlayerActivityComponent() == nullptr || Pawn->GetInteractionComponent() == nullptr)
		{
			return Fail(TEXT("The player character has no activity or interaction component"));
		}
		return false;
	}
	if (Now - StartedAt > 300.0)
	{
		return Fail(FString::Printf(TEXT("Playing the stations took more than 300s (stuck at %s, phase %d)"), *Steps[Index].Name, Phase));
	}
	if (Index >= Steps.Num())
	{
		Reset();
		return true;
	}

	const StationPath::FStep& Step = Steps[Index];
	UPlayerActivityComponent* Activity = Pawn->GetPlayerActivityComponent();
	UInteractionComponent* Interaction = Pawn->GetInteractionComponent();
	AActor* Station = Step.Find(World);
	if (!Station && Step.Name.StartsWith(TEXT("supply ")) && Phase >= 3)
	{
		// Taken: the pickup destroyed itself. The item must have landed in the inventory.
		const UInventoryComponent* Inventory = Pawn->GetInventoryComponent();
		Test->TestTrue(FString::Printf(TEXT("After taking %s the inventory holds something"), *Step.Name), Inventory && Inventory->GetUsedSlotCount() > 0);
		Test->AddInfo(FString::Printf(TEXT("STATIONPATH %s: taken, %.1fs"), *Step.Name, Now - StartedAt));
		++Index; Phase = 0; PhaseAt = -1.0; Presses = 0;
		return false;
	}
	if (!Test->TestNotNull(FString::Printf(TEXT("The demo map has the %s"), *Step.Name), Station))
	{
		return Fail(TEXT("station missing"));
	}

	switch (Phase)
	{
	case 0:
		if (!Step.ObjectiveActiveBefore.IsNone())
		{
			Test->TestTrue(FString::Printf(TEXT("Before the %s, %s is the active objective"), *Step.Name, *Step.ObjectiveActiveBefore.ToString()),
				AQuickDemoMissionDirector::IsObjectiveActive(World, Step.ObjectiveActiveBefore));
		}
		if (!StationPath::StandBefore(World, Pawn, Station))
		{
			return Fail(FString::Printf(TEXT("No clear spot to stand at the %s"), *Step.Name));
		}
		Phase = 1; PhaseAt = Now;
		return false;

	case 1:
		// The focus trace runs on the component's tick; give it a moment, then check it found the station.
		if (Now - PhaseAt < 0.5)
		{
			TArray<FOverlapResult> Touching;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(StationPathTouch), false, Pawn);
			World->OverlapMultiByChannel(Touching, Pawn->GetActorLocation(), FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(42.0f, 96.0f), Params);
			FString Names;
			for (const FOverlapResult& O : Touching) { if (O.bBlockingHit && O.GetActor()) { Names += O.GetActor()->GetName() + TEXT("/") + (O.GetComponent() ? O.GetComponent()->GetName() : TEXT("?")) + TEXT(" "); } }
			if (Now - PhaseAt < 0.1)
			{
				if (UCharacterMovementComponent* Move = Pawn->GetCharacterMovement()) { Move->StopMovementImmediately(); }
			}
			static int32 SettleFrame = 0;
			if ((SettleFrame++ % 8) == 0)
			{
				UE_LOG(LogTemp, Display, TEXT("STATIONPATH settling %s t=%.2f pawn %s vel %s touching %s"), *Step.Name, Now - PhaseAt,
					*Pawn->GetActorLocation().ToCompactString(), *Pawn->GetVelocity().ToCompactString(), *Names);
			}
			return false;
		}
		if (Interaction->GetFocusedInteractable() != Station)
		{
			// Not every station is the thing the eye-line hits first (a bench's prop can be); aim at its
			// bounds centre once, then judge.
			// Colliding components only: a door's hidden, collision-free visual mesh sits at the world
			// origin and would drag the bounds centre (and the aim) into the floor.
			FVector Origin, Extent;
			Station->GetActorBounds(true, Origin, Extent, false);
			if (Extent.IsNearlyZero()) { Station->GetActorBounds(false, Origin, Extent, false); }
			if (Now - PhaseAt >= 1.2)
			{
				UE_LOG(LogTemp, Display, TEXT("STATIONPATH aim at %s: bounds origin %s extent %s (actor at %s)"), *Step.Name, *Origin.ToCompactString(), *Extent.ToCompactString(), *Station->GetActorLocation().ToCompactString());
			}
			if (AController* C = Pawn->GetController())
			{
				FVector Eye; FRotator EyeRot;
				Pawn->GetActorEyesViewPoint(Eye, EyeRot);
				C->SetControlRotation((Origin - Eye).Rotation());
			}
			if (Now - PhaseAt < 1.2) return false;
			const AActor* Focused = Interaction->GetFocusedInteractable();
			{
				// What the eye-line actually hits, for the log.
				FVector Eye; FRotator EyeRot;
				Pawn->GetActorEyesViewPoint(Eye, EyeRot);
				FHitResult Hit;
				FCollisionQueryParams TraceParams(SCENE_QUERY_STAT(StationPathEye), false, Pawn);
				const bool bHit = World->LineTraceSingleByChannel(Hit, Eye, Eye + EyeRot.Vector() * 250.0f, ECC_Visibility, TraceParams);
				UE_LOG(LogTemp, Display, TEXT("STATIONPATH eye-line at %s from %s rot %s hits %s.%s at %.0f cm"), *Step.Name, *Eye.ToCompactString(), *EyeRot.ToCompactString(),
					bHit && Hit.GetActor() ? *Hit.GetActor()->GetName() : TEXT("nothing"), bHit && Hit.GetComponent() ? *Hit.GetComponent()->GetName() : TEXT("-"), bHit ? Hit.Distance : 0.0f);
			}
			{
				const UPrimitiveComponent* Base = Pawn->GetMovementBase();
				const UCharacterMovementComponent* Move = Pawn->GetCharacterMovement();
				UE_LOG(LogTemp, Display, TEXT("STATIONPATH after wait at %s: pawn %s base %s.%s mode %d velocity %s"), *Step.Name,
					*Pawn->GetActorLocation().ToCompactString(), Base && Base->GetOwner() ? *Base->GetOwner()->GetName() : TEXT("none"),
					Base ? *Base->GetName() : TEXT("-"), Move ? (int32)Move->MovementMode.GetValue() : -1, *Pawn->GetVelocity().ToCompactString());
			}
			Test->TestEqual(FString::Printf(TEXT("Looking at the %s puts it under the interaction prompt (focused: %s at %s; pawn at %s)"), *Step.Name,
				Focused ? *Focused->GetName() : TEXT("nothing"), Focused ? *Focused->GetActorLocation().ToCompactString() : TEXT("-"), *Pawn->GetActorLocation().ToCompactString()),
				Focused, static_cast<const AActor*>(Station));
		}
		Phase = 2; PhaseAt = Now;
		return false;

	case 2:
		PC->PressInteract();
		Presses = 1;
		Phase = 3; PhaseAt = Now;
		return false;

	case 3:
		if (Step.Name == TEXT("locked CIC door"))
		{
			// The press must do nothing: the door stays sealed and says why. Only maps that lock it
			// (the corvette) are strict; elsewhere the step just records what the door did.
			if (Now - PhaseAt < 2.6) return false;   // longer than a door cycle
			const ABulkheadDoor* Door = Cast<ABulkheadDoor>(Station);
			bSawLockedCICDoor = Door && Door->bLocked;
			if (Door && Door->bLocked)
			{
				Test->TestTrue(TEXT("A locked CIC door stays sealed after the E press"), Door->bIsSealed && !Door->IsPassable());
				const FText Prompt = IInteractable::Execute_GetInteractionPrompt(Station, Pawn);
				Test->TestTrue(FString::Printf(TEXT("The locked door's prompt says so (%s)"), *Prompt.ToString()), Prompt.ToString().Contains(TEXT("locked")));
			}
			Test->AddInfo(FString::Printf(TEXT("STATIONPATH %s: sealed %d locked %d, %.1fs"), *Step.Name, Door && Door->bIsSealed ? 1 : 0, Door && Door->bLocked ? 1 : 0, Now - StartedAt));
			++Index; Phase = 0; PhaseAt = -1.0; Presses = 0;
			return false;
		}
		if (Step.Name.StartsWith(TEXT("supply ")))
		{
			// A pickup either vanished on the press (handled above, once Find returns null) or did
			// not take it; give it a moment, then say so.
			if (Now - PhaseAt < 0.6) return false;
			return Fail(FString::Printf(TEXT("%s was not taken by the E press (still at %s)"), *Step.Name, *Station->GetActorLocation().ToCompactString()));
		}
		if (Activity->IsActivityActive())
		{
			// Answer whatever the prompt asks for, at a human-ish cadence. Primary goes through the
			// same Interact handler a player's E key does; the others through their bound actions.
			if (Now - PhaseAt >= 0.25)
			{
				const EActivityInput Wanted = Activity->GetSnapshot().ExpectedInput;
				if (Wanted == EActivityInput::Primary) { PC->PressInteract(); }
				else { Activity->SubmitInput(Wanted); }
				++Presses;
				PhaseAt = Now;
			}
			return false;
		}
		// Not active: either it finished, or Interact never started it (give the start a moment).
		if (Presses == 1 && Now - PhaseAt < 0.6) return false;
		Phase = 4; PhaseAt = Now;
		return false;

	case 4:
	{
		if (Now - PhaseAt < 0.4) return false;   // completion side effects (objective, lights) are same-tick, but be generous
		const FPlayerActivitySnapshot& Snap = Activity->GetSnapshot();
		Test->TestTrue(FString::Printf(TEXT("The %s was completed from the keyboard (%d presses, state %d)"), *Step.Name, Presses, static_cast<int32>(Snap.State)),
			Snap.State == EPlayerActivityState::Completed);
		if (!Step.ObjectiveActiveAfter.IsNone())
		{
			Test->TestTrue(FString::Printf(TEXT("After the %s, %s is the active objective"), *Step.Name, *Step.ObjectiveActiveAfter.ToString()),
				AQuickDemoMissionDirector::IsObjectiveActive(World, Step.ObjectiveActiveAfter));
		}
		else if (Step.Name == TEXT("CIC console"))
		{
			Test->TestFalse(TEXT("After the CIC console the chain is complete: ReachCIC is no longer active"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_ReachCIC")));
		}
		if (Step.Name.StartsWith(TEXT("barrier ")))
		{
			const AObstructionBarrier* Barrier = Cast<AObstructionBarrier>(Station);
			Test->TestTrue(FString::Printf(TEXT("After working it, %s is cleared"), *Step.Name), Barrier && Barrier->bCleared);
		}
		if (Step.Name == TEXT("CIC access station") && bSawLockedCICDoor)
		{
			// Only where the door was locked (the corvette): the older map's door opens on the
			// objective rather than the override, on its own timing.
			for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
			{
				if (It->ActorHasTag(TEXT("QuickDemoCICDoor")))
				{
					Test->TestTrue(TEXT("After the override the CIC door is unlocked and passable"), !It->bLocked && It->IsPassable());
				}
			}
		}
		if (Step.Name == TEXT("welded door"))
		{
			const ABulkheadDoor* Door = Cast<ABulkheadDoor>(Station);
			Test->TestTrue(TEXT("After cutting the weld, the door is passable"), Door && Door->IsPassable());
		}
		Test->AddInfo(FString::Printf(TEXT("STATIONPATH %s: %d presses, %.1fs"), *Step.Name, Presses, Now - StartedAt));
		++Index; Phase = 0; PhaseAt = -1.0; Presses = 0;
		return false;
	}
	}
	return false;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPlayerStationPathTest,
	"Ginnungagap.Smoke.PlayerPlaysEveryStation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPlayerStationPathTest::RunTest(const FString& Parameters)
{
	// A fresh run: the director restores the last checkpoint on the next tick, and a completed
	// chain from an earlier session would leave nothing to play.
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	AutomationOpenMap(GinnungagapTestMap::Path());
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FPlayEveryStation(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
