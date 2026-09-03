#include "UI/SettingsMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/GameUserSettings.h"
#include "Input/Reply.h"
#include "TimerManager.h"

namespace
{
	const FLinearColor IceBlue(0.30f, 0.86f, 1.0f, 1.0f);
	const FLinearColor White(0.88f, 0.94f, 0.95f, 1.0f);
	const FLinearColor Steel(0.48f, 0.58f, 0.62f, 1.0f);
}

void USettingsMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildFallbackLayout();
	if (QualitySlider) QualitySlider->OnValueChanged.AddDynamic(this, &USettingsMenuWidget::OnQualityChanged);
	if (ResolutionScaleSlider) ResolutionScaleSlider->OnValueChanged.AddDynamic(this, &USettingsMenuWidget::OnResolutionScaleChanged);
	if (WindowModeButton) WindowModeButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnWindowModeClicked);
	if (VSyncButton) VSyncButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnVSyncClicked);
	if (FrameRateButton) FrameRateButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnFrameRateClicked);
	if (DefaultsButton) DefaultsButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnDefaultsClicked);
	if (ApplyButton) ApplyButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnApplyClicked);
	if (BackButton) BackButton->OnClicked.AddDynamic(this, &USettingsMenuWidget::OnBackClicked);
	SetIsFocusable(true);
	LoadCurrentSettings();
	if (QualitySlider) QualitySlider->SetKeyboardFocus();
}

void USettingsMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if (QualitySlider) QualitySlider->SetKeyboardFocus();
}

void USettingsMenuWidget::NativeDestruct()
{
	if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(ConfirmationTimer);
	if (bAwaitingConfirmation) RestoreUnconfirmedSettings();
	if (QualitySlider) QualitySlider->OnValueChanged.RemoveDynamic(this, &USettingsMenuWidget::OnQualityChanged);
	if (ResolutionScaleSlider) ResolutionScaleSlider->OnValueChanged.RemoveDynamic(this, &USettingsMenuWidget::OnResolutionScaleChanged);
	if (WindowModeButton) WindowModeButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnWindowModeClicked);
	if (VSyncButton) VSyncButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnVSyncClicked);
	if (FrameRateButton) FrameRateButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnFrameRateClicked);
	if (DefaultsButton) DefaultsButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnDefaultsClicked);
	if (ApplyButton) ApplyButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnApplyClicked);
	if (BackButton) BackButton->OnClicked.RemoveDynamic(this, &USettingsMenuWidget::OnBackClicked);
	Super::NativeDestruct();
}

void USettingsMenuWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (!bAwaitingConfirmation || !StatusText || !GetWorld()) return;
	const int32 Remaining = FMath::Max(0, FMath::CeilToInt(ConfirmationDeadline - GetWorld()->GetTimeSeconds()));
	StatusText->SetText(FText::FromString(FString::Printf(TEXT("KEEP THESE SETTINGS? APPLY AGAIN  //  REVERTING IN %02ds"), Remaining)));
}

void USettingsMenuWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SettingsRoot"));
	Root->SetBrushColor(FLinearColor(0.006f, 0.012f, 0.018f, 1.0f));
	Root->SetPadding(FMargin(110.0f, 72.0f));
	WidgetTree->RootWidget = Root;
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Root->SetContent(Stack);
	auto AddText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetText(FText::FromString(Copy)); Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
		Text->SetColorAndOpacity(FSlateColor(Color)); return Text;
	};
	Stack->AddChildToVerticalBox(AddText(TEXT("SectionText"), TEXT("SHIP SYSTEMS  //  DISPLAY"), 12, IceBlue));
	UTextBlock* Heading = AddText(TEXT("HeadingText"), TEXT("SYSTEM SETTINGS"), 36, White);
	if (UVerticalBoxSlot* HeadingSlot = Stack->AddChildToVerticalBox(Heading)) HeadingSlot->SetPadding(FMargin(0, 12, 0, 48));
	auto AddSliderRow = [this, Stack, AddText](const TCHAR* Label, const TCHAR* SliderName, USlider*& Slider, const TCHAR* ValueName, UTextBlock*& Value)
	{
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		Stack->AddChildToVerticalBox(Row);
		UTextBlock* LabelText = AddText(TEXT("SettingLabel"), Label, 15, White);
		UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(LabelText); LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		Value = AddText(ValueName, TEXT(""), 14, IceBlue); Row->AddChildToHorizontalBox(Value);
		Slider = WidgetTree->ConstructWidget<USlider>(USlider::StaticClass(), SliderName);
		Slider->SetStepSize(0.25f); Slider->SetSliderBarColor(Steel); Slider->SetSliderHandleColor(IceBlue);
		if (UVerticalBoxSlot* SliderSlot = Stack->AddChildToVerticalBox(Slider)) SliderSlot->SetPadding(FMargin(0, 12, 0, 34));
	};
	AddSliderRow(TEXT("OVERALL QUALITY"), TEXT("QualitySlider"), QualitySlider, TEXT("QualityValueText"), QualityValueText);
	AddSliderRow(TEXT("RENDER SCALE"), TEXT("ResolutionScaleSlider"), ResolutionScaleSlider, TEXT("ResolutionValueText"), ResolutionValueText);
	WindowModeButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("WindowModeButton"));
	WindowModeButton->SetBackgroundColor(FLinearColor(0.04f, 0.10f, 0.12f, 1.0f));
	UHorizontalBox* WindowRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass()); WindowModeButton->AddChild(WindowRow);
	UHorizontalBoxSlot* WindowLabelSlot = WindowRow->AddChildToHorizontalBox(AddText(TEXT("WindowModeLabel"), TEXT("WINDOW MODE"), 15, White));
	WindowLabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	WindowModeValueText = AddText(TEXT("WindowModeValueText"), TEXT(""), 14, IceBlue); WindowRow->AddChildToHorizontalBox(WindowModeValueText);
	Stack->AddChildToVerticalBox(WindowModeButton);
	auto AddToggleRow = [this, Stack, AddText](const TCHAR* ButtonName, const TCHAR* Label, UButton*& Button, const TCHAR* ValueName, UTextBlock*& Value)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), ButtonName);
		Button->SetBackgroundColor(FLinearColor(0.04f, 0.10f, 0.12f, 1.0f));
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass()); Button->AddChild(Row);
		UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(AddText(TEXT("SettingLabel"), Label, 15, White));
		LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		Value = AddText(ValueName, TEXT(""), 14, IceBlue); Row->AddChildToHorizontalBox(Value);
		if (UVerticalBoxSlot* RowSlot = Stack->AddChildToVerticalBox(Button)) RowSlot->SetPadding(FMargin(0, 10, 0, 0));
	};
	AddToggleRow(TEXT("VSyncButton"), TEXT("VERTICAL SYNC"), VSyncButton, TEXT("VSyncValueText"), VSyncValueText);
	AddToggleRow(TEXT("FrameRateButton"), TEXT("FRAME RATE LIMIT"), FrameRateButton, TEXT("FrameRateValueText"), FrameRateValueText);
	StatusText = AddText(TEXT("StatusText"), TEXT("CHANGES ARE APPLIED AFTER CONFIRMATION"), 11, Steel);
	if (UVerticalBoxSlot* StatusSlot = Stack->AddChildToVerticalBox(StatusText)) StatusSlot->SetPadding(FMargin(0, 18, 0, 0));
	UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UVerticalBoxSlot* ActionsSlot = Stack->AddChildToVerticalBox(Actions)) ActionsSlot->SetPadding(FMargin(0, 52, 0, 0));
	auto AddAction = [this, Actions, AddText](const TCHAR* Name, const TCHAR* Copy, UButton*& Button, FLinearColor Color)
	{
		Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name); Button->SetBackgroundColor(Color);
		Button->AddChild(AddText(TEXT("ActionLabel"), Copy, 14, White));
		UHorizontalBoxSlot* ButtonSlot = Actions->AddChildToHorizontalBox(Button); ButtonSlot->SetPadding(FMargin(0, 0, 12, 0));
	};
	AddAction(TEXT("BackButton"), TEXT("<  DISCARD & BACK"), BackButton, FLinearColor(0.05f, 0.08f, 0.09f));
	AddAction(TEXT("DefaultsButton"), TEXT("RESTORE DEFAULTS"), DefaultsButton, FLinearColor(0.08f, 0.11f, 0.12f));
	AddAction(TEXT("ApplyButton"), TEXT("APPLY SETTINGS"), ApplyButton, FLinearColor(0.02f, 0.34f, 0.42f));
}

void USettingsMenuWidget::LoadCurrentSettings()
{
	if (UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings())
	{
		if (QualitySlider) QualitySlider->SetValue(Settings->GetOverallScalabilityLevel() / 4.0f);
		if (ResolutionScaleSlider) ResolutionScaleSlider->SetValue(Settings->GetResolutionScaleNormalized());
		bPendingVSync = Settings->IsVSyncEnabled();
		PendingFrameRateLimit = Settings->GetFrameRateLimit();
	}
	RefreshValueLabels();
}

void USettingsMenuWidget::RefreshValueLabels()
{
	static const TCHAR* QualityNames[] = { TEXT("LOW"), TEXT("MEDIUM"), TEXT("HIGH"), TEXT("EPIC"), TEXT("CINEMATIC") };
	if (QualityValueText && QualitySlider)
	{
		const int32 Index = FMath::Clamp(FMath::RoundToInt(QualitySlider->GetValue() * 4.0f), 0, 4);
		QualityValueText->SetText(FText::FromString(QualityNames[Index]));
	}
	if (ResolutionValueText && ResolutionScaleSlider)
	{
		ResolutionValueText->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(FMath::Lerp(50.0f, 100.0f, ResolutionScaleSlider->GetValue())))));
	}
	if (WindowModeValueText)
	{
		FString Label = TEXT("WINDOWED");
		if (const UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings())
		{
			if (Settings->GetFullscreenMode() == EWindowMode::Fullscreen) Label = TEXT("FULLSCREEN");
			else if (Settings->GetFullscreenMode() == EWindowMode::WindowedFullscreen) Label = TEXT("BORDERLESS");
		}
		WindowModeValueText->SetText(FText::FromString(Label));
	}
	if (VSyncValueText) VSyncValueText->SetText(FText::FromString(bPendingVSync ? TEXT("ON") : TEXT("OFF")));
	if (FrameRateValueText)
	{
		const FString Limit = PendingFrameRateLimit <= 0.0f ? TEXT("UNLIMITED") : FString::Printf(TEXT("%d FPS"), FMath::RoundToInt(PendingFrameRateLimit));
		FrameRateValueText->SetText(FText::FromString(Limit));
	}
}

void USettingsMenuWidget::OnVSyncClicked()
{
	bPendingVSync = !bPendingVSync;
	RefreshValueLabels();
}

void USettingsMenuWidget::OnFrameRateClicked()
{
	if (PendingFrameRateLimit <= 0.0f) PendingFrameRateLimit = 30.0f;
	else if (PendingFrameRateLimit <= 30.0f) PendingFrameRateLimit = 60.0f;
	else if (PendingFrameRateLimit <= 60.0f) PendingFrameRateLimit = 120.0f;
	else PendingFrameRateLimit = 0.0f;
	RefreshValueLabels();
}

void USettingsMenuWidget::OnDefaultsClicked()
{
	if (QualitySlider) QualitySlider->SetValue(0.5f);
	if (ResolutionScaleSlider) ResolutionScaleSlider->SetValue(1.0f);
	bPendingVSync = false;
	PendingFrameRateLimit = 60.0f;
	if (UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings()) Settings->SetFullscreenMode(EWindowMode::WindowedFullscreen);
	RefreshValueLabels();
}

void USettingsMenuWidget::OnQualityChanged(float Value) { RefreshValueLabels(); }
void USettingsMenuWidget::OnResolutionScaleChanged(float Value) { RefreshValueLabels(); }

void USettingsMenuWidget::OnWindowModeClicked()
{
	if (UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings())
	{
		const EWindowMode::Type Current = Settings->GetFullscreenMode();
		const EWindowMode::Type Next = Current == EWindowMode::Windowed ? EWindowMode::WindowedFullscreen : Current == EWindowMode::WindowedFullscreen ? EWindowMode::Fullscreen : EWindowMode::Windowed;
		Settings->SetFullscreenMode(Next);
		RefreshValueLabels();
	}
}

void USettingsMenuWidget::OnApplyClicked()
{
	if (UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings())
	{
		if (bAwaitingConfirmation)
		{
			bAwaitingConfirmation = false;
			if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(ConfirmationTimer);
			Settings->SaveSettings();
			OnBackRequested.Broadcast();
			return;
		}
		Settings->SetOverallScalabilityLevel(FMath::Clamp(FMath::RoundToInt(QualitySlider ? QualitySlider->GetValue() * 4.0f : 2.0f), 0, 4));
		if (ResolutionScaleSlider) Settings->SetResolutionScaleNormalized(ResolutionScaleSlider->GetValue());
		Settings->SetVSyncEnabled(bPendingVSync);
		Settings->SetFrameRateLimit(PendingFrameRateLimit);
		Settings->ApplySettings(false);
		bAwaitingConfirmation = true;
		ConfirmationDeadline = GetWorld() ? GetWorld()->GetTimeSeconds() + 12.0f : 12.0f;
		if (StatusText) StatusText->SetText(FText::FromString(TEXT("KEEP THESE SETTINGS? APPLY AGAIN  //  REVERTING IN 12s")));
		if (ApplyButton) ApplyButton->SetToolTipText(FText::FromString(TEXT("Confirm and save these settings.")));
		if (GetWorld()) GetWorld()->GetTimerManager().SetTimer(ConfirmationTimer, this, &USettingsMenuWidget::RestoreUnconfirmedSettings, 12.0f, false);
	}
}

void USettingsMenuWidget::OnBackClicked()
{
	RestoreUnconfirmedSettings();
	OnBackRequested.Broadcast();
}

void USettingsMenuWidget::RestoreUnconfirmedSettings()
{
	if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(ConfirmationTimer);
	bAwaitingConfirmation = false;
	ConfirmationDeadline = 0.0f;
	if (UGameUserSettings* Settings = UGameUserSettings::GetGameUserSettings())
	{
		Settings->LoadSettings(false);
		Settings->ApplySettings(false);
	}
	LoadCurrentSettings();
	if (StatusText) StatusText->SetText(FText::FromString(TEXT("UNCONFIRMED CHANGES REVERTED")));
	if (ApplyButton) ApplyButton->SetToolTipText(FText::FromString(TEXT("Apply settings")));
}

FReply USettingsMenuWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Gamepad_Special_Left || InKeyEvent.GetKey() == EKeys::Gamepad_FaceButton_Right)
	{
		OnBackClicked();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}
