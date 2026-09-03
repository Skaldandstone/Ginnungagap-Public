#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Equipment/EquipmentComponent.h"
#include "Equipment/EquipmentSystem.h"

/**
 * Equipment bonuses were empty stubs, so every item in the game was cosmetic. These cover the
 * aggregation contract that the hazard and movement code now reads from, without needing a world.
 */

namespace
{
	FEquipmentItem MakeItem(EEquipmentSlot Slot, const FEquipmentStats& Stats)
	{
		FEquipmentItem Item;
		Item.Slot = Slot;
		Item.Stats = Stats;
		return Item;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEquipmentBonusAggregationTest,
	"Ginnungagap.Gameplay.Equipment.BonusAggregation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEquipmentBonusAggregationTest::RunTest(const FString& Parameters)
{
	UEquipmentComponent* Equipment = NewObject<UEquipmentComponent>();
	Equipment->EquipmentSlots.SetNum(5);

	// Nothing equipped must aggregate to zero, not to a default-item's stats.
	TestEqual(TEXT("An empty loadout grants no radiation resistance"),
		Equipment->GetTotalBonuses().RadiationResistance, 0.0f);
	TestEqual(TEXT("An empty loadout grants no movement bonus"),
		Equipment->GetTotalBonuses().MovementSpeedBonus, 0.0f);
	TestEqual(TEXT("An empty loadout has no equipped items"), Equipment->GetEquippedItemCount(), 0);

	// Fresh gear so aggregation is tested at full condition; damage scaling has its own test.
	FEquipmentStats HeadStats;
	HeadStats.RadiationResistance = 20.0f;
	HeadStats.MovementSpeedBonus = -5.0f;
	TestTrue(TEXT("Head equips"), Equipment->EquipItem(MakeItem(EEquipmentSlot::Head, HeadStats)));

	FEquipmentStats ChestStats;
	ChestStats.RadiationResistance = 30.0f;
	ChestStats.SuitIntegrityBonus = 25.0f;
	TestTrue(TEXT("Chest equips"), Equipment->EquipItem(MakeItem(EEquipmentSlot::Chest, ChestStats)));

	// Bonuses accumulate across slots -- this is what the radiation shielding calculation reads.
	const FEquipmentStats Total = Equipment->GetTotalBonuses();
	TestEqual(TEXT("Radiation resistance sums across slots"), Total.RadiationResistance, 50.0f);
	TestEqual(TEXT("Suit integrity bonus carries from a single slot"), Total.SuitIntegrityBonus, 25.0f);
	TestEqual(TEXT("A negative movement bonus is preserved rather than clamped away"),
		Total.MovementSpeedBonus, -5.0f);
	TestEqual(TEXT("Both slots count as equipped"), Equipment->GetEquippedItemCount(), 2);

	// Unequipping must actually withdraw the contribution; a stale bonus here would mean gear kept
	// protecting the player after removal.
	TestTrue(TEXT("Chest unequips"), Equipment->UnequipSlot(EEquipmentSlot::Chest));
	TestEqual(TEXT("Unequipping withdraws its resistance"),
		Equipment->GetTotalBonuses().RadiationResistance, 20.0f);
	TestEqual(TEXT("Unequipping withdraws its integrity bonus"),
		Equipment->GetTotalBonuses().SuitIntegrityBonus, 0.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEquipmentDamageScalesProtectionTest,
	"Ginnungagap.Gameplay.Equipment.DamageScalesProtection",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEquipmentDamageScalesProtectionTest::RunTest(const FString& Parameters)
{
	UEquipmentComponent* Equipment = NewObject<UEquipmentComponent>();
	Equipment->EquipmentSlots.SetNum(5);

	FEquipmentStats Stats;
	Stats.RadiationResistance = 40.0f;
	Stats.MovementSpeedBonus = -10.0f;

	FEquipmentItem Item = MakeItem(EEquipmentSlot::Chest, Stats);
	Item.MaxDurability = 100.0f;
	Item.CurrentDurability = 100.0f;
	Item.DurabilityLossPerSecond = 25.0f;
	Equipment->EquipItem(Item);

	TestEqual(TEXT("Intact gear gives full protection"),
		Equipment->GetTotalBonuses().RadiationResistance, 40.0f);
	TestEqual(TEXT("Intact gear reports full condition"),
		Equipment->GetSlotCondition(EEquipmentSlot::Chest), 1.0f);

	// Damage is proportional, not binary: torn gear protects less in step with how torn it is.
	Equipment->DegradeEquipment(2.0f); // 100 -> 50 durability
	TestEqual(TEXT("Half-ruined gear reports half condition"),
		Equipment->GetSlotCondition(EEquipmentSlot::Chest), 0.5f);
	TestEqual(TEXT("Half-ruined gear gives half protection"),
		Equipment->GetTotalBonuses().RadiationResistance, 20.0f);

	// Bulk is physical, so damage must never turn a heavy item into a speed upgrade.
	TestEqual(TEXT("Damage does not relieve the movement penalty"),
		Equipment->GetTotalBonuses().MovementSpeedBonus, -10.0f);

	Equipment->DegradeEquipment(2.0f); // 50 -> 0 durability
	TestEqual(TEXT("Fully ruined gear gives no protection"),
		Equipment->GetTotalBonuses().RadiationResistance, 0.0f);

	// Ruined gear is still worn. It does not vanish off the body when it fails, and its penalty
	// persists -- carrying a destroyed heavy suit should not be free.
	TestTrue(TEXT("Ruined gear stays equipped"), Equipment->IsSlotEquipped(EEquipmentSlot::Chest));
	TestEqual(TEXT("Ruined gear still counts as worn"), Equipment->GetEquippedItemCount(), 1);
	TestEqual(TEXT("Ruined gear still carries its bulk penalty"),
		Equipment->GetTotalBonuses().MovementSpeedBonus, -10.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEquipmentRepairTest,
	"Ginnungagap.Gameplay.Equipment.Repair",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEquipmentRepairTest::RunTest(const FString& Parameters)
{
	UEquipmentComponent* Equipment = NewObject<UEquipmentComponent>();
	Equipment->EquipmentSlots.SetNum(5);

	FEquipmentStats Stats;
	Stats.RadiationResistance = 40.0f;

	FEquipmentItem Item = MakeItem(EEquipmentSlot::Chest, Stats);
	Item.MaxDurability = 100.0f;
	Item.CurrentDurability = 100.0f;
	Item.DurabilityLossPerSecond = 25.0f;
	Equipment->EquipItem(Item);

	// Undamaged gear is not repairable. Spending a repair charge on something already whole reads
	// to a player as the game wasting their supplies.
	TestFalse(TEXT("Intact gear cannot be repaired"), Equipment->CanRepairSlot(EEquipmentSlot::Chest));
	TestFalse(TEXT("Repairing intact gear is refused"), Equipment->RepairSlot(EEquipmentSlot::Chest, 20.0f));

	TestFalse(TEXT("An empty slot cannot be repaired"), Equipment->CanRepairSlot(EEquipmentSlot::Legs));

	// Damage it, then put it back. This is the loop degradation never had: protection scales
	// continuously with durability and nothing restored it, so a run only ever got worse.
	Equipment->DegradeEquipment(2.0f); // 100 -> 50
	TestTrue(TEXT("Damaged gear can be repaired"), Equipment->CanRepairSlot(EEquipmentSlot::Chest));

	const float ProtectionWhenDamaged = Equipment->GetTotalBonuses().RadiationResistance;
	TestTrue(TEXT("Repairing damaged gear succeeds"), Equipment->RepairSlot(EEquipmentSlot::Chest, 25.0f));
	TestTrue(TEXT("Repair restores condition"), Equipment->GetSlotCondition(EEquipmentSlot::Chest) > 0.5f);
	TestTrue(TEXT("Restored condition restores protection"),
		Equipment->GetTotalBonuses().RadiationResistance > ProtectionWhenDamaged);

	// Cannot be repaired past new. Over-repair would make a damaged item better than a fresh one.
	Equipment->RepairSlot(EEquipmentSlot::Chest, 9999.0f);
	TestEqual(TEXT("Repair caps at full condition"),
		Equipment->GetSlotCondition(EEquipmentSlot::Chest), 1.0f);
	TestEqual(TEXT("Protection returns to its undamaged value"),
		Equipment->GetTotalBonuses().RadiationResistance, 40.0f);

	// Ruined gear must be recoverable. It deliberately stays worn rather than unequipping itself,
	// which is only a fair rule if it can be brought back -- otherwise that choice is a trap.
	Equipment->DegradeEquipment(4.0f); // 100 -> 0
	TestEqual(TEXT("Ruined gear gives no protection"),
		Equipment->GetTotalBonuses().RadiationResistance, 0.0f);
	TestTrue(TEXT("Ruined gear is still worn"), Equipment->IsSlotEquipped(EEquipmentSlot::Chest));
	TestTrue(TEXT("Ruined gear can still be repaired"), Equipment->CanRepairSlot(EEquipmentSlot::Chest));
	TestTrue(TEXT("Repairing ruined gear works"), Equipment->RepairSlot(EEquipmentSlot::Chest, 100.0f));
	TestTrue(TEXT("Repaired gear protects again"),
		Equipment->GetTotalBonuses().RadiationResistance > 0.0f);

	// RepairAll reports what actually went in, not what was offered, so a caller can charge for
	// the real work rather than the request.
	Equipment->DegradeEquipment(1.0f); // shave a little off
	const float Restored = Equipment->RepairAllEquipment(9999.0f);
	TestTrue(TEXT("RepairAll reports what it actually restored"), Restored > 0.0f && Restored < 9999.0f);
	TestEqual(TEXT("RepairAll on whole gear restores nothing"), Equipment->RepairAllEquipment(50.0f), 0.0f);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEquipmentSwapTest,
	"Ginnungagap.Gameplay.Equipment.Swap",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FEquipmentSwapTest::RunTest(const FString& Parameters)
{
	UEquipmentComponent* Equipment = NewObject<UEquipmentComponent>();
	Equipment->EquipmentSlots.SetNum(5);

	FEquipmentStats FirstStats;
	FirstStats.RadiationResistance = 10.0f;
	FEquipmentItem First = MakeItem(EEquipmentSlot::Head, FirstStats);
	First.DisplayName = TEXT("First Helmet");

	FEquipmentItem Displaced;
	bool bDisplaced = true;

	// Swapping into an empty slot displaces nothing, and must say so rather than handing back a
	// default-constructed item a caller might then try to store.
	TestTrue(TEXT("Swapping into an empty slot succeeds"),
		Equipment->SwapSlot(First, Displaced, bDisplaced));
	TestFalse(TEXT("An empty slot displaces nothing"), bDisplaced);

	FEquipmentStats SecondStats;
	SecondStats.RadiationResistance = 30.0f;
	FEquipmentItem Second = MakeItem(EEquipmentSlot::Head, SecondStats);
	Second.DisplayName = TEXT("Second Helmet");

	// The point of the verb: the old item comes back rather than evaporating. EquipItem overwrites
	// silently, which is right for applying a saved loadout and wrong for a person swapping gear.
	TestTrue(TEXT("Swapping over an occupied slot succeeds"),
		Equipment->SwapSlot(Second, Displaced, bDisplaced));
	TestTrue(TEXT("The occupied slot reports a displaced item"), bDisplaced);
	TestEqual(TEXT("The displaced item is the one that was worn"), Displaced.DisplayName, FString(TEXT("First Helmet")));

	TestEqual(TEXT("The new item is now worn"),
		Equipment->GetEquippedItem(EEquipmentSlot::Head).DisplayName, FString(TEXT("Second Helmet")));
	TestEqual(TEXT("Only the new item contributes"), Equipment->GetTotalBonuses().RadiationResistance, 30.0f);
	TestEqual(TEXT("Swapping does not add a slot"), Equipment->GetEquippedItemCount(), 1);

	return true;
}

#endif
