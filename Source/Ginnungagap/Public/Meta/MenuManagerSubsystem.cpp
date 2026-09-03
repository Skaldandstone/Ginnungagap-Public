#include "Meta/MenuManagerSubsystem.h"
#include "UI/StartScreenWidget.h"
#include "UI/BootSplashWidget.h"
#include "UI/CharacterCreatorWidget.h"
#include "UI/LoadingTransitionWidget.h"
#include "UI/MultiplayerLobbyWidget.h"
#include "UI/ModeSelectWidget.h"
#include "UI/FirstLaunchCharacterCreationWidget.h"
#include "UI/MultiplayerOptionsWidget.h"
#include "UI/SettingsMenuWidget.h"
#include "UI/PreGameLoadoutWidget.h"
#include "UI/MenuWidgetResolution.h"
#include "Meta/ExpeditionRunSave.h"
#include "Meta/CharacterProfileSubsystem.h"
#include "Engine/GameInstance.h"
#include "Meta/MultiplayerSessionSubsystem.h"
#include "Meta/LobbyGameState.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "Misc/PackageName.h"
#include "TimerManager.h"

namespace
{
	bool IsValidCustomization(const FGameCustomization& Customization)
	{
		return StaticEnum<EShipSize>()->IsValidEnumValue(static_cast<int64>(Customization.ShipSize))
			&& StaticEnum<EGameDifficulty>()->IsValidEnumValue(static_cast<int64>(Customization.Difficulty))
			&& Customization.VersusSettings.IsValid();
	}

	FString FactionOption(EAntagonistFaction Faction)
	{
		switch (Faction)
		{
		case EAntagonistFaction::Bloom: return TEXT("Bloom");
		case EAntagonistFaction::Pirates: return TEXT("Pirates");
		case EAntagonistFaction::Rebels: return TEXT("Rebels");
		case EAntagonistFaction::Alien: return TEXT("Alien");
		default: return TEXT("None");
		}
	}

	bool IsValidRunSave(const UExpeditionRunSave* Save)
	{
		return Save
			&& StaticEnum<EGameMode>()->IsValidEnumValue(static_cast<int64>(Save->GameMode))
			&& IsValidCustomization(Save->Customization);
	}

}

using GinnungagapMenuWidgets::ResolveClass;

void UMenuManagerSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Set default widget classes
	if (!StartScreenClass)
	{
		StartScreenClass = ResolveClass<UStartScreenWidget>(GINNUNGAGAP_MENU_WBP("StartScreen"));
	}
	if (!BootSplashClass)
	{
		BootSplashClass = ResolveClass<UBootSplashWidget>(GINNUNGAGAP_MENU_WBP("BootSplash"));
	}
	if (!ModeSelectClass)
	{
		ModeSelectClass = ResolveClass<UModeSelectWidget>(GINNUNGAGAP_MENU_WBP("ModeSelect"));
	}
	if (!CharacterCreationClass)
	{
		CharacterCreationClass = ResolveClass<UFirstLaunchCharacterCreationWidget>(GINNUNGAGAP_MENU_WBP("FirstLaunchCharacterCreation"));
	}
	if (!CharacterCreatorClass)
	{
		CharacterCreatorClass = ResolveClass<UCharacterCreatorWidget>(GINNUNGAGAP_MENU_WBP("CharacterCreator"));
	}
	if (!MapCustomizationClass)
	{
		MapCustomizationClass = ResolveClass<UMapCustomizationWidget>(GINNUNGAGAP_MENU_WBP("MapCustomization"));
	}
	if (!MultiplayerOptionsClass)
	{
		MultiplayerOptionsClass = ResolveClass<UMultiplayerOptionsWidget>(GINNUNGAGAP_MENU_WBP("MultiplayerOptions"));
	}
	if (!SettingsMenuClass)
	{
		SettingsMenuClass = ResolveClass<USettingsMenuWidget>(GINNUNGAGAP_MENU_WBP("SettingsMenu"));
	}
	if (!PreGameLoadoutClass)
	{
		PreGameLoadoutClass = ResolveClass<UPreGameLoadoutWidget>(GINNUNGAGAP_MENU_WBP("PreGameLoadout"));
	}
	if (!LoadingTransitionClass)
	{
		LoadingTransitionClass = ResolveClass<ULoadingTransitionWidget>(GINNUNGAGAP_MENU_WBP("LoadingTransition"));
	}
	if (!MultiplayerLobbyClass)
	{
		MultiplayerLobbyClass = ResolveClass<UMultiplayerLobbyWidget>(GINNUNGAGAP_MENU_WBP("MultiplayerLobby"));
	}
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UMultiplayerSessionSubsystem* Sessions = GI->GetSubsystem<UMultiplayerSessionSubsystem>())
		{
			Sessions->OnHostSessionComplete.AddDynamic(this, &UMenuManagerSubsystem::OnHostSessionComplete);
		Sessions->OnJoinCrewSessionComplete.AddDynamic(this, &UMenuManagerSubsystem::OnJoinCrewSessionComplete);
		Sessions->OnLeaveCrewSessionComplete.AddDynamic(this, &UMenuManagerSubsystem::OnLeaveCrewSessionComplete);
		Sessions->OnCrewConnectionLost.AddDynamic(this, &UMenuManagerSubsystem::OnCrewConnectionLost);
		}
	}
}

void UMenuManagerSubsystem::ShowBootSplash()
{
	if (bBootSequenceCompleted)
	{
		ShowStartScreen();
		return;
	}
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentBootSplash = CreateWidget<UBootSplashWidget>(PC, BootSplashClass);
			if (CurrentBootSplash)
			{
				CurrentBootSplash->OnFinished.AddDynamic(this, &UMenuManagerSubsystem::OnBootSplashFinished);
				CurrentBootSplash->AddToViewport(200);
				PrepareMenuInput(PC, CurrentBootSplash);
			}
		}
	}
}

void UMenuManagerSubsystem::OnBootSplashFinished()
{
	bBootSequenceCompleted = true;
	ShowStartScreen();
}

void UMenuManagerSubsystem::OnTitleGateFinished()
{
	bTitleGateCompleted = true;
}

void UMenuManagerSubsystem::ShowStartScreen()
{
	HideAllMenus();

	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentStartScreen = CreateWidget<UStartScreenWidget>(PC, StartScreenClass);
			if (CurrentStartScreen)
			{
				CurrentStartScreen->SetTitleGateEnabled(!bTitleGateCompleted);
				CurrentStartScreen->AddToViewport(100);
				CurrentStartScreen->OnStartGameClicked.AddDynamic(this, &UMenuManagerSubsystem::ShowModeSelect);
				CurrentStartScreen->OnContinueGameClicked.AddDynamic(this, &UMenuManagerSubsystem::ContinueGame);
				CurrentStartScreen->OnSettingsRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowSettings);
				CurrentStartScreen->OnTitleGateCompleted.AddDynamic(this, &UMenuManagerSubsystem::OnTitleGateFinished);
				PrepareMenuInput(PC, CurrentStartScreen);
			}
		}
	}
}

void UMenuManagerSubsystem::ShowModeSelect()
{
	HideAllMenus();

	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentModeSelect = CreateWidget<UModeSelectWidget>(PC, ModeSelectClass);
			if (CurrentModeSelect)
			{
				CurrentModeSelect->AddToViewport(100);
				CurrentModeSelect->OnModeSelected.AddDynamic(this, &UMenuManagerSubsystem::OnModeSelected);
				CurrentModeSelect->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowStartScreen);
				PrepareMenuInput(PC, CurrentModeSelect);
			}
		}
	}
}

void UMenuManagerSubsystem::OnModeSelected(EGameMode Mode)
{
	SelectedGameMode = Mode;
	OnGameModeSelected.Broadcast(Mode);

	ShowMapCustomization();
}

void UMenuManagerSubsystem::Deinitialize()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UMultiplayerSessionSubsystem* Sessions = GI->GetSubsystem<UMultiplayerSessionSubsystem>())
		{
			Sessions->OnHostSessionComplete.RemoveDynamic(this, &UMenuManagerSubsystem::OnHostSessionComplete);
		Sessions->OnJoinCrewSessionComplete.RemoveDynamic(this, &UMenuManagerSubsystem::OnJoinCrewSessionComplete);
		Sessions->OnLeaveCrewSessionComplete.RemoveDynamic(this, &UMenuManagerSubsystem::OnLeaveCrewSessionComplete);
		Sessions->OnCrewConnectionLost.RemoveDynamic(this, &UMenuManagerSubsystem::OnCrewConnectionLost);
		}
	}
	Super::Deinitialize();
}

void UMenuManagerSubsystem::ShowSettings()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentSettingsMenu = CreateWidget<USettingsMenuWidget>(PC, SettingsMenuClass);
			if (CurrentSettingsMenu)
			{
				CurrentSettingsMenu->AddToViewport(100);
				CurrentSettingsMenu->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowStartScreen);
				PrepareMenuInput(PC, CurrentSettingsMenu);
			}
		}
	}
}

void UMenuManagerSubsystem::ShowMapCustomization()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentMapCustomization = CreateWidget<UMapCustomizationWidget>(PC, MapCustomizationClass);
			if (CurrentMapCustomization)
			{
				CurrentMapCustomization->SetGameMode(SelectedGameMode);
				CurrentMapCustomization->AddToViewport(100);
				CurrentMapCustomization->OnGameStarted.AddDynamic(this, &UMenuManagerSubsystem::OnMapCustomizationStarted);
				CurrentMapCustomization->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowModeSelect);
				PrepareMenuInput(PC, CurrentMapCustomization);
			}
		}
	}
}

void UMenuManagerSubsystem::OnCharacterCreationComplete(const FString& CharacterName, ECharacterAppearance Appearance, EPressureSuitRole SuitRole)
{
	OnCharacterCreated.Broadcast();
	ContinueAfterCharacterGate();
}

void UMenuManagerSubsystem::ShowCharacterCreation()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentCharacterCreator = CreateWidget<UCharacterCreatorWidget>(PC, CharacterCreatorClass);
			if (CurrentCharacterCreator)
			{
				CurrentCharacterCreator->AddToViewport(100);
				CurrentCharacterCreator->OnIdentityConfirmed.AddDynamic(this, &UMenuManagerSubsystem::OnCharacterIdentityConfirmed);
				CurrentCharacterCreator->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowMapCustomization);
				PrepareMenuInput(PC, CurrentCharacterCreator);
			}
		}
	}
}

void UMenuManagerSubsystem::OnCharacterIdentityConfirmed(const FCharacterProfile& CharacterDraft)
{
	PendingCharacterProfile = CharacterDraft;
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentCharacterCreation = CreateWidget<UFirstLaunchCharacterCreationWidget>(PC, CharacterCreationClass);
			if (CurrentCharacterCreation)
			{
				CurrentCharacterCreation->SetCharacterDraft(PendingCharacterProfile);
				CurrentCharacterCreation->AddToViewport(100);
				CurrentCharacterCreation->OnCharacterCreated.AddDynamic(this, &UMenuManagerSubsystem::OnCharacterCreationComplete);
				CurrentCharacterCreation->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowCharacterCreation);
				PrepareMenuInput(PC, CurrentCharacterCreation);
			}
		}
	}
}

void UMenuManagerSubsystem::OnMapCustomizationStarted()
{
	if (CurrentMapCustomization)
	{
		PendingCustomization = CurrentMapCustomization->GetCurrentCustomization();
	}
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		// This path represents a confirmed new expedition. ContinueGame deliberately
		// skips this clear so it can resume the four-deck ship checkpoint.
		if (UShipCheckpointSubsystem* Checkpoints = GI->GetSubsystem<UShipCheckpointSubsystem>())
		{
			Checkpoints->ClearCheckpoint();
		}
		if (UCharacterProfileSubsystem* Profile = GI->GetSubsystem<UCharacterProfileSubsystem>())
		{
			if (!Profile->HasCreatedCharacter())
			{
				ShowCharacterCreation();
				return;
			}
		}
	}
	ContinueAfterCharacterGate();
}

void UMenuManagerSubsystem::ContinueAfterCharacterGate()
{
	ShowPreGameLoadout();
}

void UMenuManagerSubsystem::ShowPreGameLoadout()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentPreGameLoadout = CreateWidget<UPreGameLoadoutWidget>(PC, PreGameLoadoutClass);
			if (CurrentPreGameLoadout)
			{
				CurrentPreGameLoadout->AddToViewport(100);
				CurrentPreGameLoadout->OnDeployRequested.AddDynamic(this, &UMenuManagerSubsystem::OnPreGameDeploy);
				CurrentPreGameLoadout->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowMapCustomization);
				PrepareMenuInput(PC, CurrentPreGameLoadout);
			}
		}
	}
}

void UMenuManagerSubsystem::OnPreGameDeploy()
{
	if (SelectedGameMode == EGameMode::SinglePlayerSurvival)
	{
		LoadGameMode(SelectedGameMode);
	}
	else if (SelectedGameMode == EGameMode::CoopSurvival || SelectedGameMode == EGameMode::Versus)
	{
		ShowMultiplayerOptions();
	}
}

void UMenuManagerSubsystem::ShowMultiplayerOptions()
{
	HideAllMenus();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentMultiplayerOptions = CreateWidget<UMultiplayerOptionsWidget>(PC, MultiplayerOptionsClass);
			if (CurrentMultiplayerOptions)
			{
				CurrentMultiplayerOptions->SetGameMode(SelectedGameMode);
				CurrentMultiplayerOptions->SetGameCustomization(PendingCustomization);
				CurrentMultiplayerOptions->AddToViewport(100);
				CurrentMultiplayerOptions->OnLobbyCreated.AddDynamic(this, &UMenuManagerSubsystem::OnMultiplayerLobbyCreated);
				CurrentMultiplayerOptions->OnMatchmakingStarted.AddDynamic(this, &UMenuManagerSubsystem::StartCrewMatchmaking);
				CurrentMultiplayerOptions->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::ShowPreGameLoadout);
				if(!PendingMultiplayerError.IsEmpty()){CurrentMultiplayerOptions->SetStatusMessage(FText::FromString(PendingMultiplayerError),true);PendingMultiplayerError.Reset();}
				PrepareMenuInput(PC, CurrentMultiplayerOptions);
			}
		}
	}
}

void UMenuManagerSubsystem::StartCrewMatchmaking()
{
	if(UGameInstance* GI=GetGameInstance())if(UMultiplayerSessionSubsystem* Sessions=GI->GetSubsystem<UMultiplayerSessionSubsystem>()){Sessions->FindAndJoinCrewSession(true);return;}
	OnJoinCrewSessionComplete(false,TEXT("Session services are unavailable."));
}

void UMenuManagerSubsystem::OnJoinCrewSessionComplete(bool bSuccess,const FString& ErrorMessage)
{
	if(bSuccess){HideAllMenus();return;}
	UE_LOG(LogTemp,Warning,TEXT("Crew matchmaking failed: %s"),*ErrorMessage);
	PendingMultiplayerError=FString::Printf(TEXT("CREW SEARCH FAILED // %s"),*ErrorMessage.ToUpper());
	ShowMultiplayerOptions();
}

void UMenuManagerSubsystem::OnMultiplayerLobbyCreated()
{
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UMultiplayerSessionSubsystem* Sessions = GI->GetSubsystem<UMultiplayerSessionSubsystem>())
		{
			const int32 Slots = SelectedGameMode == EGameMode::Versus
				? PendingCustomization.VersusSettings.ProtagonistSlots + PendingCustomization.VersusSettings.AntagonistSlots
				: 4;
			Sessions->HostSession(Slots, PendingCustomization.SelectedMap, true);
			return;
		}
	}
	OnHostSessionComplete(false, TEXT("Session services are unavailable."));
}

void UMenuManagerSubsystem::OnHostSessionComplete(bool bSuccess, const FString& ErrorMessage)
{
	if (!bSuccess)
	{
		UE_LOG(LogTemp, Error, TEXT("Unable to host crew lobby: %s"), *ErrorMessage);
		PendingMultiplayerError=FString::Printf(TEXT("HOSTING FAILED // %s"),*ErrorMessage.ToUpper());
		ShowMultiplayerOptions();
		return;
	}
	ShowCrewLobby();
}

void UMenuManagerSubsystem::ShowCrewLobby()
{
	HideAllMenus();
	if(ALobbyGameState* LobbyState=GetWorld()?GetWorld()->GetGameState<ALobbyGameState>():nullptr;LobbyState&&LobbyState->HasAuthority())
	{
		LobbyState->SetLobbyConfiguration(SelectedGameMode,PendingCustomization);
	}
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentMultiplayerLobby = CreateWidget<UMultiplayerLobbyWidget>(PC, MultiplayerLobbyClass);
			if (CurrentMultiplayerLobby)
			{
				FString HostName = TEXT("HOST");
				if (UCharacterProfileSubsystem* Profile = GI->GetSubsystem<UCharacterProfileSubsystem>()) HostName = Profile->GetCharacterName();
				CurrentMultiplayerLobby->Configure(SelectedGameMode, PendingCustomization, HostName);
				CurrentMultiplayerLobby->OnLaunchRequested.AddDynamic(this, &UMenuManagerSubsystem::OnLobbyLaunchRequested);
				CurrentMultiplayerLobby->OnBackRequested.AddDynamic(this, &UMenuManagerSubsystem::LeaveCrewLobby);
				CurrentMultiplayerLobby->AddToViewport(100);
				PrepareMenuInput(PC, CurrentMultiplayerLobby);
			}
		}
	}
}

void UMenuManagerSubsystem::OnLobbyLaunchRequested()
{
	LoadGameMode(SelectedGameMode);
}

void UMenuManagerSubsystem::LeaveCrewLobby()
{
	if(CurrentMultiplayerLobby)CurrentMultiplayerLobby->SetIsEnabled(false);
	if(UGameInstance* GI=GetGameInstance())
	{
		if(UMultiplayerSessionSubsystem* Sessions=GI->GetSubsystem<UMultiplayerSessionSubsystem>())
		{
			Sessions->LeaveCrewSession();
			return;
		}
	}
	OnLeaveCrewSessionComplete(false,TEXT("Session services are unavailable."));
}

void UMenuManagerSubsystem::OnLeaveCrewSessionComplete(bool bSuccess,const FString& ErrorMessage)
{
	if(!bSuccess)UE_LOG(LogTemp,Warning,TEXT("Unable to leave crew lobby: %s"),*ErrorMessage);
	ShowMultiplayerOptions();
}

void UMenuManagerSubsystem::OnCrewConnectionLost(const FString& ErrorMessage)
{
	PendingMultiplayerError=FString::Printf(TEXT("CONNECTION LOST // %s"),*ErrorMessage.ToUpper());
	ShowMultiplayerOptions();
}

void UMenuManagerSubsystem::StartGame(EGameMode GameMode)
{
	SelectedGameMode = GameMode;
	ShowMapCustomization();
}

void UMenuManagerSubsystem::ContinueGame()
{
	if (UExpeditionRunSave* Save = Cast<UExpeditionRunSave>(UGameplayStatics::LoadGameFromSlot(RunSaveSlot, 0)); IsValidRunSave(Save))
	{
		SelectedGameMode = Save->GameMode;
		PendingCustomization = Save->Customization;
		LoadGameMode(SelectedGameMode);
		return;
	}

	if (CurrentStartScreen)
	{
		CurrentStartScreen->SetStatusMessage(FText::FromString(TEXT("EXPEDITION SAVE COULD NOT BE READ")), true);
	}
}

void UMenuManagerSubsystem::HideAllMenus()
{
	if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(MenuEntranceTimer);
	AnimatedMenuWidget.Reset();
	if (CurrentBootSplash)
	{
		CurrentBootSplash->OnFinished.RemoveDynamic(this, &UMenuManagerSubsystem::OnBootSplashFinished);
		CurrentBootSplash->RemoveFromParent();
		CurrentBootSplash = nullptr;
	}

	if (CurrentStartScreen)
	{
		CurrentStartScreen->OnStartGameClicked.RemoveDynamic(this, &UMenuManagerSubsystem::ShowModeSelect);
		CurrentStartScreen->OnContinueGameClicked.RemoveDynamic(this, &UMenuManagerSubsystem::ContinueGame);
		CurrentStartScreen->OnSettingsRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowSettings);
		CurrentStartScreen->OnTitleGateCompleted.RemoveDynamic(this, &UMenuManagerSubsystem::OnTitleGateFinished);
		CurrentStartScreen->RemoveFromParent();
		CurrentStartScreen = nullptr;
	}

	if (CurrentModeSelect)
	{
		CurrentModeSelect->OnModeSelected.RemoveDynamic(this, &UMenuManagerSubsystem::OnModeSelected);
		CurrentModeSelect->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowStartScreen);
		CurrentModeSelect->RemoveFromParent();
		CurrentModeSelect = nullptr;
	}

	if (CurrentCharacterCreation)
	{
		CurrentCharacterCreation->OnCharacterCreated.RemoveDynamic(this, &UMenuManagerSubsystem::OnCharacterCreationComplete);
		CurrentCharacterCreation->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowCharacterCreation);
		CurrentCharacterCreation->RemoveFromParent();
		CurrentCharacterCreation = nullptr;
	}

	if (CurrentCharacterCreator)
	{
		CurrentCharacterCreator->OnIdentityConfirmed.RemoveDynamic(this, &UMenuManagerSubsystem::OnCharacterIdentityConfirmed);
		CurrentCharacterCreator->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowMapCustomization);
		CurrentCharacterCreator->RemoveFromParent();
		CurrentCharacterCreator = nullptr;
	}

	if (CurrentMapCustomization)
	{
		CurrentMapCustomization->OnGameStarted.RemoveDynamic(this, &UMenuManagerSubsystem::OnMapCustomizationStarted);
		CurrentMapCustomization->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowModeSelect);
		CurrentMapCustomization->RemoveFromParent();
		CurrentMapCustomization = nullptr;
	}

	if (CurrentMultiplayerOptions)
	{
		CurrentMultiplayerOptions->OnLobbyCreated.RemoveDynamic(this, &UMenuManagerSubsystem::OnMultiplayerLobbyCreated);
		CurrentMultiplayerOptions->OnMatchmakingStarted.RemoveDynamic(this, &UMenuManagerSubsystem::StartCrewMatchmaking);
		CurrentMultiplayerOptions->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowPreGameLoadout);
		CurrentMultiplayerOptions->RemoveFromParent();
		CurrentMultiplayerOptions = nullptr;
	}

	if (CurrentSettingsMenu)
	{
		CurrentSettingsMenu->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowStartScreen);
		CurrentSettingsMenu->RemoveFromParent();
		CurrentSettingsMenu = nullptr;
	}

	if (CurrentLoadingTransition)
	{
		CurrentLoadingTransition->RemoveFromParent();
		CurrentLoadingTransition = nullptr;
	}

	if (CurrentMultiplayerLobby)
	{
		CurrentMultiplayerLobby->OnLaunchRequested.RemoveDynamic(this, &UMenuManagerSubsystem::OnLobbyLaunchRequested);
		CurrentMultiplayerLobby->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::LeaveCrewLobby);
		CurrentMultiplayerLobby->RemoveFromParent();
		CurrentMultiplayerLobby = nullptr;
	}

	if (CurrentPreGameLoadout)
	{
		CurrentPreGameLoadout->OnDeployRequested.RemoveDynamic(this, &UMenuManagerSubsystem::OnPreGameDeploy);
		CurrentPreGameLoadout->OnBackRequested.RemoveDynamic(this, &UMenuManagerSubsystem::ShowMapCustomization);
		CurrentPreGameLoadout->RemoveFromParent();
		CurrentPreGameLoadout = nullptr;
	}
}

void UMenuManagerSubsystem::PrepareMenuInput(APlayerController* PlayerController, UUserWidget* FocusWidget)
{
	if (!PlayerController || !FocusWidget) return;
	BeginMenuEntrance(FocusWidget);
	PlayerController->bShowMouseCursor = true;
	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(FocusWidget->TakeWidget());
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PlayerController->SetInputMode(InputMode);
}

void UMenuManagerSubsystem::BeginMenuEntrance(UUserWidget* Widget)
{
	if(!Widget)return;
	AnimatedMenuWidget=Widget;MenuEntranceElapsed=0.0f;
	Widget->SetRenderOpacity(0.0f);Widget->SetRenderTranslation(FVector2D(0.0f,18.0f));
	if(UWorld* World=GetWorld())World->GetTimerManager().SetTimer(MenuEntranceTimer,this,&UMenuManagerSubsystem::TickMenuEntrance,1.0f/60.0f,true);
}

void UMenuManagerSubsystem::TickMenuEntrance()
{
	UUserWidget* Widget=AnimatedMenuWidget.Get();if(!Widget){if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(MenuEntranceTimer);return;}
	MenuEntranceElapsed+=1.0f/60.0f;const float Alpha=FMath::Clamp(MenuEntranceElapsed/0.22f,0.0f,1.0f);const float Ease=1.0f-FMath::Pow(1.0f-Alpha,3.0f);
	Widget->SetRenderOpacity(Ease);Widget->SetRenderTranslation(FVector2D(0.0f,FMath::Lerp(18.0f,0.0f,Ease)));
	if(Alpha>=1.0f){if(UWorld* World=GetWorld())World->GetTimerManager().ClearTimer(MenuEntranceTimer);AnimatedMenuWidget.Reset();}
}

void UMenuManagerSubsystem::LoadGameMode(EGameMode GameMode)
{
	HideAllMenus();

	// The authored four-deck ship is the prototype's sole deployable vessel for now.
	// Keep this independent of legacy save-file size selections so Continue also
	// returns to the same level while it is under active development.
	const FString LevelName = TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck");

	FString Options = GameMode == EGameMode::SinglePlayerSurvival ? FString() : TEXT("listen");
	if (GameMode == EGameMode::Versus)
	{
		FVersusMatchSettings Settings = PendingCustomization.VersusSettings;
		Settings.Sanitize();
		TArray<FString> IndependentFactions;
		for (const EAntagonistFaction Faction : Settings.IndependentAIFactions)
		{
			IndependentFactions.Add(FactionOption(Faction));
		}
		Options += FString::Printf(TEXT("?game=/Script/Ginnungagap.VersusGameMode?Team=Protagonist?Protagonists=%d?Antagonists=%d?AntagonistFaction=%s?IndependentAI=%s"),
			Settings.ProtagonistSlots, Settings.AntagonistSlots,
			*FactionOption(Settings.PlayerAntagonistFaction), *FString::Join(IndependentFactions, TEXT(",")));
	}
	if (!FPackageName::DoesPackageExist(LevelName))
	{
		UE_LOG(LogTemp, Error, TEXT("Cannot deploy expedition: map package '%s' does not exist."), *LevelName);
		ShowStartScreen();
		if (CurrentStartScreen) CurrentStartScreen->SetStatusMessage(FText::FromString(TEXT("DEPLOYMENT MAP IS MISSING")), true);
		return;
	}

	SaveRunState();
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			PC->bShowMouseCursor = false;
			PC->SetInputMode(FInputModeGameOnly());
		}
	}
	PendingLevelTravel = LevelName;
	PendingTravelOptions = Options;
	if (UGameInstance* GI = GetGameInstance())
	{
		if (APlayerController* PC = GI->GetFirstLocalPlayerController())
		{
			CurrentLoadingTransition = CreateWidget<ULoadingTransitionWidget>(PC, LoadingTransitionClass);
			if (CurrentLoadingTransition)
			{
				FCharacterProfile Character;
				if (UCharacterProfileSubsystem* Profile = GI->GetSubsystem<UCharacterProfileSubsystem>()) Character = Profile->GetProfile();
				CurrentLoadingTransition->Configure(Character, PendingCustomization, GameMode);
				CurrentLoadingTransition->AddToViewport(500);
			}
		}
	}
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(LevelTravelTimer, this, &UMenuManagerSubsystem::CompletePendingLevelTravel, 0.35f, false);
	}
}

void UMenuManagerSubsystem::CompletePendingLevelTravel()
{
	if (PendingLevelTravel.IsEmpty()) return;
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UMultiplayerSessionSubsystem* Sessions = GI->GetSubsystem<UMultiplayerSessionSubsystem>(); Sessions && Sessions->HasHostedSession())
		{
			if (UWorld* World = GetWorld(); World && World->GetNetMode() != NM_Client)
			{
				FString TravelURL = PendingLevelTravel;
				if (!PendingTravelOptions.IsEmpty()) TravelURL += TEXT("?") + PendingTravelOptions;
				World->ServerTravel(TravelURL, false);
				PendingLevelTravel.Reset();
				PendingTravelOptions.Reset();
				return;
			}
		}
	}
	UGameplayStatics::OpenLevel(GetWorld(), *PendingLevelTravel, true, PendingTravelOptions);
	PendingLevelTravel.Reset();
	PendingTravelOptions.Reset();
}

void UMenuManagerSubsystem::SaveRunState()
{
	if (!IsValidCustomization(PendingCustomization))
	{
		UE_LOG(LogTemp, Error, TEXT("Refusing to save invalid expedition customization."));
		return;
	}
	UExpeditionRunSave* Save = Cast<UExpeditionRunSave>(UGameplayStatics::CreateSaveGameObject(UExpeditionRunSave::StaticClass()));
	if (!Save) return;
	Save->GameMode = SelectedGameMode;
	Save->Customization = PendingCustomization;
	Save->SavedAtUtc = FDateTime::UtcNow();
	if (!UGameplayStatics::SaveGameToSlot(Save, RunSaveSlot, 0))
	{
		UE_LOG(LogTemp, Warning, TEXT("Failed to persist expedition run state."));
	}
}
