#include "UI/ModeSelectWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/Spacer.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/SafeZone.h"
#include "UI/MenuVisualStyle.h"
#include "Input/Reply.h"

void UModeSelectWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (SinglePlayerButton)
	{
		SinglePlayerButton->OnClicked.AddDynamic(this, &UModeSelectWidget::OnSinglePlayerSelected);
	}

	if (CoopButton)
	{
		CoopButton->OnClicked.AddDynamic(this, &UModeSelectWidget::OnCoopSelected);
	}

	if (VersusButton)
	{
		VersusButton->OnClicked.AddDynamic(this, &UModeSelectWidget::OnVersusSelected);
	}

	if (BackButton)
	{
		BackButton->OnClicked.AddDynamic(this, &UModeSelectWidget::OnBackClicked);
	}

	// Show default mode info
	DisplayModeInfo(EGameMode::SinglePlayerSurvival);
	SetIsFocusable(true);
	if (SinglePlayerButton) SinglePlayerButton->SetKeyboardFocus();
}

FReply UModeSelectWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_Special_Left || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UModeSelectWidget::NativeDestruct()
{
	if (SinglePlayerButton) SinglePlayerButton->OnClicked.RemoveDynamic(this, &UModeSelectWidget::OnSinglePlayerSelected);
	if (CoopButton) CoopButton->OnClicked.RemoveDynamic(this, &UModeSelectWidget::OnCoopSelected);
	if (VersusButton) VersusButton->OnClicked.RemoveDynamic(this, &UModeSelectWidget::OnVersusSelected);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &UModeSelectWidget::OnBackClicked);
	Super::NativeDestruct();
}

void UModeSelectWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ModeSelectRoot"));
	GinnungagapMenuStyle::ApplyTerminalPanel(Root);
	Root->SetPadding(FMargin(110.0f, 72.0f));
	USafeZone* Safe=WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(),TEXT("SafeZone"));Safe->AddChild(Root);WidgetTree->RootWidget=Safe;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Root->SetContent(Stack);
	auto Text = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Result = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Result->SetText(FText::FromString(Copy)); Result->SetFont(FSlateFontInfo(Result->GetFont().FontObject, Size));
		Result->SetColorAndOpacity(FSlateColor(Color)); return Result;
	};
	Stack->AddChildToVerticalBox(Text(TEXT("StepText"), TEXT("DERELICT CONTROL  //  WAKE PROTOCOL 01 OF 03"), 12, GinnungagapMenuStyle::SafetyAmber));
	UTextBlock* Heading = Text(TEXT("HeadingText"), TEXT("SELECT SURVIVAL PROTOCOL"), 36, GinnungagapMenuStyle::CryoWhite);
	if (UVerticalBoxSlot* HeadingSlot = Stack->AddChildToVerticalBox(Heading)) HeadingSlot->SetPadding(FMargin(0, 12, 0, 44));
	UHorizontalBox* Cards = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Stack->AddChildToVerticalBox(Cards);
	auto Card = [this, Cards](const TCHAR* Name, const TCHAR* Label, const TCHAR* Detail, UButton*& Out)
	{
		Out = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
		Out->SetBackgroundColor(FLinearColor(0.04f, 0.10f, 0.12f, 1.0f));
		GinnungagapMenuStyle::ApplyButton(Out);
		UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		UTextBlock* LabelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		LabelText->SetText(FText::FromString(Label)); LabelText->SetFont(FSlateFontInfo(LabelText->GetFont().FontObject, 24));
		LabelText->SetColorAndOpacity(FSlateColor(GinnungagapMenuStyle::CryoWhite));
		Body->AddChildToVerticalBox(LabelText);
		UTextBlock* DetailText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		DetailText->SetText(FText::FromString(Detail)); DetailText->SetAutoWrapText(true);
		DetailText->SetColorAndOpacity(FSlateColor(GinnungagapMenuStyle::MutedSteel));
		if (UVerticalBoxSlot* DetailSlot = Body->AddChildToVerticalBox(DetailText)) DetailSlot->SetPadding(FMargin(0, 14, 0, 0));
		Out->AddChild(Body); Cards->AddChildToHorizontalBox(Out);
	};
	Card(TEXT("SinglePlayerButton"), TEXT("SOLO WAKE"), TEXT("01 life sign. No rescue response. Full vessel authority."), SinglePlayerButton);
	Card(TEXT("CoopButton"), TEXT("CREW WAKE"), TEXT("02-04 life signs. Shared oxygen, power, and trauma systems."), CoopButton);
	Card(TEXT("VersusButton"), TEXT("CONTAINMENT FAILURE"), TEXT("Crew survival protocol with hostile asymmetric presence."), VersusButton);
	ModeNameText = Text(TEXT("ModeNameText"), TEXT("Solo Wake"), 18, GinnungagapMenuStyle::SafetyAmber);
	if (UVerticalBoxSlot* InfoSlot = Stack->AddChildToVerticalBox(ModeNameText)) InfoSlot->SetPadding(FMargin(0, 36, 0, 8));
	ModeDescriptionText = Text(TEXT("ModeDescriptionText"), TEXT(""), 15, GinnungagapMenuStyle::MutedSteel);
	Stack->AddChildToVerticalBox(ModeDescriptionText);
	BackButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BackButton"));
	UTextBlock* BackLabel = Text(TEXT("BackLabel"), TEXT("<  RETURN TO TITLE"), 13, FLinearColor(0.62f, 0.70f, 0.73f));
	BackButton->AddChild(BackLabel);
	if (UVerticalBoxSlot* BackSlot = Stack->AddChildToVerticalBox(BackButton)) BackSlot->SetPadding(FMargin(0, 38, 0, 0));
}

void UModeSelectWidget::OnSinglePlayerSelected()
{
	SelectMode(EGameMode::SinglePlayerSurvival);
}

void UModeSelectWidget::OnCoopSelected()
{
	SelectMode(EGameMode::CoopSurvival);
}

void UModeSelectWidget::OnVersusSelected()
{
	SelectMode(EGameMode::Versus);
}

void UModeSelectWidget::OnBackClicked()
{
	OnBackRequested.Broadcast();
}

void UModeSelectWidget::SelectMode(EGameMode Mode)
{
	DisplayModeInfo(Mode);
	OnModeSelected.Broadcast(Mode);
}

void UModeSelectWidget::DisplayModeInfo(EGameMode Mode)
{
	FString ModeName;
	FString Description;

	switch (Mode)
	{
		case EGameMode::SinglePlayerSurvival:
			ModeName = TEXT("Single Player");
			Description = SinglePlayerDescription;
			break;
		case EGameMode::CoopSurvival:
			ModeName = TEXT("Co-op (2-4 Players)");
			Description = CoopDescription;
			break;
		case EGameMode::Versus:
			ModeName = TEXT("Versus (1v1 to 8v4)");
			Description = VersusDescription;
			break;
	}

	if (ModeNameText)
	{
		ModeNameText->SetText(FText::FromString(ModeName));
	}

	if (ModeDescriptionText)
	{
		ModeDescriptionText->SetText(FText::FromString(Description));
	}
}
