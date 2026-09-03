#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "UI/UiSoundSubsystem.h"

#include "CoopSurvivalCharacter.h"
#include "Net/UnrealNetwork.h"

UPlayerStatusEffectComponent::UPlayerStatusEffectComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.25f;
    SetIsReplicatedByDefault(true);
}

void UPlayerStatusEffectComponent::BeginPlay()
{
    Super::BeginPlay();
    CharacterOwner = Cast<ACoopSurvivalCharacter>(GetOwner());
}

void UPlayerStatusEffectComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UPlayerStatusEffectComponent, ActiveStatusEffects);
}

void UPlayerStatusEffectComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!CharacterOwner || !CharacterOwner->HasAuthority() || CharacterOwner->bIsDead)
    {
        return;
    }

    // The memory of recent events fades whether or not any condition is active, so a player who has
    // had a quiet few minutes pays base rates again. Decayed here rather than stamped with times so
    // that pausing, or a long load, does not silently reset the escalation.
    if (RecentStressEvents > 0.0f && StressEventMemorySeconds > 0.0f)
    {
        RecentStressEvents = FMath::Max(0.0f, RecentStressEvents - DeltaTime / StressEventMemorySeconds);
    }

    bool bChanged = false;
    for (int32 Index = ActiveStatusEffects.Num() - 1; Index >= 0; --Index)
    {
        FPlayerStatusEffectState& Effect = ActiveStatusEffects[Index];
        if (Effect.RemainingSeconds >= 0.0f)
        {
            Effect.RemainingSeconds -= DeltaTime;
            if (Effect.RemainingSeconds <= 0.0f)
            {
                ActiveStatusEffects.RemoveAt(Index);
                bChanged = true;
            }
        }
    }

    UpdatePhysiologicalStatuses();
    if (CharacterOwner->OxygenLevelPercent >= 60.0f && CharacterOwner->Stability >= 0.7f)
    {
        TreatStatusEffect(EPlayerStatusEffect::AcuteStress, DeltaTime * 0.012f);
        TreatStatusEffect(EPlayerStatusEffect::SpaceMotionSickness, DeltaTime * 0.018f);
        TreatStatusEffect(EPlayerStatusEffect::CarbonDioxideToxicity, DeltaTime * 0.01f);
    }
    ApplyConsequences(DeltaTime);
    if (bChanged)
    {
        OnStatusEffectsChanged.Broadcast();
    }
}

bool UPlayerStatusEffectComponent::ApplyStatusEffect(EPlayerStatusEffect Type, float Severity, float DurationSeconds, EPlayerStatusSource Source)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return false;
    }

    const float ClampedSeverity = FMath::Clamp(Severity, 0.0f, 1.0f);
    if (ClampedSeverity <= KINDA_SMALL_NUMBER)
    {
        return false;
    }
    const int32 ExistingIndex = FindEffectIndex(Type);
    bool bChanged = false;
    if (ExistingIndex != INDEX_NONE)
    {
        FPlayerStatusEffectState& Existing = ActiveStatusEffects[ExistingIndex];
        const float NewSeverity = FMath::Max(Existing.Severity, ClampedSeverity);
        const float NewDuration = (Existing.RemainingSeconds < 0.0f || DurationSeconds < 0.0f)
            ? -1.0f : FMath::Max(Existing.RemainingSeconds, DurationSeconds);
        bChanged = !FMath::IsNearlyEqual(Existing.Severity, NewSeverity) || !FMath::IsNearlyEqual(Existing.RemainingSeconds, NewDuration);
        Existing.Severity = NewSeverity;
        Existing.RemainingSeconds = NewDuration;
        if (Existing.Source == EPlayerStatusSource::Unknown && Source != EPlayerStatusSource::Unknown)
        {
            Existing.Source = Source;
            bChanged = true;
        }
    }
    else
    {
        FPlayerStatusEffectState& Added = ActiveStatusEffects.AddDefaulted_GetRef();
        Added.Type = Type;
        Added.Severity = ClampedSeverity;
        Added.RemainingSeconds = DurationSeconds;
        Added.Source = Source;
        bChanged = true;

        // Only on a *new* condition, not on every top-up. A player accumulating stress across a
        // chase would otherwise get the same alert on every event, which stops meaning anything by
        // the third one. The Bloom gets its own sound because it should feel unlike the ship's.
        if (UWorld* World = GetWorld())
        {
            if (UGameInstance* GameInstance = World->GetGameInstance())
            {
                if (UUiSoundSubsystem* UiSound = GameInstance->GetSubsystem<UUiSoundSubsystem>())
                {
                    UiSound->PlayUiSound(Source == EPlayerStatusSource::JumpExposure
                        ? EUiSoundEvent::Corruption : EUiSoundEvent::Warning);
                }
            }
        }
    }
    if (bChanged) OnStatusEffectsChanged.Broadcast();
    return true;
}

bool UPlayerStatusEffectComponent::AccumulateStatusEffect(EPlayerStatusEffect Type, float SeverityDelta,
    float DurationSeconds, EPlayerStatusSource Source)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return false;
    }
    if (SeverityDelta <= KINDA_SMALL_NUMBER)
    {
        return false;
    }

    const int32 ExistingIndex = FindEffectIndex(Type);
    if (ExistingIndex == INDEX_NONE)
    {
        // Nothing to add to. ApplyStatusEffect does the right thing for a first occurrence, and
        // duplicating its insert here would be two places to keep in step.
        return ApplyStatusEffect(Type, SeverityDelta, DurationSeconds, Source);
    }

    FPlayerStatusEffectState& Existing = ActiveStatusEffects[ExistingIndex];
    const float NewSeverity = FMath::Clamp(Existing.Severity + SeverityDelta, 0.0f, 1.0f);

    // The refreshed duration is taken rather than the longer of the two, because a new event
    // restarts the clock. Taking the max would let a long-expiring early event mask later ones and
    // make the condition outlast its own cause.
    const float NewDuration = (Existing.RemainingSeconds < 0.0f || DurationSeconds < 0.0f)
        ? -1.0f : FMath::Max(Existing.RemainingSeconds, DurationSeconds);

    const bool bChanged = !FMath::IsNearlyEqual(Existing.Severity, NewSeverity)
        || !FMath::IsNearlyEqual(Existing.RemainingSeconds, NewDuration);

    Existing.Severity = NewSeverity;
    Existing.RemainingSeconds = NewDuration;
    if (Source != EPlayerStatusSource::Unknown)
    {
        Existing.Source = Source;
    }

    if (bChanged)
    {
        OnStatusEffectsChanged.Broadcast();
    }
    return true;
}

float UPlayerStatusEffectComponent::GetStressEscalation() const
{
    return FMath::Clamp(1.0f + RecentStressEvents * StressEscalationPerRecentEvent,
        1.0f, FMath::Max(1.0f, MaxStressEscalation));
}

float UPlayerStatusEffectComponent::ApplyStressEvent(EPlayerStressEvent Event, float Intensity)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return 0.0f;
    }

    float Base = 0.0f;
    switch (Event)
    {
    case EPlayerStressEvent::SurvivedEncounter: Base = StressPerSurvivedEncounter; break;
    case EPlayerStressEvent::FailedTask:        Base = StressPerFailedTask; break;
    case EPlayerStressEvent::NearEntrapment:    Base = StressPerNearEntrapment; break;
    }

    // Escalation is read before the event is remembered, so the first event of a run costs its base
    // and not base-times-something. An event should not make itself worse.
    const float Added = Base * FMath::Max(0.0f, Intensity) * GetStressEscalation();
    RecentStressEvents += 1.0f;

    if (Added <= KINDA_SMALL_NUMBER)
    {
        return 0.0f;
    }

    AccumulateStatusEffect(EPlayerStatusEffect::AcuteStress, Added, StressEventDurationSeconds,
        EPlayerStatusSource::Psychological);
    return Added;
}

float UPlayerStatusEffectComponent::GetWeldingBackfireChance(float ToolCondition) const
{
    const float Condition = FMath::Clamp(ToolCondition, 0.0f, 1.0f);
    const float Safe = FMath::Clamp(WeldingBackfireSafeCondition, 0.0f, 1.0f);
    if (Condition >= Safe || Safe <= KINDA_SMALL_NUMBER)
    {
        return 0.0f;
    }

    // Linear from nothing at the safe threshold to the maximum at zero. Linear rather than curved
    // because the player has to be able to predict it from a condition readout, and a curve would
    // make "half worn" mean something different from what the number says.
    const float HowFarPastSafe = (Safe - Condition) / Safe;
    return FMath::Clamp(HowFarPastSafe * WeldingBackfireMaxChance, 0.0f, 1.0f);
}

float UPlayerStatusEffectComponent::ApplyWeldingBurn(float ToolCondition)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return 0.0f;
    }

    // Worse the worse the gear was. A weld that backfires on nearly-good equipment stings; one that
    // backfires on gear the player has been ignoring for an hour is a real injury.
    const float Condition = FMath::Clamp(ToolCondition, 0.0f, 1.0f);
    const float Severity = FMath::Lerp(WeldingBurnSeverityAtZeroCondition, 0.0f, Condition);
    if (Severity <= KINDA_SMALL_NUMBER)
    {
        return 0.0f;
    }

    AccumulateStatusEffect(EPlayerStatusEffect::BurnTrauma, Severity, -1.0f, EPlayerStatusSource::Fire);
    return Severity;
}

bool UPlayerStatusEffectComponent::ApplyWeldingBackfire(float ToolCondition)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return false;
    }

    const float Chance = GetWeldingBackfireChance(ToolCondition);
    if (Chance <= KINDA_SMALL_NUMBER || FMath::FRand() >= Chance)
    {
        return false;
    }

    ApplyWeldingBurn(ToolCondition);
    return true;
}

float UPlayerStatusEffectComponent::ApplyHeatSourceExposure(float NormalizedProximity, float DeltaTime)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return 0.0f;
    }

    const float Proximity = FMath::Clamp(NormalizedProximity, 0.0f, 1.0f);
    if (Proximity <= KINDA_SMALL_NUMBER || DeltaTime <= 0.0f)
    {
        return 0.0f;
    }

    const float Added = Proximity * Proximity * BurnSeverityPerSecondAtContact * DeltaTime;
    if (Added <= KINDA_SMALL_NUMBER)
    {
        return 0.0f;
    }

    AccumulateStatusEffect(EPlayerStatusEffect::BurnTrauma, Added, -1.0f, EPlayerStatusSource::Fire);
    return Added;
}

bool UPlayerStatusEffectComponent::RemoveStatusEffect(EPlayerStatusEffect Type)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return false;
    }
    const int32 Removed = ActiveStatusEffects.RemoveAll([Type](const FPlayerStatusEffectState& Effect) { return Effect.Type == Type; });
    if (Removed > 0)
    {
        OnStatusEffectsChanged.Broadcast();
    }
    return Removed > 0;
}

bool UPlayerStatusEffectComponent::TreatStatusEffect(EPlayerStatusEffect Type, float TreatmentStrength)
{
    if ((GetOwner() && !GetOwner()->HasAuthority()) || TreatmentStrength <= 0.0f)
    {
        return false;
    }
    const int32 Index = FindEffectIndex(Type);
    if (Index == INDEX_NONE)
    {
        return false;
    }
    ActiveStatusEffects[Index].Severity -= TreatmentStrength;
    if (ActiveStatusEffects[Index].Severity <= KINDA_SMALL_NUMBER)
    {
        ActiveStatusEffects.RemoveAt(Index);
    }
    OnStatusEffectsChanged.Broadcast();
    return true;
}

bool UPlayerStatusEffectComponent::TreatMostSevereStatusEffect(float TreatmentStrength)
{
    if (ActiveStatusEffects.IsEmpty())
    {
        return false;
    }
    int32 WorstIndex = 0;
    for (int32 Index = 1; Index < ActiveStatusEffects.Num(); ++Index)
    {
        const float CandidatePriority = ActiveStatusEffects[Index].Severity
            + (GetClinicalSeverity(ActiveStatusEffects[Index].Type) == EPlayerStatusSeverity::Critical ? 1.0f : 0.0f);
        const float WorstPriority = ActiveStatusEffects[WorstIndex].Severity
            + (GetClinicalSeverity(ActiveStatusEffects[WorstIndex].Type) == EPlayerStatusSeverity::Critical ? 1.0f : 0.0f);
        if (CandidatePriority > WorstPriority)
        {
            WorstIndex = Index;
        }
    }
    return TreatStatusEffect(ActiveStatusEffects[WorstIndex].Type, TreatmentStrength);
}

void UPlayerStatusEffectComponent::ApplyEnvironmentalExposure(const FPhysicsEnvironmentState& EnvironmentState, float Intensity)
{
    if (GetOwner() && !GetOwner()->HasAuthority())
    {
        return;
    }
    const float Exposure = FMath::Clamp(Intensity, 0.0f, 1.0f);
    if (EnvironmentState.bVacuumZone || EnvironmentState.AmbientPressureKPa < 20.0f)
    {
        ApplyStatusEffect(EPlayerStatusEffect::Decompression, Exposure, 12.0f, EPlayerStatusSource::Atmosphere);
    }
    if (EnvironmentState.TemperatureC <= ColdStressTemperatureC)
    {
        const float Severity = FMath::Clamp((ColdStressTemperatureC - EnvironmentState.TemperatureC) / 80.0f, 0.15f, 1.0f) * Exposure;
        ApplyStatusEffect(EPlayerStatusEffect::Hypothermia, Severity, 45.0f, EPlayerStatusSource::Temperature);
    }
    if (EnvironmentState.TemperatureC >= HeatStressTemperatureC)
    {
        const float Severity = FMath::Clamp((EnvironmentState.TemperatureC - HeatStressTemperatureC) / 100.0f, 0.15f, 1.0f) * Exposure;
        ApplyStatusEffect(EPlayerStatusEffect::Hyperthermia, Severity, 45.0f, EPlayerStatusSource::Temperature);
    }
    if (EnvironmentState.bMicrogravityZone && CharacterOwner && CharacterOwner->Stability < 0.65f)
    {
        ApplyStatusEffect(EPlayerStatusEffect::SpaceMotionSickness, (1.0f - CharacterOwner->Stability) * Exposure, 90.0f, EPlayerStatusSource::Microgravity);
    }
}

void UPlayerStatusEffectComponent::ClearAllStatusEffects()
{
    if ((GetOwner() && !GetOwner()->HasAuthority()) || ActiveStatusEffects.IsEmpty())
    {
        return;
    }
    ActiveStatusEffects.Reset();
    OnStatusEffectsChanged.Broadcast();
}

bool UPlayerStatusEffectComponent::HasStatusEffect(EPlayerStatusEffect Type) const
{
    return FindEffectIndex(Type) != INDEX_NONE;
}

float UPlayerStatusEffectComponent::GetStatusSeverity(EPlayerStatusEffect Type) const
{
    const int32 Index = FindEffectIndex(Type);
    return Index == INDEX_NONE ? 0.0f : ActiveStatusEffects[Index].Severity;
}

FText UPlayerStatusEffectComponent::GetStatusDisplayName(EPlayerStatusEffect Type)
{
    switch (Type)
    {
    case EPlayerStatusEffect::Hypoxia: return NSLOCTEXT("PlayerStatus", "Hypoxia", "Hypoxia");
    case EPlayerStatusEffect::JumpPsychosis: return NSLOCTEXT("PlayerStatus", "JumpPsychosis", "Jump Psychosis");
    case EPlayerStatusEffect::RadiationSickness: return NSLOCTEXT("PlayerStatus", "RadiationSickness", "Radiation Sickness");
    case EPlayerStatusEffect::Decompression: return NSLOCTEXT("PlayerStatus", "Decompression", "Decompression Trauma");
    case EPlayerStatusEffect::Hypothermia: return NSLOCTEXT("PlayerStatus", "Hypothermia", "Hypothermia");
    case EPlayerStatusEffect::Hyperthermia: return NSLOCTEXT("PlayerStatus", "Hyperthermia", "Heat Stress");
    case EPlayerStatusEffect::SpaceMotionSickness: return NSLOCTEXT("PlayerStatus", "SpaceMotionSickness", "Space Motion Sickness");
    case EPlayerStatusEffect::CarbonDioxideToxicity: return NSLOCTEXT("PlayerStatus", "CarbonDioxideToxicity", "CO2 Toxicity");
    case EPlayerStatusEffect::AcuteStress: return NSLOCTEXT("PlayerStatus", "AcuteStress", "Acute Stress");
    case EPlayerStatusEffect::Hemorrhage: return NSLOCTEXT("PlayerStatus", "Hemorrhage", "Hemorrhage");
    case EPlayerStatusEffect::Fracture: return NSLOCTEXT("PlayerStatus", "Fracture", "Fracture");
    case EPlayerStatusEffect::BurnTrauma: return NSLOCTEXT("PlayerStatus", "BurnTrauma", "Burn Trauma");
    default: return FText::GetEmpty();
    }
}

FText UPlayerStatusEffectComponent::GetStatusDescription(EPlayerStatusEffect Type)
{
    switch (Type)
    {
    case EPlayerStatusEffect::Hypoxia: return NSLOCTEXT("PlayerStatus", "HypoxiaDescription", "Insufficient oxygen is impairing cognition and tissue function.");
    case EPlayerStatusEffect::JumpPsychosis: return NSLOCTEXT("PlayerStatus", "JumpPsychosisDescription", "Unshielded jump exposure is destabilizing perception and judgment.");
    case EPlayerStatusEffect::RadiationSickness: return NSLOCTEXT("PlayerStatus", "RadiationDescription", "Ionizing radiation exposure is causing systemic injury.");
    case EPlayerStatusEffect::Decompression: return NSLOCTEXT("PlayerStatus", "DecompressionDescription", "Rapid pressure loss has injured lungs and soft tissue.");
    case EPlayerStatusEffect::Hypothermia: return NSLOCTEXT("PlayerStatus", "HypothermiaDescription", "Core temperature is dangerously low.");
    case EPlayerStatusEffect::Hyperthermia: return NSLOCTEXT("PlayerStatus", "HyperthermiaDescription", "Heat load is exceeding the body's cooling capacity.");
    case EPlayerStatusEffect::SpaceMotionSickness: return NSLOCTEXT("PlayerStatus", "MotionDescription", "Vestibular conflict is reducing coordination and task performance.");
    case EPlayerStatusEffect::CarbonDioxideToxicity: return NSLOCTEXT("PlayerStatus", "CO2Description", "Carbon dioxide accumulation is causing headache, panic, and confusion.");
    case EPlayerStatusEffect::AcuteStress: return NSLOCTEXT("PlayerStatus", "StressDescription", "Acute stress is degrading fine motor control and decision speed.");
    case EPlayerStatusEffect::Hemorrhage: return NSLOCTEXT("PlayerStatus", "HemorrhageDescription", "Ongoing blood loss requires immediate control.");
    case EPlayerStatusEffect::Fracture: return NSLOCTEXT("PlayerStatus", "FractureDescription", "Skeletal trauma is limiting safe movement.");
    case EPlayerStatusEffect::BurnTrauma: return NSLOCTEXT("PlayerStatus", "BurnDescription", "Thermal tissue injury is causing pain and fluid loss.");
    default: return FText::GetEmpty();
    }
}

FText UPlayerStatusEffectComponent::GetRecommendedTreatment(EPlayerStatusEffect Type)
{
    switch (Type)
    {
    case EPlayerStatusEffect::Hypoxia: return NSLOCTEXT("PlayerStatus", "TreatHypoxia", "Restore oxygen and verify the suit seal.");
    case EPlayerStatusEffect::JumpPsychosis: return NSLOCTEXT("PlayerStatus", "TreatPsychosis", "Move to a calm environment; administer neuro-stabilization.");
    case EPlayerStatusEffect::RadiationSickness: return NSLOCTEXT("PlayerStatus", "TreatRadiation", "Leave the radiation field and begin medical stabilization.");
    case EPlayerStatusEffect::Decompression: return NSLOCTEXT("PlayerStatus", "TreatDecompression", "Repressurize, provide oxygen, and avoid rapid recompression.");
    case EPlayerStatusEffect::Hypothermia: return NSLOCTEXT("PlayerStatus", "TreatCold", "Rewarm gradually in a pressurized compartment.");
    case EPlayerStatusEffect::Hyperthermia: return NSLOCTEXT("PlayerStatus", "TreatHeat", "Cool the patient and restore fluids and oxygen.");
    case EPlayerStatusEffect::SpaceMotionSickness: return NSLOCTEXT("PlayerStatus", "TreatMotion", "Stabilize orientation or use functioning cryo.");
    case EPlayerStatusEffect::CarbonDioxideToxicity: return NSLOCTEXT("PlayerStatus", "TreatCO2", "Restore scrubbing and move to clean atmosphere immediately.");
    case EPlayerStatusEffect::AcuteStress: return NSLOCTEXT("PlayerStatus", "TreatStress", "Remove immediate threats and provide assisted recovery.");
    case EPlayerStatusEffect::Hemorrhage: return NSLOCTEXT("PlayerStatus", "TreatBleeding", "Control bleeding before treating other injuries.");
    case EPlayerStatusEffect::Fracture: return NSLOCTEXT("PlayerStatus", "TreatFracture", "Immobilize the injury and restrict thrust maneuvers.");
    case EPlayerStatusEffect::BurnTrauma: return NSLOCTEXT("PlayerStatus", "TreatBurn", "Stop the heat source, cool tissue, and cover the wound.");
    default: return FText::GetEmpty();
    }
}

EPlayerStatusEffect UPlayerStatusEffectComponent::GetMostUrgentStatusEffect(bool& bHasEffect) const
{
    bHasEffect = !ActiveStatusEffects.IsEmpty();
    if (!bHasEffect) return EPlayerStatusEffect::Hypoxia;
    int32 BestIndex = 0;
    for (int32 Index = 1; Index < ActiveStatusEffects.Num(); ++Index)
    {
        const float Candidate = ActiveStatusEffects[Index].Severity
            + (ActiveStatusEffects[Index].Type == EPlayerStatusEffect::Hemorrhage ? 0.75f : 0.0f)
            + (ActiveStatusEffects[Index].Type == EPlayerStatusEffect::Decompression ? 0.5f : 0.0f);
        const float Best = ActiveStatusEffects[BestIndex].Severity
            + (ActiveStatusEffects[BestIndex].Type == EPlayerStatusEffect::Hemorrhage ? 0.75f : 0.0f)
            + (ActiveStatusEffects[BestIndex].Type == EPlayerStatusEffect::Decompression ? 0.5f : 0.0f);
        if (Candidate > Best) BestIndex = Index;
    }
    return ActiveStatusEffects[BestIndex].Type;
}

EPlayerStatusSeverity UPlayerStatusEffectComponent::GetClinicalSeverity(EPlayerStatusEffect Type) const
{
    const float Severity = GetStatusSeverity(Type);
    if (Severity >= 0.85f) return EPlayerStatusSeverity::Critical;
    if (Severity >= 0.6f) return EPlayerStatusSeverity::Severe;
    if (Severity >= 0.3f) return EPlayerStatusSeverity::Moderate;
    return EPlayerStatusSeverity::Minor;
}

float UPlayerStatusEffectComponent::GetMobilityMultiplier() const
{
    const float Fracture = GetStatusSeverity(EPlayerStatusEffect::Fracture);
    const float Hypoxia = GetStatusSeverity(EPlayerStatusEffect::Hypoxia);
    const float Thermal = FMath::Max(GetStatusSeverity(EPlayerStatusEffect::Hypothermia), GetStatusSeverity(EPlayerStatusEffect::Hyperthermia));
    return FMath::Clamp(1.0f - Fracture * 0.55f - Hypoxia * 0.2f - Thermal * 0.2f, 0.25f, 1.0f);
}

float UPlayerStatusEffectComponent::GetTaskEfficiencyMultiplier() const
{
    const float Cognitive = FMath::Max3(GetStatusSeverity(EPlayerStatusEffect::Hypoxia),
        GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis), GetStatusSeverity(EPlayerStatusEffect::CarbonDioxideToxicity));
    const float Coordination = FMath::Max(GetStatusSeverity(EPlayerStatusEffect::SpaceMotionSickness), GetStatusSeverity(EPlayerStatusEffect::AcuteStress));
    return FMath::Clamp(1.0f - Cognitive * 0.45f - Coordination * 0.3f, 0.2f, 1.0f);
}

float UPlayerStatusEffectComponent::GetAdditionalOxygenDrainMultiplier() const
{
    return 1.0f + GetStatusSeverity(EPlayerStatusEffect::Hyperthermia) * 0.5f
        + GetStatusSeverity(EPlayerStatusEffect::AcuteStress) * 0.35f
        + GetStatusSeverity(EPlayerStatusEffect::CarbonDioxideToxicity) * 0.25f;
}

void UPlayerStatusEffectComponent::OnRep_ActiveStatusEffects()
{
    OnStatusEffectsChanged.Broadcast();
}

int32 UPlayerStatusEffectComponent::FindEffectIndex(EPlayerStatusEffect Type) const
{
    return ActiveStatusEffects.IndexOfByPredicate([Type](const FPlayerStatusEffectState& Effect) { return Effect.Type == Type; });
}

void UPlayerStatusEffectComponent::UpdatePhysiologicalStatuses()
{
    if (CharacterOwner->OxygenLevelPercent < HypoxiaStartsBelowOxygenPercent)
    {
        const float Severity = 1.0f - CharacterOwner->OxygenLevelPercent / FMath::Max(1.0f, HypoxiaStartsBelowOxygenPercent);
        const int32 Index = FindEffectIndex(EPlayerStatusEffect::Hypoxia);
        if (Index == INDEX_NONE) ApplyStatusEffect(EPlayerStatusEffect::Hypoxia, Severity, -1.0f, EPlayerStatusSource::Atmosphere);
        else ActiveStatusEffects[Index].Severity = FMath::Clamp(Severity, 0.0f, 1.0f);
    }
    else if (CharacterOwner->OxygenLevelPercent >= HypoxiaClearsAboveOxygenPercent)
    {
        RemoveStatusEffect(EPlayerStatusEffect::Hypoxia);
    }

    const float DoseLimit = CharacterOwner->GetHazardComponent()
        ? CharacterOwner->GetHazardComponent()->RadiationDoseLimitSv : 0.75f;
    if (CharacterOwner->RadiationDoseSv >= DoseLimit * 0.35f)
    {
        ApplyStatusEffect(EPlayerStatusEffect::RadiationSickness,
            FMath::Clamp(CharacterOwner->RadiationDoseSv / FMath::Max(0.01f, DoseLimit), 0.0f, 1.0f), -1.0f, EPlayerStatusSource::Radiation);
    }
}

void UPlayerStatusEffectComponent::ApplyConsequences(float DeltaTime)
{
    const float Hypoxia = GetStatusSeverity(EPlayerStatusEffect::Hypoxia);
    const float Decompression = GetStatusSeverity(EPlayerStatusEffect::Decompression);
    const float Radiation = GetStatusSeverity(EPlayerStatusEffect::RadiationSickness);
    const float Thermal = FMath::Max(GetStatusSeverity(EPlayerStatusEffect::Hypothermia), GetStatusSeverity(EPlayerStatusEffect::Hyperthermia));
    const float Psychosis = GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis);
    const float MotionSickness = GetStatusSeverity(EPlayerStatusEffect::SpaceMotionSickness);
    const float CarbonDioxide = GetStatusSeverity(EPlayerStatusEffect::CarbonDioxideToxicity);
    const float AcuteStress = GetStatusSeverity(EPlayerStatusEffect::AcuteStress);
    const float Hemorrhage = GetStatusSeverity(EPlayerStatusEffect::Hemorrhage);
    const float Burns = GetStatusSeverity(EPlayerStatusEffect::BurnTrauma);

    const float DamagePerSecond = SevereHypoxiaDamagePerSecond * FMath::Square(Hypoxia)
        + DecompressionDamagePerSecond * Decompression
        + 1.5f * Radiation + 1.0f * Thermal + HemorrhageDamagePerSecond * Hemorrhage + 1.5f * Burns;
    CharacterOwner->HealthPercent = FMath::Clamp(CharacterOwner->HealthPercent - DamagePerSecond * DeltaTime, 0.0f, 100.0f);
    CharacterOwner->Stability = FMath::Clamp(CharacterOwner->Stability
        - (0.025f * Psychosis + 0.01f * MotionSickness + 0.018f * CarbonDioxide + 0.012f * AcuteStress) * DeltaTime, 0.0f, 1.0f);
    if (CharacterOwner->HealthPercent <= 0.0f)
    {
        CharacterOwner->bIsDead = true;
    }
}
