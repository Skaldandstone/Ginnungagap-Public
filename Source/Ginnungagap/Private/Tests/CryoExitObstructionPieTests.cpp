#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "Equipment/EquipmentComponent.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/InventoryItemPickup.h"
#include "Kismet/GameplayStatics.h"
#include "Obstructions/ObstructionBarrier.h"

/**
 * That the wake-up sequence's cryo-exit obstruction is actually clearable by a fresh player.
 *
 * place_cryo_exit_obstruction.py placed a Cut/Squeeze-only, non-bypassable AObstructionBarrier at
 * the cryo bay's own door, and the demo's smoke tests confirmed it does not break navmesh
 * reachability or the mission chain -- but neither of those simulates a player actually standing at
 * it and asking whether either verb is available, which is the thing the story beat depends on: cut
 * it with the tool, the result is a gap to squeeze through.
 *
 * Cut is gated on GetWorstSlotCondition() >= MinimumEquipmentCondition (0.2), which is a check on
 * general equipment wear, not a check for a specific cutting tool -- worth knowing, because it means
 * the narrative beat ("find the engineer tool, then cut") is not literally enforced by this
 * obstruction; any equipped gear in decent condition satisfies it. Squeeze has no equipment gate at
 * all. So the real question this test answers is narrower than the story: is the door clearable from
 * the player's actual state at demo start, with nothing hand-fed to it.
 *
 * Also checks the tool pickup place_cryo_tool_pickup.py placed inside the room, on the near side of
 * the same door: that it exists with real item data, and that the transfer mechanism a genuine
 * interaction would trigger -- UInventoryComponent::AddItem -- actually accepts it. Not a full
 * walk-up-and-press-E simulation: AInventoryItemPickup::CanBeCollectedBy also gates on physical
 * distance from the pawn, and simulating real movement is a different, larger kind of test than this
 * file's others attempt. This proves the mechanism is sound the same way the obstruction check
 * proves ResolveWith is sound, without proving a pawn can physically walk there.
 */

namespace CryoExitObstructionPie
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

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertCryoExitClearable, FAutomationTestBase*, Test);

bool FAssertCryoExitClearable::Update()
{
	UWorld* World = CryoExitObstructionPie::FindPieWorld();
	if (!Test->TestNotNull(TEXT("A PIE world exists"), World))
	{
		return true;
	}

	AObstructionBarrier* Barrier = nullptr;
	for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
	{
		if (It->ActorHasTag(TEXT("CRYO-EXIT")))
		{
			Barrier = *It;
			break;
		}
	}
	if (!Test->TestNotNull(TEXT("The cryo-exit obstruction exists in the running level"), Barrier))
	{
		return true;
	}

	Test->TestFalse(TEXT("It has not already been cleared"), Barrier->bCleared);
	Test->TestFalse(TEXT("It is not bypassable -- this is the one way out of cryo"),
		Barrier->bBypassable);

	APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);
	if (!Test->TestNotNull(TEXT("There is a player pawn to test against"), Pawn))
	{
		return true;
	}

	const bool bCutAvailable = Barrier->CanResolveWith(EObstructionVerb::Cut, Pawn);
	const bool bSqueezeAvailable = Barrier->CanResolveWith(EObstructionVerb::Squeeze, Pawn);

	if (const UEquipmentComponent* Equipment = Pawn->FindComponentByClass<UEquipmentComponent>())
	{
		Test->AddInfo(FString::Printf(
			TEXT("Player worst equipment condition at demo start: %.2f (Cut needs >= 0.20)"),
			Equipment->GetWorstSlotCondition()));
	}
	else
	{
		Test->AddWarning(TEXT("Player has no UEquipmentComponent at all -- Cut will read as "
			"EquipmentTooWorn regardless of condition, since GetRefusal treats a missing "
			"component the same as gear too worn to use."));
	}

	// The beat only needs ONE way through to be real. Squeeze has no equipment gate, so this should
	// hold even if Cut does not -- and if neither holds, the door is not the wake-up mechanic the
	// story wants, it is a wall.
	Test->TestTrue(TEXT("At least one of Cut or Squeeze is available to a fresh player"),
		bCutAvailable || bSqueezeAvailable);

	Test->AddInfo(FString::Printf(TEXT("Cut available: %s   Squeeze available: %s"),
		bCutAvailable ? TEXT("yes") : TEXT("no"),
		bSqueezeAvailable ? TEXT("yes") : TEXT("no")));

	// The tool pickup, checked before clearing the door -- it sits on the room side, where a player
	// would reach it first.
	AInventoryItemPickup* ToolPickup = nullptr;
	for (TActorIterator<AInventoryItemPickup> It(World); It; ++It)
	{
		if (It->ActorHasTag(TEXT("CRYO-TOOL")))
		{
			ToolPickup = *It;
			break;
		}
	}
	if (Test->TestNotNull(TEXT("The cryo tool pickup exists in the running level"), ToolPickup))
	{
		Test->TestNotNull(TEXT("It has a real item definition"),
			ToolPickup->ItemDefinition.Get());
		Test->TestTrue(TEXT("Its quantity is positive"), ToolPickup->Quantity > 0);

		if (UInventoryComponent* Inventory = Pawn->FindComponentByClass<UInventoryComponent>())
		{
			Test->TestTrue(TEXT("The player's inventory can accept the tool item"),
				Inventory->CanAddItem(ToolPickup->ItemDefinition, ToolPickup->Quantity));
			Test->TestTrue(TEXT("AddItem -- the transfer OnInteract would trigger -- succeeds"),
				Inventory->AddItem(ToolPickup->ItemDefinition, ToolPickup->Quantity));
		}
		else
		{
			Test->AddError(TEXT("Player has no UInventoryComponent -- the tool could never be "
				"collected regardless of position"));
		}
	}

	// Actually clear it, the way a player would, and confirm the state that unlocks.
	const EObstructionVerb ChosenVerb = bCutAvailable ? EObstructionVerb::Cut : EObstructionVerb::Squeeze;
	if (Test->TestTrue(TEXT("ResolveWith the available verb succeeds"),
		Barrier->ResolveWith(ChosenVerb, Pawn)))
	{
		Test->TestTrue(TEXT("The barrier reports cleared afterward"), Barrier->bCleared);
		Test->TestEqual(TEXT("ClearedWith records the verb actually used"),
			Barrier->ClearedWith, ChosenVerb);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCryoExitObstructionPieTest,
	"Ginnungagap.Smoke.CryoExitObstructionClearable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCryoExitObstructionPieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertCryoExitClearable(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
