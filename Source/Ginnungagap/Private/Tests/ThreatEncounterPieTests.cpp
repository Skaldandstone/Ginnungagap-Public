#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

#include "AI/PatrollingEnemyController.h"
#include "CoopSurvivalCharacter.h"
#include "Ship/ShipSection.h"
#include "Stealth/NoisePerceptionSubsystem.h"
#include "Stealth/PlayerNoiseEmitterComponent.h"
#include "Stealth/PlayerVisibilityComponent.h"
#include "Threats/ShipThreatDirector.h"
#include "Threats/ShipboardThreat.h"

/**
 * Proves the demo encounter actually functions, rather than merely existing.
 *
 * The map had no antagonist at all until a threat director was placed in it. Confirming that
 * threats spawn is easy and not enough: the chain from director to a hunting enemy runs through
 * several links that fail silently. A threat whose controller is not a patrolling one, or one that
 * gets an empty patrol list, spawns perfectly and then stands still forever -- which reads as an
 * empty ship rather than as a bug.
 *
 * These assert every link in that chain, in the real map, so an enemy that has quietly stopped
 * hunting shows up as a failing test rather than as a level that feels lifeless.
 */

namespace ThreatPie
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

/** Waits until the director has actually started its encounter, or gives up on its own deadline. */
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForEncounter, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForEncounter::Update()
{
	UWorld* World = ThreatPie::FindPieWorld();
	if (World)
	{
		for (TActorIterator<AShipThreatDirector> It(World); It; ++It)
		{
			if (It->EncounterState == EThreatEncounterState::Active)
			{
				return true;
			}
		}
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(World
			? TEXT("No threat director reached the Active state before the deadline")
			: TEXT("No PIE world existed before the deadline"));
		return true;
	}

	return false;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertEncounterWiring, FAutomationTestBase*, Test);

bool FAssertEncounterWiring::Update()
{
	UWorld* World = ThreatPie::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("PIE world vanished before the encounter assertions ran"));
		return true;
	}

	// The director has to be in the map at all. It was absent for the entire life of this map
	// before it was placed, and nothing complained -- which is exactly why this is asserted.
	AShipThreatDirector* Director = nullptr;
	for (TActorIterator<AShipThreatDirector> It(World); It; ++It)
	{
		Director = *It;
		break;
	}

	Test->TestNotNull(TEXT("The demo map contains a threat director"), Director);
	if (!Director)
	{
		return true;
	}

	Test->TestEqual(TEXT("The encounter started"), Director->EncounterState, EThreatEncounterState::Active);
	Test->TestTrue(TEXT("The encounter produced threats"), Director->GetRemainingThreatCount() > 0);

	// Sections are what threats spawn against and patrol between. Without them the director places
	// everything at its own location and the AI has nowhere to walk.
	int32 SectionCount = 0;
	for (TActorIterator<AShipSection> It(World); It; ++It)
	{
		++SectionCount;
	}
	Test->TestTrue(TEXT("The map has ship sections to patrol"), SectionCount > 0);

	// The chain that fails silently: spawned -> possessed -> possessed by a *patrolling* controller
	// -> given somewhere to patrol. A break at any link leaves a threat standing still, and a
	// motionless enemy is indistinguishable from an empty room.
	int32 Threats = 0;
	int32 WithController = 0;
	int32 WithPatrolController = 0;
	int32 WithPatrolRoute = 0;

	for (TActorIterator<AShipboardThreat> It(World); It; ++It)
	{
		AShipboardThreat* Threat = *It;
		if (!IsValid(Threat))
		{
			continue;
		}

		++Threats;

		AController* Controller = Threat->GetController();
		if (!Controller)
		{
			continue;
		}
		++WithController;

		APatrollingEnemyController* Patroller = Cast<APatrollingEnemyController>(Controller);
		if (!Patroller)
		{
			continue;
		}
		++WithPatrolController;

		if (Patroller->PatrolSections.Num() > 0)
		{
			++WithPatrolRoute;
		}
	}

	Test->TestTrue(TEXT("Threats exist in the world"), Threats > 0);

	// Each of these is reported separately rather than as one combined check, so a failure says
	// which link broke instead of only that something did.
	Test->TestEqual(TEXT("Every threat is possessed"), WithController, Threats);
	Test->TestEqual(TEXT("Every threat is possessed by a patrolling controller"), WithPatrolController, Threats);
	Test->TestEqual(TEXT("Every threat was given somewhere to patrol"), WithPatrolRoute, Threats);

	// The other half of the stealth loop. Perception is worthless if the player emits nothing for
	// it to read, and the components are easy to lose in a pawn refactor.
	Test->TestNotNull(TEXT("The noise perception subsystem exists"),
		World->GetSubsystem<UNoisePerceptionSubsystem>());

	ACoopSurvivalCharacter* Player = nullptr;
	for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
	{
		Player = *It;
		break;
	}

	Test->TestNotNull(TEXT("A player character exists to be hunted"), Player);
	if (Player)
	{
		Test->TestNotNull(TEXT("The player emits noise"), Player->GetNoiseEmitterComponent());
		Test->TestNotNull(TEXT("The player has a visibility signature"), Player->GetVisibilityComponent());
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapThreatEncounterPieTest,
	"Ginnungagap.Smoke.ThreatEncounter",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapThreatEncounterPieTest::RunTest(const FString& Parameters)
{
	const double Deadline = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForEncounter(this, Deadline));

	// Possession is deferred a frame past spawning, so asserting immediately would race it and
	// report every threat as unpossessed.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertEncounterWiring(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
