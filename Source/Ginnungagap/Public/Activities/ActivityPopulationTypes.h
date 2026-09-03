#pragma once

#include "CoreMinimal.h"
#include "ActivityPopulationTypes.generated.h"

class AActivityStation;

UENUM(BlueprintType)
enum class EActivityStationMount : uint8
{
    Automatic,
    FloorConsole,
    WallPanel,
    Workbench,
    CeilingNode
};

UENUM(BlueprintType)
enum class EActivityStationCondition : uint8
{
    Pristine,
    Serviceable,
    Worn,
    Faulted,
    BloomTouched,
    BloomOverrun
};

UENUM(BlueprintType)
enum class EActivityStationRarity : uint8
{
    Routine,
    Specialized,
    Critical,
    Anomalous
};

/** Stable procedural record used for debugging, checkpoints and future streaming regeneration. */
USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FProceduralActivitySpawnRecord
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    FName StationId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    FName RoomCode = NAME_None;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    TSoftClassPtr<AActivityStation> StationClass;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    FTransform SpawnTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    EActivityStationMount Mount = EActivityStationMount::Automatic;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    EActivityStationCondition Condition = EActivityStationCondition::Serviceable;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    EActivityStationRarity Rarity = EActivityStationRarity::Routine;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    float ConditionPercent = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    float BloomPressure = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    int32 PopulationSeed = 0;

    UPROPERTY(BlueprintReadOnly, Category="Activity Population")
    int32 SlotIndex = INDEX_NONE;

    bool IsValid() const
    {
        return !StationId.IsNone() && !RoomCode.IsNone() && !StationClass.IsNull() && SlotIndex >= 0;
    }
};
