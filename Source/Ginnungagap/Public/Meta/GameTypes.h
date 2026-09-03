#pragma once

#include "CoreMinimal.h"
#include "GameTypes.generated.h"

UENUM(BlueprintType)
enum class EGameMode : uint8
{
	SinglePlayerSurvival,
	CoopSurvival,
	Versus
};

USTRUCT(BlueprintType)
struct FGameModeInfo
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Mode")
	EGameMode ModeType = EGameMode::SinglePlayerSurvival;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Mode")
	FString ModeName = TEXT("Survival");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Mode")
	FString ModeDescription = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Mode")
	FString LevelPath = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Game Mode")
	bool bIsCooperative = false;
};
