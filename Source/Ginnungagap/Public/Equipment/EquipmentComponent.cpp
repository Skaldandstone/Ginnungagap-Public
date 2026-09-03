// Copyright Epic Games, Inc. All Rights Reserved.

#include "EquipmentComponent.h"
#include "Progression/ClassSkillComponent.h"
#include "CoopSurvivalCharacter.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

UEquipmentComponent::UEquipmentComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UEquipmentComponent::BeginPlay()
{
    Super::BeginPlay();
    OwnerCharacter = Cast<ACoopSurvivalCharacter>(GetOwner());
    InitializeSlots();
    if (OwnerCharacter) OwnerCharacter->RefreshEquipmentVisuals();
}

void UEquipmentComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    DegradeEquipment(DeltaTime);
}

bool UEquipmentComponent::EquipItem(const FEquipmentItem& Item)
{
    // Deliberately overwrites an occupied slot rather than refusing. This is the primitive the
    // loadout subsystem uses to apply a saved set in one pass, where every slot is being assigned
    // and anything already there is meant to go. SwapSlot is the verb for a person making the
    // choice, and it hands the displaced item back instead of dropping it on the floor.
    int32 SlotIndex = static_cast<int32>(Item.Slot);
    if (!EquipmentSlots.IsValidIndex(SlotIndex))
    {
        return false;
    }

    RemoveEquipmentBonuses();

    EquipmentSlots[SlotIndex].bEquipped = true;
    EquipmentSlots[SlotIndex].EquippedItem = Item;

    ApplyEquipmentBonuses();
    if (OwnerCharacter) { OwnerCharacter->RefreshEquipmentVisuals(); OwnerCharacter->OnEquipmentChanged(); }
    return true;
}

bool UEquipmentComponent::UnequipSlot(EEquipmentSlot Slot)
{
    int32 SlotIndex = static_cast<int32>(Slot);
    if (!EquipmentSlots.IsValidIndex(SlotIndex) || !EquipmentSlots[SlotIndex].bEquipped)
    {
        return false;
    }

    RemoveEquipmentBonuses();

    EquipmentSlots[SlotIndex].bEquipped = false;
    EquipmentSlots[SlotIndex].EquippedItem = FEquipmentItem();

    ApplyEquipmentBonuses();
    if (OwnerCharacter) { OwnerCharacter->RefreshEquipmentVisuals(); OwnerCharacter->OnEquipmentChanged(); }
    return true;
}

FEquipmentItem UEquipmentComponent::GetEquippedItem(EEquipmentSlot Slot) const
{
    int32 SlotIndex = static_cast<int32>(Slot);
    if (EquipmentSlots.IsValidIndex(SlotIndex))
    {
        return EquipmentSlots[SlotIndex].EquippedItem;
    }
    return FEquipmentItem();
}

bool UEquipmentComponent::IsSlotEquipped(EEquipmentSlot Slot) const
{
    int32 SlotIndex = static_cast<int32>(Slot);
    return EquipmentSlots.IsValidIndex(SlotIndex) && EquipmentSlots[SlotIndex].bEquipped;
}

float UEquipmentComponent::GetSlotCondition(EEquipmentSlot Slot) const
{
    const int32 SlotIndex = static_cast<int32>(Slot);
    if (!EquipmentSlots.IsValidIndex(SlotIndex) || !EquipmentSlots[SlotIndex].bEquipped)
    {
        return 0.0f;
    }

    const FEquipmentItem& Item = EquipmentSlots[SlotIndex].EquippedItem;
    if (Item.MaxDurability <= 0.0f)
    {
        return 0.0f;
    }
    return FMath::Clamp(Item.CurrentDurability / Item.MaxDurability, 0.0f, 1.0f);
}

FEquipmentStats UEquipmentComponent::GetTotalBonuses() const
{
    FEquipmentStats Total;

    for (const FEquipmentSlotState& SlotState : EquipmentSlots)
    {
        if (!SlotState.bEquipped)
        {
            continue;
        }

        // Protection degrades with the item rather than switching off at zero. A suit with tears
        // still holds some pressure, a cracked visor still blocks some radiation, a punctured
        // shield still stops something. Scaling by remaining condition means damage is felt
        // continuously as gear wears, instead of gear working perfectly and then vanishing.
        const FEquipmentItem& Item = SlotState.EquippedItem;
        const float Condition = Item.MaxDurability > 0.0f
            ? FMath::Clamp(Item.CurrentDurability / Item.MaxDurability, 0.0f, 1.0f)
            : 0.0f;

        const FEquipmentStats& Stats = Item.Stats;
        Total.RadiationResistance += Stats.RadiationResistance * Condition;
        Total.ThermalResistance += Stats.ThermalResistance * Condition;
        Total.PressureResistance += Stats.PressureResistance * Condition;
        Total.SuitIntegrityBonus += Stats.SuitIntegrityBonus * Condition;
        Total.DustProtection += Stats.DustProtection * Condition;

        // Movement is deliberately not scaled. Bulk is physical: a torn heavy suit still weighs
        // what it weighs, so a damaged item must not become a speed upgrade.
        Total.MovementSpeedBonus += Stats.MovementSpeedBonus;
    }

    return Total;
}

void UEquipmentComponent::DegradeEquipment(float DeltaTime)
{
    bool bVisualsChanged = false;
    for (FEquipmentSlotState& SlotState : EquipmentSlots)
    {
        if (!SlotState.bEquipped)
        {
            continue;
        }

        const float Previous = SlotState.EquippedItem.CurrentDurability;
        SlotState.EquippedItem.CurrentDurability = FMath::Clamp(
            Previous - SlotState.EquippedItem.DurabilityLossPerSecond * DeltaTime,
            0.0f,
            SlotState.EquippedItem.MaxDurability
        );

        // A ruined item stays worn. Gear does not disappear off a body when it fails -- a torn
        // suit is still a torn suit -- and its protection has already fallen to nothing through
        // condition scaling in GetTotalBonuses(). Auto-unequipping here would both teleport the
        // item away and make failure a sudden cliff rather than a slide.
        if (Previous > 0.0f && SlotState.EquippedItem.CurrentDurability <= 0.0f)
        {
            bVisualsChanged = true;
        }
    }

    if (bVisualsChanged && OwnerCharacter)
    {
        OwnerCharacter->RefreshEquipmentVisuals();
        OwnerCharacter->OnEquipmentChanged();
    }
}

int32 UEquipmentComponent::GetEquippedItemCount() const
{
    int32 Count = 0;
    for (const FEquipmentSlotState& SlotState : EquipmentSlots)
    {
        if (SlotState.bEquipped)
        {
            Count++;
        }
    }
    return Count;
}

void UEquipmentComponent::InitializeSlots()
{
    // One slot state per EEquipmentSlot value (Head, Chest, Arms, Legs, Accessory)
    const int32 NumSlots = 5;
    EquipmentSlots.SetNum(NumSlots);
}

void UEquipmentComponent::ApplyEquipmentBonuses()
{
    // Only stats that must be cached somewhere are pushed here. Hazard resistances are read live
    // from GetTotalBonuses() at their point of use instead, which is stateless and therefore
    // cannot drift or double-stack -- see ACoopSurvivalCharacter::UpdateSurvival.
    ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
    UCharacterMovementComponent* Movement = OwningCharacter ? OwningCharacter->GetCharacterMovement() : nullptr;
    if (!Movement)
    {
        return;
    }

    // Capture the unmodified speed once, so every later recompute starts from the same baseline.
    if (BaseMaxWalkSpeed <= 0.0f)
    {
        BaseMaxWalkSpeed = Movement->MaxWalkSpeed;
    }

    // Recomputed from the baseline rather than adjusted incrementally: applying twice yields the
    // same result, which is what removes the double-stacking hazard the old stub pair guarded
    // against by hand.
    const float SpeedPercent = GetTotalBonuses().MovementSpeedBonus;
    Movement->MaxWalkSpeed = FMath::Max(1.0f, BaseMaxWalkSpeed * (1.0f + SpeedPercent / 100.0f));
}

void UEquipmentComponent::RemoveEquipmentBonuses()
{
    // Kept as the explicit "return to baseline" step for teardown. Re-applying is idempotent, so
    // this is no longer required between equip changes, but unequipping everything should restore
    // the original speed rather than leave the last multiplier applied.
    ACharacter* OwningCharacter = Cast<ACharacter>(GetOwner());
    UCharacterMovementComponent* Movement = OwningCharacter ? OwningCharacter->GetCharacterMovement() : nullptr;
    if (Movement && BaseMaxWalkSpeed > 0.0f)
    {
        Movement->MaxWalkSpeed = BaseMaxWalkSpeed;
    }
}

bool UEquipmentComponent::SwapSlot(const FEquipmentItem& NewItem, FEquipmentItem& OutDisplaced, bool& bOutDisplaced)
{
    bOutDisplaced = false;
    OutDisplaced = FEquipmentItem();

    const int32 SlotIndex = static_cast<int32>(NewItem.Slot);
    if (!EquipmentSlots.IsValidIndex(SlotIndex))
    {
        return false;
    }

    // Capture before overwriting. The whole reason this exists rather than calling EquipItem is
    // that the caller needs somewhere to put the old item -- an inventory, the floor, a container
    // -- and cannot do that once it has already been overwritten.
    if (EquipmentSlots[SlotIndex].bEquipped)
    {
        OutDisplaced = EquipmentSlots[SlotIndex].EquippedItem;
        bOutDisplaced = true;
    }

    return EquipItem(NewItem);
}

bool UEquipmentComponent::CanRepairSlot(EEquipmentSlot Slot) const
{
    const int32 SlotIndex = static_cast<int32>(Slot);
    if (!EquipmentSlots.IsValidIndex(SlotIndex) || !EquipmentSlots[SlotIndex].bEquipped)
    {
        return false;
    }

    const FEquipmentItem& Item = EquipmentSlots[SlotIndex].EquippedItem;
    if (Item.MaxDurability <= 0.0f)
    {
        return false;
    }

    // Already whole is not repairable. Spending a repair charge on undamaged gear reads to a
    // player as the game wasting their supplies, the same way using a medkit at full health does.
    return Item.CurrentDurability < Item.MaxDurability;
}

bool UEquipmentComponent::RepairSlot(EEquipmentSlot Slot, float Amount)
{
    if (Amount <= 0.0f || !CanRepairSlot(Slot))
    {
        return false;
    }

    const int32 SlotIndex = static_cast<int32>(Slot);
    FEquipmentItem& Item = EquipmentSlots[SlotIndex].EquippedItem;

    // Scaled by repair training, exactly as the maintenance stations are. The same patch kit in
    // an engineer's hands should accomplish more, or the Engineering role's identity stops at the
    // stations rather than following them into the field.
    float Effective = Amount;
    if (OwnerCharacter)
    {
        if (const UClassSkillComponent* Skills = OwnerCharacter->GetSkillComponent())
        {
            Effective *= 1.0f + Skills->GetEffect(SkillEffects::RepairEffectiveness);
        }
    }

    Item.CurrentDurability = FMath::Clamp(Item.CurrentDurability + Effective, 0.0f, Item.MaxDurability);

    // Protection is read live from durability, so nothing needs recomputing here -- but the visuals
    // and any listening UI still describe a damaged item and have to be told it is not any more.
    if (OwnerCharacter)
    {
        OwnerCharacter->RefreshEquipmentVisuals();
        OwnerCharacter->OnEquipmentChanged();
    }

    return true;
}

float UEquipmentComponent::RepairAllEquipment(float AmountPerSlot)
{
    if (AmountPerSlot <= 0.0f)
    {
        return 0.0f;
    }

    float TotalRestored = 0.0f;
    for (int32 SlotIndex = 0; SlotIndex < EquipmentSlots.Num(); ++SlotIndex)
    {
        const EEquipmentSlot Slot = static_cast<EEquipmentSlot>(SlotIndex);
        if (!CanRepairSlot(Slot))
        {
            continue;
        }

        // Measure what actually went in rather than what was offered. A caller charging for the
        // work needs the real figure: topping up a nearly-whole item should not cost the same as
        // rebuilding a ruined one.
        const float Before = EquipmentSlots[SlotIndex].EquippedItem.CurrentDurability;
        if (RepairSlot(Slot, AmountPerSlot))
        {
            TotalRestored += EquipmentSlots[SlotIndex].EquippedItem.CurrentDurability - Before;
        }
    }

    return TotalRestored;
}

float UEquipmentComponent::GetWorstSlotCondition() const
{
    float Worst = 1.0f;
    bool bFoundAny = false;

    for (int32 SlotIndex = 0; SlotIndex < EquipmentSlots.Num(); ++SlotIndex)
    {
        if (!EquipmentSlots[SlotIndex].bEquipped)
        {
            continue;
        }

        bFoundAny = true;
        Worst = FMath::Min(Worst, GetSlotCondition(static_cast<EEquipmentSlot>(SlotIndex)));
    }

    // Nothing worn is not the same as everything ruined. Reporting zero here would drive a warning
    // readout for a player who simply has no gear on, which is a different problem.
    return bFoundAny ? Worst : 1.0f;
}
