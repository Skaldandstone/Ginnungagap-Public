#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GinnungagapAssetDefinition.generated.h"

UENUM(BlueprintType)
enum class EGinnungagapAssetDomain : uint8
{
    Character,
    Creature,
    ShipSystem,
    Environment,
    Equipment,
    Pickup,
    UI,
    VFX,
    Audio,
    Prototype
};

UENUM(BlueprintType)
enum class EGinnungagapAssetStatus : uint8
{
    Concept,
    Blockout,
    FirstPass,
    GameplayReady,
    Polish,
    Final
};

/**
 * Blueprint-authored planning record for art assets, Blueprint actors, widgets, and effects.
 *
 * Create instances from the Content Browser with Miscellaneous > Data Asset, then choose this
 * class to track ownership, implementation notes, references, and readiness inside the project.
 */
UCLASS(BlueprintType)
class GINNUNGAGAP_API UGinnungagapAssetDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Definition")
    FName AssetId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Definition")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Definition", meta = (MultiLine = "true"))
    FText CreativeBrief;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Definition")
    EGinnungagapAssetDomain Domain = EGinnungagapAssetDomain::Prototype;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Definition")
    EGinnungagapAssetStatus Status = EGinnungagapAssetStatus::Concept;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Art Direction", meta = (MultiLine = "true"))
    FText DesignPillars;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Art Direction")
    TArray<FName> ThemeTags;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Art Direction", meta = (MultiLine = "true"))
    FText ReferenceNotes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Production")
    FDirectoryPath TargetContentFolder;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Production")
    TSoftObjectPtr<UObject> PrimaryAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Production")
    TArray<TSoftObjectPtr<UObject>> SupportingAssets;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Production", meta = (MultiLine = "true"))
    FText BlueprintImplementationNotes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Production", meta = (MultiLine = "true"))
    FText AcceptanceChecklist;
};
