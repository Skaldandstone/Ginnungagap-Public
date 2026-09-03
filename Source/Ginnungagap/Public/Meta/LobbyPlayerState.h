#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "LobbyPlayerState.generated.h"

UCLASS()
class GINNUNGAGAP_API ALobbyPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	ALobbyPlayerState();
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(Server, Reliable, BlueprintCallable, Category="Lobby")
	void ServerSetReady(bool bNewReady);

	UFUNCTION(Server, Reliable, BlueprintCallable, Category="Lobby")
	void ServerSetLobbyName(const FString& NewName);

	UPROPERTY(Replicated, BlueprintReadOnly, Category="Lobby")
	bool bLobbyReady = false;
};
