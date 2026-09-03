#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/World.h"

#include "Threats/EncounterPacingSubsystem.h"

/**
 * The rhythm the ship presses on and lets go of.
 *
 * The demo has hunters that patrol, perceive and give up; what it has not had is anyone deciding
 * when. Pressure arriving whenever a patrol route happens to cross the player is not pacing, it is
 * weather.
 *
 * Two things are asserted here and they are both about *shape*, because the durations are balance
 * and will move:
 *
 *   1. Pressure is entered only by something finding the player, never by a clock. The moment a
 *      hunt can arrive on a timer, the player learns the interval and the horror is gone.
 *   2. Relief gets longer the worse the player is doing. That is the opposite of a difficulty
 *      curve and the single most likely thing to be "fixed" by someone who has not read why.
 */

namespace PacingTest
{
	UEncounterPacingSubsystem* Get(UWorld* World)
	{
		return World ? World->GetSubsystem<UEncounterPacingSubsystem>() : nullptr;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPacingPhasesTest,
	"Ginnungagap.Threats.PacingPhases",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPacingPhasesTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	UEncounterPacingSubsystem* Pacing = PacingTest::Get(World);
	if (!TestNotNull(TEXT("The world has an encounter pacing subsystem"), Pacing))
	{
		return false;
	}

	// A run opens quiet. Waking in a cryo pod to something already hunting you is not an opening,
	// it is a fail state with a cutscene.
	TestEqual(TEXT("A run opens quiet"), Pacing->GetPhase(), EEncounterPhase::Quiet);

	// --- quiet drifts into building on its own ---------------------------------------------------
	Pacing->Tick(Pacing->QuietSecondsBeforeBuilding + 1.0f);
	TestEqual(TEXT("A long enough quiet stretch becomes Building"),
		Pacing->GetPhase(), EEncounterPhase::Building);

	// --- but building never becomes pressure by itself -------------------------------------------
	// The assertion this file exists for. If Building ever escalates on a timer, the ship produces
	// a hunt whether or not there is anyone to hunt, and the interval becomes learnable.
	Pacing->Tick(Pacing->BuildingSecondsBeforeQuiet + 1.0f);
	TestEqual(TEXT("Building that finds nobody falls back to Quiet, it does not escalate"),
		Pacing->GetPhase(), EEncounterPhase::Quiet);

	// --- something finding the player is what escalates -------------------------------------------
	Pacing->NotifyPlayerDetected();
	TestEqual(TEXT("Being seen is what causes Pressure"),
		Pacing->GetPhase(), EEncounterPhase::Pressure);

	// --- and a hunter giving up is what ends it ---------------------------------------------------
	Pacing->NotifyEncounterSurvived();
	TestEqual(TEXT("Getting away ends the pressure"),
		Pacing->GetPhase(), EEncounterPhase::Relief);

	// Relief eventually returns to quiet on its own.
	Pacing->Tick(Pacing->BaseReliefSeconds + Pacing->MaximumMercySeconds + 1.0f);
	TestEqual(TEXT("Relief returns to Quiet"), Pacing->GetPhase(), EEncounterPhase::Quiet);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPacingMercyTest,
	"Ginnungagap.Threats.PacingMercy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPacingMercyTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	UEncounterPacingSubsystem* Pacing = PacingTest::Get(World);
	if (!TestNotNull(TEXT("The world has an encounter pacing subsystem"), Pacing))
	{
		return false;
	}

	const float Calm = Pacing->GetReliefSecondsForStress(0.0f);
	const float Rattled = Pacing->GetReliefSecondsForStress(0.5f);
	const float Spent = Pacing->GetReliefSecondsForStress(1.0f);

	// The mercy rule, and the thing most likely to look like a bug to someone who has not read why.
	//
	// Acute stress already degrades coordination, which loses activities, which raises stress.
	// Pressing a player who is deep in that spiral does not make the game frightening -- it makes it
	// unwinnable on a schedule, and a run lost before the player knows it is lost reads as unfair
	// rather than as tense. The scare works because there was a chance.
	TestTrue(TEXT("A rattled player gets longer to recover than a calm one"), Rattled > Calm);
	TestTrue(TEXT("and a spent one gets longer still"), Spent > Rattled);

	// Not free, either. Relief has a floor so a calm player still gets a breath, and a ceiling so a
	// stressed one does not get an empty ship.
	TestTrue(TEXT("Even a calm player gets some relief"), Calm > 0.0f);
	TestTrue(TEXT("Mercy is bounded rather than unlimited"),
		Spent <= Pacing->BaseReliefSeconds + Pacing->MaximumMercySeconds + 0.001f);

	// --- perception actually differs by phase -----------------------------------------------------
	// The one number this whole system exports. If the phases all scaled perception the same, every
	// transition above would be bookkeeping with no effect on anything.
	Pacing->SetPhase(EEncounterPhase::Relief);
	const float DuringRelief = Pacing->GetPerceptionScale();

	Pacing->SetPhase(EEncounterPhase::Pressure);
	const float DuringPressure = Pacing->GetPerceptionScale();

	Pacing->SetPhase(EEncounterPhase::Quiet);
	const float DuringQuiet = Pacing->GetPerceptionScale();

	TestTrue(TEXT("Hunters are sharpest under pressure"), DuringPressure > DuringQuiet);
	TestTrue(TEXT("and dullest during relief"), DuringRelief < DuringQuiet);

	// Under 1.0 specifically: relief means the ship genuinely stops looking, not that it looks
	// slightly less hard. A player who has just got away should be able to believe it.
	TestTrue(TEXT("Relief suppresses perception below normal rather than merely reducing it"),
		DuringRelief < 1.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPacingReliefIsFixedOnEntryTest,
	"Ginnungagap.Threats.PacingReliefIsFixedOnEntry",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPacingReliefIsFixedOnEntryTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	UEncounterPacingSubsystem* Pacing = PacingTest::Get(World);
	if (!TestNotNull(TEXT("The world has an encounter pacing subsystem"), Pacing))
	{
		return false;
	}

	// With no player in the world, stress reads zero, so relief should be exactly the base value.
	// The point of the assertion is not the number -- it is that the length is decided once, on
	// entry, rather than recomputed each frame from a stress value that is decaying the whole time.
	// A live reading would shorten the player's own mercy while they were receiving it: the calmer
	// they got, the sooner it would end, which inverts the entire rule.
	Pacing->SetPhase(EEncounterPhase::Pressure);
	Pacing->NotifyEncounterSurvived();
	TestEqual(TEXT("Relief began"), Pacing->GetPhase(), EEncounterPhase::Relief);

	Pacing->Tick(Pacing->BaseReliefSeconds - 1.0f);
	TestEqual(TEXT("Relief is still running just before its length"),
		Pacing->GetPhase(), EEncounterPhase::Relief);

	Pacing->Tick(2.0f);
	TestEqual(TEXT("and ends at it"), Pacing->GetPhase(), EEncounterPhase::Quiet);

	return true;
}

#endif
