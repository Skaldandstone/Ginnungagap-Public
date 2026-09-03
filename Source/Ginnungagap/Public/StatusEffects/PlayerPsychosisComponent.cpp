#include "StatusEffects/PlayerPsychosisComponent.h"

#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

UPlayerPsychosisComponent::UPlayerPsychosisComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.1f;
    bAutoActivate = true;
}

void UPlayerPsychosisComponent::BeginPlay()
{
    Super::BeginPlay();
    CharacterOwner = Cast<ACoopSurvivalCharacter>(GetOwner());
    HallucinationRandom.Initialize(FMath::Rand());
    ScheduleNextEpisode(0.5f);
    if (!PhantomBloomSound)
    {
        PhantomBloomSound = LoadObject<USoundBase>(nullptr,
            TEXT("/Game/Assets/Ships/Production/Audio/S_Bloom_Atmosphere_Loop.S_Bloom_Atmosphere_Loop"));
    }
}

void UPlayerPsychosisComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!CharacterOwner || !CharacterOwner->IsLocallyControlled() || CharacterOwner->bIsDead) return;

    FalseInfectionSecondsRemaining = FMath::Max(0.0f, FalseInfectionSecondsRemaining - DeltaTime);
    GroundingSecondsRemaining = FMath::Max(0.0f, GroundingSecondsRemaining - DeltaTime);
    RealityCheckCooldownRemaining = FMath::Max(0.0f, RealityCheckCooldownRemaining - DeltaTime);
    ActiveVisuals.RemoveAll([](const APlayerHallucinationActor* Visual) { return !IsValid(Visual); });
    EffectiveSeverity = CalculateEffectiveSeverity();
    UpdatePhase(EffectiveSeverity);
    if (GroundingSecondsRemaining > 0.0f) return;
    const float Severity = EffectiveSeverity;
    if (Severity < MinimumPsychosisSeverity)
    {
        SecondsUntilNextEpisode = FMath::Max(SecondsUntilNextEpisode, 2.0f);
        return;
    }

    SecondsUntilNextEpisode -= DeltaTime;
    if (SecondsUntilNextEpisode <= 0.0f)
    {
        TriggerEpisode(ChooseEpisodeType(Severity), Severity);
        ScheduleNextEpisode(Severity);
    }
}

EPsychosisPhase UPlayerPsychosisComponent::GetPhaseForSeverity(float Severity)
{
    if (Severity < 0.2f) return EPsychosisPhase::Stable;
    if (Severity < 0.45f) return EPsychosisPhase::Uneasy;
    if (Severity < 0.7f) return EPsychosisPhase::Distorted;
    return EPsychosisPhase::Break;
}

FText UPlayerPsychosisComponent::GetPhaseDisplayName(EPsychosisPhase Phase)
{
    switch (Phase)
    {
    case EPsychosisPhase::Stable: return NSLOCTEXT("Psychosis", "PhaseStable", "Perception stable");
    case EPsychosisPhase::Uneasy: return NSLOCTEXT("Psychosis", "PhaseUneasy", "Perceptual unease");
    case EPsychosisPhase::Distorted: return NSLOCTEXT("Psychosis", "PhaseDistorted", "Perception distorted");
    case EPsychosisPhase::Break: return NSLOCTEXT("Psychosis", "PhaseBreak", "Reality break");
    default: return FText::GetEmpty();
    }
}

float UPlayerPsychosisComponent::CalculateEffectiveSeverity() const
{
    const UPlayerStatusEffectComponent* StatusEffects = CharacterOwner ? CharacterOwner->GetStatusEffectComponent() : nullptr;
    if (!StatusEffects) return 0.0f;
    const float Base = StatusEffects->GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis);
    const float Amplification =
        StatusEffects->GetStatusSeverity(EPlayerStatusEffect::AcuteStress) * StressAmplification +
        StatusEffects->GetStatusSeverity(EPlayerStatusEffect::Hypoxia) * HypoxiaAmplification +
        StatusEffects->GetStatusSeverity(EPlayerStatusEffect::CarbonDioxideToxicity) * CarbonDioxideAmplification;
    return FMath::Clamp(Base + Amplification * Base, 0.0f, 1.0f);
}

void UPlayerPsychosisComponent::UpdatePhase(float Severity)
{
    const EPsychosisPhase NewPhase = GetPhaseForSeverity(Severity);
    if (NewPhase == CurrentPhase) return;
    const EPsychosisPhase PreviousPhase = CurrentPhase;
    CurrentPhase = NewPhase;
    OnPsychosisPhaseChanged.Broadcast(PreviousPhase, NewPhase);
}

EPlayerHallucinationType UPlayerPsychosisComponent::ChooseEpisodeType(float Severity)
{
    const int32 MaxType = Severity >= 0.7f ? 4 : (Severity >= 0.45f ? 3 : 2);
    EPlayerHallucinationType Candidate = LastEpisodeType;
    for (int32 Attempt = 0; Attempt < 4; ++Attempt)
    {
        Candidate = static_cast<EPlayerHallucinationType>(HallucinationRandom.RandRange(0, MaxType));
        if (Candidate != LastEpisodeType || ConsecutiveEpisodeCount == 0) break;
    }
    ConsecutiveEpisodeCount = Candidate == LastEpisodeType ? ConsecutiveEpisodeCount + 1 : 1;
    LastEpisodeType = Candidate;
    return Candidate;
}

void UPlayerPsychosisComponent::ScheduleNextEpisode(float Severity)
{
    const float Alpha = FMath::Clamp((Severity - MinimumPsychosisSeverity) / FMath::Max(0.01f, 1.0f - MinimumPsychosisSeverity), 0.0f, 1.0f);
    const FVector2D Interval = FMath::Lerp(EpisodeIntervalAtMinimum, EpisodeIntervalAtMaximum, Alpha);
    SecondsUntilNextEpisode = HallucinationRandom.FRandRange(Interval.X, Interval.Y);
}

void UPlayerPsychosisComponent::TriggerEpisodeForTesting(EPlayerHallucinationType Type, float Severity)
{
    if (CharacterOwner && CharacterOwner->IsLocallyControlled()) TriggerEpisode(Type, FMath::Clamp(Severity, 0.0f, 1.0f));
}

void UPlayerPsychosisComponent::TriggerEpisode(EPlayerHallucinationType Type, float Severity)
{
    const float Duration = HallucinationRandom.FRandRange(1.0f, FMath::Lerp(2.0f, 6.0f, Severity));
    if (Type == EPlayerHallucinationType::FalseInfection)
    {
        FalseInfectionSeverity = FMath::Clamp(FMath::Lerp(0.35f, 1.0f, Severity), 0.0f, 1.0f);
        FalseInfectionSecondsRemaining = Duration;
    }
    else if (Type == EPlayerHallucinationType::PhantomSound)
    {
        EmitVoice(Severity);
        if (PhantomBloomSound)
        {
            const FVector Offset(HallucinationRandom.FRandRange(-500.0f, 500.0f), HallucinationRandom.FRandRange(-500.0f, 500.0f), HallucinationRandom.FRandRange(-150.0f, 150.0f));
            UGameplayStatics::PlaySoundAtLocation(this, PhantomBloomSound, CharacterOwner->GetActorLocation() + Offset,
                FMath::Lerp(0.15f, 0.65f, Severity));
        }
    }
    else
    {
        SpawnVisualEpisode(Type, Severity, Duration);
    }
    OnPsychosisEpisode.Broadcast(Type, Severity, Duration);
}

void UPlayerPsychosisComponent::ApplyGrounding(float DurationSeconds, float TreatmentStrength)
{
    if (!CharacterOwner || !CharacterOwner->IsLocallyControlled()) return;
    GroundingSecondsRemaining = FMath::Max(GroundingSecondsRemaining, FMath::Max(0.0f, DurationSeconds));
    ClearPerceptualArtifacts();
    if (UPlayerStatusEffectComponent* StatusEffects = CharacterOwner->GetStatusEffectComponent())
    {
        if (CharacterOwner->HasAuthority()) StatusEffects->TreatStatusEffect(EPlayerStatusEffect::JumpPsychosis, TreatmentStrength);
    }
    EmitVoice(FMath::Clamp(TreatmentStrength + 0.2f, 0.0f, 1.0f), true);
}

bool UPlayerPsychosisComponent::PerformRealityCheck(bool bHasExternalConfirmation)
{
    if (!CharacterOwner || !CharacterOwner->IsLocallyControlled() || RealityCheckCooldownRemaining > 0.0f) return false;
    const bool bContradicted = FalseInfectionSecondsRemaining > 0.0f || ActiveVisuals.Num() > 0;
    const float Relief = bHasExternalConfirmation ? 12.0f : (bContradicted ? 6.0f : 2.0f);
    RealityCheckCooldownRemaining = RealityCheckCooldownSeconds;
    ClearPerceptualArtifacts();
    GroundingSecondsRemaining = FMath::Max(GroundingSecondsRemaining, Relief);
    SecondsUntilNextEpisode = FMath::Max(SecondsUntilNextEpisode, Relief + 2.0f);
    EmitVoice(bHasExternalConfirmation ? 0.65f : 0.35f, true);
    OnPsychosisRealityCheck.Broadcast(bContradicted, Relief);
    return bContradicted;
}

void UPlayerPsychosisComponent::ClearPerceptualArtifacts()
{
    FalseInfectionSecondsRemaining = 0.0f;
    FalseInfectionSeverity = 0.0f;
    for (APlayerHallucinationActor* Visual : ActiveVisuals)
    {
        if (IsValid(Visual)) Visual->Destroy();
    }
    ActiveVisuals.Reset();
}

void UPlayerPsychosisComponent::EmitVoice(float Severity, bool bForceGrounding)
{
    if (!CharacterOwner) return;
    const EPsychosisVoiceIntent Intent = bForceGrounding ? EPsychosisVoiceIntent::Grounding
        : static_cast<EPsychosisVoiceIntent>(HallucinationRandom.RandRange(0, Severity >= 0.65f ? 3 : 1));
    FText Line;
    switch (Intent)
    {
    case EPsychosisVoiceIntent::Warning: Line = NSLOCTEXT("Psychosis", "Warning", "Something moved behind you."); break;
    case EPsychosisVoiceIntent::Doubt: Line = NSLOCTEXT("Psychosis", "Doubt", "That reading changed. You cannot trust it."); break;
    case EPsychosisVoiceIntent::Accusation: Line = NSLOCTEXT("Psychosis", "Accusation", "They saw the infection. They are hiding it from you."); break;
    case EPsychosisVoiceIntent::FalseGuidance: Line = NSLOCTEXT("Psychosis", "FalseGuidance", "Do not enter cryo. The pod is compromised."); break;
    case EPsychosisVoiceIntent::Grounding: Line = NSLOCTEXT("Psychosis", "Grounding", "Breathe. Check the seal. Follow the real telemetry."); break;
    default: break;
    }
    const FVector Side = CharacterOwner->GetActorRightVector() * (HallucinationRandom.RandBool() ? 1.0f : -1.0f);
    const FVector PerceivedLocation = CharacterOwner->GetActorLocation() + Side * HallucinationRandom.FRandRange(80.0f, 260.0f)
        + CharacterOwner->GetActorUpVector() * HallucinationRandom.FRandRange(20.0f, 100.0f);
    OnPsychosisVoice.Broadcast(Intent, Line, PerceivedLocation, Severity);
}

void UPlayerPsychosisComponent::SpawnVisualEpisode(EPlayerHallucinationType Type, float Severity, float Duration)
{
    UWorld* World = GetWorld();
    if (!World) return;
    const FVector Forward = CharacterOwner->GetActorForwardVector();
    const FVector Right = CharacterOwner->GetActorRightVector();
    const float Distance = HallucinationRandom.FRandRange(350.0f, 900.0f);
    const FVector Location = CharacterOwner->GetActorLocation() + Forward * Distance
        + Right * HallucinationRandom.FRandRange(-450.0f, 450.0f) + FVector(0.0f, 0.0f, Type == EPlayerHallucinationType::BloomGrowth ? -85.0f : 0.0f);
    const FRotator Rotation = (CharacterOwner->GetActorLocation() - Location).Rotation();
    FActorSpawnParameters Params;
    Params.Owner = CharacterOwner;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    if (APlayerHallucinationActor* Visual = World->SpawnActor<APlayerHallucinationActor>(Location, Rotation, Params))
    {
        Visual->Configure(Type, Severity, Duration);
        ActiveVisuals.Add(Visual);
    }
}
