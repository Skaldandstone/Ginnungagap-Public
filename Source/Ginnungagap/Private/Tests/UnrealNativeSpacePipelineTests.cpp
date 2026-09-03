#include "Misc/AutomationTest.h"

#include "StarSystem/ProceduralStarSystemMap.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FUnrealNativeSpacePipelineDefaultsTest,
    "Ginnungagap.SpaceSystems.UnrealNativePipeline.Defaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FUnrealNativeSpacePipelineDefaultsTest::RunTest(const FString& Parameters)
{
    const AProceduralStarSystemMap* SystemMap = GetDefault<AProceduralStarSystemMap>();
    TestNotNull(TEXT("Procedural system map has a default object"), SystemMap);
    TestTrue(TEXT("Unreal-native visuals are enabled by default"), SystemMap->bUseUnrealNativeVisualPipeline);
    TestFalse(TEXT("Legacy concept-art skydome is disabled by default"), SystemMap->bUseLegacyCosmicSky);
    TestEqual(TEXT("High visual quality is the default"), SystemMap->VisualQualityTier, ESystemVisualQualityTier::High);
    TestTrue(TEXT("Arrival exclusion radius is meaningful"), SystemMap->VisualExclusionRadiusCm >= 100000.0f);
    TestTrue(TEXT("Optional landmark probability is normalized"),
        SystemMap->LandmarkSpawnChance >= 0.0f && SystemMap->LandmarkSpawnChance <= 1.0f);
    TestTrue(TEXT("Landmark target size is exterior-scale"), SystemMap->LandmarkTargetDiameterCm >= 10000.0f);
    TestNotNull(TEXT("Runtime asteroid PCG attachment exists"), SystemMap->AsteroidPCG.Get());
    TestNotNull(TEXT("Runtime radiation Niagara attachment exists"), SystemMap->RadiationDustFX.Get());
    TestNotNull(TEXT("Runtime nebula Niagara attachment exists"), SystemMap->NebulaFX.Get());

    const int32 AsteroidSeed = SystemMap->GetVisualLayerSeed(TEXT("Asteroids"));
    const int32 RepeatAsteroidSeed = SystemMap->GetVisualLayerSeed(TEXT("Asteroids"));
    const int32 RadiationSeed = SystemMap->GetVisualLayerSeed(TEXT("RadiationDust"));
    TestEqual(TEXT("Named layer seeds are deterministic"), AsteroidSeed, RepeatAsteroidSeed);
    TestNotEqual(TEXT("Different visual layers receive independent seeds"), AsteroidSeed, RadiationSeed);
    return true;
}

#endif
