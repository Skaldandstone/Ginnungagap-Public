#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "UI/MapCustomizationWidget.h"
#include "UIDataStructures.generated.h"

USTRUCT(BlueprintType)
struct FMapInfo : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Map")
	FString MapName = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Map")
	FString MapDescription = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Map")
	FString LevelPath = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Map")
	FString PreviewImagePath = TEXT("");
};

USTRUCT(BlueprintType)
struct FShipSizeInfo : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	EShipSize SizeType = EShipSize::Medium;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	FString DisplayName = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	FString Description = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	int32 ResourceMultiplier = 100; // Percentage
};

USTRUCT(BlueprintType)
struct FDifficultyInfo : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	EGameDifficulty DifficultyType = EGameDifficulty::Normal;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	FString DisplayName = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	FString Description = TEXT("");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	float EnemyDamageMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	float EnemyHealthMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Difficulty")
	float ResourceScarcityMultiplier = 1.0f;
};
