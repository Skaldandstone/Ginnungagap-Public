#include "UI/MultiplayerOptionsWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"
#include "UI/MenuVisualStyle.h"
#include "Input/Reply.h"

void UMultiplayerOptionsWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildFallbackLayout();

	if (TitleText)
	{
		TitleText->SetText(FText::FromString(SelectedGameMode == EGameMode::Versus
			? TEXT("Host Versus Match") : TEXT("Multiplayer Options")));
	}

	// Set descriptions
	if (MatchmakingDescText)
	{
		MatchmakingDescText->SetText(FText::FromString(TEXT("Find players with matching game settings")));
	}

	if (InviteFriendsDescText)
	{
		InviteFriendsDescText->SetText(FText::FromString(TEXT("Invite friends to play with you")));
	}

	if (CreateLobbyDescText)
	{
		CreateLobbyDescText->SetText(FText::FromString(TEXT("Create a lobby and wait for players to join")));
	}

	// Bind button events
	if (MatchmakingButton)
	{
		MatchmakingButton->OnClicked.AddDynamic(this, &UMultiplayerOptionsWidget::OnMatchmakingClicked);
		MatchmakingButton->SetIsEnabled(true);
		MatchmakingButton->SetToolTipText(FText::FromString(TEXT("Find a compatible crew session on the local network.")));
	}

	if (InviteFriendsButton)
	{
		InviteFriendsButton->OnClicked.AddDynamic(this, &UMultiplayerOptionsWidget::OnInviteFriendsClicked);
		InviteFriendsButton->SetIsEnabled(false);
		InviteFriendsButton->SetToolTipText(FText::FromString(TEXT("Platform invitations require online services configuration.")));
	}

	if (CreateLobbyButton)
	{
		CreateLobbyButton->OnClicked.AddDynamic(this, &UMultiplayerOptionsWidget::OnCreateLobbyClicked);
	}

	if (BackButton)
	{
		BackButton->OnClicked.AddDynamic(this, &UMultiplayerOptionsWidget::OnBackClicked);
	}
	SetIsFocusable(true);
	if (CreateLobbyButton) CreateLobbyButton->SetKeyboardFocus();
	RefreshExpeditionSummary();
}

void UMultiplayerOptionsWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if (CreateLobbyButton) CreateLobbyButton->SetKeyboardFocus();
}

FReply UMultiplayerOptionsWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_Special_Left || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UMultiplayerOptionsWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("MultiplayerRoot"));
	GinnungagapMenuStyle::ApplyTerminalPanel(Root); Root->SetPadding(FMargin(110, 72)); USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Root->SetContent(Stack);
	auto MakeText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name); T->SetText(FText::FromString(Copy));
		GinnungagapMenuStyle::ApplyTerminalText(T,Size,Color,Size<=12); T->SetAutoWrapText(true); return T;
	};
	Stack->AddChildToVerticalBox(MakeText(TEXT("StepText"), SelectedGameMode == EGameMode::Versus
		? TEXT("SHIPNET RELAY  //  CONTAINMENT PARTIES") : TEXT("SHIPNET RELAY  //  SURVIVOR LINK"), 12, GinnungagapMenuStyle::SafetyAmber));
	TitleText = MakeText(TEXT("TitleText"), SelectedGameMode == EGameMode::Versus
		? TEXT("ESTABLISH OPPOSING LINKS") : TEXT("ESTABLISH CREW LINK"), 36, GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* TitleSlot = Stack->AddChildToVerticalBox(TitleText)) TitleSlot->SetPadding(FMargin(0, 12, 0, 44));
	ExpeditionSummaryText = MakeText(TEXT("ExpeditionSummaryText"), TEXT(""), 14, GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* SummarySlot = Stack->AddChildToVerticalBox(ExpeditionSummaryText)) SummarySlot->SetPadding(FMargin(0, 0, 0, 24));
	UHorizontalBox* Cards = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass()); Stack->AddChildToVerticalBox(Cards);
	auto Card = [this, Cards, MakeText](const TCHAR* Name, const TCHAR* Label, const TCHAR* Detail, UButton*& Button, UTextBlock*& Desc)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(FLinearColor(0.04f, 0.10f, 0.12f));
		GinnungagapMenuStyle::ApplyButton(Button,FString(Name).Contains(TEXT("Create")));
		UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Body->AddChildToVerticalBox(MakeText(TEXT("OptionLabel"), Label, 20, GinnungagapMenuStyle::CryoWhite));
		Desc = MakeText(TEXT("OptionDescription"), Detail, 13, GinnungagapMenuStyle::MutedSteel);
		if (UVerticalBoxSlot* DescSlot = Body->AddChildToVerticalBox(Desc)) DescSlot->SetPadding(FMargin(0, 14, 0, 0));
		Button->AddChild(Body); Cards->AddChildToHorizontalBox(Button);
	};
	Card(TEXT("MatchmakingButton"), TEXT("SCAN FOR SURVIVORS"), TEXT("Sweep nearby relays for operators matching this wake profile."), MatchmakingButton, MatchmakingDescText);
	Card(TEXT("InviteFriendsButton"), TEXT("OPEN PRIVATE CHANNEL"), TEXT("Transmit an encrypted wake request to known crew."), InviteFriendsButton, InviteFriendsDescText);
	Card(TEXT("CreateLobbyButton"), TEXT("HOST CREW RELAY"), TEXT("Bring a staging relay online and assume expedition command."), CreateLobbyButton, CreateLobbyDescText);
	StatusText = MakeText(TEXT("StatusText"), TEXT("LOCAL RELAY READY // LONG-RANGE MATCHMAKING OFFLINE"), 11, GinnungagapMenuStyle::SafetyAmber);
	if (UVerticalBoxSlot* StatusSlot = Stack->AddChildToVerticalBox(StatusText)) StatusSlot->SetPadding(FMargin(0, 28, 0, 0));
	BackButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BackButton"));
	GinnungagapMenuStyle::ApplyButton(BackButton);
	BackButton->AddChild(MakeText(TEXT("BackLabel"), TEXT("<  EDIT EXPEDITION"), 13, FLinearColor(0.62f, 0.70f, 0.73f)));
	if (UVerticalBoxSlot* BackSlot = Stack->AddChildToVerticalBox(BackButton)) BackSlot->SetPadding(FMargin(0, 42, 0, 0));
}

void UMultiplayerOptionsWidget::NativeDestruct()
{
	if (MatchmakingButton) MatchmakingButton->OnClicked.RemoveDynamic(this, &UMultiplayerOptionsWidget::OnMatchmakingClicked);
	if (InviteFriendsButton) InviteFriendsButton->OnClicked.RemoveDynamic(this, &UMultiplayerOptionsWidget::OnInviteFriendsClicked);
	if (CreateLobbyButton) CreateLobbyButton->OnClicked.RemoveDynamic(this, &UMultiplayerOptionsWidget::OnCreateLobbyClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UMultiplayerOptionsWidget::OnBackClicked);
	Super::NativeDestruct();
}

void UMultiplayerOptionsWidget::SetGameCustomization(const FGameCustomization& InCustomization)
{
	CurrentCustomization = InCustomization;
	RefreshExpeditionSummary();
}

void UMultiplayerOptionsWidget::SetStatusMessage(const FText& Message,bool bIsError)
{
	if(StatusText){StatusText->SetText(Message);StatusText->SetColorAndOpacity(FSlateColor(bIsError?GinnungagapMenuStyle::FaultRed:GinnungagapMenuStyle::CryoWhite));}
}

void UMultiplayerOptionsWidget::RefreshExpeditionSummary()
{
	if (!ExpeditionSummaryText) return;
	const UEnum* ShipEnum = StaticEnum<EShipSize>();
	const UEnum* DifficultyEnum = StaticEnum<EGameDifficulty>();
	const FString Ship = ShipEnum ? ShipEnum->GetDisplayNameTextByValue(static_cast<int64>(CurrentCustomization.ShipSize)).ToString().ToUpper() : TEXT("UNKNOWN");
	const FString Difficulty = DifficultyEnum ? DifficultyEnum->GetDisplayNameTextByValue(static_cast<int64>(CurrentCustomization.Difficulty)).ToString().ToUpper() : TEXT("UNKNOWN");
	FString Summary = FString::Printf(TEXT("%s VESSEL  //  %s THREAT  //  %s"), *Ship, *Difficulty, *CurrentCustomization.SelectedMap);
	if (SelectedGameMode == EGameMode::Versus)
	{
		const FVersusMatchSettings& Versus = CurrentCustomization.VersusSettings;
		const UEnum* FactionEnum = StaticEnum<EAntagonistFaction>();
		const FString Faction = FactionEnum
			? FactionEnum->GetDisplayNameTextByValue(static_cast<int64>(Versus.PlayerAntagonistFaction)).ToString().ToUpper()
			: TEXT("ANTAGONIST");
		Summary += FString::Printf(TEXT("  //  %d CREW v %d %s"),
			Versus.ProtagonistSlots, Versus.AntagonistSlots, *Faction);
	}
	ExpeditionSummaryText->SetText(FText::FromString(Summary));
}

void UMultiplayerOptionsWidget::OnMatchmakingClicked()
{
	if(MatchmakingButton)MatchmakingButton->SetIsEnabled(false);
	if(StatusText){StatusText->SetText(FText::FromString(TEXT("SCANNING FOR SURVIVOR BEACONS...")));StatusText->SetColorAndOpacity(FSlateColor(GinnungagapMenuStyle::CryoWhite));}
	OnMatchmakingStarted.Broadcast();
}

void UMultiplayerOptionsWidget::OnInviteFriendsClicked()
{
	// TODO: Implement friend invite system
	UE_LOG(LogTemp, Warning, TEXT("Friend invite system not yet implemented"));
}

void UMultiplayerOptionsWidget::OnCreateLobbyClicked()
{
	if (CreateLobbyButton) CreateLobbyButton->SetIsEnabled(false);
	if (StatusText)
	{
		StatusText->SetText(FText::FromString(TEXT("OPENING CREW LOBBY...")));
		StatusText->SetColorAndOpacity(FSlateColor(FLinearColor(0.30f, 0.86f, 1.0f)));
	}
	OnLobbyCreated.Broadcast();
}

void UMultiplayerOptionsWidget::OnBackClicked()
{
	OnBackRequested.Broadcast();
}
