#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

#include "Bloom/BloomDirector.h"
#include "CoopSurvivalCharacter.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "Meta/RunSeedSubsystem.h"
#include "Ship/EscapePodSystem.h"

/**
 * How a run ends when the crew decides to end it.
 *
 * Scuttling the ship is the one outcome the crew chooses deliberately, and the Bloom gets to
 * contest it. Both halves of that contest were unreachable by test until the roll became seeded --
 * and both are forced here by moving the Bloom above or below the stage that lets it interfere,
 * rather than by hunting a seed, so no randomness is involved at all.
 *
 * The countdown is driven through the real timer rather than by calling detonation directly. That
 * path is private, and short-circuiting it would skip the arming, ticking and cancellation the
 * player actually interacts with.
 */

namespace SelfDestructPie
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

	URunOutcomeSubsystem* FindOutcome()
	{
		UWorld* World = FindPieWorld();
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		return GameInstance ? GameInstance->GetSubsystem<URunOutcomeSubsystem>() : nullptr;
	}

	/** A short fuse, so the real countdown can be waited out inside a test. */
	constexpr float ShortFuseSeconds = 1.0f;
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForOutcomeSubsystem, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForOutcomeSubsystem::Update()
{
	if (SelfDestructPie::FindOutcome())
	{
		return true;
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(TEXT("No run outcome subsystem existed before the deadline"));
		return true;
	}

	return false;
}

/** Arms a short-fused self destruct, having first put the Bloom where the test needs it. */
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FArmSelfDestruct, FAutomationTestBase*, Test, bool, bBloomShouldCounter);

bool FArmSelfDestruct::Update()
{
	UWorld* World = SelfDestructPie::FindPieWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	URunOutcomeSubsystem* Outcome = GameInstance ? GameInstance->GetSubsystem<URunOutcomeSubsystem>() : nullptr;
	UBloomDirector* Bloom = GameInstance ? GameInstance->GetSubsystem<UBloomDirector>() : nullptr;

	if (!Outcome || !Bloom)
	{
		Test->AddError(TEXT("Run outcome or Bloom director missing"));
		return true;
	}

	if (URunSeedSubsystem* Seeds = GameInstance->GetSubsystem<URunSeedSubsystem>())
	{
		Seeds->SeedRun(8181);
	}

	Bloom->ForceResetBloom();

	if (bBloomShouldCounter)
	{
		// Above the stage that permits interference, and made certain. RollChance treats a
		// certainty as certain without consuming a draw, so this is the real path with none of
		// the randomness.
		Bloom->RestoreStage(EBloomStage::Manifestation);
		Bloom->BaseSelfDestructCounterChance = 1.0f;
		Bloom->SelfDestructCounterChancePerStageBeyondMin = 0.0f;
	}
	else
	{
		// Latent is below MinStageForSelfDestructCounter, so the roll returns false before any
		// chance is consulted. A latent Bloom cannot contest anything.
		Bloom->RestoreStage(EBloomStage::Latent);
	}

	// Fresh run state. Arming refuses outright once a run has resolved, and the map's own actors
	// may have resolved one on the way up.
	Outcome->bRunResolved = false;
	Outcome->CurrentOutcome = ERunOutcome::InProgress;
	Outcome->SelfDestructCountdownSeconds = SelfDestructPie::ShortFuseSeconds;

	Test->TestTrue(TEXT("Self destruct arms"), Outcome->ArmSelfDestruct());
	Test->TestTrue(TEXT("Arming records the ship as armed"), Outcome->bSelfDestructArmed);
	Test->TestTrue(TEXT("Arming starts a countdown with time on it"),
		Outcome->SelfDestructSecondsRemaining > 0.0f);

	// Arming twice must not restart the fuse. A player mashing the control should not be able to
	// keep the ship alive indefinitely by re-arming it.
	Test->TestFalse(TEXT("An already-armed ship cannot be armed again"), Outcome->ArmSelfDestruct());

	return true;
}

/** Waits for the run to resolve, or fails rather than hanging. */
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForRunResolved, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForRunResolved::Update()
{
	const URunOutcomeSubsystem* Outcome = SelfDestructPie::FindOutcome();
	if (Outcome && Outcome->bRunResolved)
	{
		return true;
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(TEXT("The self destruct never resolved before the deadline"));
		return true;
	}

	return false;
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FAssertOutcome, FAutomationTestBase*, Test, ERunOutcome, Expected);

bool FAssertOutcome::Update()
{
	URunOutcomeSubsystem* Outcome = SelfDestructPie::FindOutcome();
	if (!Outcome)
	{
		Test->AddError(TEXT("Run outcome subsystem vanished before the assertions ran"));
		return true;
	}

	Test->TestTrue(TEXT("The run resolved"), Outcome->bRunResolved);
	Test->TestEqual(TEXT("The run reached the expected outcome"), Outcome->CurrentOutcome, Expected);
	Test->TestFalse(TEXT("A resolved run is no longer armed"), Outcome->bSelfDestructArmed);

	// A countered detonation must leave the crew alive. The Bloom stopping the scuttle is a
	// setback, not a casualty event -- if it killed everyone anyway the two outcomes would be the
	// same thing with different names.
	if (Expected == ERunOutcome::SelfDestructCountered)
	{
		if (UWorld* World = SelfDestructPie::FindPieWorld())
		{
			for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
			{
				Test->TestFalse(TEXT("A countered detonation kills nobody"), It->bIsDead);
			}
		}
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapSelfDestructSuccessTest,
	"Ginnungagap.Smoke.SelfDestructSuccess",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapSelfDestructSuccessTest::RunTest(const FString& Parameters)
{
	const double Ready = FPlatformTime::Seconds() + 60.0;
	const double Resolved = FPlatformTime::Seconds() + 90.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForOutcomeSubsystem(this, Ready));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FArmSelfDestruct(this, /*bBloomShouldCounter*/ false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForRunResolved(this, Resolved));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertOutcome(this, ERunOutcome::SelfDestructSuccess));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapSelfDestructCounteredTest,
	"Ginnungagap.Smoke.SelfDestructCountered",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapSelfDestructCounteredTest::RunTest(const FString& Parameters)
{
	const double Ready = FPlatformTime::Seconds() + 60.0;
	const double Resolved = FPlatformTime::Seconds() + 90.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForOutcomeSubsystem(this, Ready));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FArmSelfDestruct(this, /*bBloomShouldCounter*/ true));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForRunResolved(this, Resolved));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertOutcome(this, ERunOutcome::SelfDestructCountered));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

/** Cancelling is the other half of the control, and stands alone without a countdown to wait out. */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertSelfDestructCancel, FAutomationTestBase*, Test);

bool FAssertSelfDestructCancel::Update()
{
	URunOutcomeSubsystem* Outcome = SelfDestructPie::FindOutcome();
	if (!Outcome)
	{
		Test->AddError(TEXT("Run outcome subsystem missing"));
		return true;
	}

	Outcome->bRunResolved = false;
	Outcome->CurrentOutcome = ERunOutcome::InProgress;

	// Nothing to cancel yet. This must refuse rather than pretend, or a stray input would report
	// success and leave a player believing they had stopped something that was never running.
	Test->TestFalse(TEXT("Cancelling an unarmed ship is refused"), Outcome->CancelSelfDestruct());

	Test->TestTrue(TEXT("Self destruct arms"), Outcome->ArmSelfDestruct());
	Test->TestTrue(TEXT("Cancelling an armed ship succeeds"), Outcome->CancelSelfDestruct());
	Test->TestFalse(TEXT("A cancelled ship is no longer armed"), Outcome->bSelfDestructArmed);
	Test->TestFalse(TEXT("Cancelling does not resolve the run"), Outcome->bRunResolved);
	Test->TestEqual(TEXT("A cancelled run is still in progress"),
		Outcome->CurrentOutcome, ERunOutcome::InProgress);

	// Having cancelled, the ship must be armable again -- otherwise one cancellation permanently
	// disables the crew's last resort.
	Test->TestTrue(TEXT("A cancelled ship can be armed again"), Outcome->ArmSelfDestruct());
	Outcome->CancelSelfDestruct();

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapSelfDestructCancelTest,
	"Ginnungagap.Smoke.SelfDestructCancel",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapSelfDestructCancelTest::RunTest(const FString& Parameters)
{
	const double Ready = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForOutcomeSubsystem(this, Ready));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertSelfDestructCancel(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
