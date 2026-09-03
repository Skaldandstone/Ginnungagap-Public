#include "Meta/MainMenuGameMode.h"

#include "Player/GameInitializerController.h"
#include "Meta/LobbyPlayerState.h"
#include "Meta/LobbyGameState.h"

AMainMenuGameMode::AMainMenuGameMode()
{
	PlayerControllerClass = AGameInitializerController::StaticClass();
	PlayerStateClass = ALobbyPlayerState::StaticClass();
	GameStateClass = ALobbyGameState::StaticClass();
	DefaultPawnClass = nullptr;
	HUDClass = nullptr;
	bStartPlayersAsSpectators = true;
}
