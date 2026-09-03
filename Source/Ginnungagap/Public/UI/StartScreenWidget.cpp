#include "UI/StartScreenWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Spacer.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "TimerManager.h"
#include "Meta/ExpeditionRunSave.h"
#include "Engine/Texture2D.h"
#include "Input/Reply.h"
#include "UI/MenuVisualStyle.h"

void UStartScreenWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	// A designer tree that binds none of the widgets this class knows about is a tree with nothing
	// in it: the widget existed, was added to the viewport, and showed the game underneath. WBP_
	// StartScreen is exactly that -- an empty canvas over this class -- so the native layout is the
	// title screen, and an empty Blueprint root must not be allowed to suppress it.
	if (WidgetTree && WidgetTree->RootWidget && !NewGameButton && !ContinueButton && !TitleText && !QuitButton)
	{
		WidgetTree->RootWidget = nullptr;
	}
	BuildFallbackLayout();
	bTitleGateActive = bRequireTitleGate;
	if (MenuPanel) MenuPanel->SetVisibility(bTitleGateActive ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
	if (TitleGate) TitleGate->SetVisibility(bTitleGateActive ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	if (TitleText) TitleText->SetText(FText::FromString(TEXT("GINNUNGAGAP")));
	if (VersionText)
	{
		VersionText->SetText(FText::FromString(TEXT("BUILD 0.1 // PROTOTYPE\n\u00a9 2026 Skald and Stone LLC")));
		VersionText->SetFont(FSlateFontInfo(VersionText->GetFont().FontObject, 12));
		VersionText->SetColorAndOpacity(FSlateColor(FLinearColor(0.70f, 0.80f, 0.79f, 1.0f)));
	}
	if (NewGameButton) NewGameButton->OnClicked.AddDynamic(this, &UStartScreenWidget::OnNewGameClicked);
	if (ContinueButton)
	{
		ContinueButton->OnClicked.AddDynamic(this, &UStartScreenWidget::OnContinueClicked);
		UpdateContinueButtonState();
	}
	if (SettingsButton) SettingsButton->OnClicked.AddDynamic(this, &UStartScreenWidget::OnSettingsClicked);
	if (QuitButton) QuitButton->OnClicked.AddDynamic(this, &UStartScreenWidget::HandleQuitClicked);
	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->bShowMouseCursor = true;
		PC->SetInputMode(FInputModeUIOnly());
	}
	SetIsFocusable(true);
	IntroElapsed = 0.0f;
	AmbientElapsed = 0.0f;
	SetRenderOpacity(0.0f);
	if (MenuPanel) MenuPanel->SetRenderTranslation(FVector2D(-34.0f, 0.0f));
	if (!bAnimateBackground)
	{
		if (BackdropImage) BackdropImage->SetRenderScale(FVector2D(1.0f));
		if (BackdropGlowImage) BackdropGlowImage->SetRenderOpacity(0.0f);
		if (AccentRail) AccentRail->SetRenderOpacity(0.8f);
	}
	if (!bTitleGateActive && NewGameButton) NewGameButton->SetKeyboardFocus();
}

void UStartScreenWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// The menu manager sets the title gate between CreateWidget and AddToViewport, after the
	// tree was built at initialisation; apply it here, where it is final.
	bTitleGateActive = bRequireTitleGate;
	if (MenuPanel) MenuPanel->SetVisibility(bTitleGateActive ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
	if (TitleGate) TitleGate->SetVisibility(bTitleGateActive ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	// Focus needs the Slate tree, which exists only once the widget is constructed.
	if (!bTitleGateActive && NewGameButton) NewGameButton->SetKeyboardFocus();
}

void UStartScreenWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	IntroElapsed = FMath::Min(IntroElapsed + InDeltaTime, 0.75f);
	const float IntroAlpha = FMath::InterpEaseOut(0.0f, 1.0f, IntroElapsed / 0.75f, 2.0f);
	SetRenderOpacity(IntroAlpha);
	if (MenuPanel)
	{
		MenuPanel->SetRenderTranslation(FVector2D(FMath::Lerp(-34.0f, 0.0f, IntroAlpha), 0.0f));
	}

	if (!bAnimateBackground) return;
	AmbientElapsed += InDeltaTime;
	const float Motion = FMath::Clamp(BackgroundMotionStrength, 0.0f, 1.0f);
	if (BackdropImage)
	{
		const float DriftX = FMath::Sin(AmbientElapsed * 0.055f) * 18.0f * Motion;
		const float DriftY = FMath::Cos(AmbientElapsed * 0.043f) * 8.0f * Motion;
		const float Scale = 1.045f + FMath::Sin(AmbientElapsed * 0.037f) * 0.012f * Motion;
		BackdropImage->SetRenderTranslation(FVector2D(DriftX, DriftY));
		BackdropImage->SetRenderScale(FVector2D(Scale));
	}
	if (BackdropGlowImage)
	{
		const float Pulse = 0.075f + (0.035f * (0.5f + 0.5f * FMath::Sin(AmbientElapsed * 0.72f)));
		BackdropGlowImage->SetRenderOpacity(Pulse * Motion);
		BackdropGlowImage->SetRenderScale(FVector2D(1.06f + 0.008f * FMath::Sin(AmbientElapsed * 0.41f)));
	}
	if (AccentRail)
	{
		AccentRail->SetRenderOpacity(0.62f + 0.28f * (0.5f + 0.5f * FMath::Sin(AmbientElapsed * 1.15f)));
	}
	// The title's emissive layer breathes: cores and haze swell and settle on a slow cycle, the
	// way the hosts' glow lights do, with an occasional deeper dip so it never reads as a loop.
	// The plate itself does not move. Matter is still; the organism in it is not.
	if (TitleGlow)
	{
		const float Breath = 0.5f + 0.5f * FMath::Sin(AmbientElapsed * 0.55f);
		const float Dip = FMath::Fmod(AmbientElapsed, 17.0f) < 0.35f ? 0.45f : 1.0f;
		TitleGlow->SetRenderOpacity((0.42f + 0.5f * Breath) * Dip * Motion + 0.3f * (1.0f - Motion));
		TitleGlow->SetRenderScale(FVector2D(1.0f + 0.012f * Breath * Motion));
	}

	if (EmergencyLamp)
	{
		// A hard step, not a fade: an alarm lamp, not a breath.
		EmergencyLamp->SetRenderOpacity(FMath::Fmod(AmbientElapsed, 1.2f) < 0.6f ? 1.0f : 0.25f);
	}
	if (EmergencyTicker)
	{
		// The readout is written twice so the slide wraps without a gap.
		const float Loop = FMath::Max(1.0f, EmergencyTicker->GetDesiredSize().X * 0.5f);
		EmergencyTicker->SetRenderTranslation(FVector2D(-FMath::Fmod(AmbientElapsed * 42.0f, Loop), 0.0f));
	}
}

void UStartScreenWidget::NativeDestruct()
{
	if (NewGameButton) NewGameButton->OnClicked.RemoveDynamic(this, &UStartScreenWidget::OnNewGameClicked);
	if (ContinueButton) ContinueButton->OnClicked.RemoveDynamic(this, &UStartScreenWidget::OnContinueClicked);
	if (SettingsButton) SettingsButton->OnClicked.RemoveDynamic(this, &UStartScreenWidget::OnSettingsClicked);
	if (QuitButton) QuitButton->OnClicked.RemoveDynamic(this, &UStartScreenWidget::HandleQuitClicked);
	if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(QuitArmTimer);
	if (GetWorld()) GetWorld()->GetTimerManager().ClearTimer(NewGameArmTimer);
	Super::NativeDestruct();
}

FReply UStartScreenWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (bTitleGateActive)
	{
		ActivateMainMenu();
		return FReply::Handled();
	}
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Left || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (bQuitArmed || bNewGameArmed)
		{
			DisarmQuit();
			DisarmNewGame();
			return FReply::Handled();
		}
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply UStartScreenWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (bTitleGateActive)
	{
		ActivateMainMenu();
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UStartScreenWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	const FLinearColor StartVoidBlack(0.002f, 0.004f, 0.005f, 1.0f);
	const FLinearColor StartPanelBlack(0.012f, 0.017f, 0.018f, 0.985f);
	const FLinearColor StartIceBlue(0.25f, 0.58f, 0.58f, 1.0f);
	const FLinearColor StartAmber(0.74f, 0.29f, 0.075f, 1.0f);
	const FLinearColor StartSteel(0.34f, 0.40f, 0.39f, 1.0f);
	const FLinearColor StartWhite(0.70f, 0.80f, 0.79f, 1.0f);

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("StartScreenRoot"));
	WidgetTree->RootWidget = Canvas;
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("VoidBackground"));
	Background->SetBrushColor(StartVoidBlack);
	UCanvasPanelSlot* BackgroundSlot = Canvas->AddChildToCanvas(Background);
	BackgroundSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
	BackgroundSlot->SetOffsets(FMargin(0.0f));
	BackdropImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("CinematicBackdrop"));
	if (UTexture2D* BackdropTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Textures/T_MainMenu_Backdrop.T_MainMenu_Backdrop")))
	{
		BackdropImage->SetBrushFromTexture(BackdropTexture, true);
		BackdropImage->SetColorAndOpacity(FLinearColor(0.34f, 0.39f, 0.39f, 1.0f));
	}
	BackdropImage->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	BackdropImage->SetRenderScale(FVector2D(1.045f));
	UCanvasPanelSlot* BackdropSlot = Canvas->AddChildToCanvas(BackdropImage);
	BackdropSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
	BackdropSlot->SetOffsets(FMargin(0.0f));
	BackdropGlowImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("CinematicGlowPass"));
	if (UTexture2D* GlowTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Textures/T_MainMenu_Backdrop.T_MainMenu_Backdrop")))
	{
		BackdropGlowImage->SetBrushFromTexture(GlowTexture, true);
		BackdropGlowImage->SetColorAndOpacity(FLinearColor(0.56f, 0.10f, 0.035f, 1.0f));
	}
	BackdropGlowImage->SetRenderOpacity(0.08f);
	BackdropGlowImage->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	UCanvasPanelSlot* GlowSlot = Canvas->AddChildToCanvas(BackdropGlowImage);
	GlowSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
	GlowSlot->SetOffsets(FMargin(0.0f));
	AccentRail = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("AccentRail"));
	AccentRail->SetBrushColor(StartAmber);
	UCanvasPanelSlot* RailSlot = Canvas->AddChildToCanvas(AccentRail);
	RailSlot->SetAnchors(FAnchors(0.0f, 0.0f, 0.0f, 1.0f));
	RailSlot->SetOffsets(FMargin(0.0f, 0.0f, 4.0f, 0.0f));

	// Vignette, approximated with two shade bands: the backdrop is a plate for the type, and UMG
	// has no gradient brush without a material.
	auto AddShade = [this, Canvas](const TCHAR* Name, const FAnchors& Anchors, const FLinearColor& Color)
	{
		UBorder* Shade = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), Name);
		Shade->SetBrushColor(Color);
		Shade->SetVisibility(ESlateVisibility::HitTestInvisible);
		UCanvasPanelSlot* ShadeSlot = Canvas->AddChildToCanvas(Shade);
		ShadeSlot->SetAnchors(Anchors);
		ShadeSlot->SetOffsets(FMargin(0.0f));
	};
	AddShade(TEXT("ShadeLeft"), FAnchors(0.0f, 0.0f, 0.34f, 1.0f), FLinearColor(0.008f, 0.014f, 0.018f, 0.30f));
	AddShade(TEXT("ShadeBottom"), FAnchors(0.0f, 0.72f, 1.0f, 1.0f), FLinearColor(0.008f, 0.014f, 0.018f, 0.55f));

	// The emergency strip: the ship's readout along the floor of the frame, and the only red on
	// the screen. Same red the lights come back in when the main bus is restored.
	EmergencyStrip = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("EmergencyStrip"));
	EmergencyStrip->SetBrushColor(FLinearColor(0.35f, 0.08f, 0.03f, 0.90f));
	EmergencyStrip->SetPadding(FMargin(18.0f, 0.0f));
	EmergencyStrip->SetVerticalAlignment(VAlign_Center);
	EmergencyStrip->SetVisibility(ESlateVisibility::HitTestInvisible);
	EmergencyStrip->SetClipping(EWidgetClipping::ClipToBounds);
	UCanvasPanelSlot* StripSlot = Canvas->AddChildToCanvas(EmergencyStrip);
	StripSlot->SetAnchors(FAnchors(0.0f, 1.0f, 1.0f, 1.0f));
	StripSlot->SetAlignment(FVector2D(0.0f, 1.0f));
	StripSlot->SetOffsets(FMargin(0.0f, 0.0f, 0.0f, 26.0f));
	UHorizontalBox* StripRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("EmergencyRow"));
	EmergencyStrip->SetContent(StripRow);
	EmergencyLamp = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("EmergencyLamp"));
	EmergencyLamp->SetBrushColor(FLinearColor(1.0f, 0.16f, 0.06f, 1.0f));
	UHorizontalBoxSlot* LampSlot = StripRow->AddChildToHorizontalBox(EmergencyLamp);
	LampSlot->SetPadding(FMargin(0.0f, 9.0f, 16.0f, 9.0f));
	LampSlot->SetVerticalAlignment(VAlign_Fill);
	USpacer* LampWidth = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	LampWidth->SetSize(FVector2D(8.0f, 8.0f));
	EmergencyLamp->SetContent(LampWidth);
	EmergencyTicker = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("EmergencyTicker"));
	const TCHAR* Readout = TEXT("MAIN BUS: EMERGENCY POWER   ·   DECK 3 AFT: UNKNOWN BIOMASS SIGNATURE   ·   HULL BREACH SEALED   ·   CIC ONLINE   ·   ");
	EmergencyTicker->SetText(FText::FromString(FString(Readout) + Readout));
	EmergencyTicker->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.70f, 0.64f, 1.0f)));
	FSlateFontInfo TickerFont(EmergencyTicker->GetFont().FontObject, 10);
	TickerFont.LetterSpacing = 200;
	EmergencyTicker->SetFont(TickerFont);
	EmergencyTicker->SetClipping(EWidgetClipping::ClipToBounds);
	UHorizontalBoxSlot* TickerSlot = StripRow->AddChildToHorizontalBox(EmergencyTicker);
	TickerSlot->SetVerticalAlignment(VAlign_Center);

	TitleGate = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("TitleGate"));
	TitleGate->SetBrushColor(FLinearColor(0.004f, 0.010f, 0.016f, 0.38f));
	TitleGate->SetPadding(FMargin(48.0f));
	UCanvasPanelSlot* GateSlot = Canvas->AddChildToCanvas(TitleGate);
	GateSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
	GateSlot->SetOffsets(FMargin(0.0f));
	UVerticalBox* GateStack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("TitleGateStack"));
	TitleGate->SetContent(GateStack);
	// The title: a baked plate of the word in ceramic plating the Bloom has taken left to right,
	// and its emissive layer over it. Built from the threat family's layering by
	// tools/build_title_bloom_plate.py, so the word is drawn with the same materials as the hosts.
	UTexture2D* PlateTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Textures/T_Title_Ginnungagap_Plate.T_Title_Ginnungagap_Plate"));
	UTexture2D* GlowTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Textures/T_Title_Ginnungagap_Glow.T_Title_Ginnungagap_Glow"));
	UOverlay* TitleStack = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(), TEXT("GateTitleStack"));
	if (PlateTexture)
	{
		// 2400 x 640 baked; shown at half, which is the size the type was drawn for at 1080p.
		const FVector2D Shown(1200.0f, 320.0f);
		TitlePlate = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("GateTitlePlate"));
		// Sized through the brush, which the widget keeps: SetDesiredSizeOverride only reaches a
		// live SImage, and this tree is built before Slate exists, so it left the plate at 32x32.
		TitlePlate->SetBrushFromTexture(PlateTexture, true);
		{ FSlateBrush PlateBrush = TitlePlate->GetBrush(); PlateBrush.ImageSize = Shown; TitlePlate->SetBrush(PlateBrush); }
		TitlePlate->SetRenderTransformPivot(FVector2D(0.5f, 0.7f));
		UOverlaySlot* PlateSlot = TitleStack->AddChildToOverlay(TitlePlate);
		PlateSlot->SetHorizontalAlignment(HAlign_Center);
		PlateSlot->SetVerticalAlignment(VAlign_Center);
		if (GlowTexture)
		{
			TitleGlow = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("GateTitleGlow"));
			TitleGlow->SetBrushFromTexture(GlowTexture, true);
			{ FSlateBrush GlowBrush = TitleGlow->GetBrush(); GlowBrush.ImageSize = Shown; TitleGlow->SetBrush(GlowBrush); }
			TitleGlow->SetRenderTransformPivot(FVector2D(0.5f, 0.7f));
			TitleGlow->SetRenderOpacity(0.7f);
			UOverlaySlot* TitleGlowSlot = TitleStack->AddChildToOverlay(TitleGlow);
			TitleGlowSlot->SetHorizontalAlignment(HAlign_Center);
			TitleGlowSlot->SetVerticalAlignment(VAlign_Center);
		}
	}
	else
	{
		TitleFallbackText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("GateTitleText"));
		TitleFallbackText->SetText(FText::FromString(TEXT("GINNUNGAGAP")));
		TitleFallbackText->SetJustification(ETextJustify::Center);
		TitleFallbackText->SetColorAndOpacity(FSlateColor(StartWhite));
		FSlateFontInfo GateTitleFont(TitleFallbackText->GetFont().FontObject, 64);
		GateTitleFont.LetterSpacing = 220;
		TitleFallbackText->SetFont(GateTitleFont);
		TitleStack->AddChildToOverlay(TitleFallbackText);
	}
	UVerticalBoxSlot* GateTitleSlot = GateStack->AddChildToVerticalBox(TitleStack);
	GateTitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	GateTitleSlot->SetVerticalAlignment(VAlign_Bottom);
	GateTitleSlot->SetHorizontalAlignment(HAlign_Center);
	UTextBlock* GatePrompt = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("GatePromptText"));
	GatePrompt->SetText(FText::FromString(TEXT("WAKE SIGNAL DETECTED // PRESS ANY KEY")));
	GatePrompt->SetJustification(ETextJustify::Center);
	GatePrompt->SetColorAndOpacity(FSlateColor(StartIceBlue));
	FSlateFontInfo GatePromptFont(GatePrompt->GetFont().FontObject, 13);
	GatePromptFont.LetterSpacing = 180;
	GatePrompt->SetFont(GatePromptFont);
	UVerticalBoxSlot* GatePromptSlot = GateStack->AddChildToVerticalBox(GatePrompt);
	GatePromptSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	GatePromptSlot->SetVerticalAlignment(VAlign_Top);
	GatePromptSlot->SetPadding(FMargin(0.0f, 34.0f, 0.0f, 0.0f));

	MenuPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("MenuPanel"));
	MenuPanel->SetBrushColor(StartPanelBlack);
	FSlateBrush TerminalPanelBrush;
	TerminalPanelBrush.DrawAs = ESlateBrushDrawType::RoundedBox;
	TerminalPanelBrush.TintColor = FSlateColor(StartPanelBlack);
	TerminalPanelBrush.OutlineSettings.CornerRadii = FVector4(3.0f, 3.0f, 3.0f, 3.0f);
	TerminalPanelBrush.OutlineSettings.Width = 2.0f;
	TerminalPanelBrush.OutlineSettings.Color = FSlateColor(FLinearColor(0.22f, 0.29f, 0.29f, 0.92f));
	MenuPanel->SetBrush(TerminalPanelBrush);
	MenuPanel->SetPadding(FMargin(56.0f, 42.0f));
	UCanvasPanelSlot* PanelSlot = Canvas->AddChildToCanvas(MenuPanel);
	PanelSlot->SetAnchors(FAnchors(0.075f, 0.5f));
	PanelSlot->SetAlignment(FVector2D(0.0f, 0.5f));
	PanelSlot->SetSize(FVector2D(520.0f, 650.0f));
	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("MenuStack"));
	MenuPanel->SetContent(Stack);

	auto AddText = [this, Stack](const TCHAR* Name, const TCHAR* Copy, const FLinearColor& Color, int32 Size)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetText(FText::FromString(Copy));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
		Stack->AddChildToVerticalBox(Text);
		return Text;
	};
	UTextBlock* Eyebrow = AddText(TEXT("EyebrowText"), TEXT("DERELICT RECOVERY INTERFACE // NODE 01"), StartAmber, 12);
	FSlateFontInfo EyebrowFont = Eyebrow->GetFont();
	EyebrowFont.LetterSpacing = 180;
	Eyebrow->SetFont(EyebrowFont);
	TitleText = AddText(TEXT("TitleText"), TEXT("GINNUNGAGAP"), StartWhite, 42);
	FSlateFontInfo TitleFont = TitleText->GetFont();
	TitleFont.LetterSpacing = 80;
	TitleText->SetFont(TitleFont);
	if (UVerticalBoxSlot* TitleBoxSlot = Cast<UVerticalBoxSlot>(TitleText->Slot)) TitleBoxSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 2.0f));
	AddText(TEXT("SubtitleText"), TEXT("CRYO ARRAY SIGNAL LOST"), StartSteel, 15);
	UTextBlock* Warning = AddText(TEXT("TerminalWarningText"), TEXT("CREW TELEMETRY: 01 RESPONSE // ORIGIN UNKNOWN"), FLinearColor(0.54f, 0.12f, 0.055f, 1.0f), 10);
	FSlateFontInfo WarningFont = Warning->GetFont();
	WarningFont.LetterSpacing = 100;
	Warning->SetFont(WarningFont);
	if (UVerticalBoxSlot* WarningSlot = Cast<UVerticalBoxSlot>(Warning->Slot)) WarningSlot->SetPadding(FMargin(0.0f, 9.0f, 0.0f, 0.0f));
	USpacer* Gap = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	Gap->SetSize(FVector2D(1.0f, 62.0f));
	Stack->AddChildToVerticalBox(Gap);

	auto AddMenuButton = [this, Stack, StartWhite, StartAmber](const TCHAR* Name, const TCHAR* Index, const TCHAR* Label, UButton*& OutButton, bool bPrimary)
	{
		OutButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
		GinnungagapMenuStyle::ApplyButton(OutButton, bPrimary);
		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UTextBlock* Number = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Number->SetText(FText::FromString(Index));
		Number->SetColorAndOpacity(FSlateColor(StartAmber));
		Number->SetFont(FSlateFontInfo(Number->GetFont().FontObject, 11));
		UHorizontalBoxSlot* NumberSlot = Row->AddChildToHorizontalBox(Number);
		NumberSlot->SetPadding(FMargin(0.0f, 3.0f, 18.0f, 0.0f));
		UTextBlock* LabelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		LabelText->SetText(FText::FromString(Label));
		LabelText->SetColorAndOpacity(FSlateColor(StartWhite));
		FSlateFontInfo LabelFont(LabelText->GetFont().FontObject, 17);
		LabelFont.LetterSpacing = 110;
		LabelText->SetFont(LabelFont);
		Row->AddChildToHorizontalBox(LabelText);
		OutButton->AddChild(Row);
		UVerticalBoxSlot* Slot = Stack->AddChildToVerticalBox(OutButton);
		Slot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 10.0f));
	};
	AddMenuButton(TEXT("NewGameButton"), TEXT("01"), TEXT("NEW EXPEDITION"), NewGameButton, true);
	AddMenuButton(TEXT("ContinueButton"), TEXT("02"), TEXT("CONTINUE"), ContinueButton, false);
	AddMenuButton(TEXT("SettingsButton"), TEXT("03"), TEXT("SYSTEM SETTINGS"), SettingsButton, false);
	AddMenuButton(TEXT("QuitButton"), TEXT("04"), TEXT("EXIT TO DESKTOP"), QuitButton, false);

	USpacer* FooterGap = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	FooterGap->SetSize(FVector2D(1.0f, 24.0f));
	Stack->AddChildToVerticalBox(FooterGap);
	UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Footer"));
	Stack->AddChildToVerticalBox(Footer);
	StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StatusText"));
	StatusText->SetText(FText::FromString(TEXT("SHIPNET // NO RESPONSE")));
	StatusText->SetColorAndOpacity(FSlateColor(StartAmber));
	StatusText->SetFont(FSlateFontInfo(StatusText->GetFont().FontObject, 10));
	UHorizontalBoxSlot* StatusSlot = Footer->AddChildToHorizontalBox(StatusText);
	StatusSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	VersionText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("VersionText"));
	VersionText->SetText(FText::FromString(TEXT("BUILD 0.1 // PROTOTYPE")));
	VersionText->SetColorAndOpacity(FSlateColor(StartSteel));
	VersionText->SetJustification(ETextJustify::Right);
	VersionText->SetFont(FSlateFontInfo(VersionText->GetFont().FontObject, 10));
	Footer->AddChildToHorizontalBox(VersionText);
}

void UStartScreenWidget::ActivateMainMenu()
{
	if (!bTitleGateActive) return;
	bTitleGateActive = false;
	if (TitleGate) TitleGate->SetVisibility(ESlateVisibility::Collapsed);
	if (MenuPanel)
	{
		MenuPanel->SetVisibility(ESlateVisibility::Visible);
		MenuPanel->SetRenderTranslation(FVector2D(-34.0f, 0.0f));
	}
	IntroElapsed = 0.0f;
	if (NewGameButton) NewGameButton->SetKeyboardFocus();
	OnTitleGateCompleted.Broadcast();
}

void UStartScreenWidget::SetStatusMessage(const FText& Message, bool bIsError)
{
	if (StatusText)
	{
		StatusText->SetText(Message);
		StatusText->SetColorAndOpacity(FSlateColor(bIsError ? FLinearColor(1.0f, 0.32f, 0.18f, 1.0f) : FLinearColor(0.30f, 0.86f, 1.0f, 1.0f)));
	}
}

void UStartScreenWidget::OnNewGameClicked()
{
	if (UGameplayStatics::DoesSaveGameExist(TEXT("GinnungagapRunSave"), 0) && !bNewGameArmed)
	{
		bNewGameArmed = true;
		SetStatusMessage(FText::FromString(TEXT("PRESS NEW EXPEDITION AGAIN TO REPLACE ACTIVE RUN")), true);
		if (NewGameButton) NewGameButton->SetToolTipText(FText::FromString(TEXT("Confirm starting a new expedition.")));
		if (GetWorld()) GetWorld()->GetTimerManager().SetTimer(NewGameArmTimer, this, &UStartScreenWidget::DisarmNewGame, 4.0f, false);
		return;
	}
	OnStartGameClicked.Broadcast();
}
void UStartScreenWidget::OnContinueClicked() { OnContinueGameClicked.Broadcast(); }
void UStartScreenWidget::OnSettingsClicked() { OnSettingsRequested.Broadcast(); }
void UStartScreenWidget::HandleQuitClicked()
{
	if (!bQuitArmed)
	{
		bQuitArmed = true;
		SetStatusMessage(FText::FromString(TEXT("PRESS EXIT AGAIN TO CONFIRM")), true);
		if (QuitButton) QuitButton->SetToolTipText(FText::FromString(TEXT("Press again within 3 seconds to exit.")));
		if (GetWorld()) GetWorld()->GetTimerManager().SetTimer(QuitArmTimer, this, &UStartScreenWidget::DisarmQuit, 3.0f, false);
		return;
	}
	OnQuitClicked.Broadcast();
	UKismetSystemLibrary::QuitGame(GetWorld(), nullptr, EQuitPreference::Quit, true);
}

void UStartScreenWidget::DisarmQuit()
{
	bQuitArmed = false;
	SetStatusMessage(FText::FromString(TEXT("SHIPNET // NO RESPONSE")), true);
	if (QuitButton) QuitButton->SetToolTipText(FText::FromString(TEXT("Exit to desktop")));
}

void UStartScreenWidget::DisarmNewGame()
{
	bNewGameArmed = false;
	if (NewGameButton) NewGameButton->SetToolTipText(FText::FromString(TEXT("Begin a new expedition")));
	UpdateContinueButtonState();
}

void UStartScreenWidget::UpdateContinueButtonState()
{
	const UExpeditionRunSave* LoadedSave = Cast<UExpeditionRunSave>(UGameplayStatics::LoadGameFromSlot(TEXT("GinnungagapRunSave"), 0));
	const bool bHasSave = LoadedSave != nullptr;
	if (ContinueButton)
	{
		ContinueButton->SetIsEnabled(bHasSave);
		FText ContinueTip = FText::FromString(TEXT("No expedition save found"));
		if (bHasSave)
		{
			ContinueTip = FText::FromString(TEXT("Resume the latest expedition"));
			if (const UExpeditionRunSave* Save = LoadedSave)
			{
				const FString SavedAt = Save->SavedAtUtc.GetTicks() > 0 ? Save->SavedAtUtc.ToString(TEXT("%Y-%m-%d %H:%M UTC")) : TEXT("UNKNOWN TIME");
				ContinueTip = FText::FromString(FString::Printf(TEXT("Resume expedition saved %s"), *SavedAt));
				SetStatusMessage(FText::FromString(FString::Printf(TEXT("ACTIVE EXPEDITION // %s"), *SavedAt)), false);
			}
		}
		ContinueButton->SetToolTipText(ContinueTip);
	}
}
