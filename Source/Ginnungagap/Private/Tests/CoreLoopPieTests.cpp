#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

#include "Bloom/BloomDirector.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "StarSystem/JumpSequenceSubsystem.h"

/**
 * The two loops the game is built on, exercised in a real play session.
 *
 * Both subsystems are game-instance scoped, so they only exist once something is actually playing.
 * That is the whole reason these are PIE tests rather than isolated ones: the object graph they
 * depend on cannot be assembled by hand, and the failures worth catching are the ones that only
 * appear when the real one exists.
 *
 * These drive the systems through their public API rather than simulating play. Waiting on a real
 * thirty-second jump countdown would make the suite unusable, and the countdown's duration is not
 * what breaks -- the state machine is.
 */

namespace CoreLoopPie
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

	UGameInstance* FindPieGameInstance()
	{
		UWorld* World = FindPieWorld();
		return World ? World->GetGameInstance() : nullptr;
	}
}

/** Waits for a play session with a game instance, or fails on its own deadline. */
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForGameInstance, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForGameInstance::Update()
{
	if (CoreLoopPie::FindPieGameInstance())
	{
		return true;
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(TEXT("No PIE game instance existed before the deadline"));
		return true;
	}

	return false;
}

// ---------------------------------------------------------------------------------------------
// Bloom lifecycle
// ---------------------------------------------------------------------------------------------

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertBloomLifecycle, FAutomationTestBase*, Test);

bool FAssertBloomLifecycle::Update()
{
	UWorld* World = CoreLoopPie::FindPieWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (!GameInstance)
	{
		Test->AddError(TEXT("PIE game instance vanished before the Bloom assertions ran"));
		return true;
	}

	UBloomDirector* Bloom = GameInstance->GetSubsystem<UBloomDirector>();
	if (!Bloom)
	{
		Test->AddError(TEXT("No UBloomDirector on the PIE game instance"));
		return true;
	}

	// Start from a known state. Whatever the map's own actors did on BeginPlay is not this test's
	// subject, and inheriting it would make the run order matter.
	Bloom->ForceResetBloom();
	Test->TestEqual(TEXT("A reset Bloom is latent"), Bloom->GetCurrentStage(), EBloomStage::Latent);
	Test->TestFalse(TEXT("A latent Bloom is not a present threat"), Bloom->IsPresentThreat());
	Test->TestTrue(TEXT("A reset Bloom counts as eradicated"), Bloom->IsFullyEradicated());

	// Every stage must be reachable and reported. A stage that advances internally but does not
	// surface would leave the crew with no symptom to read, which is the one thing the design says
	// must never happen.
	const TArray<EBloomStage> Ladder = {
		EBloomStage::Colony, EBloomStage::Swarm, EBloomStage::Puppeteer,
		EBloomStage::Infector, EBloomStage::Manifestation
	};

	for (EBloomStage Expected : Ladder)
	{
		Bloom->AdvanceStage();
		Test->TestEqual(TEXT("AdvanceStage reaches the next stage"), Bloom->GetCurrentStage(), Expected);
		Test->TestTrue(TEXT("Any stage past latent is a present threat"), Bloom->IsPresentThreat());
	}

	// The ladder has a top. Advancing past it must clamp rather than wrap back to latent, which
	// would silently hand the crew a won game.
	Bloom->AdvanceStage();
	Test->TestEqual(TEXT("Advancing past the last stage clamps"),
		Bloom->GetCurrentStage(), EBloomStage::Manifestation);

	// Infection and corruption, against throwaway actors in the live world.
	AActor* Host = World->SpawnActor<AActor>();
	AActor* System = World->SpawnActor<AActor>();
	Test->TestNotNull(TEXT("Spawned a host actor"), Host);
	Test->TestNotNull(TEXT("Spawned a system actor"), System);

	if (Host && System)
	{
		const int32 HostsBefore = Bloom->GetInfectedHostCount();
		if (Bloom->TryInfectHost(Host))
		{
			Test->TestTrue(TEXT("A successful infection raises the host count"),
				Bloom->GetInfectedHostCount() > HostsBefore);

			// Infecting the same host twice must not double-count, or the stage thresholds that
			// read this number drift away from how many bodies are actually involved.
			const int32 HostsAfterFirst = Bloom->GetInfectedHostCount();
			Bloom->TryInfectHost(Host);
			Test->TestEqual(TEXT("Re-infecting the same host does not double-count"),
				Bloom->GetInfectedHostCount(), HostsAfterFirst);
		}

		const int32 SystemsBefore = Bloom->GetCorruptedSystemCount();
		if (Bloom->TryCorruptSystem(System))
		{
			Test->TestTrue(TEXT("A successful corruption raises the system count"),
				Bloom->GetCorruptedSystemCount() > SystemsBefore);

			// Purging is the crew's counter-play, so it has to actually reverse.
			Bloom->NotifySystemPurged(System);
			Test->TestEqual(TEXT("Purging a system releases it"),
				Bloom->GetCorruptedSystemCount(), SystemsBefore);
		}

		Host->Destroy();
		System->Destroy();
	}

	// Restore is what the save path uses. A stage that cannot be put back is a stage that cannot
	// survive a reload.
	Bloom->RestoreStage(EBloomStage::Swarm);
	Test->TestEqual(TEXT("A restored stage is the stage restored"),
		Bloom->GetCurrentStage(), EBloomStage::Swarm);

	// Leave the world as it was found, so nothing downstream inherits a mid-game Bloom.
	Bloom->ForceResetBloom();
	Test->TestTrue(TEXT("The Bloom resets cleanly afterwards"), Bloom->IsFullyEradicated());

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapBloomLifecyclePieTest,
	"Ginnungagap.Smoke.BloomLifecycle",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapBloomLifecyclePieTest::RunTest(const FString& Parameters)
{
	const double Deadline = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForGameInstance(this, Deadline));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertBloomLifecycle(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

// ---------------------------------------------------------------------------------------------
// Jump loop
// ---------------------------------------------------------------------------------------------

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertJumpLoop, FAutomationTestBase*, Test);

bool FAssertJumpLoop::Update()
{
	UGameInstance* GameInstance = CoreLoopPie::FindPieGameInstance();
	if (!GameInstance)
	{
		Test->AddError(TEXT("PIE game instance vanished before the jump assertions ran"));
		return true;
	}

	UJumpSequenceSubsystem* Jump = GameInstance->GetSubsystem<UJumpSequenceSubsystem>();
	if (!Jump)
	{
		Test->AddError(TEXT("No UJumpSequenceSubsystem on the PIE game instance"));
		return true;
	}

	Test->TestEqual(TEXT("A run begins cruising"), Jump->CurrentPhase, EJumpPhase::Cruising);

	// Candidates. The six-destination ceiling is a design rule, not an implementation detail: the
	// choice is meant to be surveyable, and a system that offered twelve would be a different game.
	Jump->GenerateJumpCandidates();
	Test->TestTrue(TEXT("Generating produces at least one candidate"), Jump->CurrentCandidates.Num() > 0);
	Test->TestTrue(TEXT("Candidates never exceed the maximum"),
		Jump->CurrentCandidates.Num() <= Jump->MaxCandidates);

	// Selection has to reject nonsense rather than index out of bounds. A console is a place
	// players mash inputs.
	Test->TestFalse(TEXT("A negative candidate index is refused"), Jump->SelectJumpCandidate(-1));
	Test->TestFalse(TEXT("An out-of-range candidate index is refused"),
		Jump->SelectJumpCandidate(Jump->CurrentCandidates.Num() + 5));
	Test->TestTrue(TEXT("A valid candidate is accepted"), Jump->SelectJumpCandidate(0));
	Test->TestEqual(TEXT("Selecting records which candidate was chosen"), Jump->SelectedCandidateIndex, 0);

	// The jump is gated on mission objectives: you cannot leave a system until you have done what
	// you came for. That rule is the reason a run has stakes at all, so it is asserted in both
	// directions rather than worked around.
	UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>();
	Test->TestNotNull(TEXT("The mission subsystem exists"), Missions);

	if (Missions && !Missions->CanBeginJump())
	{
		// A blocking objective is outstanding, so the countdown must refuse -- and refuse without
		// half-entering the warning phase, which would strand the run between states.
		Test->TestFalse(TEXT("The jump is refused while an objective blocks it"),
			Jump->BeginJumpWarningCountdown());
		Test->TestEqual(TEXT("A refused jump leaves the ship cruising"),
			Jump->CurrentPhase, EJumpPhase::Cruising);

		// Resolve every objective that blocks, and only those: an optional objective must never
		// have been holding the ship in the first place.
		for (const FMissionObjectiveRuntime& Objective : Missions->GetAllObjectives(true))
		{
			const FMissionObjectiveDefinition& Definition = Objective.Definition;
			if (!Definition.bOptional && Definition.bBlocksJumpWhileUnresolved && !Objective.IsResolved())
			{
				Missions->CompleteObjective(Definition.ObjectiveId);
			}
		}

		Test->TestTrue(TEXT("Clearing the blocking objectives opens the jump"), Missions->CanBeginJump());
	}

	// The countdown is the cryo deadline, which is the run's central pressure. It must start, and
	// it must start with time on it.
	Test->TestTrue(TEXT("The warning countdown begins"), Jump->BeginJumpWarningCountdown());
	Test->TestEqual(TEXT("Beginning the countdown enters the warning phase"),
		Jump->CurrentPhase, EJumpPhase::WarningCountdown);
	Test->TestTrue(TEXT("The countdown starts with time remaining"), Jump->WarningSecondsRemaining > 0.0f);

	const int32 JumpsBefore = Jump->JumpsCompleted;

	// ExecuteJump resolves the whole transit synchronously and calls CompleteArrival itself, so
	// Jumping is a phase the state machine passes through rather than one it rests in. Asserting
	// the destination rather than the transient avoids a test that only passes by accident of
	// timing.
	Jump->ExecuteJump();
	Test->TestTrue(TEXT("Executing a jump lands the ship in arrival or back at cruising"),
		Jump->CurrentPhase == EJumpPhase::Arrival || Jump->CurrentPhase == EJumpPhase::Cruising);

	// Exactly one, not two: ExecuteJump increments and then calls CompleteArrival, so a second
	// increment hidden in the arrival path would quietly halve the distance to the destination.
	Test->TestEqual(TEXT("One jump counts exactly once"), Jump->JumpsCompleted, JumpsBefore + 1);

	// The destination is a finite distance away, so the counter has to mean something.
	Test->TestFalse(TEXT("One jump in is not the final jump"), Jump->IsFinalJump());
	Test->TestTrue(TEXT("The run has a destination to reach"), Jump->TotalJumpsToDestination > 0);

	// A null character is not outside the ship. This is asked during the jump to decide a fatal
	// outcome, so it must not treat "no data" as "in vacuum".
	Test->TestFalse(TEXT("A null character is not treated as outside the ship"),
		Jump->IsCharacterOutsideShip(nullptr));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapJumpLoopPieTest,
	"Ginnungagap.Smoke.JumpLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapJumpLoopPieTest::RunTest(const FString& Parameters)
{
	const double Deadline = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForGameInstance(this, Deadline));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertJumpLoop(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
