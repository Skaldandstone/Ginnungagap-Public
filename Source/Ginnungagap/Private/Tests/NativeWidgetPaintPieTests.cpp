#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"
#include "Widgets/SWidget.h"
#include "Layout/Children.h"
#include "Misc/App.h"

#include "Meta/MenuManagerSubsystem.h"
#include "Player/SurvivalPlayerController.h"
#include "UI/StartScreenWidget.h"
#include "UI/SurvivalHUDWidget.h"

/**
 * The project's widgets build their trees in code, not in a designer. UMG builds the Slate widget
 * from WidgetTree->RootWidget in RebuildWidget() and only then calls NativeConstruct(), so a tree
 * assigned in NativeConstruct is never what the player sees: the widget reports InViewport and
 * Visible, every reflection check passes, and the screen shows the bare game underneath. That was
 * the state of the suit HUD and the title screen until 2026-09-03, invisible to every other test.
 *
 * So this asks the only question that matters: once the widget is on screen and Slate has done a
 * layout pass, does it measure as something? A tree that was built too late measures as the
 * SSpacer UMG substitutes for a missing root: zero by zero.
 */
namespace WidgetPaint
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

	void AssertMeasures(FAutomationTestBase* Test, const TCHAR* What, UUserWidget* Widget)
	{
		if (!Test->TestNotNull(FString::Printf(TEXT("%s exists"), What), Widget))
		{
			return;
		}
		Test->TestTrue(FString::Printf(TEXT("%s is in the viewport"), What), Widget->IsInViewport());
		Test->TestNotNull(FString::Printf(TEXT("%s has a root in its widget tree"), What),
			Widget->WidgetTree ? Widget->WidgetTree->RootWidget.Get() : nullptr);
		const TSharedPtr<SWidget> Slate = Widget->GetCachedWidget();
		if (!Test->TestTrue(FString::Printf(TEXT("%s has a Slate widget"), What), Slate.IsValid()))
		{
			return;
		}
		// The SObjectWidget wraps whatever RebuildWidget returned: the root's Slate widget, or the
		// SSpacer UMG substitutes when there was no root yet. The spacer is the bug.
		FString ContentType = TEXT("(none)");
		if (FChildren* Children = Slate->GetChildren())
		{
			if (Children->Num() > 0)
			{
				ContentType = Children->GetChildAt(0)->GetTypeAsString();
			}
		}
		Test->TestNotEqual(FString::Printf(TEXT("%s's Slate content is its own tree, not the empty-root spacer (%s)"), What, *ContentType),
			ContentType, FString(TEXT("SSpacer")));
		// Desired size needs a Slate prepass, which needs a renderer; headless (-nullrhi) runs
		// have no layout to measure, so only ask when something is actually drawing.
		if (FApp::CanEverRender())
		{
			const FVector2D Desired = Widget->GetDesiredSize();
			Test->TestTrue(FString::Printf(TEXT("%s measures a non-zero size on screen (was %s)"), What, *Desired.ToString()),
				Desired.X > 1.0f && Desired.Y > 1.0f);
		}
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertHudPaints, FAutomationTestBase*, Test);

bool FAssertHudPaints::Update()
{
	UWorld* World = WidgetPaint::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world for the widget paint assertions"));
		return true;
	}
	ASurvivalPlayerController* PC = Cast<ASurvivalPlayerController>(UGameplayStatics::GetPlayerController(World, 0));
	if (!Test->TestNotNull(TEXT("The demo map's player controller is the survival controller"), PC))
	{
		return true;
	}
	WidgetPaint::AssertMeasures(Test, TEXT("The suit HUD"), PC->GetHUDWidget());

	// Then the title screen the mission director cuts to, through the same call it makes.
	if (UMenuManagerSubsystem* Menus = World->GetGameInstance() ? World->GetGameInstance()->GetSubsystem<UMenuManagerSubsystem>() : nullptr)
	{
		Menus->ShowStartScreen();
	}
	else
	{
		Test->AddError(TEXT("No menu manager subsystem on the PIE game instance"));
	}
	return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertStartScreenPaints, FAutomationTestBase*, Test);

bool FAssertStartScreenPaints::Update()
{
	UWorld* World = WidgetPaint::FindPieWorld();
	UMenuManagerSubsystem* Menus = (World && World->GetGameInstance()) ? World->GetGameInstance()->GetSubsystem<UMenuManagerSubsystem>() : nullptr;
	if (!Menus)
	{
		return true;
	}
	UUserWidget* StartScreen = nullptr;
	if (const FObjectProperty* Property = CastField<FObjectProperty>(Menus->GetClass()->FindPropertyByName(TEXT("CurrentStartScreen"))))
	{
		StartScreen = Cast<UUserWidget>(Property->GetObjectPropertyValue_InContainer(Menus));
	}
	WidgetPaint::AssertMeasures(Test, TEXT("The start screen"), StartScreen);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapNativeWidgetsPaintTest,
	"Ginnungagap.Smoke.NativeWidgetsPaint",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapNativeWidgetsPaintTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	// The opening sequence hides the HUD while the sleeper is in the pod; it is back by ten seconds.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(12.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertHudPaints(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertStartScreenPaints(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
