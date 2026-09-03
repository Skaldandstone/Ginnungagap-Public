#include "Misc/AutomationTest.h"

#include "Inventory/InventoryItemPickup.h"
#include "Inventory/ItemDefinition.h"
#include "WorldItems/WorldItemSeedCatalog.h"
#include "WorldItems/WorldItemSeedPoint.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FWorldItemSeedSafeDefaultsTest,
    "Ginnungagap.WorldItems.SafeDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWorldItemSeedSafeDefaultsTest::RunTest(const FString& Parameters)
{
    const AWorldItemSeedPoint* SeedPoint = GetDefault<AWorldItemSeedPoint>();
    TestNotNull(TEXT("Seed point has a default object"), SeedPoint);
    TestTrue(TEXT("Default spawn chance is normalized"), SeedPoint->SpawnChance >= 0.0f && SeedPoint->SpawnChance <= 1.0f);
    TestTrue(TEXT("At least one spawn roll is requested"), SeedPoint->SpawnRolls >= 1);
    TestTrue(TEXT("Negative scatter is disabled"), SeedPoint->ScatterRadiusCm >= 0.0f);

    const AInventoryItemPickup* Pickup = GetDefault<AInventoryItemPickup>();
    TestNotNull(TEXT("Inventory pickup has a default object"), Pickup);
    TestTrue(TEXT("Pickup quantity is positive"), Pickup->Quantity > 0);
    TestTrue(TEXT("Pickup actor replicates"), Pickup->GetIsReplicated());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FWorldItemSeedCatalogIdentityTest,
    "Ginnungagap.WorldItems.CatalogIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWorldItemSeedCatalogIdentityTest::RunTest(const FString& Parameters)
{
    const UWorldItemSeedCatalog* Catalog = NewObject<UWorldItemSeedCatalog>();
    TestEqual(TEXT("Catalog primary asset type is stable"), Catalog->GetPrimaryAssetId().PrimaryAssetType, FPrimaryAssetType(TEXT("WorldItemSeedCatalog")));

    UItemDefinition* Item = NewObject<UItemDefinition>();
    Item->ItemId = TEXT("TestSalvageItem");
    TestEqual(TEXT("Item identity remains data driven"), Item->GetPrimaryAssetId().PrimaryAssetName, FName(TEXT("TestSalvageItem")));
    return true;
}

#endif
