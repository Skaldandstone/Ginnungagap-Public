#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "StarSystemTypes.h"
#include "JumpSequenceSubsystem.generated.h"

class ACoopSurvivalCharacter;
class ASensorArraySystem;

UENUM(BlueprintType)
enum class EJumpPhase : uint8
{
    Cruising,
    WarningCountdown,
    Jumping,
    Arrival
};

UCLASS()
class GINNUNGAGAP_API UJumpSequenceSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Deinitialize() override;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    EJumpPhase CurrentPhase = EJumpPhase::Cruising;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    TArray<FJumpCandidate> CurrentCandidates;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    int32 SelectedCandidateIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    FStarSystemData CurrentSystemData;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float WarningCountdownSeconds = 30.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    float WarningSecondsRemaining = 0.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 MaxCandidates = 6;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 MinHazardsPerSystem = 1;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 MaxHazardsPerSystem = 4;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 MinResourcesPerSystem = 2;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 MaxResourcesPerSystem = 5;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float BaseFalsificationChance = 0.15f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float FalsificationChancePerStageBeyondPuppeteer = 0.1f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float MaxFalsificationChance = 0.9f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float EVAInstantFatalChance = 0.6f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float NoPodDetrimentalHealthLoss = 30.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float NoPodMinHealthPercent = 10.0f;

    // Total pre-jump heading-offset magnitude (summed across all AShipHelmSystem instances) that maps to the full landing-error severity bonus.
    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float LandingErrorOffsetScale = 500.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    float MaxLandingErrorSeverityBonus = 0.5f;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    int32 JumpsCompleted = 0;

    UPROPERTY(EditDefaultsOnly, Category = "Jump")
    int32 TotalJumpsToDestination = 10;

    UFUNCTION(BlueprintCallable, Category = "Jump")
    bool IsFinalJump() const { return JumpsCompleted >= TotalJumpsToDestination; }

    UFUNCTION(BlueprintCallable, Category = "Jump")
    void GenerateJumpCandidates();

    UFUNCTION(BlueprintCallable, Category = "Jump")
    bool SelectJumpCandidate(int32 CandidateIndex);

    UFUNCTION(BlueprintCallable, Category = "Jump")
    bool BeginJumpWarningCountdown();

    UFUNCTION(BlueprintCallable, Category = "Jump")
    void ExecuteJump();

    UFUNCTION(BlueprintCallable, Category = "Jump")
    void CompleteArrival();

    UFUNCTION(BlueprintCallable, Category = "Jump")
    float ComputeFalsificationChance(ASensorArraySystem* Sensors) const;

    UFUNCTION(BlueprintCallable, Category = "Jump")
    bool IsCharacterOutsideShip(const ACoopSurvivalCharacter* Character) const;

    /**
     * The run's seeded randomness. Every roll in this subsystem draws from a named channel rather
     * than global random, so a run can be reproduced from one number.
     */
    class URunSeedSubsystem& GetSeeds() const;

    UFUNCTION(BlueprintImplementableEvent, Category = "Jump")
    void OnJumpWarningTick(float SecondsRemaining);

    UFUNCTION(BlueprintImplementableEvent, Category = "Jump")
    void OnArrivalComplete(const FStarSystemData& NewSystemData);

private:
    FStarSystemData GenerateRandomSystemData() const;
    void ResolveCharacterJumpFate(ACoopSurvivalCharacter* Character);
    void TickWarningCountdown();

    // Despawns the previous system's hazard/resource actors, then spawns a fresh set matching
    // CurrentSystemData.Hazards/.Resources, so a jump visibly changes the level content.
    void DespawnSystemContentActors();
    void SpawnSystemContentActors();

    float PendingLandingErrorSeverityBonus = 0.0f;
    FTimerHandle WarningTimerHandle;

    UPROPERTY()
    TArray<TObjectPtr<AActor>> SpawnedSystemContentActors;
};
