#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/ItemDefinition.h"

/**
 * The refusal rules on the inventory verbs.
 *
 * These cover the cases that protect the player from the game rather than the happy paths.
 * Applying an effect and consuming an item are easy to get right; refusing to spend a medkit that
 * would heal nothing, and refusing to drop the object the run depends on, are the parts that stop
 * a player losing something they cannot get back.
 *
 * No world here, so the character-facing half of UseItem is not exercised -- that needs a real
 * pawn and belongs with the PIE tests. What is checked is every guard that fires before a
 * character is ever touched.
 */

namespace
{
    UItemDefinition* MakeItem(bool bConsumable = false, bool bCanDrop = true, bool bMission = false)
    {
        UItemDefinition* Item = NewObject<UItemDefinition>();
        Item->ItemId = TEXT("TestItem");
        Item->MaxStackSize = 10;
        Item->bIsConsumable = bConsumable;
        Item->bCanDrop = bCanDrop;
        Item->bMissionItem = bMission;
        return Item;
    }

    UInventoryComponent* MakeInventory()
    {
        return NewObject<UInventoryComponent>();
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryDropRulesTest,
    "Ginnungagap.Gameplay.Inventory.DropRules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FInventoryDropRulesTest::RunTest(const FString& Parameters)
{
    UInventoryComponent* Inventory = MakeInventory();

    UItemDefinition* Ordinary = MakeItem();
    Inventory->AddItem(Ordinary, 3);
    TestTrue(TEXT("An ordinary held item can be dropped"), Inventory->CanDropItem(Ordinary, 1));
    TestTrue(TEXT("The whole held stack can be dropped"), Inventory->CanDropItem(Ordinary, 3));

    // Asking for more than is held must fail rather than dropping whatever happens to be there.
    // A partial drop looks like the game losing count.
    TestFalse(TEXT("More than is held cannot be dropped"), Inventory->CanDropItem(Ordinary, 4));
    TestFalse(TEXT("A quantity of zero is refused"), Inventory->CanDropItem(Ordinary, 0));
    TestFalse(TEXT("A negative quantity is refused"), Inventory->CanDropItem(Ordinary, -2));
    TestFalse(TEXT("A null item is refused"), Inventory->CanDropItem(nullptr, 1));

    // Not held at all.
    UItemDefinition* Absent = MakeItem();
    TestFalse(TEXT("An item that is not held cannot be dropped"), Inventory->CanDropItem(Absent, 1));

    // Flagged undroppable by its own definition.
    UItemDefinition* Bolted = MakeItem(false, /*bCanDrop*/ false);
    Inventory->AddItem(Bolted, 1);
    TestFalse(TEXT("An item marked undroppable is refused"), Inventory->CanDropItem(Bolted, 1));

    // The rule that matters most: a player who drops the thing the run depends on has softlocked
    // themselves, and no confirmation dialog reliably prevents that.
    UItemDefinition* MissionCritical = MakeItem(false, /*bCanDrop*/ true, /*bMission*/ true);
    Inventory->AddItem(MissionCritical, 1);
    TestFalse(TEXT("A mission item is refused even when marked droppable"),
        Inventory->CanDropItem(MissionCritical, 1));

    // Refusing must not have consumed anything on the way.
    TestEqual(TEXT("A refused drop leaves the stack untouched"), Inventory->GetItemQuantity(Bolted), 1);
    TestEqual(TEXT("A refused mission drop leaves the item held"),
        Inventory->GetItemQuantity(MissionCritical), 1);

    // Without a world there is nowhere to spawn a pickup, so the drop must fail and -- critically
    // -- must not delete the items on the way out.
    TestFalse(TEXT("Dropping without a world fails"), Inventory->DropItem(Ordinary, 1));
    TestEqual(TEXT("A failed drop does not destroy the stack"), Inventory->GetItemQuantity(Ordinary), 3);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryUseRulesTest,
    "Ginnungagap.Gameplay.Inventory.UseRules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FInventoryUseRulesTest::RunTest(const FString& Parameters)
{
    UInventoryComponent* Inventory = MakeInventory();

    // A tool or a salvage stack is not a consumable and using it should do nothing at all rather
    // than quietly destroying it.
    UItemDefinition* Tool = MakeItem(/*bConsumable*/ false);
    Inventory->AddItem(Tool, 2);
    TestFalse(TEXT("A non-consumable cannot be used"), Inventory->CanUseItem(Tool));
    TestFalse(TEXT("Using a non-consumable fails"), Inventory->UseItem(Tool));
    TestEqual(TEXT("A refused use consumes nothing"), Inventory->GetItemQuantity(Tool), 2);

    TestFalse(TEXT("A null item cannot be used"), Inventory->CanUseItem(nullptr));

    // Consumable but not held.
    UItemDefinition* Medkit = MakeItem(/*bConsumable*/ true);
    Medkit->HealthRestorePercent = 40.0f;
    TestFalse(TEXT("A consumable that is not held cannot be used"), Inventory->CanUseItem(Medkit));

    // Held, but with no character to apply to. It must refuse rather than consume into nothing --
    // the same protection as the full-health case, arrived at from a different direction.
    Inventory->AddItem(Medkit, 1);
    TestFalse(TEXT("A consumable with no owning character cannot be used"), Inventory->CanUseItem(Medkit));
    TestFalse(TEXT("Using it fails"), Inventory->UseItem(Medkit));
    TestEqual(TEXT("The medkit survives a refused use"), Inventory->GetItemQuantity(Medkit), 1);

    // A consumable that restores nothing is not usable, whatever its flags say. This is the case
    // that stops an empty definition being treated as a valid item.
    UItemDefinition* Inert = MakeItem(/*bConsumable*/ true);
    Inventory->AddItem(Inert, 1);
    TestFalse(TEXT("A consumable that restores nothing cannot be used"), Inventory->CanUseItem(Inert));

    return true;
}

#endif
