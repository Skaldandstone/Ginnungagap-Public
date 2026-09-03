#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Meta/ExpeditionRunSave.h"
#include "Meta/MainMenuGameMode.h"
#include "Meta/LobbyGameState.h"
#include "Meta/LobbyPlayerState.h"
#include "Meta/MultiplayerSessionSubsystem.h"
#include "Player/GameInitializerController.h"
#include "UI/BootSplashWidget.h"
#include "UI/StartScreenWidget.h"
#include "UI/ModeSelectWidget.h"
#include "UI/CharacterCreatorWidget.h"
#include "UI/FirstLaunchCharacterCreationWidget.h"
#include "UI/MapCustomizationWidget.h"
#include "UI/MultiplayerOptionsWidget.h"
#include "UI/MultiplayerLobbyWidget.h"
#include "UI/LoadingTransitionWidget.h"
#include "UI/ProgressionMenuWidget.h"
#include "UI/PreGameLoadoutWidget.h"
#include "UI/SkillTreeWidget.h"
#include "Misc/PackageName.h"
#include "Misc/ConfigCacheIni.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMenuFlowDefaultsTest,
	"Ginnungagap.UI.MenuFlowDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMenuFlowDefaultsTest::RunTest(const FString& Parameters)
{
	const AMainMenuGameMode* MenuMode = GetDefault<AMainMenuGameMode>();
	TestTrue(TEXT("Menu uses the initializer controller"), MenuMode->PlayerControllerClass.Get() == AGameInitializerController::StaticClass());
	// The front end is the default entry point. Start Game, Continue, and Settings are only
	// reachable from the start screen, so shortcutting past it strands two of the three.
	TestFalse(TEXT("Startup opens the front end rather than skipping to expedition setup"),
		GetDefault<AGameInitializerController>()->bLaunchIntoPreGameWorkflow);
	TestTrue(TEXT("Menu uses the replicated lobby game state"), MenuMode->GameStateClass.Get() == ALobbyGameState::StaticClass());
	TestTrue(TEXT("Menu uses the replicated lobby player state"), MenuMode->PlayerStateClass.Get() == ALobbyPlayerState::StaticClass());
	TestNull(TEXT("Menu does not spawn a gameplay pawn"), MenuMode->DefaultPawnClass);
	TestTrue(TEXT("Lobby player state replicates"), GetDefault<ALobbyPlayerState>()->GetIsReplicated());
	TestFalse(TEXT("Lobby players default to not ready"), GetDefault<ALobbyPlayerState>()->bLobbyReady);
	TestFalse(TEXT("Lobby configuration waits for the host"), GetDefault<ALobbyGameState>()->bConfigurationReady);
	TestTrue(TEXT("Session subsystem is a game instance subsystem"), UMultiplayerSessionSubsystem::StaticClass()->IsChildOf(UGameInstanceSubsystem::StaticClass()));
	TestNotNull(TEXT("Boot splash UI is available"), UBootSplashWidget::StaticClass());
	TestNotNull(TEXT("Title/start UI is available"), UStartScreenWidget::StaticClass());
	TestNotNull(TEXT("Mode selection UI is available"), UModeSelectWidget::StaticClass());
	TestNotNull(TEXT("Character identity UI is available"), UCharacterCreatorWidget::StaticClass());
	TestNotNull(TEXT("Operator class UI is available"), UFirstLaunchCharacterCreationWidget::StaticClass());
	TestNotNull(TEXT("Expedition customization UI is available"), UMapCustomizationWidget::StaticClass());
	TestNotNull(TEXT("Multiplayer options UI is available"), UMultiplayerOptionsWidget::StaticClass());
	TestNotNull(TEXT("Replicated lobby UI is available"), UMultiplayerLobbyWidget::StaticClass());
	TestNotNull(TEXT("Loading transition UI is available"), ULoadingTransitionWidget::StaticClass());
	TestNotNull(TEXT("Pre-game loadout UI is available"), UPreGameLoadoutWidget::StaticClass());
	TestNotNull(TEXT("Class skill tree UI is available"), USkillTreeWidget::StaticClass());

	const UExpeditionRunSave* RunSave = GetDefault<UExpeditionRunSave>();
	TestEqual(TEXT("New runs default to solo"), RunSave->GameMode, EGameMode::SinglePlayerSurvival);
	TestEqual(TEXT("New runs default to a medium vessel"), RunSave->Customization.ShipSize, EShipSize::Medium);
	TestEqual(TEXT("New runs default to normal difficulty"), RunSave->Customization.Difficulty, EGameDifficulty::Normal);
	TestEqual(TEXT("New runs identify the four-deck prototype"), RunSave->Customization.SelectedMap,
		FString(TEXT("GINNUNGAGAP // FOUR-DECK PROTOTYPE")));
	TestTrue(TEXT("Main menu map is available"), FPackageName::DoesPackageExist(TEXT("/Game/UI/MainMenu")));
	TestTrue(TEXT("Main menu backdrop is available"), FPackageName::DoesPackageExist(TEXT("/Game/UI/Textures/T_MainMenu_Backdrop")));
	TestTrue(TEXT("Four-deck prototype map is available"), FPackageName::DoesPackageExist(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck")));
	TestTrue(TEXT("Small vessel map is available"), FPackageName::DoesPackageExist(TEXT("/Game/Assets/Maps/ShipProduction/L_Small_Companionway_Showcase")));
	TestTrue(TEXT("Medium vessel map is available"), FPackageName::DoesPackageExist(TEXT("/Game/Assets/Maps/ShipProduction/L_Medium_ExpressSpine_Showcase")));
	TestTrue(TEXT("Large vessel map is available"), FPackageName::DoesPackageExist(TEXT("/Game/Assets/Maps/ShipProduction/L_Large_CarrierConcourse_Showcase")));
	TestFalse(TEXT("Pause menu defaults to closed"), GetDefault<UProgressionMenuWidget>()->IsMenuOpen());

	FString EditorStartupMap;
	FString GameDefaultMap;
	const TCHAR* MapsSection = TEXT("/Script/EngineSettings.GameMapsSettings");
	TestTrue(TEXT("Editor startup map is configured"), GConfig->GetString(MapsSection, TEXT("EditorStartupMap"), EditorStartupMap, GEngineIni));
	TestTrue(TEXT("Packaged game startup map is configured"), GConfig->GetString(MapsSection, TEXT("GameDefaultMap"), GameDefaultMap, GEngineIni));
	TestEqual(TEXT("Editor opens on the playable main menu"), EditorStartupMap, FString(TEXT("/Game/UI/MainMenu.MainMenu")));
	TestEqual(TEXT("Packaged builds open on the playable main menu"), GameDefaultMap, FString(TEXT("/Game/UI/MainMenu.MainMenu")));

	if (UWorld* MenuWorld = LoadObject<UWorld>(nullptr, TEXT("/Game/UI/MainMenu.MainMenu")))
	{
		TestNotNull(TEXT("Main menu world has settings"), MenuWorld->GetWorldSettings());
		TestTrue(TEXT("Main menu world uses native menu mode"), MenuWorld->GetWorldSettings()->DefaultGameMode == AMainMenuGameMode::StaticClass());
	}
	else
	{
		AddError(TEXT("Main menu world could not be loaded"));
	}
	return true;
}

#endif
