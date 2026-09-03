#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

#include "CoopSurvivalCharacter.h"
#include "Player/SurvivalPlayerController.h"
#include "UI/SurvivalHUDWidget.h"

/**
 * The baseline smoke pass, made repeatable.
 *
 * Everything else in this suite runs against objects built in isolation, which is fast and proves
 * the rules but never proves the game starts. This one actually plays the canonical map and checks
 * the things that have to be true before any other test matters: the right controller possesses the
 * right pawn, the HUD exists and is on screen, and the input bindings are wired.
 *
 * Input is verified by binding contract rather than by synthesising key events. Injected input
 * headless is timing-dependent and fails for reasons that have nothing to do with the game, so it
 * would produce a test that gets muted rather than fixed. Asserting that every expected axis and
 * action is bound catches the regression that actually happens -- a rename or a dropped
 * SetupInputComponent call -- and catches it deterministically.
 */

namespace
{
	const TCHAR* SmokeMapPath = TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck");

	/** The PIE world, once one exists. Null while the editor is still the only world around. */
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

	ASurvivalPlayerController* FindSurvivalController(UWorld* World)
	{
		if (!World)
		{
			return nullptr;
		}

		for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
		{
			if (ASurvivalPlayerController* Controller = Cast<ASurvivalPlayerController>(It->Get()))
			{
				return Controller;
			}
		}
		return nullptr;
	}
}

/**
 * Waits until the play session has a controller holding a pawn, or gives up.
 *
 * Possession is not immediate after PIE starts, and the amount of deferred work in front of it
 * varies with what the map streams in. A fixed sleep would either be slow or flaky, so this polls
 * and carries its own deadline -- the test fails on timeout rather than hanging a CI run.
 */
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(
	FWaitForPossessedPawn, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FWaitForPossessedPawn::Update()
{
	UWorld* World = FindPieWorld();
	const ASurvivalPlayerController* Controller = FindSurvivalController(World);
	if (Controller && Controller->GetPawn())
	{
		return true;
	}

	if (FPlatformTime::Seconds() >= DeadlineSeconds)
	{
		Test->AddError(World
			? TEXT("PIE started but no ASurvivalPlayerController possessed a pawn before the deadline")
			: TEXT("No PIE world existed before the deadline"));
		return true;
	}

	return false;
}

/** The assertions themselves, run once the world has settled. */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
	FAssertSmokeState, FAutomationTestBase*, Test);

bool FAssertSmokeState::Update()
{
	UWorld* World = FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("PIE world vanished before assertions ran"));
		return true;
	}

	ASurvivalPlayerController* Controller = FindSurvivalController(World);
	if (!Controller)
	{
		Test->AddError(TEXT("The map produced no ASurvivalPlayerController -- check the GameMode on the map"));
		return true;
	}

	// The pawn must be the survival character specifically. A DefaultPawn would still let the
	// player fly around and would pass a weaker check, while every survival system silently did
	// nothing.
	APawn* Pawn = Controller->GetPawn();
	ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Pawn);
	Test->TestNotNull(TEXT("The controller possesses a pawn"), Pawn);
	Test->TestNotNull(TEXT("The possessed pawn is a CoopSurvivalCharacter"), Character);

	if (Character)
	{
		// Components the rest of the suite assumes exist. Cheap to check here, and this is the
		// only place that proves they survive real spawning rather than direct construction.
		Test->TestNotNull(TEXT("The character has a skill component"), Character->GetSkillComponent());
		Test->TestNotNull(TEXT("The character has a status effect component"), Character->GetStatusEffectComponent());
		Test->TestFalse(TEXT("The character does not start dead"), Character->bIsDead);
		Test->TestTrue(TEXT("The character starts with oxygen"), Character->OxygenLevelPercent > 0.0f);
	}

	// The HUD is native and built in C++, so its absence means the controller failed to create it
	// rather than a Blueprint being unassigned.
	USurvivalHUDWidget* HUD = Controller->GetHUDWidget();
	Test->TestNotNull(TEXT("The survival HUD was created"), HUD);
	if (HUD)
	{
		Test->TestTrue(TEXT("The survival HUD is in the viewport"), HUD->IsInViewport());
	}

	// Input contracts. A rename on either side of these bindings breaks the game silently -- the
	// key simply stops doing anything -- so the binding list is worth asserting directly.
	UInputComponent* Input = Controller->InputComponent;
	Test->TestNotNull(TEXT("The controller has an input component"), Input);

	if (Input)
	{
		const TArray<FName> ExpectedAxes = {
			TEXT("MoveForward"), TEXT("MoveRight"), TEXT("LookUp"), TEXT("Turn")
		};
		for (const FName& AxisName : ExpectedAxes)
		{
			const bool bBound = Input->AxisBindings.ContainsByPredicate(
				[&AxisName](const FInputAxisBinding& Binding) { return Binding.AxisName == AxisName; });
			Test->TestTrue(FString::Printf(TEXT("Axis '%s' is bound"), *AxisName.ToString()), bBound);
		}

		const TArray<FName> ExpectedActions = {
			TEXT("Jump"), TEXT("Interact"), TEXT("ActivitySecondary"),
			TEXT("ActivityTertiary"), TEXT("ActivityQuaternary"), TEXT("ActivityCancel")
		};
		for (const FName& ActionName : ExpectedActions)
		{
			bool bBound = false;
			for (int32 Index = 0; Index < Input->GetNumActionBindings(); ++Index)
			{
				if (Input->GetActionBinding(Index).GetActionName() == ActionName)
				{
					bBound = true;
					break;
				}
			}
			Test->TestTrue(FString::Printf(TEXT("Action '%s' is bound"), *ActionName.ToString()), bBound);
		}
	}

	// The pawn binds its own actions separately from the controller, including the three ability
	// slots added with the payload system. Those are the newest bindings here and the likeliest to
	// be lost to a merge.
	if (Character && Character->InputComponent)
	{
		const TArray<FName> ExpectedPawnActions = {
			TEXT("ToggleMagneticBoots"), TEXT("RotationThruster"),
			TEXT("ActivateSkillSlot1"), TEXT("ActivateSkillSlot2"), TEXT("ActivateSkillSlot3")
		};
		for (const FName& ActionName : ExpectedPawnActions)
		{
			bool bBound = false;
			for (int32 Index = 0; Index < Character->InputComponent->GetNumActionBindings(); ++Index)
			{
				if (Character->InputComponent->GetActionBinding(Index).GetActionName() == ActionName)
				{
					bBound = true;
					break;
				}
			}
			Test->TestTrue(FString::Printf(TEXT("Pawn action '%s' is bound"), *ActionName.ToString()), bBound);
		}
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPieSmokeTest,
	"Ginnungagap.Smoke.PlayInEditor",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPieSmokeTest::RunTest(const FString& Parameters)
{
	// Deadlines are absolute rather than tick counts so a slow machine waits longer instead of
	// failing, while a genuinely stuck session still gives up instead of hanging the run.
	const double PossessionDeadline = FPlatformTime::Seconds() + 60.0;

	AutomationOpenMap(SmokeMapPath);
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForPossessedPawn(this, PossessionDeadline));

	// One settle tick after possession: the HUD is created in BeginPlay and added to the viewport
	// on the frame after, so asserting immediately would race it.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertSmokeState(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
