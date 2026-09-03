#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Equipment/EquipmentSystem.h"
#include "EquipmentComponent.generated.h"

class ACoopSurvivalCharacter;

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UEquipmentComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UEquipmentComponent();

    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    // Equipment management
    UFUNCTION(BlueprintCallable, Category="Equipment")
    bool EquipItem(const FEquipmentItem& Item);

    UFUNCTION(BlueprintCallable, Category="Equipment")
    bool UnequipSlot(EEquipmentSlot Slot);

    UFUNCTION(BlueprintCallable, Category="Equipment")
    FEquipmentItem GetEquippedItem(EEquipmentSlot Slot) const;

    UFUNCTION(BlueprintCallable, Category="Equipment")
    bool IsSlotEquipped(EEquipmentSlot Slot) const;

    UFUNCTION(BlueprintCallable, Category="Equipment")
    FEquipmentStats GetTotalBonuses() const;

    /**
     * Remaining condition of a slot, 0..1. Protection scales by this rather than switching off,
     * so worn gear degrades continuously. Exposed for damage-state visuals and UI readouts.
     */
    UFUNCTION(BlueprintPure, Category="Equipment")
    float GetSlotCondition(EEquipmentSlot Slot) const;

    UFUNCTION(BlueprintCallable, Category="Equipment")
    void DegradeEquipment(float DeltaTime);

    /**
     * Sets a slot, handing back whatever it displaced.
     *
     * EquipItem overwrites an occupied slot and destroys what was there. That is correct for
     * applying a saved loadout, which is what it exists for, but wrong for a player swapping gear
     * in the field -- their old helmet should not evaporate. Use this wherever a person is making
     * the choice, and check bOutDisplaced before assuming nothing came off.
     */
    UFUNCTION(BlueprintCallable, Category="Equipment")
    bool SwapSlot(const FEquipmentItem& NewItem, FEquipmentItem& OutDisplaced, bool& bOutDisplaced);

    /**
     * Restores durability to one slot, scaled by the wearer's repair training.
     *
     * This is the counter-play degradation never had. Protection scales continuously with
     * durability and nothing put it back, so a run was a one-way ratchet toward no protection at
     * all. It also closes a trap the equipment model would otherwise set: ruined gear deliberately
     * stays worn rather than unequipping itself, which is only a reasonable rule if ruined gear can
     * be brought back.
     *
     * Returns false when the slot is empty or already whole, so a repair charge is never spent on
     * nothing.
     */
    UFUNCTION(BlueprintCallable, Category="Equipment")
    bool RepairSlot(EEquipmentSlot Slot, float Amount);

    /** Whether RepairSlot would achieve anything, for greying a control rather than failing on use. */
    UFUNCTION(BlueprintPure, Category="Equipment")
    bool CanRepairSlot(EEquipmentSlot Slot) const;

    /**
     * Repairs every damaged slot. Returns the total durability actually restored, which is what a
     * caller needs to charge for the work rather than the amount it offered.
     */
    UFUNCTION(BlueprintCallable, Category="Equipment")
    float RepairAllEquipment(float AmountPerSlot);

    /** Worst condition across everything worn, 0..1, or 1 when nothing is worn. */
    UFUNCTION(BlueprintPure, Category="Equipment")
    float GetWorstSlotCondition() const;

    UFUNCTION(BlueprintCallable, Category="Equipment")
    int32 GetEquippedItemCount() const;

    UPROPERTY(BlueprintReadOnly, Category="Equipment")
    TArray<FEquipmentSlotState> EquipmentSlots;

    UPROPERTY()
    ACoopSurvivalCharacter* OwnerCharacter;

private:
    void InitializeSlots();
    void ApplyEquipmentBonuses();

    /** Unmodified MaxWalkSpeed, captured once so bonus recomputes always start from baseline. */
    float BaseMaxWalkSpeed = 0.0f;
    void RemoveEquipmentBonuses();
};
