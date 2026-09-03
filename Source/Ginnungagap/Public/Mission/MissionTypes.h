#pragma once

#include "CoreMinimal.h"
#include "MissionTypes.generated.h"

UENUM(BlueprintType)
enum class EMissionObjectiveType : uint8
{
    Repair,
    Salvage,
    Rescue,
    Quarantine,
    Survey,
    Protect,
    Investigate,
    Escape,
    Custom,
    RepelBoarders,
    EliminateThreats
};

UENUM(BlueprintType)
enum class EMissionObjectiveState : uint8
{
    Pending,
    Active,
    Completed,
    Failed,
    Abandoned
};

USTRUCT(BlueprintType)
struct FMissionObjectiveDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    FName ObjectiveId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    FText Title;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission", meta = (MultiLine = true))
    FText Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    EMissionObjectiveType Type = EMissionObjectiveType::Custom;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    float TargetProgress = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    bool bOptional = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    bool bHiddenUntilActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    bool bAutoActivate = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    bool bBlocksJumpWhileUnresolved = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    bool bPersistsAcrossSystems = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    TArray<FName> PrerequisiteObjectiveIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mission")
    int32 CurrencyReward = 0;
};

USTRUCT(BlueprintType)
struct FMissionObjectiveRuntime
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Mission")
    FMissionObjectiveDefinition Definition;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission")
    EMissionObjectiveState State = EMissionObjectiveState::Pending;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission")
    float CurrentProgress = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mission")
    FText FailureReason;

    float GetProgressFraction() const
    {
        return Definition.TargetProgress > 0.0f
            ? FMath::Clamp(CurrentProgress / Definition.TargetProgress, 0.0f, 1.0f)
            : 0.0f;
    }

    bool IsResolved() const
    {
        return State == EMissionObjectiveState::Completed
            || State == EMissionObjectiveState::Failed
            || State == EMissionObjectiveState::Abandoned;
    }
};

