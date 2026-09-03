#include "UI/JumpDestinationRowWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "UI/JumpDestinationWidget.h"

void UJumpDestinationRowWidget::Configure(UJumpDestinationWidget* InOwner, int32 InIndex, const FText& Label, const FLinearColor& Color)
{
    Owner = InOwner;
    CandidateIndex = InIndex;
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("DestinationButton"));
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DestinationLabel"));
    Text->SetText(Label);
    Text->SetColorAndOpacity(FSlateColor(Color));
    Button->AddChild(Text);
    Button->OnClicked.AddDynamic(this, &UJumpDestinationRowWidget::HandleClicked);
    WidgetTree->RootWidget = Button;
}

void UJumpDestinationRowWidget::HandleClicked()
{
    if (Owner)
    {
        Owner->SelectCandidate(CandidateIndex);
    }
}
