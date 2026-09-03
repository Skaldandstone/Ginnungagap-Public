#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "StatusEffects/PlayerStatusEffectComponent.h"

/**
 * The causes of acute stress and burn trauma, which until now barely had any.
 *
 * AcuteStress fed five separate systems -- psychosis, coordination, a weighted penalty, stamina
 * recovery, and its own decay -- from exactly one producer: a hard physics collision. A player's
 * stress could only ever rise by being thrown into a wall. BurnTrauma had display text, a
 * description, a recommended treatment, and a severity read every frame by the consequence pass,
 * and **zero** producers anywhere in the project. Nothing could cause it. It was a UI string.
 *
 * These are unit tests rather than PIE tests deliberately. Everything asserted here is arithmetic
 * over component state with no world involved, and a PIE test would take fifteen seconds to prove
 * something a constructed component proves instantly. The wiring that connects these to the game --
 * a failed activity, an enemy giving up -- is what needs a world, and that is a separate concern
 * from whether the numbers are right.
 */

namespace StressTest
{
	/**
	 * A component with no owner.
	 *
	 * Every mutator early-returns when GetOwner() exists without authority; with no owner at all the
	 * check passes, which is what makes this testable without a world. Verified rather than assumed
	 * by the first assertion in each test -- if this stopped being true the tests would silently
	 * assert nothing.
	 */
	UPlayerStatusEffectComponent* MakeComponent()
	{
		return NewObject<UPlayerStatusEffectComponent>();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapStressAccumulatesTest,
	"Ginnungagap.StatusEffects.StressAccumulates",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapStressAccumulatesTest::RunTest(const FString& Parameters)
{
	UPlayerStatusEffectComponent* Status = StressTest::MakeComponent();
	if (!TestNotNull(TEXT("Constructed a status component"), Status))
	{
		return false;
	}

	// --- the primitive: adding, not taking the worse ---------------------------------------------
	// ApplyStatusEffect keeps whichever severity is higher, which is right for exposure and wrong
	// for anything cumulative. If AccumulateStatusEffect ever regressed to that behaviour this is
	// the assertion that would catch it: two 0.2s max to 0.2 and add to 0.4.
	Status->AccumulateStatusEffect(EPlayerStatusEffect::AcuteStress, 0.2f);
	Status->AccumulateStatusEffect(EPlayerStatusEffect::AcuteStress, 0.2f);
	TestEqual(TEXT("Two accumulations add rather than taking the larger"),
		Status->GetStatusSeverity(EPlayerStatusEffect::AcuteStress), 0.4f, 0.001f);

	// Clamped at the top, because severity is a 0..1 quantity everywhere it is read.
	Status->AccumulateStatusEffect(EPlayerStatusEffect::AcuteStress, 5.0f);
	TestEqual(TEXT("Accumulation clamps at 1.0"),
		Status->GetStatusSeverity(EPlayerStatusEffect::AcuteStress), 1.0f, 0.001f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapStressEscalatesTest,
	"Ginnungagap.StatusEffects.StressEscalates",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapStressEscalatesTest::RunTest(const FString& Parameters)
{
	UPlayerStatusEffectComponent* Status = StressTest::MakeComponent();
	if (!TestNotNull(TEXT("Constructed a status component"), Status))
	{
		return false;
	}

	// The whole point of the direction: stress is "an escalating value", not a per-event spike. A
	// run of near misses has to cost more than the same events spread out, or surviving repeatedly
	// reads identically to surviving once.
	TestEqual(TEXT("Escalation starts at 1.0 with nothing having happened"),
		Status->GetStressEscalation(), 1.0f, 0.001f);

	const float First = Status->ApplyStressEvent(EPlayerStressEvent::SurvivedEncounter);
	const float Second = Status->ApplyStressEvent(EPlayerStressEvent::SurvivedEncounter);
	const float Third = Status->ApplyStressEvent(EPlayerStressEvent::SurvivedEncounter);

	TestTrue(TEXT("The first escape costs something"), First > 0.0f);
	TestTrue(TEXT("The second escape costs more than the first"), Second > First);
	TestTrue(TEXT("The third costs more than the second"), Third > Second);

	// An event must not make itself worse: escalation is read before the event is remembered, so
	// the first event of a run costs its base rate exactly. Without this the very first thing that
	// happens to a player is already amplified, which is not what "escalating" means.
	TestTrue(TEXT("The first event is not amplified by itself"), Second > First * 1.05f);

	// The cap is what keeps the spiral survivable. Stress degrades coordination, which loses
	// activities, which raises stress -- uncapped that is a fail state on a timer rather than
	// tension.
	for (int32 Index = 0; Index < 40; ++Index)
	{
		Status->ApplyStressEvent(EPlayerStressEvent::FailedTask);
	}
	TestTrue(TEXT("Escalation is capped rather than unbounded"),
		Status->GetStressEscalation() <= 2.5f + 0.001f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapWeldingBackfireTest,
	"Ginnungagap.StatusEffects.WeldingBackfire",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapWeldingBackfireTest::RunTest(const FString& Parameters)
{
	UPlayerStatusEffectComponent* Status = StressTest::MakeComponent();
	if (!TestNotNull(TEXT("Constructed a status component"), Status))
	{
		return false;
	}

	// The chance curve is asserted rather than the roll. A test that rolls dice either passes by
	// luck or needs a seeded stream threaded through a component that has no reason to own one, and
	// neither tells you whether the curve is right.
	TestEqual(TEXT("Gear in full condition cannot backfire"),
		Status->GetWeldingBackfireChance(1.0f), 0.0f, 0.001f);
	TestEqual(TEXT("Gear at the safe threshold cannot backfire"),
		Status->GetWeldingBackfireChance(0.55f), 0.0f, 0.001f);

	const float HalfWorn = Status->GetWeldingBackfireChance(0.275f);
	const float Ruined = Status->GetWeldingBackfireChance(0.0f);

	TestTrue(TEXT("Gear past the threshold can backfire"), HalfWorn > 0.0f);
	TestTrue(TEXT("Worse gear backfires more often"), Ruined > HalfWorn);
	TestTrue(TEXT("Even ruined gear is a risk rather than a certainty"), Ruined < 1.0f);

	// The burn itself, without the roll. This is the half that matters to the player: durability
	// now has a consequence instead of only ever locking an action out.
	const float BurnFromRuined = Status->ApplyWeldingBurn(0.0f);
	TestTrue(TEXT("A backfire on ruined gear burns the welder"), BurnFromRuined > 0.0f);
	TestTrue(TEXT("BurnTrauma is actually applied, not just returned"),
		Status->GetStatusSeverity(EPlayerStatusEffect::BurnTrauma) > 0.0f);

	UPlayerStatusEffectComponent* Fresh = StressTest::MakeComponent();
	const float BurnFromGoodGear = Fresh->ApplyWeldingBurn(1.0f);
	TestEqual(TEXT("A backfire on perfect gear does no damage"), BurnFromGoodGear, 0.0f, 0.001f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapHeatExposureTest,
	"Ginnungagap.StatusEffects.HeatExposure",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapHeatExposureTest::RunTest(const FString& Parameters)
{
	UPlayerStatusEffectComponent* Status = StressTest::MakeComponent();
	if (!TestNotNull(TEXT("Constructed a status component"), Status))
	{
		return false;
	}

	TestEqual(TEXT("Standing outside a fire's reach does nothing"),
		Status->ApplyHeatSourceExposure(0.0f, 1.0f), 0.0f, 0.001f);

	const float AtEdge = Status->ApplyHeatSourceExposure(0.25f, 1.0f);
	const float AtContact = Status->ApplyHeatSourceExposure(1.0f, 1.0f);

	TestTrue(TEXT("Being near a fire burns"), AtEdge > 0.0f);

	// Squared falloff, so the last step toward a fire costs far more than the first. Four times the
	// proximity is sixteen times the burn, which is what lets a player judge "close" from a
	// distance instead of discovering the threshold by crossing it.
	TestTrue(TEXT("Proximity costs disproportionately, not linearly"), AtContact > AtEdge * 8.0f);

	// Accrued over time rather than applied as a hit: half the exposure for half as long.
	UPlayerStatusEffectComponent* Fresh = StressTest::MakeComponent();
	const float ShortExposure = Fresh->ApplyHeatSourceExposure(1.0f, 0.5f);
	TestEqual(TEXT("Burn scales with time spent in the fire"),
		ShortExposure, AtContact * 0.5f, 0.001f);

	return true;
}

#endif
