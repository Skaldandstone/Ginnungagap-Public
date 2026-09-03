#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "Inventory/InventoryComponent.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "Weapons/CaptiveBoltDriver.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/WeaponMountComponent.h"

/**
 * That the workshop bench's grant actually changes a live player's state, not just its own fields.
 *
 * WorkshopBenchGrantTests (a unit test, NewObject-constructed, no world) proved the bench's
 * constructor assigns real defaults -- GrantedWeaponClass, GrantedWeaponDefinition, two
 * GrantedItems -- closing the bug where the bench granted nothing at all. It does not, and by its
 * own design cannot, prove that calling the bench's actual completion trigger against a live pawn
 * results in that pawn holding a weapon and the items. This is the PIE half of that proof: find the
 * bench placed in the real demo map, call its real OnActivityCompleted_Implementation against the
 * real player pawn, and check the pawn's own state afterward.
 *
 * Calls the completion function directly rather than driving the five-second activity timer and
 * whatever input completes it -- consistent with how this session's other new PIE tests prove a
 * mechanism (ResolveWith, AddItem) without claiming to prove the player input or navigation that
 * would trigger it for real. CanStartActivity's objective gate is bypassed by that same choice; this
 * proves the grant is sound, not that a fresh player can reach and start the activity.
 */

namespace WorkshopBenchLivePie
{
	UWorld* FindPieWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertWorkshopBenchGrantsLive, FAutomationTestBase*, Test);

bool FAssertWorkshopBenchGrantsLive::Update()
{
	UWorld* World = WorkshopBenchLivePie::FindPieWorld();
	if (!Test->TestNotNull(TEXT("A PIE world exists"), World))
	{
		return true;
	}

	AQuickDemoWorkshopBench* Bench = nullptr;
	for (TActorIterator<AQuickDemoWorkshopBench> It(World); It; ++It)
	{
		Bench = *It;
		break;
	}
	if (!Test->TestNotNull(TEXT("The workshop bench exists in the running demo map"), Bench))
	{
		return true;
	}

	// Not the constructor's exact values: a placed instance's saved properties replace the
	// constructor defaults outright, so the map's bench legitimately carries four items where the
	// constructor adds two, and a constructor fix never reaches it. Assert shape, not the CDO.
	Test->TestTrue(TEXT("The placed bench grants at least one item"), Bench->GrantedItems.Num() > 0);
	for (const UItemDefinition* Item : Bench->GrantedItems)
	{
		Test->TestNotNull(TEXT("No granted item slot is empty"), Item);
	}

	// The trap this test found on its first run: the placed bench's saved class was the bare
	// AShipboardWeapon base, which would grant an inert weapon -- or nothing, if it cannot spawn.
	UClass* GrantClass = Bench->GrantedWeaponClass.Get();
	Test->TestNotNull(TEXT("The placed bench has a weapon class to grant"), GrantClass);
	Test->TestTrue(TEXT("...and it is a real weapon, not the bare AShipboardWeapon base"),
		GrantClass && GrantClass != AShipboardWeapon::StaticClass());

	ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(
		UGameplayStatics::GetPlayerPawn(World, 0));
	if (!Test->TestNotNull(TEXT("There is a player character to grant onto"), Character))
	{
		return true;
	}

	UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>();
	UInventoryComponent* Inventory = Character->FindComponentByClass<UInventoryComponent>();
	Test->TestNotNull(TEXT("The player has a weapon mount"), Mount);
	Test->TestNotNull(TEXT("The player has an inventory"), Inventory);

	// "Nothing mounted" was never the real starting state: the character constructor auto-arms
	// every pawn with a captive bolt driver via bSpawnDefaultWeapon. That is precisely why the
	// bench's grant used to be a silent no-op.
	AShipboardWeapon* Before = Mount ? Mount->GetMountedWeapon() : nullptr;
	Test->TestNotNull(TEXT("Before the grant, the pawn is already auto-armed"), Before);
	Test->TestTrue(TEXT("...with the constructor's default captive bolt driver"),
		Before && Before->IsA<ACaptiveBoltDriver>());

	const int32 ItemsBefore = Inventory ? Inventory->GetStacks().Num() : 0;

	// The real trigger, called directly.
	Bench->OnActivityCompleted_Implementation(Character);

	if (Mount)
	{
		AShipboardWeapon* After = Mount->GetMountedWeapon();
		Test->TestNotNull(TEXT("After the grant, a weapon is mounted"), After);
		Test->TestTrue(TEXT("The swap actually happened: the mounted weapon changed identity"),
			After && After != Before);
		Test->TestTrue(TEXT("...and it is the bench's tool, not the auto-armed driver"),
			After && GrantClass && After->IsA(GrantClass));
	}
	if (Inventory)
	{
		Test->TestTrue(TEXT("After the grant, the inventory holds more than it did"),
			Inventory->GetStacks().Num() > ItemsBefore);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapWorkshopBenchLivePieTest,
	"Ginnungagap.Smoke.WorkshopBenchGrantsLive",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapWorkshopBenchLivePieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertWorkshopBenchGrantsLive(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
