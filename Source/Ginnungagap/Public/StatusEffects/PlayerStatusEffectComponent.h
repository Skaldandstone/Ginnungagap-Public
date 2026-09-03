#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AstrophysicsHazardComponent.h"
#include "PlayerStatusEffectComponent.generated.h"

class ACoopSurvivalCharacter;

UENUM(BlueprintType)
enum class EPlayerStatusEffect : uint8
{
    Hypoxia,
    JumpPsychosis,
    RadiationSickness,
    Decompression,
    Hypothermia,
    Hyperthermia,
    SpaceMotionSickness,
    CarbonDioxideToxicity,
    AcuteStress,
    Hemorrhage,
    Fracture,
    BurnTrauma
};

UENUM(BlueprintType)
enum class EPlayerStatusSeverity : uint8
{
    Minor,
    Moderate,
    Severe,
    Critical
};

UENUM(BlueprintType)
enum class EPlayerStatusSource : uint8
{
    Unknown,
    Atmosphere,
    JumpExposure,
    Radiation,
    Temperature,
    Microgravity,
    Trauma,
    Fire,
    Psychological
};

/**
 * Things that raise acute stress.
 *
 * These are named for what happened to the player rather than for how much stress they cause, so a
 * caller does not have to know the balance numbers to report an event honestly. The severity of a
 * given event is a property of this component, and it is not constant: the same event costs more
 * when it follows others, which is what makes stress escalate rather than tick.
 */
UENUM(BlueprintType)
enum class EPlayerStressEvent : uint8
{
    /** Got out of an encounter alive. Surviving is not free. */
    SurvivedEncounter,

    /** Botched a repair, a hack, or any other activity that can be failed. */
    FailedTask,

    /** Nearly did not get back out of a gap. */
    NearEntrapment
};

USTRUCT(BlueprintType)
struct FPlayerStatusEffectState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    EPlayerStatusEffect Type = EPlayerStatusEffect::Hypoxia;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0.0", ClampMax="1.0"))
    float Severity = 0.0f;

    /** Negative values do not expire automatically. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float RemainingSeconds = -1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    EPlayerStatusSource Source = EPlayerStatusSource::Unknown;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPlayerStatusEffectsChanged);

UCLASS(ClassGroup=(Survival), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPlayerStatusEffectComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPlayerStatusEffectComponent();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool ApplyStatusEffect(EPlayerStatusEffect Type, float Severity, float DurationSeconds = -1.0f,
        EPlayerStatusSource Source = EPlayerStatusSource::Unknown);

    /**
     * Adds to a condition instead of taking the worse of the two.
     *
     * ApplyStatusEffect keeps whichever severity is higher, which is right for exposure -- being in
     * vacuum twice is not twice as decompressed. It is wrong for anything cumulative: a player who
     * escapes five encounters would end at the severity of the worst single one, so a run of near
     * misses would read the same as one bad moment.
     */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool AccumulateStatusEffect(EPlayerStatusEffect Type, float SeverityDelta,
        float DurationSeconds = -1.0f, EPlayerStatusSource Source = EPlayerStatusSource::Unknown);

    /**
     * Reports something that happened to the player, and raises acute stress by what it cost.
     *
     * Returns the severity actually added, which is not the base cost of the event: it is scaled by
     * how much has already happened recently. Escape one thing and it barely registers; escape four
     * in a minute and the fourth costs well over twice the first.
     */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    float ApplyStressEvent(EPlayerStressEvent Event, float Intensity = 1.0f);

    /** Current multiplier on stress events, 1.0 when nothing has happened lately. */
    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    float GetStressEscalation() const;

    /**
     * Chance that a weld attempted with gear in this condition goes wrong, 0..1.
     *
     * Separated from the roll so it can be reasoned about and tested without randomness. Zero at
     * and above WeldingBackfireSafeCondition: gear in decent shape does not backfire at all, so
     * durability is a thing the player manages rather than a slot machine they pull every time.
     */
    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    float GetWeldingBackfireChance(float ToolCondition) const;

    /**
     * Rolls for a backfire on a failed weld and burns the player if it goes wrong.
     *
     * Returns whether it backfired. Called on a failed welding activity rather than on every weld:
     * a clean weld with worn gear is a warning, and only a botched one bites.
     */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool ApplyWeldingBackfire(float ToolCondition);

    /** The burn itself, without the roll. Public because the roll is the part worth skipping in a test. */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    float ApplyWeldingBurn(float ToolCondition);

    /**
     * Standing too near a fire, accrued over time rather than applied as a hit.
     *
     * NormalizedProximity is 1.0 in the flame and 0.0 at the edge of its reach. Squared inside, so
     * the last step toward a fire costs far more than the first -- close is survivable and closer
     * is not, which is the read a player needs to be able to make from a distance.
     */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    float ApplyHeatSourceExposure(float NormalizedProximity, float DeltaTime);

    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool RemoveStatusEffect(EPlayerStatusEffect Type);

    /** Reduces severity; removing the condition when treatment reaches zero. */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool TreatStatusEffect(EPlayerStatusEffect Type, float TreatmentStrength);

    /** Medical-station helper that treats the patient's most severe active condition. */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    bool TreatMostSevereStatusEffect(float TreatmentStrength);

    /** Translates a physical environment into human-readable clinical conditions. */
    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    void ApplyEnvironmentalExposure(const FPhysicsEnvironmentState& EnvironmentState, float Intensity = 1.0f);

    UFUNCTION(BlueprintCallable, Category="Survival|Status Effects")
    void ClearAllStatusEffects();

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    bool HasStatusEffect(EPlayerStatusEffect Type) const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    float GetStatusSeverity(EPlayerStatusEffect Type) const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    TArray<FPlayerStatusEffectState> GetActiveStatusEffects() const { return ActiveStatusEffects; }

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    static FText GetStatusDisplayName(EPlayerStatusEffect Type);

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    static FText GetStatusDescription(EPlayerStatusEffect Type);

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    static FText GetRecommendedTreatment(EPlayerStatusEffect Type);

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    EPlayerStatusEffect GetMostUrgentStatusEffect(bool& bHasEffect) const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    EPlayerStatusSeverity GetClinicalSeverity(EPlayerStatusEffect Type) const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects|Consequences")
    float GetMobilityMultiplier() const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects|Consequences")
    float GetTaskEfficiencyMultiplier() const;

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects|Consequences")
    float GetAdditionalOxygenDrainMultiplier() const;

    UPROPERTY(BlueprintAssignable, Category="Survival|Status Effects")
    FOnPlayerStatusEffectsChanged OnStatusEffectsChanged;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Thresholds")
    float HypoxiaStartsBelowOxygenPercent = 30.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Thresholds")
    float HypoxiaClearsAboveOxygenPercent = 45.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Consequences")
    float SevereHypoxiaDamagePerSecond = 4.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Consequences")
    float DecompressionDamagePerSecond = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Thresholds")
    float ColdStressTemperatureC = -20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Thresholds")
    float HeatStressTemperatureC = 55.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Consequences")
    float HemorrhageDamagePerSecond = 5.0f;

    // --- acute stress ---------------------------------------------------------------------------
    // Base cost of each event before escalation. Near-entrapment is the dearest of the three on
    // purpose: it is the one where the player was helpless rather than merely losing.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="0.0", ClampMax="1.0"))
    float StressPerSurvivedEncounter = 0.14f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="0.0", ClampMax="1.0"))
    float StressPerFailedTask = 0.10f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="0.0", ClampMax="1.0"))
    float StressPerNearEntrapment = 0.18f;

    /** How much each remembered event adds to the cost of the next. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="0.0"))
    float StressEscalationPerRecentEvent = 0.45f;

    /**
     * Ceiling on escalation.
     *
     * Without one the spiral is unrecoverable rather than tense: stress degrades coordination,
     * which loses activities, which raises stress. A cap keeps a bad run punishing and survivable,
     * which is the difference between horror and a fail state that arrives on a timer.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="1.0"))
    float MaxStressEscalation = 2.5f;

    /** How long one event keeps making the next one worse. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="1.0"))
    float StressEventMemorySeconds = 90.0f;

    /** How long the stress from a single event lasts before it expires on its own. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Stress", meta=(ClampMin="1.0"))
    float StressEventDurationSeconds = 120.0f;

    // --- burns ----------------------------------------------------------------------------------
    /** At and above this condition a weld cannot backfire at all. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Burns", meta=(ClampMin="0.0", ClampMax="1.0"))
    float WeldingBackfireSafeCondition = 0.55f;

    /** Backfire chance with gear at zero condition. Not 1.0: worn gear is a risk, not a guarantee. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Burns", meta=(ClampMin="0.0", ClampMax="1.0"))
    float WeldingBackfireMaxChance = 0.65f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Burns", meta=(ClampMin="0.0", ClampMax="1.0"))
    float WeldingBurnSeverityAtZeroCondition = 0.55f;

    /** Burn accrued per second in the flame itself. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Status Effects|Burns", meta=(ClampMin="0.0"))
    float BurnSeverityPerSecondAtContact = 0.22f;

private:
    /**
     * Decaying count of recent stress events. Not an integer: it falls continuously so that
     * escalation eases off rather than dropping a step at a time, and a player who has been quiet
     * for a while is genuinely back to baseline instead of one event short of it.
     */
    float RecentStressEvents = 0.0f;

    UPROPERTY(ReplicatedUsing=OnRep_ActiveStatusEffects)
    TArray<FPlayerStatusEffectState> ActiveStatusEffects;

    UPROPERTY()
    TObjectPtr<ACoopSurvivalCharacter> CharacterOwner;

    UFUNCTION()
    void OnRep_ActiveStatusEffects();

    int32 FindEffectIndex(EPlayerStatusEffect Type) const;
    void UpdatePhysiologicalStatuses();
    void ApplyConsequences(float DeltaTime);
};
