#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Inventory/ItemDefinition.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/ShipboardWeaponDefinition.h"

/**
 * That the workshop bench hands something over.
 *
 * AQuickDemoWorkshopBench has always had the full grant path: it assigns StartingWeaponClass, calls
 * GrantStartingWeapon, and walks GrantedItems into the inventory. GrantStartingWeapon's own comment
 * says the demo "hands a weapon over at the workshop rather than in cryo". And GrantedWeaponClass
 * was assigned in exactly nowhere -- not in C++, not in a Blueprint, not in any of the Python
 * placement scripts -- so `if (GrantedWeaponClass)` was false on every run and GrantedItems was
 * empty. The player crossed the ship, ran a five-second activity called "Draw field equipment", and
 * walked away with what they arrived with.
 *
 * Constructed with NewObject rather than read off the CDO on purpose. The constructor resolves its
 * assets with LoadObject, matching the mesh loading already in that file; the CDO is built during
 * module startup, and asserting against it would be asserting about load order rather than about
 * the bench. NewObject re-runs the constructor at test time, which is when the game would.
 */

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapWorkshopBenchGrantsTest,
	"Ginnungagap.LevelSetup.WorkshopBenchGrants",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapWorkshopBenchGrantsTest::RunTest(const FString& Parameters)
{
	AQuickDemoWorkshopBench* Bench = NewObject<AQuickDemoWorkshopBench>();
	if (!TestNotNull(TEXT("Constructed a workshop bench"), Bench))
	{
		return false;
	}

	// --- the weapon -------------------------------------------------------------------------
	// The assertion that would have failed for the entire life of this class.
	TestNotNull(TEXT("The bench has a weapon class to grant"), Bench->GrantedWeaponClass.Get());

	if (Bench->GrantedWeaponClass)
	{
		TestTrue(TEXT("...and it is a weapon, not some other actor that happened to load"),
			Bench->GrantedWeaponClass->IsChildOf(AShipboardWeapon::StaticClass()));

		// The class alone would spawn a weapon with no stats. AShipboardWeapon reads its definition
		// in BeginPlay, so a class without one is a tool that does nothing when fired -- which would
		// look exactly like the bug this test exists to catch.
		TestNotNull(TEXT("...and comes with the definition that gives it its numbers"),
			Bench->GrantedWeaponDefinition.Get());
	}

	// --- the consumables --------------------------------------------------------------------
	TestEqual(TEXT("The bench grants both field supplies"), Bench->GrantedItems.Num(), 2);

	// Guarded individually in the constructor so one missing asset costs one item; that means a
	// count of 2 is not sufficient evidence on its own that neither entry is null.
	for (int32 Index = 0; Index < Bench->GrantedItems.Num(); ++Index)
	{
		TestNotNull(*FString::Printf(TEXT("Granted item %d resolved to a real definition"), Index),
			Bench->GrantedItems[Index].Get());
	}

	// --- the bench is still single-use ------------------------------------------------------
	// Now that it grants something, this stops being cosmetic: a repeatable bench would let a
	// player stack fastener tools and empty the field supplies in a loop.
	TestEqual(TEXT("The bench can still only be drawn from once"), Bench->RemainingUses, 1);

	return true;
}

#endif
