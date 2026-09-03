#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WorldItems/WorldItemSeedCatalog.h"
#include "WorldItemSeedPoint.generated.h"

class UArrowComponent;
class USceneComponent;

/** Server-authoritative, deterministic anchor for distributed tools, pickups, weapons, and props. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AWorldItemSeedPoint : public AActor
{
    GENERATED_BODY()

public:
    AWorldItemSeedPoint();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "World Items")
    void SeedNow();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "World Items")
    void ClearSpawnedItems();

    UFUNCTION(BlueprintPure, Category = "World Items")
    TArray<FWorldItemSeedEntry> GetEligibleEntries() const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "World Items")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "World Items")
    TObjectPtr<UArrowComponent> SpawnDirection;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    TObjectPtr<UWorldItemSeedCatalog> Catalog = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    TArray<FWorldItemSeedEntry> LocalEntries;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    FName RoomProfile = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    int32 Seed = 1337;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float SpawnChance = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items", meta = (ClampMin = "1"))
    int32 SpawnRolls = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items", meta = (ClampMin = "0.0"))
    float ScatterRadiusCm = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    bool bSeedOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "World Items")
    bool bAllowDuplicateEntries = false;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "World Items")
    TArray<TObjectPtr<AActor>> SpawnedItems;

private:
    const FWorldItemSeedEntry* ChooseWeightedEntry(const TArray<FWorldItemSeedEntry>& Entries, FRandomStream& Stream) const;
};
