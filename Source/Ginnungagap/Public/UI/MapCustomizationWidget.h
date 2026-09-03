#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Slider.h"
#include "Components/ComboBoxString.h"
#include "Meta/GameTypes.h"
#include "Versus/VersusTypes.h"
#include "MapCustomizationWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGameStarted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCustomizationBackRequested);

UENUM(BlueprintType)
enum class EShipSize : uint8
{
	Small,
	Medium,
	Large
};

UENUM(BlueprintType)
enum class EGameDifficulty : uint8
{
	Easy,
	Normal,
	Hard,
	Impossible
};

USTRUCT(BlueprintType)
struct FGameCustomization
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Game")
	EShipSize ShipSize = EShipSize::Medium;

	UPROPERTY(BlueprintReadWrite, Category = "Game")
	EGameDifficulty Difficulty = EGameDifficulty::Normal;

	UPROPERTY(BlueprintReadWrite, Category = "Game")
	FString SelectedMap = TEXT("GINNUNGAGAP // FOUR-DECK PROTOTYPE");

	UPROPERTY(BlueprintReadWrite, Category = "Game|Versus")
	FVersusMatchSettings VersusSettings;
};

UCLASS()
class GINNUNGAGAP_API UMapCustomizationWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UFUNCTION(BlueprintCallable, Category = "Customization")
	void SetIsCoopMode(bool bIsCoopMode);

	UFUNCTION(BlueprintCallable, Category = "Customization")
	void SetGameMode(EGameMode InGameMode);

	UPROPERTY(BlueprintAssignable, Category = "Customization")
	FOnGameStarted OnGameStarted;

	UPROPERTY(BlueprintAssignable, Category = "Customization")
	FOnCustomizationBackRequested OnBackRequested;

	UFUNCTION(BlueprintCallable, Category = "Customization")
	FGameCustomization GetCurrentCustomization() const { return CurrentCustomization; }

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* ShipSizeCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* DifficultyCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* MapCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* ShipSizeDescriptionText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* DifficultyDescriptionText;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* ProtagonistSlotsCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* AntagonistSlotsCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* AntagonistFactionCombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UComboBoxString* IndependentAICombo;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* StartGameButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* BackButton;

	UPROPERTY()
	bool bIsCoopMode = false;

	UPROPERTY()
	EGameMode SelectedGameMode = EGameMode::SinglePlayerSurvival;

	UPROPERTY()
	FGameCustomization CurrentCustomization;

	// Descriptions for UI
	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString SmallShipDesc = TEXT("Compact ship - Limited resources but faster movement");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString MediumShipDesc = TEXT("Four-deck derelict prototype - 96 rooms, damaged systems, and a cryo wake-up mission");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString LargeShipDesc = TEXT("Large ship - Abundant resources but slower movement");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString EasyDesc = TEXT("Reduced enemy threats and generous resources");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString NormalDesc = TEXT("Standard survival challenge");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString HardDesc = TEXT("Increased enemy presence and resource scarcity");

	UPROPERTY(EditDefaultsOnly, Category = "Descriptions")
	FString ImpossibleDesc = TEXT("Extreme difficulty - For expert players only");

	UFUNCTION()
	void OnShipSizeChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnDifficultyChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnMapChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnProtagonistSlotsChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnAntagonistSlotsChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnAntagonistFactionChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnIndependentAIChanged(FString SelectedItem, ESelectInfo::Type SelectionType);

	UFUNCTION()
	void OnStartGameClicked();

	UFUNCTION()
	void OnBackClicked();

	void PopulateDropdowns();
	void RefreshDeploymentSite();
	void UpdateDescriptions();
	void BuildFallbackLayout();
	bool bLaunchRequested = false;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
};
