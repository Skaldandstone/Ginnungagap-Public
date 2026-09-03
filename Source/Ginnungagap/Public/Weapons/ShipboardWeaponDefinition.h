#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Weapons/ShipboardWeaponTypes.h"
#include "ShipboardWeaponDefinition.generated.h"

class UStaticMesh;

/** Data shared by every physical instance of a shipboard tool-weapon. */
UCLASS(BlueprintType)
class GINNUNGAGAP_API UShipboardWeaponDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FName WeaponId = TEXT("ShipboardTool");

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FText DisplayName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity", meta = (MultiLine = true))
    FText Description;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
    TObjectPtr<UStaticMesh> WeaponMesh;

    /** Corrective transform for donor meshes whose authored origin or forward axis differs. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
    FTransform WeaponMeshTransform = FTransform::Identity;

    /** Definition-authored projectile or trace origin relative to the weapon actor. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
    FVector MuzzleOffset = FVector(50.0f, 0.0f, 0.0f);

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Operation")
    FWeaponFiringProfile SafeProfile;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Operation")
    FWeaponFiringProfile UnsafeModifiedProfile;

    /** Ordered permanent upgrades. Array index zero is installed as weapon level one. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Upgrade")
    TArray<FWeaponUpgradeStage> UpgradeStages;

    UFUNCTION(BlueprintPure, Category = "Weapon|Upgrade")
    int32 GetMaxUpgradeLevel() const { return UpgradeStages.Num(); }

    UFUNCTION(BlueprintPure, Category = "Weapon|Upgrade")
    FWeaponFiringProfile GetFiringProfileForUpgradeLevel(int32 UpgradeLevel) const
    {
        const int32 ClampedLevel = FMath::Clamp(UpgradeLevel, 0, UpgradeStages.Num());
        return ClampedLevel == 0 ? SafeProfile : UpgradeStages[ClampedLevel - 1].FiringProfile;
    }

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Traversal")
    FWeaponCollisionEnvelope CollisionEnvelope;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mounting")
    bool bPlayerCompatible = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mounting")
    bool bAerialDroneCompatible = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mounting")
    bool bRoboticDroneCompatible = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Authorization")
    bool bUnsafeModificationRequiresSoldier = false;

    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId(TEXT("ShipboardWeapon"), WeaponId.IsNone() ? GetFName() : WeaponId);
    }
};
