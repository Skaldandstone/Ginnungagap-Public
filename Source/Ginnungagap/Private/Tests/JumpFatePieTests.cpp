#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "Meta/RunSeedSubsystem.h"
#include "Ship/CryoPodSystem.h"
#include "Ship/ShipSection.h"
#include "StarSystem/JumpSequenceSubsystem.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"

/**
 * What a jump does to the people aboard.
 *
 * These were untestable until randomness became seeded: every branch here sat behind a roll, so a
 * test would either have been flaky or asserted so loosely it caught nothing. That is what the run
 * seed work was for, and this is it being used.
 *
 * The two EVA outcomes are forced by setting the chance to zero and one rather than by hunting for
 * a seed that produces each. RollChance short-circuits certain outcomes without consuming a draw,
 * so this exercises the real code path while depending on no randomness at all -- a test that
 * needed a particular seed would break the first time anyone added a roll upstream.
 */

namespace JumpFatePie
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

	/** Somewhere no ship section reaches, which is what "outside the ship" actually means here. */
	const FVector FarOutsideShip(5.0e6, 5.0e6, 5.0e6);

	/** Spawns a crew member at a location, healthy. */
	ACoopSurvivalCharacter* SpawnCrew(UWorld* World, const FVector& Location)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

		ACoopSurvivalCharacter* Crew = World->SpawnActor<ACoopSurvivalCharacter>(
			ACoopSurvivalCharacter::StaticClass(), FTransform(Location), Params);
		if (Crew)
		{
			Crew->HealthPercent = 100.0f;
			Crew->OxygenLevelPercent = 100.0f;
			Crew->bIsDead = false;
		}
		return Crew;
	}

	/**
	 * Puts the subsystem in a state where ExecuteJump will actually resolve fates.
	 *
	 * The phase reset is load-bearing. ExecuteJump ends at Arrival and SelectJumpCandidate only
	 * accepts a selection while Cruising, so without this every case after the first silently
	 * fails to arm -- which is exactly what happened the first time this test ran.
	 */
	bool ArmJump(UJumpSequenceSubsystem* Jump)
	{
		Jump->CurrentPhase = EJumpPhase::Cruising;
		Jump->GenerateJumpCandidates();
		return Jump->CurrentCandidates.Num() > 0 && Jump->SelectJumpCandidate(0);
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForJumpSubsystem, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForJumpSubsystem::Update()
{
	UWorld* World = JumpFatePie::FindPieWorld();
	if (World && World->GetGameInstance()
		&& World->GetGameInstance()->GetSubsystem<UJumpSequenceSubsystem>())
	{
		return true;
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(TEXT("No jump subsystem existed before the deadline"));
		return true;
	}

	return false;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertJumpFates, FAutomationTestBase*, Test);

bool FAssertJumpFates::Update()
{
	UWorld* World = JumpFatePie::FindPieWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (!GameInstance)
	{
		Test->AddError(TEXT("PIE game instance vanished before the fate assertions ran"));
		return true;
	}

	UJumpSequenceSubsystem* Jump = GameInstance->GetSubsystem<UJumpSequenceSubsystem>();
	URunSeedSubsystem* Seeds = GameInstance->GetSubsystem<URunSeedSubsystem>();
	if (!Jump || !Seeds)
	{
		Test->AddError(TEXT("Jump or seed subsystem missing"));
		return true;
	}

	// A fixed seed so anything that does still draw is reproducible run to run.
	Seeds->SeedRun(4242);

	// Save the tuning values; these are edited below to force branches and must be put back or the
	// rest of the session inherits a game where nobody ever dies outside the ship.
	const float OriginalFatalChance = Jump->EVAInstantFatalChance;
	const float OriginalPodLoss = Jump->NoPodDetrimentalHealthLoss;

	// --- Outside the ship, fatal ------------------------------------------------------------
	// Forced rather than rolled. RollChance treats a certainty as certain without consuming a draw,
	// so this is the real code path with none of the randomness.
	Jump->EVAInstantFatalChance = 1.0f;

	ACoopSurvivalCharacter* Doomed = JumpFatePie::SpawnCrew(World, JumpFatePie::FarOutsideShip);
	Test->TestNotNull(TEXT("Spawned a crew member outside the ship"), Doomed);

	if (Doomed)
	{
		Test->TestTrue(TEXT("A crew member far from any section counts as outside"),
			Jump->IsCharacterOutsideShip(Doomed));

		if (JumpFatePie::ArmJump(Jump))
		{
			Jump->ExecuteJump();
			Test->TestTrue(TEXT("Jumping outside the ship at a certain fatality kills"), Doomed->bIsDead);
			Test->TestEqual(TEXT("A fatal jump leaves no health"), Doomed->HealthPercent, 0.0f);
		}
		else
		{
			Test->AddError(TEXT("Could not arm a jump for the fatal EVA case"));
		}

		Doomed->Destroy();
	}

	// --- Outside the ship, survivable --------------------------------------------------------
	Jump->EVAInstantFatalChance = 0.0f;

	ACoopSurvivalCharacter* Survivor = JumpFatePie::SpawnCrew(World, JumpFatePie::FarOutsideShip);
	Test->TestNotNull(TEXT("Spawned a crew member for the survivable case"), Survivor);

	const bool bArmedSurvivable = Survivor && JumpFatePie::ArmJump(Jump);
	Test->TestTrue(TEXT("Armed a jump for the survivable EVA case"), bArmedSurvivable);

	if (bArmedSurvivable)
	{
		Jump->ExecuteJump();

		// Survivable is not unharmed. Riding a jump outside the hull costs three quarters of
		// everything keeping you alive, which is what makes the cryo deadline matter.
		Test->TestFalse(TEXT("A survivable EVA jump does not kill"), Survivor->bIsDead);
		Test->TestTrue(TEXT("A survivable EVA jump costs most of the crew member's health"),
			Survivor->HealthPercent < 100.0f && Survivor->HealthPercent > 0.0f);
		Test->TestTrue(TEXT("A survivable EVA jump costs most of their oxygen"),
			Survivor->OxygenLevelPercent < 100.0f && Survivor->OxygenLevelPercent > 0.0f);

	}

	if (Survivor)
	{
		Survivor->Destroy();
	}

	// --- Inside the ship, no functioning pod --------------------------------------------------
	AShipSection* Section = nullptr;
	for (TActorIterator<AShipSection> It(World); It; ++It)
	{
		Section = *It;
		break;
	}
	Test->TestNotNull(TEXT("The map has a ship section to stand in"), Section);

	if (Section)
	{
		ACoopSurvivalCharacter* Exposed = JumpFatePie::SpawnCrew(World, Section->GetActorLocation());
		if (Exposed)
		{
			Test->TestFalse(TEXT("A crew member inside a section is not outside the ship"),
				Jump->IsCharacterOutsideShip(Exposed));

			// A visible, unambiguous loss so the assertion is about the branch being taken rather
			// than about the exact tuning value.
			Jump->NoPodDetrimentalHealthLoss = 40.0f;

			if (JumpFatePie::ArmJump(Jump))
			{
				Jump->ExecuteJump();

				Test->TestFalse(TEXT("Missing cryo is survivable"), Exposed->bIsDead);
				Test->TestTrue(TEXT("Missing cryo costs health"), Exposed->HealthPercent < 100.0f);
				Test->TestTrue(TEXT("Missing cryo never drops below its floor"),
					Exposed->HealthPercent >= Jump->NoPodMinHealthPercent);

				// The lasting consequence, and the reason missing a window is worse than it looks
				// in the moment.
				if (const UPlayerStatusEffectComponent* Status = Exposed->GetStatusEffectComponent())
				{
					Test->TestTrue(TEXT("Missing cryo inflicts jump psychosis"),
						Status->GetStatusSeverity(EPlayerStatusEffect::JumpPsychosis) > 0.0f);
				}
			}
			else
			{
				Test->AddError(TEXT("Could not arm a jump for the no-pod case"));
			}

			Exposed->Destroy();
		}
	}

	// Put the tuning back. Leaving it edited would hand every later test a game with different
	// rules, and the failure would surface somewhere unrelated.
	Jump->EVAInstantFatalChance = OriginalFatalChance;
	Jump->NoPodDetrimentalHealthLoss = OriginalPodLoss;

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapJumpFatePieTest,
	"Ginnungagap.Smoke.JumpFates",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapJumpFatePieTest::RunTest(const FString& Parameters)
{
	const double Deadline = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForJumpSubsystem(this, Deadline));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertJumpFates(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
