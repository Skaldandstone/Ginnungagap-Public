#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Meta/GameTypes.h"
#include "Meta/CharacterProfile.h"
#include "UI/MapCustomizationWidget.h"
#include "MenuManagerSubsystem.generated.h"

class UStartScreenWidget;
class UBootSplashWidget;
class UCharacterCreatorWidget;
class ULoadingTransitionWidget;
class UMultiplayerLobbyWidget;
class UModeSelectWidget;
class UFirstLaunchCharacterCreationWidget;
class UMapCustomizationWidget;
class UMultiplayerOptionsWidget;
class USettingsMenuWidget;
class UPreGameLoadoutWidget;
class UUserWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGameModeSelected, EGameMode, SelectedMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnMenuCharacterCreated);

UCLASS()
class GINNUNGAGAP_API UMenuManagerSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowStartScreen();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowBootSplash();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowCrewLobby();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowModeSelect();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowMapCustomization();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowCharacterCreation();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowPreGameLoadout();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void StartGame(EGameMode GameMode);

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ContinueGame();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ShowSettings();

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnGameModeSelected OnGameModeSelected;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnMenuCharacterCreated OnCharacterCreated;

	UPROPERTY(BlueprintReadOnly, Category = "Menu")
	EGameMode SelectedGameMode = EGameMode::SinglePlayerSurvival;

protected:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UStartScreenWidget> StartScreenClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UBootSplashWidget> BootSplashClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UModeSelectWidget> ModeSelectClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UFirstLaunchCharacterCreationWidget> CharacterCreationClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UCharacterCreatorWidget> CharacterCreatorClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UMapCustomizationWidget> MapCustomizationClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UMultiplayerOptionsWidget> MultiplayerOptionsClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<USettingsMenuWidget> SettingsMenuClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UPreGameLoadoutWidget> PreGameLoadoutClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<ULoadingTransitionWidget> LoadingTransitionClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "UI")
	TSubclassOf<UMultiplayerLobbyWidget> MultiplayerLobbyClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Levels")
	FString MenuLevelName = TEXT("MainMenu");

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Levels")
	TMap<EGameMode, FString> GameModeLevelMap = {
		{EGameMode::SinglePlayerSurvival, TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck")},
		{EGameMode::CoopSurvival, TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck")},
		{EGameMode::Versus, TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck")}
	};

	UPROPERTY()
	TObjectPtr<UStartScreenWidget> CurrentStartScreen;

	UPROPERTY()
	TObjectPtr<UBootSplashWidget> CurrentBootSplash;

	UPROPERTY()
	TObjectPtr<UModeSelectWidget> CurrentModeSelect;

	UPROPERTY()
	TObjectPtr<UFirstLaunchCharacterCreationWidget> CurrentCharacterCreation;

	UPROPERTY()
	TObjectPtr<UCharacterCreatorWidget> CurrentCharacterCreator;

	UPROPERTY()
	TObjectPtr<UMapCustomizationWidget> CurrentMapCustomization;

	UPROPERTY()
	TObjectPtr<UMultiplayerOptionsWidget> CurrentMultiplayerOptions;

	UPROPERTY()
	TObjectPtr<USettingsMenuWidget> CurrentSettingsMenu;

	UPROPERTY()
	TObjectPtr<UPreGameLoadoutWidget> CurrentPreGameLoadout;

	UPROPERTY()
	TObjectPtr<ULoadingTransitionWidget> CurrentLoadingTransition;

	UPROPERTY()
	TObjectPtr<UMultiplayerLobbyWidget> CurrentMultiplayerLobby;

	UPROPERTY()
	FGameCustomization PendingCustomization;

	UPROPERTY()
	FCharacterProfile PendingCharacterProfile;

	UFUNCTION()
	void OnModeSelected(EGameMode Mode);

	UFUNCTION()
	void OnCharacterCreationComplete(const FString& CharacterName, ECharacterAppearance Appearance, EPressureSuitRole SuitRole);

	UFUNCTION()
	void OnCharacterIdentityConfirmed(const FCharacterProfile& CharacterDraft);

	UFUNCTION()
	void OnMapCustomizationStarted();

	UFUNCTION()
	void OnMultiplayerLobbyCreated();

	UFUNCTION()
	void OnPreGameDeploy();

	UFUNCTION()
	void OnHostSessionComplete(bool bSuccess, const FString& ErrorMessage);

	UFUNCTION()
	void StartCrewMatchmaking();

	UFUNCTION()
	void OnJoinCrewSessionComplete(bool bSuccess, const FString& ErrorMessage);

	UFUNCTION()
	void OnLobbyLaunchRequested();

	UFUNCTION()
	void LeaveCrewLobby();

	UFUNCTION()
	void OnLeaveCrewSessionComplete(bool bSuccess, const FString& ErrorMessage);

	UFUNCTION()
	void OnCrewConnectionLost(const FString& ErrorMessage);

	UFUNCTION()
	void OnBootSplashFinished();

	UFUNCTION()
	void OnTitleGateFinished();

	UFUNCTION()
	void ShowMultiplayerOptions();

	void HideAllMenus();
	void LoadGameMode(EGameMode GameMode);
	void CompletePendingLevelTravel();
	void SaveRunState();
	void ContinueAfterCharacterGate();
	void PrepareMenuInput(class APlayerController* PlayerController, UUserWidget* FocusWidget);
	void BeginMenuEntrance(UUserWidget* Widget);
	void TickMenuEntrance();
	static constexpr const TCHAR* RunSaveSlot = TEXT("GinnungagapRunSave");
	bool bBootSequenceCompleted = false;
	bool bTitleGateCompleted = false;
	FString PendingLevelTravel;
	FString PendingTravelOptions;
	FString PendingMultiplayerError;
	FTimerHandle LevelTravelTimer;
	FTimerHandle MenuEntranceTimer;
	TWeakObjectPtr<UUserWidget> AnimatedMenuWidget;
	float MenuEntranceElapsed=0.0f;
};
