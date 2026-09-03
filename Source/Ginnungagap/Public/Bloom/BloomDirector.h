#pragma once

#include "CoreMinimal.h"
#include "TimerManager.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "BloomDirector.generated.h"

UENUM(BlueprintType)
enum class EBloomHazardType : uint8
{
    Radiation,
    Thermal,
    Vacuum,
    Microgravity,
    Dust
};

UENUM(BlueprintType)
enum class EBloomStage : uint8
{
    Latent,
    Colony,
    Swarm,
    Puppeteer,
    Infector,
    Manifestation
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBloomStageChanged, EBloomStage, NewStage);

/**
 * Evasion approaches the Bloom can learn to counter. Deliberately coarse: the organism adapts to
 * *how* the crew avoids it, not to individual inputs, so a player who varies their approach stays
 * ahead while one who leans on a single trick finds it stops working.
 */
UENUM(BlueprintType)
enum class EBloomStealthTactic : uint8
{
    /** Hiding in unpowered rooms. */
    Darkness,
    /** Holding still to avoid drawing attention. */
    Stillness,
    /** Pulling investigators away with thrown-object noise. */
    Distraction
};

UENUM(BlueprintType)
enum class EBloomPlayerActionType : uint8
{
    ReactivatedShipSystem,
    PerformedEVA,
    DispatchedDrone,
    PurgedCorruption
};

USTRUCT(BlueprintType)
struct FSystemVisitCriteria
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    TMap<EBloomHazardType, float> ExposureByType;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    float TotalHazardExposure = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    int32 ShipSystemsReactivated = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    int32 EVAExcursions = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    int32 DronesDispatched = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    int32 CorruptionPurges = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    float WeightedActionScore = 0.0f;
};

UCLASS()
class GINNUNGAGAP_API UBloomDirector : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    EBloomStage CurrentStage = EBloomStage::Latent;

    UPROPERTY(BlueprintAssignable, Category = "Bloom")
    FOnBloomStageChanged OnBloomStageChanged;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    float EvolutionProgress = 0.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float EvolutionProgressPerStage = 100.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float PassiveProgressPerTick = 0.1f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float TickInterval = 5.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float ResistanceGainPerExposure = 0.02f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float MaxHazardResistance = 0.9f;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    FSystemVisitCriteria CurrentVisitCriteria;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float JumpEvolutionBaseAmount = 25.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float JumpEvolutionPerExposurePoint = 0.05f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float JumpEvolutionPerPlayerAction = 2.0f;

    /** Counter-adaptation gained per point of tactic use, applied at each jump. */
    UPROPERTY(EditDefaultsOnly, Category = "Bloom|Stealth")
    float StealthCounterGainPerUse = 0.015f;

    /**
     * Floor on tactic effectiveness. Never zero: a tactic that stops working entirely removes a
     * verb from the player rather than pressuring them, and leaves an over-adapted Bloom with no
     * counterplay at all.
     */
    UPROPERTY(EditDefaultsOnly, Category = "Bloom|Stealth", meta = (ClampMin = "0.05", ClampMax = "1.0"))
    float MinStealthTacticEffectiveness = 0.4f;

    /**
     * Fraction of accumulated counter-adaptation that fades at each jump. Without this the Bloom
     * only ever hardens, so a player who switches approach could never recover ground they gave
     * up earlier in a long run.
     */
    UPROPERTY(EditDefaultsOnly, Category = "Bloom|Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float StealthCounterDecayPerJump = 0.2f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    EBloomStage MinStageForJumpSabotage = EBloomStage::Puppeteer;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float BaseSabotageChance = 0.25f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float SabotageChancePerStageBeyondMin = 0.2f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    EBloomStage MinStageForSelfDestructCounter = EBloomStage::Colony;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float BaseSelfDestructCounterChance = 0.2f;

    UPROPERTY(EditDefaultsOnly, Category = "Bloom")
    float SelfDestructCounterChancePerStageBeyondMin = 0.15f;

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void RegisterHazardExposure(EBloomHazardType HazardType, float Amount);

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void RegisterPlayerAction(EBloomPlayerActionType ActionType, float Weight = 1.0f);

    /**
     * Records that an evasion tactic was used *against an observer* and worked. Called during
     * play; it does not change effectiveness immediately. Accumulated use is converted into
     * counter-adaptation at the next jump, matching the design pillar that the Bloom evolves
     * during jumps and the crew discovers what changed only after arrival.
     */
    UFUNCTION(BlueprintCallable, Category = "Bloom|Stealth")
    void RegisterStealthTacticUse(EBloomStealthTactic Tactic, float Weight = 1.0f);

    /**
     * How well a tactic still works, 1.0 down to MinStealthTacticEffectiveness. Multiplied into
     * the benefit that tactic provides, so over-reliance erodes it while variety preserves it.
     */
    UFUNCTION(BlueprintPure, Category = "Bloom|Stealth")
    float GetStealthTacticEffectiveness(EBloomStealthTactic Tactic) const;

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool RollForJumpSabotage(AActor* System);

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool RollForSelfDestructCounter();

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool IsPresentThreat() const { return CurrentStage != EBloomStage::Latent; }

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void NotifySystemPurged(AActor* System);

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    float GetHazardEffectiveness(EBloomHazardType HazardType) const;

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void AdvanceStage();

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void OnSystemJump();

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool TryInfectHost(AActor* Host);

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool TryCorruptSystem(AActor* System);

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    EBloomStage GetCurrentStage() const { return CurrentStage; }

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    int32 GetInfectedHostCount() const { return InfectedHosts.Num(); }

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    int32 GetCorruptedSystemCount() const { return CorruptedSystems.Num(); }

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    bool IsFullyEradicated() const { return CurrentStage == EBloomStage::Latent && InfectedHosts.Num() == 0 && CorruptedSystems.Num() == 0; }

    // Destroying the ship with a successful self-destruct destroys the Bloom along with it.
    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void ForceResetBloom();

    /** Restores a persisted stage and emits a single state-change notification. */
    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void RestoreStage(EBloomStage RestoredStage);

protected:
    UPROPERTY()
    TMap<EBloomHazardType, float> HazardResistance;

    /** Tactic use accumulated during the current system visit, cleared at each jump. */
    UPROPERTY()
    TMap<EBloomStealthTactic, float> PendingStealthTacticUse;

    /** Permanent counter-adaptation per tactic, updated only at jumps. */
    UPROPERTY()
    TMap<EBloomStealthTactic, float> StealthTacticCounter;

    UPROPERTY()
    TArray<TWeakObjectPtr<AActor>> InfectedHosts;

    UPROPERTY()
    TArray<TWeakObjectPtr<AActor>> CorruptedSystems;

private:
    void TickPassiveProgress();

    FTimerHandle PassiveProgressTimerHandle;
};
