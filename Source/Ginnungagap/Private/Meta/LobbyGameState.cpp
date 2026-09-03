#include "Meta/LobbyGameState.h"

#include "Net/UnrealNetwork.h"

void ALobbyGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ALobbyGameState,SelectedMode);
	DOREPLIFETIME(ALobbyGameState,Customization);
	DOREPLIFETIME(ALobbyGameState,bConfigurationReady);
}

void ALobbyGameState::SetLobbyConfiguration(EGameMode NewMode,const FGameCustomization& NewCustomization)
{
	if(!HasAuthority())return;
	SelectedMode=NewMode;
	Customization=NewCustomization;
	bConfigurationReady=true;
	ForceNetUpdate();
}
