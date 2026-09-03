#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "WorldItemSeedCatalog.generated.h"

USTRUCT(BlueprintType)
struct FWorldItemSeedEntry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed")
    FName ContentId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed")
    TSubclassOf<AActor> ActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed", meta = (ClampMin = "0.0"))
    float Weight = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed", meta = (ClampMin = "1"))
    int32 MinQuantity = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed", meta = (ClampMin = "1"))
    int32 MaxQuantity = 1;

    /** Empty means the entry is valid in every room profile. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed")
    TArray<FName> RoomProfiles;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Seed")
    TArray<FName> ContentTags;
};

/** Authorable weighted pool shared by ship rooms, derelicts, stations, and mission maps. */
UCLASS(BlueprintType)
class GINNUNGAGAP_API UWorldItemSeedCatalog : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Seed")
    FName CatalogId = TEXT("ShipboardItems");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Seed")
    TArray<FWorldItemSeedEntry> Entries;

    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId(TEXT("WorldItemSeedCatalog"), CatalogId.IsNone() ? GetFName() : CatalogId);
    }
};
