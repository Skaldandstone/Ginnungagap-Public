#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Inventory/ItemDefinition.h"
#include "InventoryComponent.generated.h"

USTRUCT(BlueprintType)
struct FInventoryStack
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Inventory")
    TObjectPtr<UItemDefinition> Item = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Inventory")
    int32 Quantity = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInventoryChanged);

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UInventoryComponent();

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool AddItem(UItemDefinition* Item, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItem(UItemDefinition* Item, int32 Quantity = 1);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool TransferItemTo(UInventoryComponent* TargetInventory, UItemDefinition* Item, int32 Quantity = 1);

    /**
     * Consumes one of an item and applies its effect to the owning character.
     *
     * Authority only, and refuses rather than partially applying: an item that cannot help is not
     * spent. Using a full-health medkit at full health would otherwise silently destroy it, which
     * players read as the game eating their supplies.
     *
     * Returns false when the item is absent, not consumable, or would achieve nothing.
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool UseItem(UItemDefinition* Item);

    /**
     * Drops a quantity into the world as a collectable pickup.
     *
     * Respects bCanDrop and refuses mission items outright -- a player who drops the thing the run
     * depends on has softlocked themselves, and no amount of warning UI reliably prevents it.
     *
     * The stack only leaves the inventory once the pickup exists, so a failed spawn cannot delete
     * the items.
     */
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool DropItem(UItemDefinition* Item, int32 Quantity = 1);

    /** Whether DropItem would succeed, for greying out a control rather than failing on click. */
    UFUNCTION(BlueprintPure, Category = "Inventory")
    bool CanDropItem(const UItemDefinition* Item, int32 Quantity = 1) const;

    /** Whether UseItem would achieve anything right now. */
    UFUNCTION(BlueprintPure, Category = "Inventory")
    bool CanUseItem(const UItemDefinition* Item) const;

    /** Where a dropped stack appears, in centimetres ahead of the owner. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory", meta = (ClampMin = "0.0"))
    float DropDistanceCm = 120.0f;

    UFUNCTION(BlueprintPure, Category = "Inventory")
    bool CanAddItem(const UItemDefinition* Item, int32 Quantity = 1) const;

    UFUNCTION(BlueprintPure, Category = "Inventory")
    int32 GetItemQuantity(const UItemDefinition* Item) const;

    UFUNCTION(BlueprintPure, Category = "Inventory")
    float GetCurrentMassKg() const;

    UFUNCTION(BlueprintPure, Category = "Inventory")
    int32 GetUsedSlotCount() const { return Stacks.Num(); }

    UFUNCTION(BlueprintPure, Category = "Inventory")
    TArray<FInventoryStack> GetStacks() const { return Stacks; }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory", meta = (ClampMin = "0"))
    int32 MaxSlots = 12;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Inventory", meta = (ClampMin = "0.0"))
    float MaxMassKg = 40.0f;

    UPROPERTY(ReplicatedUsing = OnRep_Stacks, VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    TArray<FInventoryStack> Stacks;

    UPROPERTY(BlueprintAssignable, Category = "Inventory")
    FOnInventoryChanged OnInventoryChanged;

private:
    UFUNCTION()
    void OnRep_Stacks();

    void BroadcastInventoryChanged();
};
