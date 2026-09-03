#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "UI/MapCustomizationWidget.h"
#include "MultiplayerOptionsWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMatchmakingStarted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLobbyCreated);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMultiplayerBackRequested);

UCLASS()
class GINNUNGAGAP_API UMultiplayerOptionsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UPROPERTY(BlueprintAssignable, Category = "Multiplayer")
	FOnMatchmakingStarted OnMatchmakingStarted;

	UPROPERTY(BlueprintAssignable, Category = "Multiplayer")
	FOnLobbyCreated OnLobbyCreated;

	UPROPERTY(BlueprintAssignable, Category = "Multiplayer")
	FOnMultiplayerBackRequested OnBackRequested;

	UFUNCTION(BlueprintCallable, Category = "Multiplayer")
	void SetGameCustomization(const FGameCustomization& InCustomization);

	UFUNCTION(BlueprintCallable, Category = "Multiplayer")
	void SetGameMode(EGameMode InGameMode) { SelectedGameMode = InGameMode; }

	UFUNCTION(BlueprintCallable, Category = "Multiplayer")
	void SetStatusMessage(const FText& Message, bool bIsError = false);

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* MatchmakingButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* InviteFriendsButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* CreateLobbyButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* BackButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* TitleText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* MatchmakingDescText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* InviteFriendsDescText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* CreateLobbyDescText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* ExpeditionSummaryText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* StatusText;

	UPROPERTY()
	FGameCustomization CurrentCustomization;

	UPROPERTY()
	EGameMode SelectedGameMode = EGameMode::CoopSurvival;

	UFUNCTION()
	void OnMatchmakingClicked();

	UFUNCTION()
	void OnInviteFriendsClicked();

	UFUNCTION()
	void OnCreateLobbyClicked();

	UFUNCTION()
	void OnBackClicked();
	void BuildFallbackLayout();
	void RefreshExpeditionSummary();
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
};
