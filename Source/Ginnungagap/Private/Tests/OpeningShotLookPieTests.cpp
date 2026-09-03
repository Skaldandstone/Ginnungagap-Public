#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UnrealClient.h"

#include "CoopSurvivalCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/WeaponMountComponent.h"
#include "Components/StaticMeshComponent.h"

/**
 * Stills of the opening, one per phase, captured on phase change from the player's own view.
 * A look test: it asserts only that the sequence runs through to first person. Its value is the
 * pictures -- Opening_<phase>.png under Saved/Screenshots -- which a windowed run produces in
 * under two minutes, against twenty-five for a full recording of the walk. Under -nullrhi the
 * pictures are black and only the phase assertions mean anything.
 */
namespace OpeningLook
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

	const TCHAR* PhaseName(EQuickDemoOpeningPhase Phase)
	{
		switch (Phase)
		{
		case EQuickDemoOpeningPhase::Asleep:      return TEXT("1_asleep");
		case EQuickDemoOpeningPhase::Strike:      return TEXT("2_strike");
		case EQuickDemoOpeningPhase::Blackout:    return TEXT("3_blackout");
		case EQuickDemoOpeningPhase::Wake:        return TEXT("4_wake");
		case EQuickDemoOpeningPhase::ClimbOut:    return TEXT("5_climb_out");
		case EQuickDemoOpeningPhase::FirstPerson: return TEXT("6_first_person");
		default:                                  return nullptr;
		}
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureOpeningPhases, FAutomationTestBase*, Test);

bool FCaptureOpeningPhases::Update()
{
	static EQuickDemoOpeningPhase LastCaptured = EQuickDemoOpeningPhase::Idle;
	static double PhaseEnteredAt = 0.0;
	UWorld* World = OpeningLook::FindPieWorld();
	if (!World)
	{
		return false;
	}
	AQuickDemoOpeningSequence* Opening = nullptr;
	for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It)
	{
		Opening = *It;
		break;
	}
	if (!Test->TestNotNull(TEXT("The demo map has an opening sequence"), Opening))
	{
		LastCaptured = EQuickDemoOpeningPhase::Idle;
		return true;
	}
	const double Now = World->GetTimeSeconds();
	const EQuickDemoOpeningPhase Phase = Opening->GetPhase();
	if (Phase != LastCaptured)
	{
		if (PhaseEnteredAt == 0.0)
		{
			PhaseEnteredAt = Now;
		}
		// Half a second into the phase, so the picture is of the phase and not of the cut into it.
		// (First person completes almost at once, so it is caught sooner.)
		if (Now - PhaseEnteredAt >= (Phase == EQuickDemoOpeningPhase::FirstPerson ? 0.15 : 0.5))
		{
			if (const TCHAR* Name = OpeningLook::PhaseName(Phase))
			{
				FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Opening_%s"), Name), false, false, false, FIntRect(), true);
			}
			LastCaptured = Phase;
			PhaseEnteredAt = 0.0;
		}
	}
	if (Opening->IsComplete() || Now > 30.0)
	{
		Test->TestTrue(TEXT("The opening ran through to completion within 30s"), Opening->IsComplete());
		LastCaptured = EQuickDemoOpeningPhase::Idle;
		PhaseEnteredAt = 0.0;
		return true;
	}
	return false;
}

/** The workshop grant, applied directly, and a still of the tool in hand a moment later. */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCaptureToolInHand, FAutomationTestBase*, Test);

bool FCaptureToolInHand::Update()
{
	static double GrantedAt = 0.0;
	UWorld* World = OpeningLook::FindPieWorld();
	if (!World)
	{
		return true;
	}
	if (GrantedAt == 0.0)
	{
		AQuickDemoWorkshopBench* Bench = nullptr;
		for (TActorIterator<AQuickDemoWorkshopBench> It(World); It; ++It)
		{
			Bench = *It;
			break;
		}
		ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0));
		if (!Test->TestNotNull(TEXT("The demo map has a workshop bench"), Bench) || !Test->TestNotNull(TEXT("There is a player character"), Character))
		{
			return true;
		}
		Bench->OnActivityCompleted_Implementation(Character);
		GrantedAt = World->GetTimeSeconds();
		return false;
	}
	if (World->GetTimeSeconds() - GrantedAt < 0.7)
	{
		return false;
	}
	FScreenshotRequest::RequestScreenshot(TEXT("Opening_7_tool_in_hand"), true, false, false, FIntRect(), true);
	// Where the tool actually sits relative to the view, so a backwards mesh can be told from a
	// backwards mount from the log alone.
	if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerPawn(World, 0)))
	{
		if (UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>())
		{
			const FVector View = Character->GetBaseAimRotation().Vector();
			const FString MountInfo = FString::Printf(TEXT("mount rel loc %s rel rot %s, forward.view %.2f"),
				*Mount->GetRelativeLocation().ToCompactString(), *Mount->GetRelativeRotation().ToCompactString(),
				FVector::DotProduct(Mount->GetForwardVector(), View));
			if (AShipboardWeapon* Weapon = Mount->GetMountedWeapon())
			{
				UE_LOG(LogTemp, Display, TEXT("TOOLLOOK %s: weapon %s forward.view %.2f, mesh rel rot %s"), *MountInfo, *Weapon->GetClass()->GetName(),
					FVector::DotProduct(Weapon->GetActorForwardVector(), View),
					Weapon->VisualMesh ? *Weapon->VisualMesh->GetRelativeRotation().ToCompactString() : TEXT("-"));
			}
			else
			{
				UE_LOG(LogTemp, Display, TEXT("TOOLLOOK %s: nothing mounted"), *MountInfo);
			}
		}
	}
	GrantedAt = 0.0;
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapOpeningShotLookTest,
	"Ginnungagap.Look.OpeningShots",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapOpeningShotLookTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureOpeningPhases(this));
	ADD_LATENT_AUTOMATION_COMMAND(FCaptureToolInHand(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
