#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "HazardZoneActor.h"

/**
 * That a hot room is hot for the people in it.
 *
 * AHazardZoneActor has carried a TemperatureC since it was written, and read it in exactly one
 * place: DecayHazardContamination, where heat burns the Bloom back. The survivor loop scaled
 * radiation and dust by distance and passed temperature straight through to UpdateSurvival, and the
 * status component's ApplyHeatSourceExposure -- written for precisely this, squared falloff and all
 * -- had no caller outside its own tests. A fire could kill the infection and not the person
 * standing in it.
 *
 * The same shape as the eleven cryo materials with two wired and the 786 unused UI cues: the system
 * was finished, and nothing reached it.
 *
 * Asserts the curve rather than the wiring. Whether a survivor overlapping the box takes damage
 * needs a world, a pawn and a tick; whether 20 C is harmless and 200 C is not is arithmetic, and
 * arithmetic is worth pinning cheaply. GetNormalizedHeat exists to make that separation possible.
 */

namespace HazardThermalTest
{
	AHazardZoneActor* MakeZone(float TemperatureC)
	{
		AHazardZoneActor* Zone = NewObject<AHazardZoneActor>();
		if (Zone)
		{
			Zone->EnvironmentState.TemperatureC = TemperatureC;
		}
		return Zone;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapHazardZoneHeatCurveTest,
	"Ginnungagap.StatusEffects.HazardZoneHeatCurve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapHazardZoneHeatCurveTest::RunTest(const FString& Parameters)
{
	// --- the default ship is not on fire -----------------------------------------------------
	// The single most important assertion in this file. Every hazard zone already placed in every
	// map defaults to 20 C, and this change must not have quietly started burning players standing
	// in vacuum zones, dust zones, or anything else that was never meant to be hot.
	AHazardZoneActor* Ambient = HazardThermalTest::MakeZone(20.0f);
	if (!TestNotNull(TEXT("Constructed a hazard zone"), Ambient))
	{
		return false;
	}
	TestEqual(TEXT("A room-temperature zone does not burn anyone"),
		Ambient->GetNormalizedHeat(), 0.0f);

	// Below and at the threshold are both harmless: 50 C is where burning starts, not where it has
	// already started.
	TestEqual(TEXT("Below the threshold is harmless"),
		HazardThermalTest::MakeZone(49.0f)->GetNormalizedHeat(), 0.0f);
	TestEqual(TEXT("At the threshold is still harmless"),
		HazardThermalTest::MakeZone(50.0f)->GetNormalizedHeat(), 0.0f);

	// --- the gradient between threshold and saturation ---------------------------------------
	// Midpoint of 50..200 is 125. Linear here on purpose: the squaring that makes the last step
	// toward a fire hurt disproportionately lives in ApplyHeatSourceExposure, and doing it twice
	// would make anything short of standing in the flame free.
	TestEqual(TEXT("Halfway between threshold and saturation reads as half heat"),
		HazardThermalTest::MakeZone(125.0f)->GetNormalizedHeat(), 0.5f, 0.001f);

	TestEqual(TEXT("Saturation reads as full heat"),
		HazardThermalTest::MakeZone(200.0f)->GetNormalizedHeat(), 1.0f, 0.001f);

	// --- above saturation, and the clamp ------------------------------------------------------
	// A reactor breach should not be able to hand ApplyHeatSourceExposure a proximity above 1.0;
	// that function clamps too, but a zone reporting 8.0 heat would be a lie the moment anything
	// else read it.
	TestEqual(TEXT("Well past saturation is still exactly full heat, not more"),
		HazardThermalTest::MakeZone(1200.0f)->GetNormalizedHeat(), 1.0f, 0.001f);

	// --- a degenerate configuration is inert, not a divide by zero ----------------------------
	AHazardZoneActor* Degenerate = HazardThermalTest::MakeZone(500.0f);
	if (TestNotNull(TEXT("Constructed a degenerate zone"), Degenerate))
	{
		Degenerate->BurnSaturationC = Degenerate->BurnThresholdC;
		const float Heat = Degenerate->GetNormalizedHeat();
		TestEqual(TEXT("A zone with no gradient burns nobody rather than dividing by zero"),
			Heat, 0.0f);
		TestFalse(TEXT("...and is a real number"), FMath::IsNaN(Heat));
	}

	return true;
}

#endif
