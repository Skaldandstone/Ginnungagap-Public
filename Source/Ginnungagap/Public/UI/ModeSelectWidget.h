#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Meta/GameTypes.h"
#include "ModeSelectWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnModeSelected, EGameMode, SelectedMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnModeSelectBackRequested);

UCLASS()
class GINNUNGAGAP_API UModeSelectWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnModeSelected OnModeSelected;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnModeSelectBackRequested OnBackRequested;

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* SinglePlayerButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* CoopButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* VersusButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* BackButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* ModeDescriptionText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* ModeNameText;

	UPROPERTY(meta = (BindWidgetOptional))
	UImage* ModePreviewImage;

	// Mode descriptions
	UPROPERTY(EditDefaultsOnly, Category = "Modes")
	FString SinglePlayerDescription = TEXT("Survive alone against hostile conditions and reach the escape pod.");

	UPROPERTY(EditDefaultsOnly, Category = "Modes")
	FString CoopDescription = TEXT("Work together with up to 4 players to survive and escape.");

	UPROPERTY(EditDefaultsOnly, Category = "Modes")
	FString VersusDescription = TEXT("An asymmetric 1v1 to 8v4 hunt: crew complete the expedition while player-controlled antagonist factions evolve, sabotage, and stalk them.");

	UFUNCTION()
	void OnSinglePlayerSelected();

	UFUNCTION()
	void OnCoopSelected();

	UFUNCTION()
	void OnVersusSelected();

	UFUNCTION()
	void OnBackClicked();

	void SelectMode(EGameMode Mode);
	void DisplayModeInfo(EGameMode Mode);
	void BuildFallbackLayout();
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
};
