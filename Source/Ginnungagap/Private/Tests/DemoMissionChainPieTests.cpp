#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

#include "LevelSetup/QuickDemoMissionDirector.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Kismet/GameplayStatics.h"

/**
 * Whether the demo can actually be finished.
 *
 * Every other test in this suite asserts that one system behaves. None of them asks the question a
 * grant reviewer's eye asks first: can a player start this level and reach the end of it. That gap
 * is not theoretical -- this week alone the workshop objective told players to recover equipment
 * from a bench that had no mesh, the helm was invisible, and the jump console spent its life inside
 * a bulkhead. Every one of those passed its own tests.
 *
 * So this checks two things per objective, and the second is the one that keeps catching things:
 *
 *   1. The chain gates and advances in order -- an objective cannot be completed out of turn, and
 *      completing one arms the next.
 *   2. Something exists in the map that can complete it. An objective whose station was never
 *      placed is unfinishable, and no amount of correct mission logic reports that.
 */

namespace DemoChainPie
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

	/** The chain, in the order the director registers it. */
	struct FStep
	{
		const TCHAR* ObjectiveId;
		const TCHAR* CompletedByClass;   // an actor class that can complete it
		const TCHAR* Description;
	};

	const FStep Chain[] = {
		{TEXT("QD_SuitUp"),        TEXT("QuickDemoSuitStation"),   TEXT("suit up in the cryo bay")},
		{TEXT("QD_ReachWorkshop"), TEXT("QuickDemoWorkshopBench"), TEXT("draw equipment in the workshop")},
		{TEXT("QD_RestorePower"),  TEXT("QuickDemoPowerStation"),  TEXT("restore the main bus")},
		{TEXT("QD_SealBreach"),    TEXT("QuickDemoBreachStation"), TEXT("seal the Bloom breach")},
		{TEXT("QD_ReachCIC"),      TEXT("QuickDemoCICConsole"),    TEXT("bring the CIC online")},
	};

	/** The objective's real state, so a refusal reports why rather than only that it happened. */
	FString DescribeState(UWorld* World, FName Id)
	{
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		UMissionObjectiveSubsystem* Missions = GameInstance
			? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
		if (!Missions)
		{
			return TEXT("no mission subsystem");
		}

		FMissionObjectiveRuntime Runtime;
		if (!Missions->GetObjective(Id, Runtime))
		{
			return TEXT("not registered");
		}

		return FString::Printf(TEXT("state=%d progress=%.1f/%.1f"),
			static_cast<int32>(Runtime.State),
			Runtime.CurrentProgress, Runtime.Definition.TargetProgress);
	}

	int32 CountActorsOfClass(UWorld* World, const TCHAR* ClassName)
	{
		int32 Count = 0;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->GetClass()->GetName() == ClassName)
			{
				++Count;
			}
		}
		return Count;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertDemoChain, FAutomationTestBase*, Test);

bool FAssertDemoChain::Update()
{
	UWorld* World = DemoChainPie::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world for the mission chain assertions"));
		return true;
	}

	// --- every objective has something that can complete it -------------------------------------
	// Checked before any of them are completed, so a missing station is reported as itself rather
	// than as a mysteriously stuck chain three steps later.
	for (const DemoChainPie::FStep& Step : DemoChainPie::Chain)
	{
		const int32 Count = DemoChainPie::CountActorsOfClass(World, Step.CompletedByClass);
		Test->TestTrue(
			FString::Printf(TEXT("Something in the map can %s (a %s exists)"),
				Step.Description, Step.CompletedByClass),
			Count > 0);
	}

	// --- the first objective is live at the start -----------------------------------------------
	// If nothing is active the player is dropped into a ship with no instruction, which reads as a
	// broken build rather than as an open world.
	Test->TestTrue(TEXT("The chain starts with the first objective active"),
		AQuickDemoMissionDirector::IsObjectiveActive(World, FName(DemoChainPie::Chain[0].ObjectiveId)));

	// --- out-of-order completion is refused ------------------------------------------------------
	// The last objective is tried first. It must not be completable, or the prerequisite chain is
	// decorative and a player could finish the demo from the spawn point.
	const DemoChainPie::FStep& Last = DemoChainPie::Chain[UE_ARRAY_COUNT(DemoChainPie::Chain) - 1];
	Test->TestFalse(TEXT("The final objective cannot be completed out of turn"),
		AQuickDemoMissionDirector::CompleteActiveObjective(World, FName(Last.ObjectiveId)));

	// --- walk the chain --------------------------------------------------------------------------
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(DemoChainPie::Chain); ++Index)
	{
		const DemoChainPie::FStep& Step = DemoChainPie::Chain[Index];
		const FName Id(Step.ObjectiveId);

		Test->TestTrue(
			FString::Printf(TEXT("Step %d is active when its turn comes (%s)"), Index + 1, Step.ObjectiveId),
			AQuickDemoMissionDirector::IsObjectiveActive(World, Id));

		// Captured before the attempt. Read afterwards it cannot tell "was already resolved, so the
		// call was refused" apart from "was just completed by the call", which are the two answers
		// worth distinguishing.
		const FString StateBefore = DemoChainPie::DescribeState(World, Id);

		const bool bCompleted = AQuickDemoMissionDirector::CompleteActiveObjective(World, Id);
		Test->TestTrue(
			FString::Printf(TEXT("Step %d completes (%s) [before: %s]"),
				Index + 1, Step.ObjectiveId, *StateBefore),
			bCompleted);
		if (!bCompleted)
		{
			// Every later assertion would cascade from this one and bury the actual cause, so stop
			// at the first step that will not advance.
			Test->AddError(FString::Printf(
				TEXT("Chain stops at %s -- the demo cannot be finished past this point"),
				Step.ObjectiveId));
			return true;
		}

		Test->TestFalse(
			FString::Printf(TEXT("Step %d does not stay active once completed (%s)"),
				Index + 1, Step.ObjectiveId),
			AQuickDemoMissionDirector::IsObjectiveActive(World, Id));
	}

	// --- and the chain is genuinely finished -----------------------------------------------------
	for (const DemoChainPie::FStep& Step : DemoChainPie::Chain)
	{
		Test->TestFalse(
			FString::Printf(TEXT("Nothing is left active after the chain (%s)"), Step.ObjectiveId),
			AQuickDemoMissionDirector::IsObjectiveActive(World, FName(Step.ObjectiveId)));
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapDemoMissionChainPieTest,
	"Ginnungagap.Smoke.DemoMissionChain",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapDemoMissionChainPieTest::RunTest(const FString& Parameters)
{
	// Delete the demo's checkpoint slot before the map opens.
	//
	// The director restores a checkpoint on BeginPlay, and the slot on this machine was two days
	// old. That made the first version of this test pass four steps and fail the fifth, then fail
	// the very first step on the next run with nothing changed in between: the chain was being
	// resumed from whatever the last session left, not started.
	//
	// It has to happen before PIE, because the restore runs on the director's first tick and there
	// is no window to intervene afterwards -- and ResetAllObjectives is not an alternative, since
	// it empties the objective map rather than returning it to its initial state.
	//
	// This does delete a save file, which a test should not do lightly. It is a checkpoint for a
	// demo map on a development machine, the demo is meant to begin at the beginning, and without
	// it this test measures the save file rather than the mission chain.
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	// The director registers its objectives on BeginPlay, so the chain does not exist for a frame.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertDemoChain(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
