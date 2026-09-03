#include "UI/MultiplayerLobbyWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"
#include "UI/MenuVisualStyle.h"
#include "Input/Reply.h"
#include "Meta/LobbyPlayerState.h"
#include "Meta/LobbyGameState.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"

void UMultiplayerLobbyWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized(); BuildFallbackLayout();
	if(ReadyButton)ReadyButton->OnClicked.AddDynamic(this,&UMultiplayerLobbyWidget::OnReadyClicked);
	if(LaunchButton)LaunchButton->OnClicked.AddDynamic(this,&UMultiplayerLobbyWidget::OnLaunchClicked);
	if(BackButton)BackButton->OnClicked.AddDynamic(this,&UMultiplayerLobbyWidget::OnBackClicked);
	SetIsFocusable(true); if(ReadyButton)ReadyButton->SetKeyboardFocus(); RefreshLobby();
}

void UMultiplayerLobbyWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if(ReadyButton)ReadyButton->SetKeyboardFocus();
}

void UMultiplayerLobbyWidget::NativeDestruct()
{
	if(ReadyButton)ReadyButton->OnClicked.RemoveDynamic(this,&UMultiplayerLobbyWidget::OnReadyClicked);
	if(LaunchButton)LaunchButton->OnClicked.RemoveDynamic(this,&UMultiplayerLobbyWidget::OnLaunchClicked);
	if(BackButton)BackButton->OnClicked.RemoveDynamic(this,&UMultiplayerLobbyWidget::OnBackClicked); Super::NativeDestruct();
}

void UMultiplayerLobbyWidget::NativeTick(const FGeometry& MyGeometry,float InDeltaTime)
{
	Super::NativeTick(MyGeometry,InDeltaTime);
	RefreshAccumulator+=InDeltaTime;
	if(RefreshAccumulator>=0.25f){RefreshAccumulator=0.0f;RefreshLobby();}
}

void UMultiplayerLobbyWidget::Configure(EGameMode GameMode,const FGameCustomization& Customization,const FString& HostName)
{
	SelectedMode=GameMode; GameCustomization=Customization; HostCharacterName=HostName.IsEmpty()?TEXT("HOST"):HostName; RefreshLobby();
}

void UMultiplayerLobbyWidget::BuildFallbackLayout()
{
	if(!WidgetTree||WidgetTree->RootWidget)return;
	UBorder* Root=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("LobbyRoot"));GinnungagapMenuStyle::ApplyTerminalPanel(Root);Root->SetPadding(FMargin(100,64));USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack=WidgetTree->ConstructWidget<UVerticalBox>();Root->SetContent(Stack);
	auto Text=[this,Stack](const TCHAR* Name,const TCHAR* Copy,int32 Size,FLinearColor Color){UTextBlock* T=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),Name);T->SetText(FText::FromString(Copy));T->SetFont(FSlateFontInfo(T->GetFont().FontObject,Size));T->SetColorAndOpacity(FSlateColor(Color));T->SetAutoWrapText(true);Stack->AddChildToVerticalBox(T);return T;};
	Text(TEXT("StepText"),TEXT("SHIPNET RELAY  //  CRYO WAKE ROSTER"),12,GinnungagapMenuStyle::SafetyAmber);
	UTextBlock* Heading=Text(TEXT("HeadingText"),TEXT("CONFIRM SURVIVING CREW"),36,GinnungagapMenuStyle::CryoWhite);if(UVerticalBoxSlot* S=Cast<UVerticalBoxSlot>(Heading->Slot))S->SetPadding(FMargin(0,12,0,34));
	ExpeditionText=Text(TEXT("ExpeditionText"),TEXT(""),14,GinnungagapMenuStyle::SafetyAmber);
	RosterText=Text(TEXT("RosterText"),TEXT(""),18,GinnungagapMenuStyle::CryoWhite);if(UVerticalBoxSlot* S=Cast<UVerticalBoxSlot>(RosterText->Slot))S->SetPadding(FMargin(0,42,0,18));
	StatusText=Text(TEXT("StatusText"),TEXT(""),12,GinnungagapMenuStyle::MutedSteel);
	UHorizontalBox* Actions=WidgetTree->ConstructWidget<UHorizontalBox>();if(UVerticalBoxSlot* S=Stack->AddChildToVerticalBox(Actions))S->SetPadding(FMargin(0,46,0,0));
	auto AddButton=[this,Actions](const TCHAR* Name,const TCHAR* Copy,TObjectPtr<UButton>& Out){Out=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(),Name);GinnungagapMenuStyle::ApplyButton(Out,FString(Name).Contains(TEXT("Launch")));UTextBlock* L=WidgetTree->ConstructWidget<UTextBlock>();L->SetText(FText::FromString(Copy));Out->AddChild(L);Actions->AddChildToHorizontalBox(Out);};
	AddButton(TEXT("BackButton"),TEXT("<  LEAVE LOBBY"),BackButton);AddButton(TEXT("ReadyButton"),TEXT("TOGGLE READY"),ReadyButton);AddButton(TEXT("LaunchButton"),TEXT("LAUNCH EXPEDITION  >"),LaunchButton);
	ReadyButtonText=ReadyButton?Cast<UTextBlock>(ReadyButton->GetContent()):nullptr;
}

void UMultiplayerLobbyWidget::RefreshLobby()
{
	if(const ALobbyGameState* LobbyState=GetWorld()?GetWorld()->GetGameState<ALobbyGameState>():nullptr;LobbyState&&LobbyState->bConfigurationReady)
	{
		SelectedMode=LobbyState->SelectedMode;
		GameCustomization=LobbyState->Customization;
	}
	const UEnum* Ship=StaticEnum<EShipSize>();const UEnum* Difficulty=StaticEnum<EGameDifficulty>();const UEnum* Mode=StaticEnum<EGameMode>();
	if(ExpeditionText)ExpeditionText->SetText(FText::FromString(FString::Printf(TEXT("%s  //  %s VESSEL  //  %s THREAT"),Mode?*Mode->GetDisplayNameTextByValue(static_cast<int64>(SelectedMode)).ToString().ToUpper():TEXT("MULTIPLAYER"),Ship?*Ship->GetDisplayNameTextByValue(static_cast<int64>(GameCustomization.ShipSize)).ToString().ToUpper():TEXT("MEDIUM"),Difficulty?*Difficulty->GetDisplayNameTextByValue(static_cast<int64>(GameCustomization.Difficulty)).ToString().ToUpper():TEXT("NORMAL"))));
	APlayerController* PC=GetOwningPlayer();
	ALobbyPlayerState* LocalState=PC?PC->GetPlayerState<ALobbyPlayerState>():nullptr;
	if(LocalState&&!bIdentitySubmitted){bIdentitySubmitted=true;LocalState->ServerSetLobbyName(HostCharacterName);}
	const bool bIsHost=PC&&PC->HasAuthority();
	bool bAllReady=true;int32 CrewCount=0;TArray<FString> Lines;
	if(const AGameStateBase* GS=GetWorld()?GetWorld()->GetGameState():nullptr)
	{
		for(APlayerState* Entry:GS->PlayerArray)
		{
			const ALobbyPlayerState* LobbyState=Cast<ALobbyPlayerState>(Entry);if(!LobbyState)continue;
			++CrewCount;bAllReady&=LobbyState->bLobbyReady;
			FString Name=LobbyState->GetPlayerName();if(Name.IsEmpty())Name=CrewCount==1?HostCharacterName:TEXT("CREW MEMBER");
		Lines.Add(FString::Printf(TEXT("POD %02d  //  %s  //  %s  //  %s"),CrewCount,*Name.ToUpper(),CrewCount==1?TEXT("COMMAND"):TEXT("CREW"),LobbyState->bLobbyReady?TEXT("VITALS STABLE"):TEXT("NO WAKE CONFIRMATION")));
		}
	}
	const int32 MaxSlots=SelectedMode==EGameMode::Versus?FMath::Clamp(GameCustomization.VersusSettings.ProtagonistSlots+GameCustomization.VersusSettings.AntagonistSlots,2,12):4;
	for(int32 SlotIndex=CrewCount+1;SlotIndex<=MaxSlots;++SlotIndex)Lines.Add(FString::Printf(TEXT("POD %02d  //  NO LIFE SIGN"),SlotIndex));
	CachedRoster=FString::Join(Lines,TEXT("\n"));if(RosterText)RosterText->SetText(FText::FromString(CachedRoster));
	if(StatusText){const FString State=bAllReady&&CrewCount>0?(bIsHost?TEXT("CREW READY // EXPEDITION MAY LAUNCH"):TEXT("CREW READY // AWAITING HOST")):TEXT("WAITING FOR ALL CREW TO MARK READY");StatusText->SetText(FText::FromString(FString::Printf(TEXT("%d / %d CONNECTED  //  %s"),CrewCount,MaxSlots,*State)));}
	if(ReadyButton)ReadyButton->SetIsEnabled(LocalState!=nullptr);
	if(ReadyButtonText)ReadyButtonText->SetText(FText::FromString(LocalState&&LocalState->bLobbyReady?TEXT("CANCEL READY"):TEXT("MARK READY")));
	if(LaunchButton){LaunchButton->SetVisibility(bIsHost?ESlateVisibility::Visible:ESlateVisibility::Collapsed);LaunchButton->SetIsEnabled(bIsHost&&bAllReady&&CrewCount>0);}
}

void UMultiplayerLobbyWidget::OnReadyClicked(){if(APlayerController* PC=GetOwningPlayer())if(ALobbyPlayerState* State=PC->GetPlayerState<ALobbyPlayerState>()){State->ServerSetReady(!State->bLobbyReady);RefreshLobby();}}
void UMultiplayerLobbyWidget::OnLaunchClicked(){APlayerController* PC=GetOwningPlayer();if(PC&&PC->HasAuthority())OnLaunchRequested.Broadcast();}
void UMultiplayerLobbyWidget::OnBackClicked(){OnBackRequested.Broadcast();}
FReply UMultiplayerLobbyWidget::NativeOnKeyDown(const FGeometry& G,const FKeyEvent& E){if(E.GetKey()==EKeys::Escape||E.GetKey()==EKeys::Gamepad_FaceButton_Right){OnBackClicked();return FReply::Handled();}return Super::NativeOnKeyDown(G,E);}
