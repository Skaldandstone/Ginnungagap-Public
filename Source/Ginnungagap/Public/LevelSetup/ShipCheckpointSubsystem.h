#pragma once

#include "CoreMinimal.h"
#include "Bloom/BloomDirector.h"
#include "Activities/ActivityPopulationTypes.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ShipCheckpointSubsystem.generated.h"

class APawn;
class UWorld;

USTRUCT(BlueprintType)
struct FActivityStationCheckpointRecord
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    FName StationId = NAME_None;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    int32 CompletionCount = 0;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    EActivityStationCondition Condition = EActivityStationCondition::Serviceable;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    float ConditionPercent = 1.0f;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    int32 RemainingUses = -1;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    bool bEnabled = true;
};

USTRUCT(BlueprintType)
struct FShipCheckpointRecord
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    int32 SaveVersion = 2;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    FName DistrictMapName = NAME_None;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    FName CheckpointId = NAME_None;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    FTransform RespawnTransform = FTransform::Identity;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    TArray<FName> CompletedObjectiveIds;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    EBloomStage BloomStage = EBloomStage::Latent;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    int32 ActivityPopulationSeed = 0;

    UPROPERTY(BlueprintReadWrite, Category="Checkpoint|Activities")
    TArray<FActivityStationCheckpointRecord> ActivityStations;

    bool IsValid() const
    {
        return SaveVersion >= 1 && SaveVersion <= 2 && !DistrictMapName.IsNone() && !CheckpointId.IsNone();
    }

    bool IsForMap(FName MapName) const
    {
        return IsValid() && DistrictMapName == MapName;
    }
};

UCLASS()
class GINNUNGAGAP_API UShipCheckpointSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadWrite, Category="Checkpoint")
    FShipCheckpointRecord Record;
};

UCLASS()
class GINNUNGAGAP_API UShipCheckpointSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    UFUNCTION(BlueprintCallable, Category="Checkpoint")
    bool RecordCheckpoint(UWorld* World, FName CheckpointId, const FTransform& RespawnTransform);

    UFUNCTION(BlueprintCallable, Category="Checkpoint")
    bool RestoreCheckpoint(UWorld* World, APawn* PlayerPawn);

    UFUNCTION(BlueprintPure, Category="Checkpoint")
    bool HasCheckpointForWorld(const UWorld* World) const;

    UFUNCTION(BlueprintCallable, Category="Checkpoint")
    void ClearCheckpoint();

    UFUNCTION(BlueprintPure, Category="Checkpoint")
    const FShipCheckpointRecord& GetCheckpointRecord() const { return CachedRecord; }

private:
    static FName GetStableMapName(const UWorld* World);

    UPROPERTY(Transient)
    FShipCheckpointRecord CachedRecord;

    static const FString SaveSlotName;
    static constexpr int32 UserIndex = 0;
};
