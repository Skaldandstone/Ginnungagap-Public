#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Meta/GameTypes.h"
#include "UI/MapCustomizationWidget.h"
#include "ExpeditionRunSave.generated.h"

UCLASS()
class GINNUNGAGAP_API UExpeditionRunSave : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, Category = "Expedition")
	EGameMode GameMode = EGameMode::SinglePlayerSurvival;

	UPROPERTY(BlueprintReadWrite, Category = "Expedition")
	FGameCustomization Customization;

	UPROPERTY(BlueprintReadWrite, Category = "Expedition")
	FDateTime SavedAtUtc;
};
