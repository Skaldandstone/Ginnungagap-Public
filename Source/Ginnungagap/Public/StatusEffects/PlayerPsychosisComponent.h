#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "StatusEffects/PlayerHallucinationActor.h"
#include "PlayerPsychosisComponent.generated.h"

class ACoopSurvivalCharacter;
class USoundBase;

UENUM(BlueprintType)
enum class EPsychosisVoiceIntent : uint8
{
    Warning,
    Doubt,
    Accusation,
    FalseGuidance,
    Grounding
};

UENUM(BlueprintType)
enum class EPsychosisPhase : uint8
{
    Stable,
    Uneasy,
    Distorted,
    Break
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnPsychosisEpisode, EPlayerHallucinationType, Type, float, Severity, float, Duration);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnPsychosisVoice, EPsychosisVoiceIntent, Intent, const FText&, Line,
    FVector, PerceivedLocation, float, Severity);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnPsychosisPhaseChanged, EPsychosisPhase, PreviousPhase, EPsychosisPhase, NewPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnPsychosisRealityCheck, bool, bPerceptionContradicted, float, ReliefDuration);

/** Local-only perceptual symptoms driven by the replicated authoritative psychosis severity. */
UCLASS(ClassGroup=(Survival), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPlayerPsychosisComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPlayerPsychosisComponent();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    bool IsFalseInfectionVisible() const { return FalseInfectionSecondsRemaining > 0.0f; }

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    float GetFalseInfectionSeverity() const { return FalseInfectionSeverity; }

    UFUNCTION(BlueprintCallable, Category="Survival|Psychosis")
    void TriggerEpisodeForTesting(EPlayerHallucinationType Type, float Severity = 0.75f);

    /** Temporarily suppresses episodes; suitable for cryo, medication, or a grounding interaction. */
    UFUNCTION(BlueprintCallable, Category="Survival|Psychosis")
    void ApplyGrounding(float DurationSeconds, float TreatmentStrength = 0.1f);

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    bool IsGrounded() const { return GroundingSecondsRemaining > 0.0f; }

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    EPsychosisPhase GetCurrentPhase() const { return CurrentPhase; }

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    float GetEffectiveSeverity() const { return EffectiveSeverity; }

    /** Checks suit telemetry against the perception layer. A scanner or teammate confirmation gives stronger relief. */
    UFUNCTION(BlueprintCallable, Category="Survival|Psychosis")
    bool PerformRealityCheck(bool bHasExternalConfirmation = false);

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    static EPsychosisPhase GetPhaseForSeverity(float Severity);

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    static FText GetPhaseDisplayName(EPsychosisPhase Phase);

    UPROPERTY(BlueprintAssignable, Category="Survival|Psychosis")
    FOnPsychosisEpisode OnPsychosisEpisode;

    UPROPERTY(BlueprintAssignable, Category="Survival|Psychosis")
    FOnPsychosisVoice OnPsychosisVoice;

    UPROPERTY(BlueprintAssignable, Category="Survival|Psychosis")
    FOnPsychosisPhaseChanged OnPsychosisPhaseChanged;

    UPROPERTY(BlueprintAssignable, Category="Survival|Psychosis")
    FOnPsychosisRealityCheck OnPsychosisRealityCheck;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis")
    float MinimumPsychosisSeverity = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis")
    FVector2D EpisodeIntervalAtMinimum = FVector2D(20.0f, 45.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis")
    FVector2D EpisodeIntervalAtMaximum = FVector2D(4.0f, 12.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis", meta=(ClampMin="0.0", ClampMax="1.0"))
    float StressAmplification = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis", meta=(ClampMin="0.0", ClampMax="1.0"))
    float HypoxiaAmplification = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis", meta=(ClampMin="0.0", ClampMax="1.0"))
    float CarbonDioxideAmplification = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis", meta=(ClampMin="0.0"))
    float RealityCheckCooldownSeconds = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Psychosis|Audio")
    TObjectPtr<USoundBase> PhantomBloomSound;

private:
    void ScheduleNextEpisode(float Severity);
    void TriggerEpisode(EPlayerHallucinationType Type, float Severity);
    void SpawnVisualEpisode(EPlayerHallucinationType Type, float Severity, float Duration);
    EPlayerHallucinationType ChooseEpisodeType(float Severity);
    float CalculateEffectiveSeverity() const;
    void ClearPerceptualArtifacts();
    void UpdatePhase(float Severity);

    UPROPERTY()
    TObjectPtr<ACoopSurvivalCharacter> CharacterOwner;

    float SecondsUntilNextEpisode = 0.0f;
    float FalseInfectionSecondsRemaining = 0.0f;
    float FalseInfectionSeverity = 0.0f;
    float GroundingSecondsRemaining = 0.0f;
    float RealityCheckCooldownRemaining = 0.0f;
    float EffectiveSeverity = 0.0f;
    EPsychosisPhase CurrentPhase = EPsychosisPhase::Stable;
    EPlayerHallucinationType LastEpisodeType = EPlayerHallucinationType::BloomGrowth;
    int32 ConsecutiveEpisodeCount = 0;

    UPROPERTY(Transient)
    TArray<TObjectPtr<APlayerHallucinationActor>> ActiveVisuals;
    FRandomStream HallucinationRandom;

    void EmitVoice(float Severity, bool bForceGrounding = false);
};
