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
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "Player/SurvivalPlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace GinnungagapTestMap
{
	/** The demo map, or whatever -GinnungagapMap=<package path> names: the same tests serve every ship. */
	inline FString Path()
	{
		FString Override;
		if (FParse::Value(FCommandLine::Get(), TEXT("GinnungagapMap="), Override) && !Override.IsEmpty())
		{
			return Override;
		}
		return TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck");
	}
}

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
			const FVector Spot(Feet.X, Feet.Y, Target.Z + 96.0f);
			FCollisionQueryParams Params(SCENE_QUERY_STAT(StationPath), false, Pawn);
			Params.AddIgnoredActor(Station);
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
		Index = 0; Phase = 0; PhaseAt = -1.0;
		StartedAt = Now;
		if (Pawn->GetPlayerActivityComponent() == nullptr || Pawn->GetInteractionComponent() == nullptr)
		{
			return Fail(TEXT("The player character has no activity or interaction component"));
		}
		return false;
	}
	if (Now - StartedAt > 180.0)
	{
		return Fail(FString::Printf(TEXT("Playing the stations took more than 180s (stuck at %s, phase %d)"), *Steps[Index].Name, Phase));
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
			FVector Origin, Extent;
			Station->GetActorBounds(false, Origin, Extent, false);
			if (AController* C = Pawn->GetController())
			{
				FVector Eye; FRotator EyeRot;
				Pawn->GetActorEyesViewPoint(Eye, EyeRot);
				C->SetControlRotation((Origin - Eye).Rotation());
			}
			if (Now - PhaseAt < 1.2) return false;
			const AActor* Focused = Interaction->GetFocusedInteractable();
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
		else if (Index == Steps.Num() - 1)
		{
			Test->TestFalse(TEXT("After the CIC console the chain is complete: ReachCIC is no longer active"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_ReachCIC")));
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
