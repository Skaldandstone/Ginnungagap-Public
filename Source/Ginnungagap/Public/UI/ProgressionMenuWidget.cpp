#include "UI/ProgressionMenuWidget.h"
#include "UI/SkillTreeWidget.h"
#include "UI/SettingsMenuWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"
#include "Input/Reply.h"
#include "TimerManager.h"

void UProgressionMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildFallbackLayout();

	if (CloseButton)
	{
		CloseButton->OnClicked.AddDynamic(this, &UProgressionMenuWidget::OnCloseButtonClicked);
	}
	if (SettingsButton) SettingsButton->OnClicked.AddDynamic(this, &UProgressionMenuWidget::OnSettingsClicked);
	if (ReturnToTitleButton) ReturnToTitleButton->OnClicked.AddDynamic(this, &UProgressionMenuWidget::OnReturnToTitleClicked);

	// Start with menu closed
	CloseMenu();
}

void UProgressionMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
}

void UProgressionMenuWidget::NativeDestruct()
{
	if (CloseButton) CloseButton->OnClicked.RemoveDynamic(this, &UProgressionMenuWidget::OnCloseButtonClicked);
	if (SettingsButton) SettingsButton->OnClicked.RemoveDynamic(this, &UProgressionMenuWidget::OnSettingsClicked);
	if (ReturnToTitleButton) ReturnToTitleButton->OnClicked.RemoveDynamic(this, &UProgressionMenuWidget::OnReturnToTitleClicked);
	if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(ReturnToTitleTimer);
	DismissSettingsMenu();
	Super::NativeDestruct();
}

void UProgressionMenuWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PauseRoot"));
	Root->SetBrushColor(FLinearColor(0.006f, 0.012f, 0.018f, 0.96f)); Root->SetPadding(FMargin(90, 64)); WidgetTree->RootWidget = Root;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass()); Root->SetContent(Stack);
	auto AddText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name); Text->SetText(FText::FromString(Copy));
		Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size)); Text->SetColorAndOpacity(FSlateColor(Color)); return Text;
	};
	Stack->AddChildToVerticalBox(AddText(TEXT("SectionText"), TEXT("EXPEDITION CONTROL  //  PAUSED"), 12, FLinearColor(0.30f, 0.86f, 1.0f)));
	UTextBlock* Heading = AddText(TEXT("HeadingText"), TEXT("SHIP COMMAND"), 36, FLinearColor(0.88f, 0.94f, 0.95f));
	if (UVerticalBoxSlot* HeadingSlot = Stack->AddChildToVerticalBox(Heading)) HeadingSlot->SetPadding(FMargin(0, 12, 0, 42));
	auto AddButton = [this, Stack, AddText](const TCHAR* Name, const TCHAR* Label, UButton*& Button)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(FLinearColor(0.04f, 0.10f, 0.12f, 1.0f));
		Button->AddChild(AddText(TEXT("ButtonLabel"), Label, 17, FLinearColor(0.88f, 0.94f, 0.95f)));
		if (UVerticalBoxSlot* ButtonSlot = Stack->AddChildToVerticalBox(Button)) ButtonSlot->SetPadding(FMargin(0, 0, 0, 12));
	};
	AddButton(TEXT("CloseButton"), TEXT("RESUME EXPEDITION"), CloseButton);
	AddButton(TEXT("SettingsButton"), TEXT("SYSTEM SETTINGS"), SettingsButton);
	AddButton(TEXT("ReturnToTitleButton"), TEXT("RETURN TO TITLE"), ReturnToTitleButton);
	if (CloseButton) CloseButton->SetToolTipText(FText::FromString(TEXT("Return to the expedition")));
	if (SettingsButton) SettingsButton->SetToolTipText(FText::FromString(TEXT("Configure display and performance")));
	if (ReturnToTitleButton) ReturnToTitleButton->SetToolTipText(FText::FromString(TEXT("Leave this expedition and return to the title screen")));
	StatusText = AddText(TEXT("StatusText"), TEXT("ESC  RESUME"), 11, FLinearColor(0.48f, 0.58f, 0.62f));
	Stack->AddChildToVerticalBox(StatusText);
}

void UProgressionMenuWidget::OpenMenu()
{
	if (bIsMenuOpen)
		return;

	bIsMenuOpen = true;
	DisarmReturnToTitle();
	SetVisibility(ESlateVisibility::Visible);
	SetIsFocusable(true);

	if (SkillTreeWidget)
	{
		SkillTreeWidget->RefreshSkillTree();
	}

	// Show mouse cursor
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->bShowMouseCursor = true;
		PC->SetInputMode(FInputModeGameAndUI());
	}
	if (GetWorld() && GetWorld()->GetNetMode() == NM_Standalone) UGameplayStatics::SetGamePaused(GetWorld(), true);
	if (CloseButton) CloseButton->SetKeyboardFocus();
}

void UProgressionMenuWidget::CloseMenu()
{
	DismissSettingsMenu();
	DisarmReturnToTitle();
	bIsMenuOpen = false;
	SetVisibility(ESlateVisibility::Hidden);

	// Hide mouse cursor
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->bShowMouseCursor = false;
		PC->SetInputMode(FInputModeGameOnly());
	}
	if (GetWorld() && GetWorld()->GetNetMode() == NM_Standalone) UGameplayStatics::SetGamePaused(GetWorld(), false);
}

void UProgressionMenuWidget::ToggleMenu()
{
	if (bIsMenuOpen)
	{
		CloseMenu();
	}
	else
	{
		OpenMenu();
	}
}

void UProgressionMenuWidget::OnCloseButtonClicked()
{
	CloseMenu();
}

void UProgressionMenuWidget::OnSettingsClicked()
{
	if (!GetOwningPlayer()) return;
	if (SettingsMenu)
	{
		SettingsMenu->SetKeyboardFocus();
		return;
	}
	SetVisibility(ESlateVisibility::Hidden);
	SettingsMenu = CreateWidget<USettingsMenuWidget>(GetOwningPlayer(), USettingsMenuWidget::StaticClass());
	if (SettingsMenu)
	{
		SettingsMenu->AddToViewport(250);
		SettingsMenu->OnBackRequested.AddDynamic(this, &UProgressionMenuWidget::OnSettingsBack);
	}
}

void UProgressionMenuWidget::OnSettingsBack()
{
	DismissSettingsMenu();
	SetVisibility(ESlateVisibility::Visible);
	if (CloseButton) CloseButton->SetKeyboardFocus();
}

void UProgressionMenuWidget::OnReturnToTitleClicked()
{
	if (!bReturnToTitleArmed)
	{
		bReturnToTitleArmed = true;
		if (StatusText) StatusText->SetText(FText::FromString(TEXT("PRESS RETURN TO TITLE AGAIN TO CONFIRM")));
		if (GetWorld()) GetWorld()->GetTimerManager().SetTimer(ReturnToTitleTimer, this, &UProgressionMenuWidget::DisarmReturnToTitle, 4.0f, false);
		return;
	}
	if (GetWorld()) UGameplayStatics::SetGamePaused(GetWorld(), false);
	UGameplayStatics::OpenLevel(this, FName(TEXT("/Game/UI/MainMenu")));
}

void UProgressionMenuWidget::DisarmReturnToTitle()
{
	bReturnToTitleArmed = false;
	if (StatusText) StatusText->SetText(FText::FromString(TEXT("ESC  RESUME")));
}

void UProgressionMenuWidget::DismissSettingsMenu()
{
	if (!SettingsMenu) return;
	SettingsMenu->OnBackRequested.RemoveDynamic(this, &UProgressionMenuWidget::OnSettingsBack);
	SettingsMenu->RemoveFromParent();
	SettingsMenu = nullptr;
}

FReply UProgressionMenuWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Left || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (SettingsMenu)
		{
			OnSettingsBack();
		}
		else
		{
			CloseMenu();
		}
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
