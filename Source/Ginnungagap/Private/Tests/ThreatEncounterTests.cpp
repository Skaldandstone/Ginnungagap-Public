#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Threats/ShipboardThreat.h"
#include "Threats/ShipThreatDirector.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FThreatArchetypeCoverageTest,
    "Ginnungagap.Gameplay.Threats.ArchetypeCoverage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FThreatArchetypeCoverageTest::RunTest(const FString& Parameters)
{
    const FThreatArchetypeTuning Pirate =
        AShipboardThreat::GetArchetypeTuning(EThreatArchetype::PirateBreacher);
    const FThreatArchetypeTuning Rebel =
        AShipboardThreat::GetArchetypeTuning(EThreatArchetype::RebelSaboteur);
    const FThreatArchetypeTuning Biped =
        AShipboardThreat::GetArchetypeTuning(EThreatArchetype::AlienBipedHunter);
    const FThreatArchetypeTuning Quadruped =
        AShipboardThreat::GetArchetypeTuning(EThreatArchetype::AlienQuadrupedStalker);
    const FThreatArchetypeTuning Arachnoped =
        AShipboardThreat::GetArchetypeTuning(EThreatArchetype::AlienArachnopedAmbusher);

    TestEqual(TEXT("Pirates are human boarders"), Pirate.Faction, EThreatFaction::Pirates);
    TestEqual(TEXT("Rebels have a separate faction"), Rebel.Faction, EThreatFaction::Rebels);
    TestEqual(TEXT("Biped alien body plan exists"), Biped.BodyPlan, EThreatBodyPlan::Bipedal);
    TestEqual(TEXT("Quadruped alien body plan exists"), Quadruped.BodyPlan, EThreatBodyPlan::Quadrupedal);
    TestEqual(TEXT("Arachnoped alien body plan exists"), Arachnoped.BodyPlan, EThreatBodyPlan::Arachnoped);
    TestTrue(TEXT("Fast quadruped differs from biped hunter"), Quadruped.ChaseSpeed > Biped.ChaseSpeed);
    TestTrue(TEXT("Arachnoped is a burst-damage ambusher"), Arachnoped.DamagePerAttack > Quadruped.DamagePerAttack);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FThreatPresetPolicyTest,
    "Ginnungagap.Gameplay.Threats.PresetPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FThreatPresetPolicyTest::RunTest(const FString& Parameters)
{
    const FThreatEncounterDefinition Pirates =
        AShipThreatDirector::BuildPresetDefinition(EThreatEncounterPreset::PirateBoarding);
    const FThreatEncounterDefinition Rebels =
        AShipThreatDirector::BuildPresetDefinition(EThreatEncounterPreset::RebelTakeover);
    const FThreatEncounterDefinition Aliens =
        AShipThreatDirector::BuildPresetDefinition(EThreatEncounterPreset::MixedAlienIncursion);

    TestFalse(TEXT("Pirates do not require Bloom"), Pirates.bRequiresBloom);
    TestTrue(TEXT("Pirates may overlap Bloom"), Pirates.bCanOverlapBloom);
    TestTrue(TEXT("Pirates are a fireteam-sized primary antagonist"), Pirates.GetTotalThreatCount() >= 4);
    TestFalse(TEXT("Rebels do not require Bloom"), Rebels.bRequiresBloom);
    TestTrue(TEXT("Mixed incursion includes all three alien groups"), Aliens.SpawnGroups.Num() == 3);
    TestTrue(TEXT("Mixed incursion can happen during Bloom"), Aliens.bCanOverlapBloom);
    TestTrue(TEXT("Every preset registers a stable encounter id"),
        !Pirates.EncounterId.IsNone() && !Rebels.EncounterId.IsNone() && !Aliens.EncounterId.IsNone());
    return true;
}

#endif
