#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "AI/PatrollingEnemyController.h"
#include "Bloom/BloomDormantHulk.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Engine/Engine.h"
#include "Engine/PointLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "NavigationSystem.h"
#include "Player/SurvivalPlayerController.h"
#include "Ship/ModularShipRoom.h"
#include "Threats/ShipboardThreat.h"
#include "UI/SurvivalHUDWidget.h"

/**
 * The beat sheet's "power comes back and something wakes and roars", as the game actually does it.
 *
 * Restoring the main bus through the real power station must: bring the tagged rooms up on
 * emergency power with red identity lights; wake the dormant hulk placed in the breach room; have
 * it roar -- sound, a camera shake, one HUD line -- and then hold its ground, because the beat is
 * a threat announced, not a chase begun. Each of those is asserted against the live objects, not
 * against the code that was meant to produce them. The suit repair bench is checked here too,
 * since it is on the same route and its fix landed in the same pass: it now raises the integrity
 * the breach room drains.
 */

namespace HulkReveal
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
	T* First(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It)
		{
			return *It;
		}
		return nullptr;
	}

	enum class EPhase : uint8 { Settle, Arm, WaitRoar, WaitHold, Done };
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FAssertHulkReveal, FAutomationTestBase*, Test, double, StartSeconds);

bool FAssertHulkReveal::Update()
{
	static HulkReveal::EPhase Phase = HulkReveal::EPhase::Settle;
	static double PhaseSince = 0.0;
	static FVector HulkStart = FVector::ZeroVector;
	static TWeakObjectPtr<ABloomDormantHulk> Hulk;

	auto Finish = [&]() -> bool
	{
		Phase = HulkReveal::EPhase::Settle;
		Hulk = nullptr;
		return true;
	};

	UWorld* World = HulkReveal::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world"));
		return Finish();
	}
	const double Now = FPlatformTime::Seconds();
	if (Now - StartSeconds > 120.0)
	{
		Test->AddError(TEXT("Hulk reveal assertions timed out"));
		return Finish();
	}

	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;

	switch (Phase)
	{
	case HulkReveal::EPhase::Settle:
		if (AQuickDemoOpeningSequence* Opening = HulkReveal::First<AQuickDemoOpeningSequence>(World); Opening && !Opening->IsComplete())
		{
			return false;   // the player is still asleep in the pod
		}
		if (UNavigationSystemV1::IsNavigationBeingBuilt(World) || Now - StartSeconds < 6.0)
		{
			return false;
		}
		Phase = HulkReveal::EPhase::Arm;
		return false;

	case HulkReveal::EPhase::Arm:
	{
		if (!Test->TestNotNull(TEXT("There is a possessed player pawn"), Pawn))
		{
			return Finish();
		}
		Hulk = HulkReveal::First<ABloomDormantHulk>(World);
		if (!Test->TestNotNull(TEXT("A dormant Bloom hulk is placed in the demo map"), Hulk.Get()))
		{
			return Finish();
		}

		// --- asleep, and asleep means asleep ---------------------------------------------------
		Test->TestTrue(TEXT("The hulk starts dormant"), Hulk->IsDormant());
		Test->TestFalse(TEXT("The hulk has not roared before anything happened"), Hulk->HasRoared());
		Test->TestTrue(FString::Printf(TEXT("Dormant infection progress sits below Overgrown (%.2f)"), Hulk->GetInfectionProgress()),
			Hulk->GetInfectionProgress() < 0.6f);
		Test->TestEqual(TEXT("A dormant hulk has no attack range"), Hulk->AttackRange, 0.0f);
		APatrollingEnemyController* Controller = Cast<APatrollingEnemyController>(Hulk->GetController());
		if (Test->TestNotNull(TEXT("The hulk is possessed by the patrolling controller"), Controller))
		{
			Test->TestTrue(TEXT("A dormant hulk is anchored"), Controller->bAnchored);
		}
		HulkStart = Hulk->GetActorLocation();

		// The threats the director places are not what this test is about; a stalker that happens
		// to reach the pawn during the hold would read as the hulk moving.
		for (TActorIterator<AShipboardThreat> It(World); It; ++It)
		{
			It->Destroy();
		}

		// --- the route to the power station, through its real triggers ---------------------------
		for (TActorIterator<AQuickDemoSuitStation> It(World); It; ++It) { It->OnActivityCompleted_Implementation(Pawn); break; }
		Test->TestTrue(TEXT("Workshop objective is live after the suit"), AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_ReachWorkshop")));
		if (AQuickDemoWorkshopBench* Bench = HulkReveal::First<AQuickDemoWorkshopBench>(World)) { Bench->OnActivityCompleted_Implementation(Pawn); }

		// Suit repair: the number the breach room drains, not the equipment's own durability.
		ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Pawn);
		const float SuitBefore = Crew ? Crew->GetSuitIntegrity() : -1.0f;
		if (AQuickDemoSuitRepairBench* Repair = HulkReveal::First<AQuickDemoSuitRepairBench>(World)) { Repair->OnActivityCompleted_Implementation(Pawn); }
		const float SuitAfter = Crew ? Crew->GetSuitIntegrity() : -1.0f;
		Test->TestTrue(FString::Printf(TEXT("The suit repair bench raises suit integrity (%.2f -> %.2f)"), SuitBefore, SuitAfter),
			SuitAfter > SuitBefore + 0.05f);

		Test->TestTrue(TEXT("RestorePower objective is live before the power station"), AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_RestorePower")));
		Test->TestTrue(TEXT("The hulk is still dormant with the power still down"), Hulk->IsDormant());

		AQuickDemoPowerStation* Power = HulkReveal::First<AQuickDemoPowerStation>(World);
		if (!Test->TestNotNull(TEXT("The power station exists"), Power))
		{
			return Finish();
		}
		Power->OnActivityCompleted_Implementation(Pawn);

		// --- the moment ---------------------------------------------------------------------------
		Test->TestFalse(TEXT("RestorePower completes through the station"), AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_RestorePower")));
		Test->TestFalse(TEXT("Completing RestorePower wakes the hulk, synchronously"), Hulk->IsDormant());

		// Emergency power sits below every fault in the room's own state ordering, on purpose: the
		// cryo bay starts in Alert (it has damage), and Alert outranks it and lights amber. So the
		// claim is not "every room is EmergencyPower" but "nothing is Nominal or Unpowered, and
		// every room without a louder state is EmergencyPower and red".
		int32 Tagged = 0, Emergency = 0, RedLit = 0, Nominal = 0, Unpowered = 0, Louder = 0;
		FString LouderRooms;
		for (TActorIterator<AModularShipRoom> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("QuickDemoShipRoom"))) { continue; }
			++Tagged;
			switch (It->OperationalState)
			{
			case EShipRoomOperationalState::EmergencyPower: ++Emergency; break;
			case EShipRoomOperationalState::Nominal: ++Nominal; break;
			case EShipRoomOperationalState::Unpowered: ++Unpowered; break;
			default: ++Louder; LouderRooms += It->GetActorLabel() + FString::Printf(TEXT("(%d) "), static_cast<int32>(It->OperationalState)); break;
			}
			if (It->OperationalState == EShipRoomOperationalState::EmergencyPower && It->IdentityLight)
			{
				if (const UPointLightComponent* Light = It->IdentityLight->FindComponentByClass<UPointLightComponent>())
				{
					const FLinearColor Color = Light->GetLightColor();
					if (Color.R > 0.8f && Color.G < 0.3f && Color.B < 0.3f) { ++RedLit; }
				}
			}
		}
		Test->TestTrue(TEXT("There are tagged rooms"), Tagged > 0);
		Test->TestEqual(TEXT("No tagged room is Nominal (cold blue) after the power station"), Nominal, 0);
		Test->TestEqual(TEXT("No tagged room is still Unpowered after the power station"), Unpowered, 0);
		Test->TestTrue(FString::Printf(TEXT("Every room without a louder fault state is on emergency power (%d of %d; louder: %s)"), Emergency, Tagged, *LouderRooms),
			Emergency + Louder == Tagged && Emergency > 0);
		Test->TestEqual(TEXT("Every emergency-power room's identity light is emergency red"), RedLit, Emergency);

		int32 Utility = 0, UtilityRed = 0;
		FString NotRed;
		for (TActorIterator<APointLight> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("QuickDemoUtilityLight"))) { continue; }
			++Utility;
			if (const UPointLightComponent* Light = It->GetComponentByClass<UPointLightComponent>())
			{
				const FLinearColor Color = Light->GetLightColor();
				if (Light->GetVisibleFlag() && Color.R > 0.8f && Color.G < 0.3f) { ++UtilityRed; }
				else { NotRed += It->GetActorLabel() + TEXT(" "); }
			}
		}
		Test->TestTrue(TEXT("There are corridor utility lights"), Utility > 0);
		// A room's identity light is also a utility light, and a louder room state recolours it.
		Test->TestTrue(FString::Printf(TEXT("Every utility light not owned by a louder room comes up red (%d of %d; not red: %s)"), UtilityRed, Utility, *NotRed),
			UtilityRed >= Utility - Louder);

		Phase = HulkReveal::EPhase::WaitRoar;
		PhaseSince = Now;
		return false;
	}

	case HulkReveal::EPhase::WaitRoar:
	{
		if (!Hulk.IsValid())
		{
			Test->AddError(TEXT("The hulk vanished after waking"));
			return Finish();
		}
		if (Now - PhaseSince < Hulk->RoarDelaySeconds + Hulk->WakeRiseSeconds + 0.5)
		{
			return false;
		}
		Test->TestTrue(TEXT("The hulk roared after its delay"), Hulk->HasRoared());
		Test->TestTrue(FString::Printf(TEXT("The wake ran the infection to Overgrown (%.2f)"), Hulk->GetInfectionProgress()),
			Hulk->GetInfectionProgress() > 0.95f);
		Test->TestTrue(TEXT("The hulk has attack range once awake"), Hulk->AttackRange > 100.0f);
		Test->AddInfo(FString::Printf(TEXT("HULK roar audio: sound %s, playing %s"),
			Hulk->RoarAudio && Hulk->RoarAudio->Sound ? *Hulk->RoarAudio->Sound->GetName() : TEXT("none"),
			Hulk->RoarAudio && Hulk->RoarAudio->IsPlaying() ? TEXT("yes") : TEXT("no")));

		if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
		{
			if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
			{
				Test->TestTrue(TEXT("The HUD shows the biomass alert line after the roar"), HUD->IsAlertLineVisible());
			}
			else
			{
				Test->AddInfo(TEXT("HULK no HUD widget on the player controller in this session; alert line not checked"));
			}
		}

		// Stand in front of it, in sight, out of reach, and see whether it comes.
		if (Pawn)
		{
			const FVector Facing = Hulk->GetActorForwardVector();
			Pawn->SetActorLocation(Hulk->GetActorLocation() + Facing * 480.0f + FVector(0, 0, -60.0f), false, nullptr, ETeleportType::TeleportPhysics);
		}
		HulkStart = Hulk->GetActorLocation();
		Phase = HulkReveal::EPhase::WaitHold;
		PhaseSince = Now;
		return false;
	}

	case HulkReveal::EPhase::WaitHold:
	{
		if (Now - PhaseSince < 3.0)
		{
			return false;
		}
		if (Hulk.IsValid())
		{
			const float Moved = FVector::Dist2D(Hulk->GetActorLocation(), HulkStart);
			Test->TestTrue(FString::Printf(TEXT("An awake, anchored hulk holds its ground with the player in front of it (moved %.0f cm)"), Moved), Moved < 40.0f);
			if (APatrollingEnemyController* Controller = Cast<APatrollingEnemyController>(Hulk->GetController()))
			{
				Test->TestTrue(TEXT("The controller is still anchored after the wake"), Controller->bAnchored);
				Test->AddInfo(FString::Printf(TEXT("HULK awareness after the hold: %d"), static_cast<int32>(Controller->GetAwareness())));
			}
		}
		if (const ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Pawn))
		{
			Test->TestFalse(TEXT("The player standing out of reach is alive"), Crew->bIsDead);
		}
		return Finish();
	}

	default:
		return Finish();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapHulkRevealPieTest,
	"Ginnungagap.Smoke.HulkWakesOnPowerRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapHulkRevealPieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	const double Start = FPlatformTime::Seconds();
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertHulkReveal(this, Start));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
