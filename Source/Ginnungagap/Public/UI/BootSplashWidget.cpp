#include "UI/BootSplashWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Input/Reply.h"

void UBootSplashWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();
	ElapsedSeconds = 0.0f;
	bSkipRequested = false;
	bCompleted = false;
	SetIsFocusable(true);
	SetKeyboardFocus();
}

void UBootSplashWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	ElapsedSeconds += InDeltaTime;

	const float FadeIn = FMath::Clamp(ElapsedSeconds / 0.55f, 0.0f, 1.0f);
	const float FadeOut = ElapsedSeconds > AutomaticAdvanceSeconds - 0.45f
		? FMath::Clamp((AutomaticAdvanceSeconds - ElapsedSeconds) / 0.45f, 0.0f, 1.0f) : 1.0f;
	if (IdentityPanel) IdentityPanel->SetRenderOpacity(FMath::Min(FadeIn, FadeOut));

	if ((bSkipRequested && ElapsedSeconds >= MinimumDisplaySeconds) || ElapsedSeconds >= AutomaticAdvanceSeconds)
	{
		Complete();
	}
}

FReply UBootSplashWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	RequestSkip();
	return FReply::Handled();
}

FReply UBootSplashWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	RequestSkip();
	return FReply::Handled();
}

void UBootSplashWidget::RequestSkip()
{
	bSkipRequested = true;
	if (SkipText) SkipText->SetText(FText::FromString(TEXT("INITIALIZING CREW TERMINAL...")));
}

void UBootSplashWidget::Complete()
{
	if (bCompleted) return;
	bCompleted = true;
	OnFinished.Broadcast();
}

void UBootSplashWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;

	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), TEXT("BootRoot"));
	WidgetTree->RootWidget = Root;
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("BootBackground"));
	Background->SetBrushColor(FLinearColor(0.003f, 0.007f, 0.011f, 1.0f));
	Root->AddChildToOverlay(Background);

	IdentityPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("IdentityPanel"));
	IdentityPanel->SetBrushColor(FLinearColor::Transparent);
	IdentityPanel->SetPadding(FMargin(36.0f));
	UOverlaySlot* PanelSlot = Root->AddChildToOverlay(IdentityPanel);
	PanelSlot->SetHorizontalAlignment(HAlign_Center);
	PanelSlot->SetVerticalAlignment(VAlign_Center);

	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("IdentityStack"));
	IdentityPanel->SetContent(Stack);
	auto AddText = [this, Stack](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetText(FText::FromString(Copy));
		Text->SetJustification(ETextJustify::Center);
		Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Stack->AddChildToVerticalBox(Text);
		return Text;
	};
	UTextBlock* Studio = AddText(TEXT("StudioText"), TEXT("GINNUNGAGAP PROJECT"), 28, FLinearColor(0.88f, 0.94f, 0.95f));
	FSlateFontInfo StudioFont = Studio->GetFont();
	StudioFont.LetterSpacing = 160;
	Studio->SetFont(StudioFont);
	UTextBlock* Warning = AddText(TEXT("WarningText"), TEXT("INTENSE THEMES  //  FLASHING LIGHTS  //  ONLINE INTERACTIONS"), 11, FLinearColor(0.48f, 0.58f, 0.62f));
	if (UVerticalBoxSlot* WarningSlot = Cast<UVerticalBoxSlot>(Warning->Slot)) WarningSlot->SetPadding(FMargin(0, 18, 0, 0));
	SkipText = AddText(TEXT("SkipText"), TEXT("PRESS ANY KEY TO CONTINUE"), 11, FLinearColor(0.30f, 0.86f, 1.0f));
	if (UVerticalBoxSlot* SkipSlot = Cast<UVerticalBoxSlot>(SkipText->Slot)) SkipSlot->SetPadding(FMargin(0, 48, 0, 0));
}
