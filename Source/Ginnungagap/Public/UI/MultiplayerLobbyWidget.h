#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Meta/GameTypes.h"
#include "UI/MapCustomizationWidget.h"
#include "MultiplayerLobbyWidget.generated.h"

class UButton;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLobbyLaunchRequested);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLobbyBackRequested);

/** Host-side staging room. Online roster entries can be fed into this screen later. */
UCLASS()
class GINNUNGAGAP_API UMultiplayerLobbyWidget : public UUserWidget
{
	GENERATED_BODY()
public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
	void Configure(EGameMode GameMode, const FGameCustomization& Customization, const FString& HostName);
	UPROPERTY(BlueprintAssignable, Category="Lobby") FOnLobbyLaunchRequested OnLaunchRequested;
	UPROPERTY(BlueprintAssignable, Category="Lobby") FOnLobbyBackRequested OnBackRequested;
private:
	void BuildFallbackLayout();
	void RefreshLobby();
	UFUNCTION() void OnReadyClicked();
	UFUNCTION() void OnLaunchClicked();
	UFUNCTION() void OnBackClicked();
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ExpeditionText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> RosterText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;
	UPROPERTY(Transient) TObjectPtr<UButton> ReadyButton;
	UPROPERTY(Transient) TObjectPtr<UButton> LaunchButton;
	UPROPERTY(Transient) TObjectPtr<UButton> BackButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ReadyButtonText;
	EGameMode SelectedMode = EGameMode::CoopSurvival;
	FGameCustomization GameCustomization;
	FString HostCharacterName = TEXT("HOST");
	FString CachedRoster;
	float RefreshAccumulator = 0.0f;
	bool bIdentitySubmitted = false;
};
