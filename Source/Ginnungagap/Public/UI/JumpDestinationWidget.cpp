#include "UI/JumpDestinationWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Ship/JumpConsoleSystem.h"
#include "UI/JumpDestinationRowWidget.h"

void UJumpDestinationWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    BuildRows();
}

void UJumpDestinationWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // Focus needs the Slate tree, which exists only once the widget is constructed.
}

void UJumpDestinationWidget::Configure(AJumpConsoleSystem* InConsole, const TArray<FJumpCandidate>& InCandidates)
{
    Console = InConsole;
    Candidates = InCandidates;
    BuildRows();
}

void UJumpDestinationWidget::BuildRows()
{
    if (!WidgetTree)
    {
        return;
    }
    if (!WidgetTree->RootWidget)
    {
        UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("JumpFrame"));
        Frame->SetBrushColor(FLinearColor(0.008f, 0.015f, 0.025f, 0.97f));
        Frame->SetPadding(FMargin(28.0f));
        WidgetTree->RootWidget = Frame;
        CandidateList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("CandidateList"));
        Frame->SetContent(CandidateList);
    }
    if (!CandidateList)
    {
        return;
    }
    CandidateList->ClearChildren();
    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
    Title->SetText(FText::FromString(TEXT("JUMP NAVIGATION // SELECT DESTINATION")));
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(0.35f, 0.85f, 1.0f)));
    CandidateList->AddChildToVerticalBox(Title)->SetPadding(FMargin(0, 0, 0, 16));

    for (int32 Index = 0; Index < Candidates.Num(); ++Index)
    {
        const FStarSystemData& Data = Candidates[Index].DisplayedData;
        UJumpDestinationRowWidget* Row = CreateWidget<UJumpDestinationRowWidget>(GetOwningPlayer(), UJumpDestinationRowWidget::StaticClass());
        Row->Configure(this, Index,
            FText::FromString(FString::Printf(TEXT("%02d  //  %s  //  DANGER %d  //  %d HAZARDS  %d RESOURCES"),
                Index + 1, *Data.DisplayName.ToUpper(), Data.DangerTier, Data.Hazards.Num(), Data.Resources.Num())),
            Data.DangerTier >= 4 ? FLinearColor(1.0f, 0.25f, 0.12f)
                : (Data.DangerTier >= 2 ? FLinearColor(1.0f, 0.7f, 0.2f) : FLinearColor(0.75f, 0.9f, 1.0f)));
        CandidateList->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 0, 0, 8));
    }
}

void UJumpDestinationWidget::SelectCandidate(int32 Index)
{
    if (Console && Console->ConfirmJumpSelection(Index))
    {
        Console->CloseDestinationPicker();
    }
}
