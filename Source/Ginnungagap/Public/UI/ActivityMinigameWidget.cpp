#include "UI/ActivityMinigameWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"

namespace
{
const FLinearColor PanelBlack(0.004f, 0.012f, 0.015f, 0.94f);
const FLinearColor PanelInset(0.012f, 0.035f, 0.040f, 0.96f);
const FLinearColor Cyan(0.24f, 0.88f, 0.94f, 1.0f);
const FLinearColor Green(0.24f, 1.0f, 0.52f, 1.0f);
const FLinearColor Amber(1.0f, 0.58f, 0.10f, 1.0f);
const FLinearColor Violet(0.72f, 0.20f, 0.96f, 1.0f);
const FLinearColor Dim(0.45f, 0.58f, 0.60f, 1.0f);

UCanvasPanelSlot* Place(UCanvasPanel* Root, UWidget* Child, float X, float Y, float W, float H)
{
    UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Root->AddChild(Child));
    if (CanvasSlot)
    {
        CanvasSlot->SetPosition(FVector2D(X, Y));
        CanvasSlot->SetSize(FVector2D(W, H));
    }
    return CanvasSlot;
}

void SetTextStyle(UTextBlock* Text, int32 Size, const FLinearColor& Color)
{
    FSlateFontInfo Font = Text->GetFont();
    Font.Size = Size;
    Text->SetFont(Font);
    Text->SetColorAndOpacity(FSlateColor(Color));
}

UBorder* AddInset(UWidgetTree* Tree, UCanvasPanel* Root, const TCHAR* Name, float X, float Y, float W, float H)
{
    UBorder* Border = Tree->ConstructWidget<UBorder>(UBorder::StaticClass(), Name);
    Border->SetBrushColor(PanelInset);
    Border->SetPadding(FMargin(10.0f));
    Border->SetVisibility(ESlateVisibility::HitTestInvisible);
    Place(Root, Border, X, Y, W, H);
    return Border;
}
}

void UActivityMinigameWidget::NativeConstruct()
{
    Super::NativeConstruct();
    BuildWidgetTree();
    SetVisibility(ESlateVisibility::Collapsed);
}

void UActivityMinigameWidget::BuildWidgetTree()
{
    if (!WidgetTree || RootCanvas) return;
    RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("ActivityRoot"));
    WidgetTree->RootWidget = RootCanvas;

    BackgroundPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ActivityBackground"));
    BackgroundPanel->SetBrushColor(PanelBlack);
    BackgroundPanel->SetPadding(FMargin(12.0f));
    BackgroundPanel->SetVisibility(ESlateVisibility::HitTestInvisible);
    Place(RootCanvas, BackgroundPanel, 0, 0, 1000, 650);

    AddInset(WidgetTree, RootCanvas, TEXT("PrimaryInset"), 24, 126, 612, 350);
    AddInset(WidgetTree, RootCanvas, TEXT("MetricsInset"), 652, 126, 324, 350);
    AddInset(WidgetTree, RootCanvas, TEXT("CommandInset"), 24, 492, 952, 132);

    TitleText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ActivityTitle"));
    SetTextStyle(TitleText, 28, Cyan);
    Place(RootCanvas, TitleText, 30, 20, 620, 42);

    PhaseText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ActivityPhase"));
    SetTextStyle(PhaseText, 18, Green);
    PhaseText->SetJustification(ETextJustify::Right);
    Place(RootCanvas, PhaseText, 650, 24, 316, 32);

    StageRailText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StageRail"));
    SetTextStyle(StageRailText, 14, Dim);
    Place(RootCanvas, StageRailText, 30, 70, 936, 26);

    MainProgressBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ProcedureProgress"));
    MainProgressBar->SetFillColorAndOpacity(Green);
    Place(RootCanvas, MainProgressBar, 30, 104, 936, 10);

    PrimaryPanelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("PrimaryProcedurePanel"));
    SetTextStyle(PrimaryPanelText, 16, Cyan);
    Place(RootCanvas, PrimaryPanelText, 42, 142, 582, 180);

    SecondaryPanelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SecondaryProcedurePanel"));
    SetTextStyle(SecondaryPanelText, 15, FLinearColor(0.82f, 0.90f, 0.88f));
    Place(RootCanvas, SecondaryPanelText, 42, 324, 582, 138);

    MetricsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ProcedureMetrics"));
    SetTextStyle(MetricsText, 16, FLinearColor(0.78f, 0.88f, 0.86f));
    Place(RootCanvas, MetricsText, 668, 142, 290, 150);

    ConsumableBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ConsumableBar"));
    ConsumableBar->SetFillColorAndOpacity(Green);
    Place(RootCanvas, ConsumableBar, 668, 310, 290, 12);
    ConfidenceBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("ConfidenceBar"));
    ConfidenceBar->SetFillColorAndOpacity(Cyan);
    Place(RootCanvas, ConfidenceBar, 668, 348, 290, 12);
    LoadBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("LoadBar"));
    LoadBar->SetFillColorAndOpacity(Amber);
    Place(RootCanvas, LoadBar, 668, 386, 290, 12);
    InterferenceBar = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("InterferenceBar"));
    InterferenceBar->SetFillColorAndOpacity(Violet);
    Place(RootCanvas, InterferenceBar, 668, 424, 290, 12);

    ConnectionLampsText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ConnectionLamps"));
    SetTextStyle(ConnectionLampsText, 22, Green);
    Place(RootCanvas, ConnectionLampsText, 42, 506, 520, 34);

    InputPromptText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ActivityInputPrompt"));
    SetTextStyle(InputPromptText, 20, FLinearColor::White);
    InputPromptText->SetJustification(ETextJustify::Center);
    Place(RootCanvas, InputPromptText, 160, 554, 680, 34);

    UTextBlock* CancelText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CancelPrompt"));
    SetTextStyle(CancelText, 13, Dim);
    CancelText->SetText(FText::FromString(TEXT("[ X ] ABORT PROCEDURE")));
    CancelText->SetJustification(ETextJustify::Center);
    Place(RootCanvas, CancelText, 350, 596, 300, 22);
}

void UActivityMinigameWidget::UpdateFromSnapshot(const FPlayerActivitySnapshot& Snapshot)
{
    const bool bSupported = Snapshot.State == EPlayerActivityState::Active &&
        (Snapshot.Mechanic == EActivityMechanic::GenomeSequence || Snapshot.Mechanic == EActivityMechanic::CableMatching);
    bShowingMinigame = bSupported;
    SetVisibility(bSupported ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    if (!bSupported || !RootCanvas) return;

    TitleText->SetText(FText::FromString(Snapshot.DisplayName.ToString().ToUpper()));
    PhaseText->SetText(FText::FromString(FString::Printf(TEXT("PHASE // %s"), *PhaseLabel(Snapshot.ProcedurePhase))));
    MainProgressBar->SetPercent(FMath::Clamp(Snapshot.Progress, 0.0f, 1.0f));
    ConsumableBar->SetPercent(FMath::Clamp(Snapshot.ConsumablePercent, 0.0f, 1.0f));
    ConsumableBar->SetFillColorAndOpacity(Snapshot.ConsumablePercent <= 0.2f ? FLinearColor::Red : Green);
    ConfidenceBar->SetPercent(FMath::Clamp(Snapshot.ConfidencePercent, 0.0f, 1.0f));
    ConfidenceBar->SetFillColorAndOpacity(Snapshot.ConfidencePercent <= 0.3f ? Amber : Cyan);
    InterferenceBar->SetPercent(FMath::Clamp(Snapshot.BloomInterference, 0.0f, 1.0f));
    InterferenceBar->SetFillColorAndOpacity(Snapshot.BloomInterference >= 0.7f ? FLinearColor::Red : Violet);
    InputPromptText->SetColorAndOpacity(FSlateColor(Snapshot.Mistakes > 0 || Snapshot.bOverload ? Amber : FLinearColor::White));
    if (Snapshot.Mechanic == EActivityMechanic::GenomeSequence) UpdateGenomeLayout(Snapshot);
    else UpdateRewiringLayout(Snapshot);
}

void UActivityMinigameWidget::UpdateGenomeLayout(const FPlayerActivitySnapshot& Snapshot)
{
    StageRailText->SetText(FText::FromString(TEXT("[ 1 SAMPLE PREP ]     [ 2 READ ALIGNMENT ]     [ 3 CLASSIFY ]")));
    PrimaryPanelText->SetText(FText::FromString(FString::Printf(
        TEXT("SAMPLE PREP\nLYSIS        %3.0f%%\nREAGENT FLOW %3.0f%%\nCONTAM FILTER %3.0f%%\n\nREAD ALIGNMENT\nREF  A C G T A G C T G A C T\nR1   A C - T A G C T - A C T\nR2   - C G T A - C T G A C -\nACTIVE BASE  [ %s ]"),
        Snapshot.Progress * 100.0f, Snapshot.ConsumablePercent * 100.0f,
        (1.0f - Snapshot.BloomInterference) * 100.0f, *InputToken(Snapshot.ExpectedInput, true))));
    SecondaryPanelText->SetText(FText::FromString(TEXT(
        "CLASSIFY TARGET REGION\n( E ) PATHOGEN     ( F ) HOST TISSUE\n( 3 ) CONTAMINATION  ( 4 ) BLOOM MIMICRY\nResolve the anomalous read without exhausting reagent.")));
    MetricsText->SetText(FText::FromString(FString::Printf(
        TEXT("EVIDENCE\nCONFIDENCE       %3.0f%%\nREAGENT          %3.0f%%\nCONTAMINATION    %3.0f%%\nERRORS           %d\nBLOOM NOISE      %3.0f%%"),
        Snapshot.ConfidencePercent * 100.0f, Snapshot.ConsumablePercent * 100.0f,
        Snapshot.BloomInterference * 72.0f, Snapshot.Mistakes, Snapshot.BloomInterference * 100.0f)));
    LoadBar->SetVisibility(ESlateVisibility::Collapsed);
    ConnectionLampsText->SetText(FText::FromString(FString::Printf(TEXT("READS ALIGNED  %d / %d"), Snapshot.CurrentInputIndex, Snapshot.TotalInputs)));
    InputPromptText->SetText(FText::FromString(FString::Printf(TEXT("SELECT BASE / CLASSIFICATION  [ %s ]"), *InputToken(Snapshot.ExpectedInput, false))));
}

void UActivityMinigameWidget::UpdateRewiringLayout(const FPlayerActivitySnapshot& Snapshot)
{
    StageRailText->SetText(FText::FromString(TEXT("[ 1 TRACE ]     [ 2 REPAIR ]     [ 3 LOAD BALANCE ]     [ 4 TEST ]")));
    PrimaryPanelText->SetText(FText::FromString(FString::Printf(
        TEXT("CIRCUIT TRACE\nSOURCE  %.1f V  //  MAIN BREAKER 15 A\n\nBUS A  ->  BREAKER 1  ->  TERM 4  ->  LIFE SUPPORT\nBUS B  ->  BREAKER 2  ->  TERM 6  ->  DOOR\nBUS C  ->  BREAKER 3  ->  TERM ?  ->  SENSORS\n\nDAMAGED CONDUCTOR\nCUT BACK  //  STRIP 6 mm  //  CRIMP  //  LAND"), Snapshot.Voltage)));
    SecondaryPanelText->SetText(FText::FromString(FString::Printf(
        TEXT("LOAD BALANCE\nLIFE SUPPORT   6.3 A   PRIORITY 1\nDOOR           3.8 A   PRIORITY 2\nSENSORS        4.9 A   PRIORITY 3\n\nNEXT TERMINAL / TEST CHANNEL  [ %s ]"), *InputToken(Snapshot.ExpectedInput, false))));
    MetricsText->SetText(FText::FromString(FString::Printf(
        TEXT("LIVE TEST\nVOLTAGE       %5.1f V\nCURRENT       %5.1f A\nBUS LOAD      %5.0f%%\nCONTINUITY    %s\nOVERLOAD      %s\nBLOOM NOISE   %5.0f%%"),
        Snapshot.Voltage, Snapshot.CurrentAmps, Snapshot.LoadPercent * 100.0f,
        Snapshot.bContinuityPassed ? TEXT("PASS") : TEXT("OPEN"), Snapshot.bOverload ? TEXT("WARNING") : TEXT("CLEAR"),
        Snapshot.BloomInterference * 100.0f)));
    LoadBar->SetVisibility(ESlateVisibility::HitTestInvisible);
    LoadBar->SetPercent(FMath::Clamp(Snapshot.LoadPercent, 0.0f, 1.0f));
    LoadBar->SetFillColorAndOpacity(Snapshot.bOverload ? FLinearColor::Red : Amber);
    FString Lamps(TEXT("CONNECTIONS  "));
    for (int32 Index = 0; Index < Snapshot.TotalInputs; ++Index) Lamps += Index < Snapshot.PositiveConnections ? TEXT("● ") : TEXT("○ ");
    ConnectionLampsText->SetText(FText::FromString(Lamps));
    InputPromptText->SetText(FText::FromString(FString::Printf(TEXT("TRACE / LAND / TEST  [ %s ]"), *InputToken(Snapshot.ExpectedInput, false))));
}

FString UActivityMinigameWidget::InputToken(EActivityInput Input, bool bGenomeSymbol)
{
    if (bGenomeSymbol)
    {
        switch (Input) { case EActivityInput::Primary: return TEXT("A"); case EActivityInput::Secondary: return TEXT("C"); case EActivityInput::Tertiary: return TEXT("G"); default: return TEXT("T"); }
    }
    switch (Input) { case EActivityInput::Primary: return TEXT("E"); case EActivityInput::Secondary: return TEXT("F"); case EActivityInput::Tertiary: return TEXT("3"); default: return TEXT("4"); }
}

FString UActivityMinigameWidget::PhaseLabel(EActivityProcedurePhase Phase)
{
    switch (Phase) { case EActivityProcedurePhase::Prepare: return TEXT("PREPARE"); case EActivityProcedurePhase::Diagnose: return TEXT("DIAGNOSE"); case EActivityProcedurePhase::Repair: return TEXT("REPAIR"); case EActivityProcedurePhase::Balance: return TEXT("BALANCE"); default: return TEXT("VERIFY"); }
}
