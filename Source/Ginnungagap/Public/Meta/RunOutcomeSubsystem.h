#pragma once

#include "CoreMinimal.h"
#include "TimerManager.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Progression/PlayerClass.h"
#include "RunOutcomeSubsystem.generated.h"

UENUM(BlueprintType)
enum class ERunOutcome : uint8
{
    InProgress,
    Victory,
    HardLoss_BloomReachedDestination,
    SelfDestructSuccess,
    SelfDestructCountered
};

UCLASS()
class GINNUNGAGAP_API URunOutcomeSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UPROPERTY(BlueprintReadOnly, Category = "Run Outcome")
    ERunOutcome CurrentOutcome = ERunOutcome::InProgress;

    UPROPERTY(BlueprintReadOnly, Category = "Run Outcome")
    bool bRunResolved = false;

    UPROPERTY(BlueprintReadOnly, Category = "Self Destruct")
    bool bSelfDestructArmed = false;

    UPROPERTY(BlueprintReadOnly, Category = "Self Destruct")
    float SelfDestructSecondsRemaining = 0.0f;

    UPROPERTY(EditDefaultsOnly, Category = "Self Destruct")
    float SelfDestructCountdownSeconds = 60.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Meta")
    int32 TotalBankedCurrency = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Meta")
    int32 LastCurrencyEarned = 0;

    UPROPERTY(EditDefaultsOnly, Category = "Meta")
    int32 CurrencyPerJump = 10;

    UPROPERTY(EditDefaultsOnly, Category = "Meta")
    int32 PlayerSurvivalBonus = 100;

    UPROPERTY(EditDefaultsOnly, Category = "Meta")
    int32 BloomEradicationBonus = 150;

    UPROPERTY(EditDefaultsOnly, Category = "Meta")
    int32 PerfectRunBonus = 100;

    UPROPERTY(EditDefaultsOnly, Category = "Meta")
    float HardLossCurrencyMultiplier = 0.25f;

    UPROPERTY(BlueprintReadOnly, Category = "Progression")
    EPressureSuitRole CurrentPlayerRole = EPressureSuitRole::Scientist;

    UPROPERTY(BlueprintReadOnly, Category = "Progression")
    TMap<EPressureSuitRole, FClassSkillsArray> CurrentRoleSkills;

    UPROPERTY(BlueprintReadOnly, Category = "Progression")
    TMap<EPressureSuitRole, int32> CurrentRoleSkillPoints;

    UPROPERTY(BlueprintReadOnly, Category = "Progression")
    int32 LastRoleSkillPointsEarned = 0;

    UFUNCTION(BlueprintCallable, Category = "Self Destruct")
    bool ArmSelfDestruct();

    UFUNCTION(BlueprintCallable, Category = "Self Destruct")
    bool CancelSelfDestruct();

    UFUNCTION(BlueprintCallable, Category = "Run Outcome")
    void EvaluateDestinationArrival();

    UFUNCTION(BlueprintImplementableEvent, Category = "Self Destruct")
    void OnSelfDestructTick(float SecondsRemaining);

    UFUNCTION(BlueprintImplementableEvent, Category = "Self Destruct")
    void OnSelfDestructCountered();

    UFUNCTION(BlueprintImplementableEvent, Category = "Run Outcome")
    void OnRunResolved(ERunOutcome Outcome, int32 CurrencyEarned, int32 NewTotalBankedCurrency);

    UFUNCTION(BlueprintCallable, Category = "Progression")
    void SetPlayerRole(EPressureSuitRole NewRole);

    UFUNCTION(BlueprintCallable, Category = "Progression")
    EPressureSuitRole GetPlayerRole() const;

    UFUNCTION(BlueprintCallable, Category = "Progression")
    int32 GetRoleSkillPoints(EPressureSuitRole Role) const;

    /** Owned ranks and equipped loadout for a role. */
    UFUNCTION(BlueprintCallable, Category = "Progression")
    FClassSkillsArray GetRoleSkills(EPressureSuitRole Role) const;

    /**
     * Buys the next rank of SkillID, validating against the catalogue rather than trusting the
     * caller's arithmetic. Cost is derived here so a widget cannot name its own price.
     */
    UFUNCTION(BlueprintCallable, Category = "Progression")
    bool UnlockClassSkill(EPressureSuitRole Role, const FString& SkillID);

    UFUNCTION(BlueprintCallable, Category = "Progression")
    bool UnlockClassSkillWithCurrency(EPressureSuitRole Role, const FString& SkillID);

    /** Replaces a role's active loadout, rejecting anything unowned, illegal, or over the limit. */
    UFUNCTION(BlueprintCallable, Category = "Progression")
    bool SetEquippedActiveSkills(EPressureSuitRole Role, const TArray<FString>& SkillIDs);

    UFUNCTION(BlueprintCallable, Category = "Meta")
    void AwardPersistentCurrency(int32 Amount);

private:
    /** Single writer for the save slot, so a new progression field cannot be persisted from only some paths. */
    void SaveProgression();

    class UClassSkillTreeSubsystem* GetSkillTree() const;

    void TickSelfDestructCountdown();
    void DetonateSelfDestruct();
    void ResolveRun(ERunOutcome Outcome);

    FTimerHandle SelfDestructTimerHandle;

    static const TCHAR* SaveSlotName;
};
