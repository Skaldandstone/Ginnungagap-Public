#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/World.h"

#include "Activities/PlayerActivitySource.h"
#include "Activities/PlayerActivityTypes.h"
#include "Obstructions/ObstructionBarrier.h"

/**
 * Obstructions with more than one way past them.
 *
 * The design James asked for is three verbs whose costs are in different currencies -- blow it and
 * damage the ship, cut it and spend the gear you will need later, squeeze and risk being stuck.
 * What makes that a decision rather than a menu is that the costs are not comparable, so these
 * tests are mostly about the *shape* of the options rather than their magnitudes: which verbs a
 * given obstruction offers, what it refuses and why, and that a refusal actually refuses.
 *
 * The magnitudes are balance and will move. The shape is the design, and if it stops holding --
 * every obstruction offering every verb, or a refused verb quietly succeeding -- the feature is
 * gone while still appearing to work.
 */

namespace ObstructionTest
{
	AObstructionBarrier* Spawn(UWorld* World, FName Preset)
	{
		AObstructionBarrier* Barrier = World->SpawnActor<AObstructionBarrier>(
			AObstructionBarrier::StaticClass(), FTransform::Identity);
		if (Barrier)
		{
			Barrier->ApplyAuthoringPreset(Preset);
		}
		return Barrier;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapObstructionPresetsTest,
	"Ginnungagap.Obstructions.Presets",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapObstructionPresetsTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	if (!TestNotNull(TEXT("Created a world to spawn barriers in"), World))
	{
		return false;
	}

	// --- collapsed debris: the one that teaches the choice ---------------------------------------
	AObstructionBarrier* Debris = ObstructionTest::Spawn(World, TEXT("CollapsedDebris"));
	if (!TestNotNull(TEXT("Spawned a debris barrier"), Debris))
	{
		return false;
	}

	// Null pawn asks about the obstruction rather than about a player, so this is the full set of
	// verbs the obstruction permits at all.
	TestEqual(TEXT("Collapsed debris offers all three verbs"),
		Debris->GetAvailableVerbs(nullptr).Num(), 3);
	TestTrue(TEXT("Collapsed debris can be gone around"), Debris->bBypassable);

	// --- welded bulkhead: no gaps, and it must be gone through -----------------------------------
	AObstructionBarrier* Bulkhead = ObstructionTest::Spawn(World, TEXT("WeldedBulkhead"));
	TestFalse(TEXT("A welded bulkhead cannot be squeezed past"),
		Bulkhead->CanResolveWith(EObstructionVerb::Squeeze, nullptr));
	TestTrue(TEXT("A welded bulkhead can be cut"),
		Bulkhead->CanResolveWith(EObstructionVerb::Cut, nullptr));
	TestFalse(TEXT("A welded bulkhead is one of the cases with no way round"), Bulkhead->bBypassable);

	// The refusal says why, so a prompt can tell the player something useful rather than "no".
	TestEqual(TEXT("Squeezing a bulkhead is refused as impossible here, not as an equipment problem"),
		Bulkhead->GetRefusal(EObstructionVerb::Squeeze, nullptr),
		EObstructionRefusal::NotPossibleHere);

	// --- jammed hatch: forced through the verb with the near miss attached -----------------------
	AObstructionBarrier* Hatch = ObstructionTest::Spawn(World, TEXT("JammedHatch"));
	const TArray<EObstructionVerb> HatchVerbs = Hatch->GetAvailableVerbs(nullptr);
	TestEqual(TEXT("A jammed hatch offers exactly one way past"), HatchVerbs.Num(), 1);
	if (HatchVerbs.Num() == 1)
	{
		TestEqual(TEXT("and that way is squeezing"), HatchVerbs[0], EObstructionVerb::Squeeze);
	}

	// --- an unknown preset permits nothing --------------------------------------------------------
	// Deliberate: a barrier that silently allows everything because its name was misspelled is
	// worse than one that allows nothing and is obvious about it.
	AObstructionBarrier* Unknown = ObstructionTest::Spawn(World, TEXT("NotAPresetName"));
	TestEqual(TEXT("An unrecognised preset leaves the barrier with no options at all"),
		Unknown->GetAvailableVerbs(nullptr).Num(), 0);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapObstructionResolutionTest,
	"Ginnungagap.Obstructions.Resolution",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapObstructionResolutionTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	if (!TestNotNull(TEXT("Created a world to spawn barriers in"), World))
	{
		return false;
	}

	AObstructionBarrier* Debris = ObstructionTest::Spawn(World, TEXT("CollapsedDebris"));
	if (!TestNotNull(TEXT("Spawned a debris barrier"), Debris))
	{
		return false;
	}

	TestFalse(TEXT("A fresh barrier is in the way"), Debris->bCleared);

	// A refused verb must do nothing at all -- not clear the barrier, not apply half its costs.
	// Squeezing a bulkhead is refused, and a caller that ignores CanResolveWith must still not get
	// through.
	AObstructionBarrier* Bulkhead = ObstructionTest::Spawn(World, TEXT("WeldedBulkhead"));
	TestFalse(TEXT("Resolving with a refused verb returns false"),
		Bulkhead->ResolveWith(EObstructionVerb::Squeeze, nullptr));
	TestFalse(TEXT("and leaves the barrier in the way"), Bulkhead->bCleared);

	// A permitted verb clears it and records which one, because what the player chose should still
	// be answerable later -- a corridor the player blew open is a different place from one they
	// squeezed through.
	TestTrue(TEXT("Resolving with a permitted verb succeeds"),
		Debris->ResolveWith(EObstructionVerb::Squeeze, nullptr));
	TestTrue(TEXT("and clears the barrier"), Debris->bCleared);
	TestEqual(TEXT("and remembers how"), Debris->ClearedWith, EObstructionVerb::Squeeze);

	// It stays open. A blockage that closes behind the player turns a route choice into a one-way
	// door, which is the opposite of what paying a cost for a route should buy.
	TestEqual(TEXT("A cleared barrier refuses further resolution as already cleared"),
		Debris->GetRefusal(EObstructionVerb::Breach, nullptr),
		EObstructionRefusal::AlreadyCleared);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapObstructionCollateralTest,
	"Ginnungagap.Obstructions.Collateral",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapObstructionCollateralTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	if (!TestNotNull(TEXT("Created a world to spawn barriers in"), World))
	{
		return false;
	}

	AObstructionBarrier* Bulkhead = ObstructionTest::Spawn(World, TEXT("WeldedBulkhead"));
	if (!TestNotNull(TEXT("Spawned a bulkhead"), Bulkhead))
	{
		return false;
	}

	// The whole reason breaching is not simply the best option: it costs the ship. A player has to
	// be able to judge that cost by looking at what is standing nearby, which means the falloff has
	// to be predictable from distance alone.
	const float AtTheBarrier = Bulkhead->GetCollateralAtDistance(EObstructionVerb::Breach, 0.0f);
	const float HalfWay = Bulkhead->GetCollateralAtDistance(EObstructionVerb::Breach, 650.0f);
	const float WellClear = Bulkhead->GetCollateralAtDistance(EObstructionVerb::Breach, 2000.0f);

	TestTrue(TEXT("A breach damages a system standing next to it"), AtTheBarrier > 0.0f);
	TestTrue(TEXT("Damage falls off with distance"), HalfWay < AtTheBarrier);
	TestEqual(TEXT("Nothing outside the radius is touched"), WellClear, 0.0f, 0.001f);

	// Linear, so half the radius is half the damage. Asserted because the alternative -- inverse
	// square -- would make the near field so much worse that "is that console close" stops being a
	// judgement a player can make by eye.
	TestEqual(TEXT("Falloff is linear across the radius"), HalfWay, AtTheBarrier * 0.5f, 0.01f);

	// Cutting damages nothing. If this ever stopped being true the three verbs would collapse into
	// one expensive verb and two cheaper ones.
	TestEqual(TEXT("Cutting through causes no collateral damage"),
		Bulkhead->GetCollateralAtDistance(EObstructionVerb::Cut, 0.0f), 0.0f, 0.001f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapObstructionActivityTest,
	"Ginnungagap.Obstructions.ActivityBinding",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapObstructionActivityTest::RunTest(const FString& Parameters)
{
	UWorld* World = FAutomationEditorCommonUtils::CreateNewMap();
	if (!TestNotNull(TEXT("Created a world to spawn barriers in"), World))
	{
		return false;
	}

	AObstructionBarrier* Debris = ObstructionTest::Spawn(World, TEXT("CollapsedDebris"));
	if (!TestNotNull(TEXT("Spawned a debris barrier"), Debris))
	{
		return false;
	}

	// --- cutting is a real weld ------------------------------------------------------------------
	// The single most important thing about routing these through the activity system. Welding is
	// failable and a failed weld already spends gear condition and rolls for a burn, so cutting an
	// obstruction carries the same risk as any other weld through the same code -- no special case,
	// and no second implementation of the same consequence to keep in step.
	TestTrue(TEXT("Cut is selectable on debris"),
		Debris->SelectVerb(EObstructionVerb::Cut, nullptr));

	// Called through _Implementation rather than through Execute_. The interface dispatch returned
	// a default-constructed definition here -- every field at its struct default -- which is the
	// shape of a Blueprint-native-event thunk not reaching the native override. Worth knowing about
	// and worth not testing through: what this test is for is whether each verb maps to the right
	// activity, and going through the thunk tests UHT instead.
	FPlayerActivityDefinition Cutting = Debris->GetActivityDefinition_Implementation(nullptr);
	TestEqual(TEXT("Cutting runs as a welding activity"),
		Cutting.Type, EPlayerActivityType::Welding);
	TestEqual(TEXT("and uses the tool-path mechanic, so it can be botched"),
		Cutting.Mechanic, EActivityMechanic::ToolPath);

	// --- squeezing cannot be failed --------------------------------------------------------------
	// Deliberate. The near miss is rolled on completion, not modelled as a failure state: a squeeze
	// that can be lost is a trap, and this is meant to be a corridor.
	Debris->SelectVerb(EObstructionVerb::Squeeze, nullptr);
	FPlayerActivityDefinition Squeezing = Debris->GetActivityDefinition_Implementation(nullptr);
	TestEqual(TEXT("Squeezing is a timed activity with no failure state"),
		Squeezing.Mechanic, EActivityMechanic::Timed);

	// --- the activity carries the verb's own noise -----------------------------------------------
	// Otherwise every way past an obstruction sounds the same to whatever is listening, and the
	// quiet option stops being quiet.
	Debris->SelectVerb(EObstructionVerb::Breach, nullptr);
	FPlayerActivityDefinition Breaching = Debris->GetActivityDefinition_Implementation(nullptr);
	TestTrue(TEXT("Breaching is louder work than squeezing"),
		Breaching.WorkNoiseLoudness > Squeezing.WorkNoiseLoudness);

	// --- cycling only lands on verbs the pawn can use --------------------------------------------
	// A prompt key that can land on an impossible option is a control that sometimes does nothing.
	AObstructionBarrier* Hatch = ObstructionTest::Spawn(World, TEXT("JammedHatch"));
	for (int32 Press = 0; Press < 4; ++Press)
	{
		const EObstructionVerb Landed = Hatch->CycleVerb(nullptr);
		TestEqual(TEXT("Cycling at a squeeze-only hatch always lands on squeeze"),
			Landed, EObstructionVerb::Squeeze);
	}

	// Selecting an impossible verb is refused rather than armed, so the barrier is never sitting on
	// a choice that would do nothing when pressed.
	TestFalse(TEXT("A verb the obstruction does not permit cannot be selected"),
		Hatch->SelectVerb(EObstructionVerb::Breach, nullptr));
	TestEqual(TEXT("and the previous selection survives the refusal"),
		Hatch->SelectedVerb, EObstructionVerb::Squeeze);

	return true;
}

#endif
