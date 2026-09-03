#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "UnrealClient.h"

/**
 * Captures what a player actually sees, from the player's camera, with BeginPlay run.
 *
 * Every hero shot this project has produced is an editor-camera render: a CameraActor placed by
 * script in the editor world, screenshotted. That is a fair way to judge where light falls and a
 * poor way to judge whether the game looks presentable, because the editor world is not the world
 * the game runs in.
 *
 * The gap is provable rather than theoretical. Each room's IdentityLight sits at intensity 0 as
 * saved in the map, and AModularShipRoom::UpdateOperationalVisuals only ever sets it at runtime --
 * to 80 in a cold blue-grey now that the demo starts its rooms Unpowered. So every editor render
 * ever taken here is missing a fill light that exists in every room of the running game, and no
 * amount of re-rendering the editor world would reveal it.
 *
 * This runs PIE, waits for the mission director's BeginPlay and the checkpoint restore a tick later,
 * lets Lumen settle, and screenshots through the game viewport -- so the frame comes from the
 * player's own camera in the running game.
 *
 * WHAT THIS IS NOT. It is a still, with no input applied. It is not gameplay footage, it does not
 * show that the demo is playable, and it must not be offered as either. It answers exactly one
 * question -- what does the first frame of the demo look like to a player -- which is the question
 * standing between here and a submit-or-defer decision, and it answers it in about a minute rather
 * than by opening the editor.
 *
 * Must run in a windowed editor. Under -NullRHI there is no swap chain and the screenshot is empty.
 */

namespace PieCapture
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

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FCapturePlayerView, FAutomationTestBase*, Test);

bool FCapturePlayerView::Update()
{
	UWorld* World = PieCapture::FindPieWorld();
	if (!Test->TestNotNull(TEXT("A PIE world exists"), World))
	{
		return true;
	}

	APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0);
	if (!Test->TestNotNull(TEXT("There is a player controller to see through"), Controller))
	{
		return true;
	}

	// Assert the thing that makes this capture worth taking: that we are looking at runtime state,
	// not the saved editor state. If BeginPlay had not run there would be no controller and no pawn.
	// Named local rather than the call inline, so TestNotNull has a complete type to deduce from.
	APawn* Pawn = Controller->GetPawn();
	Test->TestNotNull(TEXT("The player has a pawn, so BeginPlay has run"), Pawn);

	if (GEngine && GEngine->GameViewport)
	{
		// Through the game viewport rather than an editor viewport, so the frame is the player's.
		GEngine->GameViewport->Exec(World, TEXT("HighResShot 2560x1440"), *GLog);
		Test->AddInfo(TEXT("Requested a 2560x1440 shot through the game viewport; "
			"it lands in Saved/Screenshots/WindowsEditor."));
	}
	else
	{
		Test->AddError(TEXT("No game viewport -- this test needs a windowed editor, not -NullRHI."));
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPieViewCaptureTest,
	"Ginnungagap.Capture.PlayerView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPieViewCaptureTest::RunTest(const FString& Parameters)
{
	// Same reason as the other PIE tests: a stale checkpoint would restore a part-finished run and
	// the capture would show the middle of the demo rather than its opening.
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	// Long enough for the director's BeginPlay, the checkpoint restore a tick later, and Lumen to
	// converge. The hero-shot rig needed 30s on this map and this is the same geometry.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(30.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FCapturePlayerView(this));
	// The screenshot is queued for the next frame, so give it frames to be taken in before PIE ends.
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(6.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
