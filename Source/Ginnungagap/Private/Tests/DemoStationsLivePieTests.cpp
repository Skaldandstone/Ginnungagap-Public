#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "Equipment/EquipmentComponent.h"
#include "Equipment/EquipmentSystem.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "Ship/ModularShipRoom.h"

/**
 * The remaining demo stations, proven through their real completion triggers against a live pawn.
 *
 * DemoMissionChainPieTests advances the chain through a direct state-transition call, which proves
 * ordering and gating but not that any station's own completion logic does what the beat needs.
 * The obstruction, the cryo pickup and the workshop bench each have that proof now; this file
 * covers the rest, sharing one PIE boot rather than paying for one per station.
 *
 * Lesson carried in from the bench test: never assert the pawn's starting state as empty. The
 * character constructor auto-arms every pawn, and BeginPlay applies an expedition loadout to the
 * equipment component, so "before" is logged as information and only the "after" state is asserted
 * -- the after state is what the story beat depends on, and the before state is whatever the
 * engine happened to leave there.
 */

namespace DemoStationsLivePie
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

// --- suit station ------------------------------------------------------------------------------

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertSuitStationEquipsLive, FAutomationTestBase*, Test);

bool FAssertSuitStationEquipsLive::Update()
{
	UWorld* World = DemoStationsLivePie::FindPieWorld();
	if (!Test->TestNotNull(TEXT("Suit: a PIE world exists"), World))
	{
		return true;
	}

	AQuickDemoSuitStation* Station = nullptr;
	for (TActorIterator<AQuickDemoSuitStation> It(World); It; ++It)
	{
		Station = *It;
		break;
	}
	if (!Test->TestNotNull(TEXT("Suit: a suit station exists in the running demo map"), Station))
	{
		return true;
	}

	ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(
		UGameplayStatics::GetPlayerPawn(World, 0));
	if (!Test->TestNotNull(TEXT("Suit: there is a player character"), Character))
	{
		return true;
	}

	UEquipmentComponent* Equipment = Character->FindComponentByClass<UEquipmentComponent>();
	if (!Test->TestNotNull(TEXT("Suit: the player has an equipment component"), Equipment))
	{
		return true;
	}

	const EEquipmentSlot Slot = Station->StarterSuit.Slot;
	Test->AddInfo(FString::Printf(
		TEXT("Suit: before -- equipped count %d, slot equipped %s, oversuit %s"),
		Equipment->GetEquippedItemCount(),
		Equipment->IsSlotEquipped(Slot) ? TEXT("yes") : TEXT("no"),
		Character->bPressureOversuitEquipped ? TEXT("yes") : TEXT("no")));

	// The real trigger, called directly.
	Station->OnActivityCompleted_Implementation(Character);

	Test->TestTrue(TEXT("Suit: after, the starter suit's slot is equipped"),
		Equipment->IsSlotEquipped(Slot));
	Test->TestTrue(TEXT("Suit: after, the character reports the oversuit as worn"),
		Character->bPressureOversuitEquipped);
	Test->TestTrue(TEXT("Suit: after, the character carries the station's suit role"),
		Character->PressureSuitRole == Station->SuitRole);

	return true;
}

// --- power station -----------------------------------------------------------------------------

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertPowerStationRestoresLive, FAutomationTestBase*, Test);

bool FAssertPowerStationRestoresLive::Update()
{
	UWorld* World = DemoStationsLivePie::FindPieWorld();
	if (!Test->TestNotNull(TEXT("Power: a PIE world exists"), World))
	{
		return true;
	}

	AQuickDemoPowerStation* Station = nullptr;
	for (TActorIterator<AQuickDemoPowerStation> It(World); It; ++It)
	{
		Station = *It;
		break;
	}
	if (!Test->TestNotNull(TEXT("Power: a power station exists in the running demo map"), Station))
	{
		return true;
	}

	APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);
	if (!Test->TestNotNull(TEXT("Power: there is a player pawn"), Pawn))
	{
		return true;
	}

	auto CountRooms = [World](int32& OutTagged, int32& OutUnpowered)
	{
		OutTagged = 0;
		OutUnpowered = 0;
		for (TActorIterator<AModularShipRoom> It(World); It; ++It)
		{
			AModularShipRoom* Room = *It;
			if (!Room || !Room->ActorHasTag(TEXT("QuickDemoShipRoom")))
			{
				continue;
			}
			++OutTagged;
			if (Room->OperationalState == EShipRoomOperationalState::Unpowered)
			{
				++OutUnpowered;
			}
		}
	};

	int32 Tagged = 0;
	int32 Unpowered = 0;
	CountRooms(Tagged, Unpowered);
	Test->TestTrue(TEXT("Power: the map has tagged ship rooms"), Tagged > 0);
	Test->TestEqual(TEXT("Power: before, every tagged room is Unpowered"), Unpowered, Tagged);

	// Position the chain. The suit command completed SuitUp through its real trigger, which makes
	// ReachWorkshop active; the workshop's own trigger is proven in WorkshopBenchLivePieTests, so
	// it is advanced here by the director's direct call purely to reach the state this station is
	// written for. Asserted, so a positioning failure reads as one rather than as a power failure.
	Test->TestTrue(TEXT("Power: ReachWorkshop advances (SuitUp was completed for real)"),
		AQuickDemoMissionDirector::CompleteActiveObjective(World, TEXT("QD_ReachWorkshop")));
	Test->TestTrue(TEXT("Power: RestorePower is now the active objective"),
		AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_RestorePower")));

	// The real trigger, called directly.
	Station->OnActivityCompleted_Implementation(Pawn);

	CountRooms(Tagged, Unpowered);
	Test->TestEqual(TEXT("Power: after, no tagged room is still Unpowered"), Unpowered, 0);
	Test->TestTrue(TEXT("Power: the station completed its own objective and the chain advanced"),
		AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_SealBreach")));

	return true;
}

// --- test --------------------------------------------------------------------------------------

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapDemoStationsLivePieTest,
	"Ginnungagap.Smoke.DemoStationsCompleteLive",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapDemoStationsLivePieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertSuitStationEquipsLive(this));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertPowerStationRestoresLive(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
