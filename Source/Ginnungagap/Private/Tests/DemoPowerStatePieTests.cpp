#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#include "Kismet/GameplayStatics.h"
#include "Ship/ModularShipRoom.h"

/**
 * That the demo actually begins with the power out.
 *
 * The third objective is "Restore the ship main bus". Nothing had ever taken the bus down.
 * AModularShipRoom::bPowered defaults to true, and every call to SetPowered in the project passed
 * true -- so every room sat at Nominal from the first frame and the objective restored power that
 * had never been lost.
 *
 * It survived review because the damage is runtime-only and invisible in the two places anybody
 * looked. Nominal drives the room's IdentityLight to 1250 in cold blue, which floods every room and
 * fights the warm per-room emergency palette the whole dressing pass is built around -- but hero
 * shots render the *editor* world, where BeginPlay never runs and those lights sit at the zero they
 * were saved with. The stills looked correct for a reason that had nothing to do with the game
 * being correct.
 *
 * A PIE test rather than a unit test, and that is the whole point: this bug is only visible with
 * BeginPlay run. Anything cheaper would have missed it exactly the way everything else did.
 */

namespace DemoPowerPie
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

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertDemoStartsUnpowered, FAutomationTestBase*, Test);

bool FAssertDemoStartsUnpowered::Update()
{
	UWorld* World = DemoPowerPie::FindPieWorld();
	if (!Test->TestNotNull(TEXT("A PIE world exists"), World))
	{
		return true;
	}

	int32 Tagged = 0;
	int32 Powered = 0;
	int32 Unpowered = 0;

	for (TActorIterator<AModularShipRoom> It(World); It; ++It)
	{
		AModularShipRoom* Room = *It;
		if (!Room || !Room->ActorHasTag(TEXT("QuickDemoShipRoom")))
		{
			continue;
		}

		++Tagged;
		if (Room->bPowered)
		{
			++Powered;
		}
		if (Room->OperationalState == EShipRoomOperationalState::Unpowered)
		{
			++Unpowered;
		}
	}

	// Guard the guard. If the tag were ever renamed this test would find nothing, assert nothing,
	// and pass -- which is the failure mode that let the original bug live.
	Test->TestTrue(TEXT("The demo map contains tagged ship rooms to power down"), Tagged > 0);

	Test->TestEqual(TEXT("No demo room is still powered at the start of the run"), Powered, 0);

	// Deliberately separate from bPowered. A room can be unpowered and still report some other
	// operational state -- RefreshOperationalState ranks contamination, quarantine, decompression
	// and damage above loss of power -- so asserting only the flag would not prove the state the
	// identity light actually reads from. On a clean demo start nothing outranks it.
	Test->TestEqual(TEXT("...and every one of them reads as Unpowered"), Unpowered, Tagged);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapDemoPowerStatePieTest,
	"Ginnungagap.Smoke.DemoStartsUnpowered",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapDemoPowerStatePieTest::RunTest(const FString& Parameters)
{
	// Same reason as the mission-chain test: the director restores a checkpoint on its first tick,
	// and a stale slot with RestorePower already completed would turn the power back on and make
	// this test measure the save file instead of the demo's opening state.
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	// The power-down happens in the director's BeginPlay and the checkpoint restore runs a tick
	// later, so the state under test is not settled for a frame or two.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertDemoStartsUnpowered(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
