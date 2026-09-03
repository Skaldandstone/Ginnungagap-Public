#pragma once

#include "CoreMinimal.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Engine/DataAsset.h"
#include "ItemDefinition.generated.h"

class UStaticMesh;

UCLASS(BlueprintType)
class GINNUNGAGAP_API UItemDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item")
    FName ItemId = NAME_None;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item")
    FText DisplayName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item", meta = (MultiLine = true))
    FText Description;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item", meta = (ClampMin = "1"))
    int32 MaxStackSize = 1;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item", meta = (ClampMin = "0.0"))
    float UnitMassKg = 0.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item")
    bool bCanDrop = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item")
    bool bMissionItem = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item")
    TArray<FName> ItemTags;

    // --- Consumable ---------------------------------------------------------------------------
    // Every field below drives a consumer that already exists. Nothing here invents a new effect
    // system: oxygen, health and suit integrity are read off the character each tick, and
    // treatment goes through the same call the medical activities use. An item that promised
    // something with no consumer would be text on a tooltip.

    /** Whether Use does anything. A tool or salvage stack is not consumable and should say so. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable")
    bool bIsConsumable = false;

    /** Percentage points of oxygen restored. Refills the tank; it does not raise the ceiling. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (ClampMin = "0.0", ClampMax = "100.0"))
    float OxygenRestorePercent = 0.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (ClampMin = "0.0", ClampMax = "100.0"))
    float HealthRestorePercent = 0.0f;

    /** Suit integrity restored, 0-1. A patch, not a replacement suit. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float SuitIntegrityRestore = 0.0f;

    /**
     * Durability restored to every damaged equipment slot, in the same units as slot durability.
     *
     * Scaled by repair training at the point of use, exactly as the repair benches are. This is
     * what makes carrying a kit different from walking back to a bench: less restored per use and
     * a finite supply, in exchange for not having to cross the ship to get it.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (ClampMin = "0.0"))
    float EquipmentRepairAmount = 0.0f;

    /**
     * Treatment strength applied to a status effect, 0-1. Zero means the item treats nothing.
     *
     * Scaled by the user's medical training at the point of use, the same way the medical
     * activities are -- a trauma kit in trained hands should achieve more than the same kit in
     * untrained ones.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float TreatmentStrength = 0.0f;

    /**
     * Which status effect this treats. Ignored unless bTreatsSpecificEffect is set, in which case
     * treatment goes to the most severe effect instead -- a general stimulant rather than a
     * targeted one.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable")
    bool bTreatsSpecificEffect = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Item|Consumable", meta = (EditCondition = "bTreatsSpecificEffect"))
    EPlayerStatusEffect TreatedEffect = EPlayerStatusEffect::Hemorrhage;

    /** Physical representation used by inventory pickups, containers, and fabrication outputs. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
    TObjectPtr<UStaticMesh> WorldMesh = nullptr;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Presentation")
    FVector WorldMeshScale = FVector(1.0f);

    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId(TEXT("Item"), ItemId.IsNone() ? GetFName() : ItemId);
    }
};
