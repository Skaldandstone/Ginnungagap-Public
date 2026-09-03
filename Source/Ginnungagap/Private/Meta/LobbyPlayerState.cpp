#include "Meta/LobbyPlayerState.h"

#include "Net/UnrealNetwork.h"

ALobbyPlayerState::ALobbyPlayerState()
{
	bReplicates = true;
}

void ALobbyPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ALobbyPlayerState, bLobbyReady);
}

void ALobbyPlayerState::ServerSetReady_Implementation(bool bNewReady)
{
	bLobbyReady = bNewReady;
	ForceNetUpdate();
}

void ALobbyPlayerState::ServerSetLobbyName_Implementation(const FString& NewName)
{
	FString SafeName = NewName.TrimStartAndEnd().Left(24);
	if (SafeName.IsEmpty()) SafeName = TEXT("CREW MEMBER");
	SetPlayerName(SafeName);
}
