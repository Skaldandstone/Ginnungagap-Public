#include "Player/GameInitializerController.h"
#include "Engine/GameInstance.h"
#include "Meta/MenuManagerSubsystem.h"
#include "Meta/MultiplayerSessionSubsystem.h"

AGameInitializerController::AGameInitializerController()
{
	bShowMouseCursor = true;
	DefaultMouseCursor = EMouseCursor::Default;
}

void AGameInitializerController::BeginPlay()
{
	Super::BeginPlay();

	if (UGameInstance* GI = GetGameInstance())
	{
		MenuManager = GI->GetSubsystem<UMenuManagerSubsystem>();
		if (MenuManager)
		{
			if (UMultiplayerSessionSubsystem* Sessions = GI->GetSubsystem<UMultiplayerSessionSubsystem>(); Sessions && Sessions->IsInCrewSession())
			{
				MenuManager->ShowCrewLobby();
			}
			else if (bLaunchIntoPreGameWorkflow)
			{
				MenuManager->ShowModeSelect();
			}
			else
			{
				// Run the one-time boot/title sequence before revealing the main menu.
				MenuManager->ShowBootSplash();
			}
		}
	}
}
