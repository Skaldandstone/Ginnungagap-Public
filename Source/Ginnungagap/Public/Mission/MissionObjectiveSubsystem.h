#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Mission/MissionTypes.h"
#include "MissionObjectiveSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMissionObjectiveChanged, FName, ObjectiveId, EMissionObjectiveState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMissionJumpReadinessChanged, bool, bCanJump);

UCLASS()
class GINNUNGAGAP_API UMissionObjectiveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool AddObjective(const FMissionObjectiveDefinition& Definition);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool ActivateObjective(FName ObjectiveId);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool SetObjectiveProgress(FName ObjectiveId, float NewProgress);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool AddObjectiveProgress(FName ObjectiveId, float ProgressDelta);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool CompleteObjective(FName ObjectiveId);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool FailObjective(FName ObjectiveId, FText FailureReason);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    bool AbandonObjective(FName ObjectiveId);

    UFUNCTION(BlueprintCallable, Category = "Mission")
    void ResetForNextSystem();

    UFUNCTION(BlueprintCallable, Category = "Mission")
    void ResetAllObjectives();

    /** Restores completion without paying rewards a second time. */
    UFUNCTION(BlueprintCallable, Category = "Mission")
    void RestoreCompletedObjectives(const TArray<FName>& ObjectiveIds);

    UFUNCTION(BlueprintPure, Category = "Mission")
    bool GetObjective(FName ObjectiveId, FMissionObjectiveRuntime& OutObjective) const;

    UFUNCTION(BlueprintPure, Category = "Mission")
    TArray<FMissionObjectiveRuntime> GetAllObjectives(bool bIncludeHidden = false) const;

    UFUNCTION(BlueprintPure, Category = "Mission")
    TArray<FMissionObjectiveRuntime> GetActiveObjectives() const;

    UFUNCTION(BlueprintPure, Category = "Mission")
    bool AreRequiredObjectivesResolved() const;

    UFUNCTION(BlueprintPure, Category = "Mission")
    bool CanBeginJump() const;

    UPROPERTY(BlueprintAssignable, Category = "Mission")
    FOnMissionObjectiveChanged OnObjectiveChanged;

    UPROPERTY(BlueprintAssignable, Category = "Mission")
    FOnMissionJumpReadinessChanged OnJumpReadinessChanged;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission")
    TMap<FName, FMissionObjectiveRuntime> Objectives;

private:
    bool ArePrerequisitesComplete(const FMissionObjectiveDefinition& Definition) const;
    void ActivateEligibleObjectives();
    void NotifyChanged(FName ObjectiveId, EMissionObjectiveState State, bool bPreviousJumpReadiness);
};

