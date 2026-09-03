#include "Equipment/ExpeditionLoadoutSubsystem.h"

#include "Equipment/EquipmentComponent.h"

namespace
{
	FEquipmentItem MakeEquipment(EEquipmentType Type, EEquipmentSlot Slot, const TCHAR* Name,
		const TCHAR* Description, int32 SupplyCost, const FEquipmentStats& Stats)
	{
		FEquipmentItem Item;
		Item.Type = Type;
		Item.Slot = Slot;
		Item.DisplayName = Name;
		Item.Description = Description;
		Item.SupplyCost = SupplyCost;
		Item.Stats = Stats;
		return Item;
	}
}

void UExpeditionLoadoutSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ResetToStarterLoadout();
}

void UExpeditionLoadoutSubsystem::ResetToStarterLoadout()
{
	BuildDefaultCatalog();
	SelectedEquipment.Reset();

	// A small, useful starter kit. Players can strip it down or replace it before deployment.
	ToggleEquipment(EEquipmentType::HelmetVisor);
	ToggleEquipment(EEquipmentType::PressureSeal);
	ToggleEquipment(EEquipmentType::OxygenFilter);
}

void UExpeditionLoadoutSubsystem::BuildDefaultCatalog()
{
	EquipmentCatalog.Reset();

	FEquipmentStats Stats;
	Stats.DustProtection = 15.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::HelmetVisor, EEquipmentSlot::Head,
		TEXT("Survey Visor"), TEXT("Highlights hull faults, loose salvage, and airborne particulates."), 1, Stats));

	Stats = FEquipmentStats();
	Stats.ThermalResistance = 35.0f;
	Stats.MovementSpeedBonus = -3.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::ThermalPlating, EEquipmentSlot::Chest,
		TEXT("Thermal Plating"), TEXT("Insulated chest laminate for fires, coolant breaches, and flash heat."), 3, Stats));

	Stats = FEquipmentStats();
	Stats.RadiationResistance = 40.0f;
	Stats.MovementSpeedBonus = -2.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::RadiationShield, EEquipmentSlot::Arms,
		TEXT("Rad-Shield Bracers"), TEXT("Layered arm guards that reduce exposure during reactor work."), 2, Stats));

	Stats = FEquipmentStats();
	Stats.PressureResistance = 45.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::PressureSeal, EEquipmentSlot::Legs,
		TEXT("Pressure Seal Kit"), TEXT("Emergency joint seals buy time after decompression or suit puncture."), 1, Stats));

	Stats = FEquipmentStats();
	Stats.SuitIntegrityBonus = 25.0f;
	Stats.MovementSpeedBonus = -6.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::ArmorPlating, EEquipmentSlot::Chest,
		TEXT("Impact Carapace"), TEXT("Heavy chest armor. Replaces thermal plating and slows movement."), 3, Stats));

	Stats = FEquipmentStats();
	Stats.DustProtection = 35.0f;
	Stats.SuitIntegrityBonus = 5.0f;
	EquipmentCatalog.Add(MakeEquipment(EEquipmentType::OxygenFilter, EEquipmentSlot::Accessory,
		TEXT("Scrubber Pack"), TEXT("Extended filter pack for dust, spores, and contaminated atmosphere."), 2, Stats));
}

const FEquipmentItem* UExpeditionLoadoutSubsystem::FindCatalogItem(EEquipmentType Type) const
{
	return EquipmentCatalog.FindByPredicate([Type](const FEquipmentItem& Item) { return Item.Type == Type; });
}

TArray<FEquipmentItem> UExpeditionLoadoutSubsystem::GetEquippedItems() const
{
	TArray<FEquipmentItem> Items;
	SelectedEquipment.GenerateValueArray(Items);
	Items.Sort([](const FEquipmentItem& A, const FEquipmentItem& B)
	{
		return static_cast<uint8>(A.Slot) < static_cast<uint8>(B.Slot);
	});
	return Items;
}

bool UExpeditionLoadoutSubsystem::ToggleEquipment(EEquipmentType Type)
{
	const FEquipmentItem* Item = FindCatalogItem(Type);
	if (!Item) return false;

	if (const FEquipmentItem* Selected = SelectedEquipment.Find(Item->Slot); Selected && Selected->Type == Type)
	{
		SelectedEquipment.Remove(Item->Slot);
		return true;
	}

	const int32 ReplacedCost = SelectedEquipment.Contains(Item->Slot) ? SelectedEquipment[Item->Slot].SupplyCost : 0;
	if (GetUsedSupply() - ReplacedCost + Item->SupplyCost > SupplyBudget) return false;

	SelectedEquipment.Add(Item->Slot, *Item);
	return true;
}

bool UExpeditionLoadoutSubsystem::IsEquipmentSelected(EEquipmentType Type) const
{
	for (const TPair<EEquipmentSlot, FEquipmentItem>& Pair : SelectedEquipment)
	{
		if (Pair.Value.Type == Type) return true;
	}
	return false;
}

int32 UExpeditionLoadoutSubsystem::GetUsedSupply() const
{
	int32 Used = 0;
	for (const TPair<EEquipmentSlot, FEquipmentItem>& Pair : SelectedEquipment) Used += Pair.Value.SupplyCost;
	return Used;
}

FEquipmentStats UExpeditionLoadoutSubsystem::GetSelectedStats() const
{
	FEquipmentStats Total;
	for (const TPair<EEquipmentSlot, FEquipmentItem>& Pair : SelectedEquipment)
	{
		const FEquipmentStats& Stats = Pair.Value.Stats;
		Total.RadiationResistance += Stats.RadiationResistance;
		Total.ThermalResistance += Stats.ThermalResistance;
		Total.PressureResistance += Stats.PressureResistance;
		Total.SuitIntegrityBonus += Stats.SuitIntegrityBonus;
		Total.MovementSpeedBonus += Stats.MovementSpeedBonus;
		Total.DustProtection += Stats.DustProtection;
	}
	return Total;
}

void UExpeditionLoadoutSubsystem::ApplyLoadout(UEquipmentComponent* EquipmentComponent) const
{
	if (!EquipmentComponent) return;
	for (uint8 SlotIndex = 0; SlotIndex <= static_cast<uint8>(EEquipmentSlot::Accessory); ++SlotIndex)
	{
		EquipmentComponent->UnequipSlot(static_cast<EEquipmentSlot>(SlotIndex));
	}
	for (const FEquipmentItem& Item : GetEquippedItems()) EquipmentComponent->EquipItem(Item);
}
