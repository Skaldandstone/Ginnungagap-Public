#include "Inventory/InventoryComponent.h"
#include "Engine/World.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Equipment/EquipmentComponent.h"
#include "Progression/ClassSkillComponent.h"
#include "Inventory/InventoryItemPickup.h"
#include "CoopSurvivalCharacter.h"
#include "Net/UnrealNetwork.h"

UInventoryComponent::UInventoryComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UInventoryComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UInventoryComponent, Stacks);
}

bool UInventoryComponent::AddItem(UItemDefinition* Item, int32 Quantity)
{
    if (!CanAddItem(Item, Quantity))
    {
        return false;
    }

    int32 Remaining = Quantity;
    const int32 MaxStack = FMath::Max(1, Item->MaxStackSize);
    for (FInventoryStack& Stack : Stacks)
    {
        if (Stack.Item == Item && Stack.Quantity < MaxStack)
        {
            const int32 Added = FMath::Min(Remaining, MaxStack - Stack.Quantity);
            Stack.Quantity += Added;
            Remaining -= Added;
            if (Remaining == 0)
            {
                break;
            }
        }
    }

    while (Remaining > 0)
    {
        FInventoryStack& Stack = Stacks.AddDefaulted_GetRef();
        Stack.Item = Item;
        Stack.Quantity = FMath::Min(Remaining, MaxStack);
        Remaining -= Stack.Quantity;
    }

    BroadcastInventoryChanged();
    return true;
}

bool UInventoryComponent::RemoveItem(UItemDefinition* Item, int32 Quantity)
{
    if (!Item || Quantity <= 0 || GetItemQuantity(Item) < Quantity)
    {
        return false;
    }

    int32 Remaining = Quantity;
    for (int32 Index = Stacks.Num() - 1; Index >= 0 && Remaining > 0; --Index)
    {
        FInventoryStack& Stack = Stacks[Index];
        if (Stack.Item == Item)
        {
            const int32 Removed = FMath::Min(Remaining, Stack.Quantity);
            Stack.Quantity -= Removed;
            Remaining -= Removed;
            if (Stack.Quantity <= 0)
            {
                Stacks.RemoveAt(Index);
            }
        }
    }

    BroadcastInventoryChanged();
    return true;
}

bool UInventoryComponent::TransferItemTo(UInventoryComponent* TargetInventory, UItemDefinition* Item, int32 Quantity)
{
    if (!TargetInventory || TargetInventory == this || GetItemQuantity(Item) < Quantity || !TargetInventory->CanAddItem(Item, Quantity))
    {
        return false;
    }

    if (!RemoveItem(Item, Quantity))
    {
        return false;
    }

    if (!TargetInventory->AddItem(Item, Quantity))
    {
        AddItem(Item, Quantity);
        return false;
    }
    return true;
}

bool UInventoryComponent::CanAddItem(const UItemDefinition* Item, int32 Quantity) const
{
    if (!Item || Quantity <= 0)
    {
        return false;
    }

    if (MaxMassKg > 0.0f && GetCurrentMassKg() + Item->UnitMassKg * Quantity > MaxMassKg + KINDA_SMALL_NUMBER)
    {
        return false;
    }

    int32 FreeInExistingStacks = 0;
    const int32 MaxStack = FMath::Max(1, Item->MaxStackSize);
    for (const FInventoryStack& Stack : Stacks)
    {
        if (Stack.Item == Item)
        {
            FreeInExistingStacks += FMath::Max(0, MaxStack - Stack.Quantity);
        }
    }

    const int32 Remaining = FMath::Max(0, Quantity - FreeInExistingStacks);
    const int32 AdditionalSlots = Remaining > 0 ? FMath::DivideAndRoundUp(Remaining, MaxStack) : 0;
    return MaxSlots <= 0 || Stacks.Num() + AdditionalSlots <= MaxSlots;
}

int32 UInventoryComponent::GetItemQuantity(const UItemDefinition* Item) const
{
    int32 Quantity = 0;
    for (const FInventoryStack& Stack : Stacks)
    {
        if (Stack.Item == Item)
        {
            Quantity += Stack.Quantity;
        }
    }
    return Quantity;
}

float UInventoryComponent::GetCurrentMassKg() const
{
    float Total = 0.0f;
    for (const FInventoryStack& Stack : Stacks)
    {
        if (Stack.Item)
        {
            Total += Stack.Item->UnitMassKg * Stack.Quantity;
        }
    }
    return Total;
}

void UInventoryComponent::OnRep_Stacks()
{
    BroadcastInventoryChanged();
}

void UInventoryComponent::BroadcastInventoryChanged()
{
    OnInventoryChanged.Broadcast();
}

bool UInventoryComponent::CanUseItem(const UItemDefinition* Item) const
{
    if (!Item || !Item->bIsConsumable || GetItemQuantity(Item) <= 0)
    {
        return false;
    }

    const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(GetOwner());
    if (!Character || Character->bIsDead)
    {
        return false;
    }

    // An item is only usable if it would actually change something. Spending a medkit at full
    // health reads to a player as the game eating their supplies, so refuse instead.
    if (Item->OxygenRestorePercent > 0.0f && Character->OxygenLevelPercent < 100.0f)
    {
        return true;
    }
    if (Item->HealthRestorePercent > 0.0f && Character->HealthPercent < 100.0f)
    {
        return true;
    }
    if (Item->SuitIntegrityRestore > 0.0f && Character->SuitIntegrity < 1.0f)
    {
        return true;
    }

    // Worn gear is the equipment component's business, and it already knows how to say "nothing
    // here needs mending" -- including the case where the crew member simply is not wearing
    // anything, which is not the same as everything being ruined.
    if (Item->EquipmentRepairAmount > 0.0f)
    {
        if (const UEquipmentComponent* Equipment = Character->FindComponentByClass<UEquipmentComponent>())
        {
            if (Equipment->GetWorstSlotCondition() < 1.0f)
            {
                return true;
            }
        }
    }

    // Treatment is only wasted if there is nothing to treat, which the status component knows.
    if (Item->TreatmentStrength > 0.0f)
    {
        if (const UPlayerStatusEffectComponent* Status = Character->GetStatusEffectComponent())
        {
            // A general treatment is only worth spending if something is actually wrong; a targeted
            // one only if that specific affliction is present.
            return Item->bTreatsSpecificEffect
                ? Status->GetStatusSeverity(Item->TreatedEffect) > 0.0f
                : Status->GetActiveStatusEffects().Num() > 0;
        }
    }

    return false;
}

bool UInventoryComponent::UseItem(UItemDefinition* Item)
{
    // Authority only: this mutates survival state, and a client applying it locally would desync
    // the moment the server disagreed about whether the item was even held.
    AActor* Owner = GetOwner();
    if (!Owner || !Owner->HasAuthority() || !CanUseItem(Item))
    {
        return false;
    }

    ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Owner);
    if (!Character)
    {
        return false;
    }

    // Consume first. Applying the effect and then failing to remove the item would let one
    // consumable be used repeatedly, which is a far worse failure than losing one to a bug.
    if (!RemoveItem(Item, 1))
    {
        return false;
    }

    if (Item->OxygenRestorePercent > 0.0f)
    {
        Character->OxygenLevelPercent = FMath::Clamp(
            Character->OxygenLevelPercent + Item->OxygenRestorePercent, 0.0f, 100.0f);
    }

    if (Item->HealthRestorePercent > 0.0f)
    {
        Character->HealthPercent = FMath::Clamp(
            Character->HealthPercent + Item->HealthRestorePercent, 0.0f, 100.0f);
    }

    if (Item->SuitIntegrityRestore > 0.0f)
    {
        Character->SuitIntegrity = FMath::Clamp(
            Character->SuitIntegrity + Item->SuitIntegrityRestore, 0.0f, 1.0f);
    }

    if (Item->EquipmentRepairAmount > 0.0f)
    {
        if (UEquipmentComponent* Equipment = Character->FindComponentByClass<UEquipmentComponent>())
        {
            // RepairAllEquipment scales by repair training and skips whole slots itself, so a kit
            // spent with one slot already at full does not quietly lose that share of its charge.
            Equipment->RepairAllEquipment(Item->EquipmentRepairAmount);
        }
    }

    if (Item->TreatmentStrength > 0.0f)
    {
        if (UPlayerStatusEffectComponent* Status = Character->GetStatusEffectComponent())
        {
            // Scaled by medical training, exactly as the medical activities are. The same kit in
            // trained hands should achieve more, or the Medical role's identity stops at the
            // activity stations and does not follow them into the field.
            const UClassSkillComponent* Skills = Character->GetSkillComponent();
            const float Strength = Item->TreatmentStrength
                * (1.0f + (Skills ? Skills->GetEffect(SkillEffects::MedicalEffectiveness) : 0.0f));

            if (Item->bTreatsSpecificEffect)
            {
                Status->TreatStatusEffect(Item->TreatedEffect, Strength);
            }
            else
            {
                Status->TreatMostSevereStatusEffect(Strength);
            }
        }
    }

    return true;
}

bool UInventoryComponent::CanDropItem(const UItemDefinition* Item, int32 Quantity) const
{
    if (!Item || Quantity <= 0 || !Item->bCanDrop)
    {
        return false;
    }

    // Mission items are refused outright. A player who drops the thing the run depends on has
    // softlocked themselves, and no amount of confirmation UI reliably prevents that.
    if (Item->bMissionItem)
    {
        return false;
    }

    return GetItemQuantity(Item) >= Quantity;
}

bool UInventoryComponent::DropItem(UItemDefinition* Item, int32 Quantity)
{
    AActor* Owner = GetOwner();
    if (!Owner || !Owner->HasAuthority() || !CanDropItem(Item, Quantity))
    {
        return false;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    // Ahead of the owner rather than underfoot, so a dropped stack is visible and reachable
    // instead of clipping into the floor the player is standing on.
    const FVector SpawnLocation = Owner->GetActorLocation() + Owner->GetActorForwardVector() * DropDistanceCm;
    const FTransform SpawnTransform(Owner->GetActorRotation(), SpawnLocation);

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

    AInventoryItemPickup* Pickup = World->SpawnActorDeferred<AInventoryItemPickup>(
        AInventoryItemPickup::StaticClass(), SpawnTransform, Owner, nullptr,
        ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);
    if (!Pickup)
    {
        return false;
    }

    Pickup->ConfigurePickup(Item, Quantity);
    Pickup->FinishSpawning(SpawnTransform);

    // Only now does the stack leave the inventory. Removing first and then failing to spawn would
    // delete the items outright, and a player cannot tell that apart from a dropped stack that
    // fell through the world.
    if (!RemoveItem(Item, Quantity))
    {
        Pickup->Destroy();
        return false;
    }

    return true;
}
