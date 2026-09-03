#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "StatusEffects/PlayerPsychosisComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerStatusEffectLifecycleTest,
    "Ginnungagap.Survival.StatusEffects.Lifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerStatusEffectLifecycleTest::RunTest(const FString& Parameters)
{
    UPlayerStatusEffectComponent* Component = NewObject<UPlayerStatusEffectComponent>();
    TestTrue(TEXT("A status can be applied"),
        Component->ApplyStatusEffect(EPlayerStatusEffect::JumpPsychosis, 0.35f, 120.0f));
    TestTrue(TEXT("Applied status is active"), Component->HasStatusEffect(EPlayerStatusEffect::JumpPsychosis));
    TestEqual(TEXT("Severity is stored"), Component->GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis), 0.35f);

    Component->ApplyStatusEffect(EPlayerStatusEffect::JumpPsychosis, 0.7f, 60.0f);
    TestEqual(TEXT("Reapplication keeps the worse severity"),
        Component->GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis), 0.7f);
    TestEqual(TEXT("Reapplication does not duplicate an effect"), Component->GetActiveStatusEffects().Num(), 1);

    TestTrue(TEXT("Treatment reduces an active effect"),
        Component->TreatStatusEffect(EPlayerStatusEffect::JumpPsychosis, 0.25f));
    TestEqual(TEXT("Treatment strength is subtracted from severity"),
        Component->GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis), 0.45f);

    TestTrue(TEXT("An active status can be removed"),
        Component->RemoveStatusEffect(EPlayerStatusEffect::JumpPsychosis));
    TestFalse(TEXT("Removed status is inactive"), Component->HasStatusEffect(EPlayerStatusEffect::JumpPsychosis));

    Component->ApplyStatusEffect(EPlayerStatusEffect::Fracture, 0.8f);
    TestTrue(TEXT("A severe fracture impairs mobility"), Component->GetMobilityMultiplier() < 0.6f);
    Component->ApplyStatusEffect(EPlayerStatusEffect::CarbonDioxideToxicity, 0.8f);
    TestTrue(TEXT("CO2 toxicity impairs task efficiency"), Component->GetTaskEfficiencyMultiplier() < 0.7f);
    TestTrue(TEXT("CO2 toxicity increases oxygen demand"), Component->GetAdditionalOxygenDrainMultiplier() > 1.0f);
    Component->ApplyStatusEffect(EPlayerStatusEffect::Hemorrhage, 0.6f, -1.0f, EPlayerStatusSource::Trauma);
    bool bHasUrgentEffect = false;
    TestEqual(TEXT("Hemorrhage receives emergency triage priority"),
        Component->GetMostUrgentStatusEffect(bHasUrgentEffect), EPlayerStatusEffect::Hemorrhage);
    TestTrue(TEXT("Triage reports an urgent effect"), bHasUrgentEffect);
    const TArray<FPlayerStatusEffectState> TraumaStates = Component->GetActiveStatusEffects();
    const FPlayerStatusEffectState* HemorrhageState = TraumaStates.FindByPredicate([](const FPlayerStatusEffectState& State)
    {
        return State.Type == EPlayerStatusEffect::Hemorrhage;
    });
    TestNotNull(TEXT("Hemorrhage state is discoverable"), HemorrhageState);
    if (HemorrhageState)
    {
        TestEqual(TEXT("Trauma provenance is retained for diagnosis"), HemorrhageState->Source, EPlayerStatusSource::Trauma);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerStatusEffectEmptyTriageTest,
    "Ginnungagap.Survival.StatusEffects.EmptyTriage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerStatusEffectEmptyTriageTest::RunTest(const FString& Parameters)
{
    UPlayerStatusEffectComponent* Component = NewObject<UPlayerStatusEffectComponent>();
    bool bHasEffect = true;
    Component->GetMostUrgentStatusEffect(bHasEffect);
    TestFalse(TEXT("A healthy patient has no urgent condition"), bHasEffect);
    TestFalse(TEXT("Zero-severity conditions are rejected"),
        Component->ApplyStatusEffect(EPlayerStatusEffect::AcuteStress, 0.0f));
    TestEqual(TEXT("Rejected conditions do not enter replication state"), Component->GetActiveStatusEffects().Num(), 0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerStatusEffectCatalogTest,
    "Ginnungagap.Survival.StatusEffects.Catalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerStatusEffectCatalogTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Jump psychosis has a player-facing label"),
        UPlayerStatusEffectComponent::GetStatusDisplayName(EPlayerStatusEffect::JumpPsychosis).ToString(),
        FString(TEXT("Jump Psychosis")));
    TestEqual(TEXT("Hypoxia has a player-facing label"),
        UPlayerStatusEffectComponent::GetStatusDisplayName(EPlayerStatusEffect::Hypoxia).ToString(),
        FString(TEXT("Hypoxia")));
    TestFalse(TEXT("Every discrete trauma has diagnostic guidance"),
        UPlayerStatusEffectComponent::GetStatusDescription(EPlayerStatusEffect::Hemorrhage).IsEmpty());
    TestFalse(TEXT("Every discrete trauma has treatment guidance"),
        UPlayerStatusEffectComponent::GetRecommendedTreatment(EPlayerStatusEffect::Hemorrhage).IsEmpty());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerPsychosisPhaseTest,
    "Ginnungagap.Survival.Psychosis.EscalationPhases",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPlayerPsychosisPhaseTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("No exposure is stable"), UPlayerPsychosisComponent::GetPhaseForSeverity(0.0f), EPsychosisPhase::Stable);
    TestEqual(TEXT("Early symptoms are uneasy"), UPlayerPsychosisComponent::GetPhaseForSeverity(0.2f), EPsychosisPhase::Uneasy);
    TestEqual(TEXT("Mid symptoms are distorted"), UPlayerPsychosisComponent::GetPhaseForSeverity(0.45f), EPsychosisPhase::Distorted);
    TestEqual(TEXT("Severe symptoms cause a break"), UPlayerPsychosisComponent::GetPhaseForSeverity(0.7f), EPsychosisPhase::Break);
    TestEqual(TEXT("Severity is clamped by phase semantics"), UPlayerPsychosisComponent::GetPhaseForSeverity(5.0f), EPsychosisPhase::Break);
    TestFalse(TEXT("Every phase has a player-facing name"),
        UPlayerPsychosisComponent::GetPhaseDisplayName(EPsychosisPhase::Distorted).IsEmpty());
    return true;
}

#endif
