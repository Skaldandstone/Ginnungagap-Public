#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "Meta/GameTypes.h"
#include "UI/MapCustomizationWidget.h"
#include "LobbyGameState.generated.h"

UCLASS()
class GINNUNGAGAP_API ALobbyGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	void SetLobbyConfiguration(EGameMode NewMode,const FGameCustomization& NewCustomization);

	UPROPERTY(Replicated,BlueprintReadOnly,Category="Lobby")
	EGameMode SelectedMode=EGameMode::CoopSurvival;

	UPROPERTY(Replicated,BlueprintReadOnly,Category="Lobby")
	FGameCustomization Customization;

	UPROPERTY(Replicated,BlueprintReadOnly,Category="Lobby")
	bool bConfigurationReady=false;
};
