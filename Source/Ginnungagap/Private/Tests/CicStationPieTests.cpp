#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

#include "Meta/RunSeedSubsystem.h"
#include "Ship/JumpConsoleSystem.h"
#include "Ship/SensorArraySystem.h"
#include "Ship/ShipHelmSystem.h"
#include "StarSystem/JumpSequenceSubsystem.h"

/**
 * The command room actually commands something.
 *
 * The demo's last objective is "Bring the Combat Information Center online" and the room was
 * empty, which made three written systems unreachable rather than merely untested:
 *
 *   ComputeFalsificationChance guards its sensor lookup with `if (Sensors)`. With no array in the
 *   world the multiplier was never applied, so every jump readout was falsified at the base rate
 *   however good the sensors nominally were.
 *
 *   ExecuteJump sums CurrentHeadingOffset across every helm to size the landing error. With no
 *   helm that sum is always zero, so the landing-error branch could not fire at all.
 *
 *   And with no jump console there was no player-facing way to pick a destination.
 *
 * So these assertions are about wiring, not tuning. Each one fails if the actor is missing from
 * the map, which is the state the project was actually in.
 */

namespace CicStationPie
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

	template <typename T>
	T* FirstOf(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It)
		{
			return *It;
		}
		return nullptr;
	}

	/**
	 * Puts the subsystem in a state where ExecuteJump will resolve.
	 *
	 * The phase reset is load-bearing for the same reason it is in the jump fate tests: ExecuteJump
	 * ends at Arrival and SelectJumpCandidate only accepts a selection while Cruising.
	 */
	bool ArmJump(UJumpSequenceSubsystem* Jump)
	{
		Jump->CurrentPhase = EJumpPhase::Cruising;
		Jump->GenerateJumpCandidates();
		return Jump->CurrentCandidates.Num() > 0 && Jump->SelectJumpCandidate(0);
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertCicStations, FAutomationTestBase*, Test);

bool FAssertCicStations::Update()
{
	UWorld* World = CicStationPie::FindPieWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (!GameInstance)
	{
		Test->AddError(TEXT("No PIE game instance for the CIC assertions"));
		return true;
	}

	UJumpSequenceSubsystem* Jump = GameInstance->GetSubsystem<UJumpSequenceSubsystem>();
	URunSeedSubsystem* Seeds = GameInstance->GetSubsystem<URunSeedSubsystem>();
	if (!Jump || !Seeds)
	{
		Test->AddError(TEXT("Jump or seed subsystem missing"));
		return true;
	}

	Seeds->SeedRun(9111);

	ASensorArraySystem* Sensors = CicStationPie::FirstOf<ASensorArraySystem>(World);
	AShipHelmSystem* Helm = CicStationPie::FirstOf<AShipHelmSystem>(World);
	AJumpConsoleSystem* Console = CicStationPie::FirstOf<AJumpConsoleSystem>(World);

	Test->TestNotNull(TEXT("The map has a sensor array"), Sensors);
	Test->TestNotNull(TEXT("The map has a helm"), Helm);
	Test->TestNotNull(TEXT("The map has a jump console"), Console);

	// --- The sensor array is actually consulted -------------------------------------------------
	if (Sensors)
	{
		const int32 OriginalLongRange = Sensors->LongRangeLevel;

		// Level 1 is no protection by design, so a difference has to be forced by upgrading. Doing
		// it directly rather than through UpgradeLongRange keeps this about the jump subsystem
		// reading the array, not about whether the ship can afford components.
		Sensors->LongRangeLevel = Sensors->MaxSensorLevel;
		Test->TestTrue(TEXT("An upgraded array resists falsification"),
			Sensors->GetFalsificationResistance() < 1.0f);

		const float WithoutArray = Jump->ComputeFalsificationChance(nullptr);
		const float WithArray = Jump->ComputeFalsificationChance(Sensors);

		// The assertion that would have failed before the array was placed: passing one has to
		// change the answer, or the array is decorative.
		Test->TestTrue(TEXT("A good array lowers the chance of a falsified readout"),
			WithArray < WithoutArray);

		Sensors->LongRangeLevel = 1;
		Test->TestEqual(TEXT("A baseline array offers no protection, as designed"),
			Jump->ComputeFalsificationChance(Sensors), WithoutArray);

		Sensors->LongRangeLevel = OriginalLongRange;
	}

	// --- The helm is actually reached by ExecuteJump ---------------------------------------------
	if (Helm)
	{
		// Large enough to be unambiguous against the offset scale, so this is about the helm being
		// found rather than about the exact severity it produces.
		Helm->CurrentHeadingOffset = FVector(400.0f, 0.0f, 0.0f);

		const bool bArmed = CicStationPie::ArmJump(Jump);
		Test->TestTrue(TEXT("Armed a jump to run the helm through"), bArmed);

		if (bArmed)
		{
			Jump->ExecuteJump();

			// ExecuteJump consumes the offset in full after folding it into the landing error. A
			// helm the subsystem never found would still be carrying its offset here, which is
			// precisely the state an empty CIC left the game in.
			Test->TestTrue(TEXT("Jumping consumes the helm's heading offset"),
				Helm->CurrentHeadingOffset.IsNearlyZero());
		}

		Helm->CurrentHeadingOffset = FVector::ZeroVector;
	}

	// --- The console can offer a destination without a Blueprint picker --------------------------
	if (Console)
	{
		// The demo has no destination widget attached, and the class carries its own fallback for
		// exactly that. Without it the console opens onto nothing selectable and the jump loop is
		// reachable only from code.
		Test->TestTrue(TEXT("The demo console falls back to auto-selecting a candidate"),
			Console->bAutoSelectFirstCandidate);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCicStationPieTest,
	"Ginnungagap.Smoke.CicStations",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCicStationPieTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertCicStations(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
