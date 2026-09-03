// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/SkillPayloadEntryWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"

void USkillPayloadEntryWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (ToggleButton)
	{
		ToggleButton->OnClicked.AddDynamic(this, &USkillPayloadEntryWidget::OnToggleClicked);
	}

	UpdateUI();
}

void USkillPayloadEntryWidget::NativeDestruct()
{
	if (ToggleButton)
	{
		ToggleButton->OnClicked.RemoveDynamic(this, &USkillPayloadEntryWidget::OnToggleClicked);
	}
	Super::NativeDestruct();
}

void USkillPayloadEntryWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PayloadEntryRoot"));
	Root->SetBrushColor(FLinearColor(0.03f, 0.06f, 0.08f, 0.9f));
	Root->SetPadding(FMargin(10.0f, 7.0f));
	WidgetTree->RootWidget = Root;

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(
		UHorizontalBox::StaticClass(), TEXT("PayloadEntryRow"));
	Root->SetContent(Row);

	UVerticalBox* Labels = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass(), TEXT("PayloadEntryLabels"));

	auto MakeText = [this](const TCHAR* Name, int32 Size, FLinearColor Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
		Text->SetColorAndOpacity(FSlateColor(Color));
		return Text;
	};

	NameText = MakeText(TEXT("NameText"), 13, FLinearColor(0.88f, 0.94f, 0.95f));
	DetailText = MakeText(TEXT("DetailText"), 10, FLinearColor(0.67f, 0.75f, 0.77f));
	Labels->AddChildToVerticalBox(NameText);
	Labels->AddChildToVerticalBox(DetailText);
	Row->AddChildToHorizontalBox(Labels);

	USpacer* Gap = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	if (UHorizontalBoxSlot* GapSlot = Row->AddChildToHorizontalBox(Gap))
	{
		GapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	ToggleButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("ToggleButton"));
	ButtonLabel = MakeText(TEXT("ButtonLabel"), 11, FLinearColor(0.88f, 0.94f, 0.95f));
	ToggleButton->AddChild(ButtonLabel);
	Row->AddChildToHorizontalBox(ToggleButton);
}

void USkillPayloadEntryWidget::SetEntryData(const FClassSkill& InSkill, int32 InRank,
	bool bInEquipped, bool bInSlotsFull)
{
	CurrentSkill = InSkill;
	CurrentRank = InRank;
	bEquipped = bInEquipped;
	bSlotsFull = bInSlotsFull;
	UpdateUI();
}

void USkillPayloadEntryWidget::UpdateUI()
{
	if (NameText)
	{
		NameText->SetText(CurrentSkill.DisplayName);
	}

	if (DetailText)
	{
		// Duration, cooldown and charges are the actual trade-off between two actives, so they are
		// on the row rather than buried in a tooltip.
		FString Detail = FString::Printf(TEXT("RANK %d / %d   %.0fs active   %.0fs cooldown"),
			CurrentRank, CurrentSkill.MaxRank,
			CurrentSkill.DurationSeconds, CurrentSkill.CooldownSeconds);

		Detail += CurrentSkill.ChargesPerRun > 0
			? FString::Printf(TEXT("   %d per run"), CurrentSkill.ChargesPerRun)
			: FString(TEXT("   no use limit"));

		DetailText->SetText(FText::FromString(Detail));
	}

	if (!ToggleButton)
	{
		return;
	}

	// A full payload disables the other entries rather than hiding them, so the limit reads as a
	// choice the player is making and not as skills having disappeared.
	const bool bEnabled = bEquipped || !bSlotsFull;
	ToggleButton->SetIsEnabled(bEnabled);
	ToggleButton->SetBackgroundColor(bEquipped
		? FLinearColor(0.10f, 0.52f, 0.38f, 1.0f)
		: (bEnabled ? FLinearColor(0.05f, 0.28f, 0.32f, 1.0f) : FLinearColor(0.09f, 0.11f, 0.12f, 1.0f)));

	if (ButtonLabel)
	{
		ButtonLabel->SetText(FText::FromString(
			bEquipped ? TEXT("REMOVE") : (bEnabled ? TEXT("BRING") : TEXT("FULL"))));
	}

	ToggleButton->SetToolTipText(bEnabled
		? CurrentSkill.Description
		: FText::FromString(TEXT("Payload is full -- remove something first")));
}

void USkillPayloadEntryWidget::OnToggleClicked()
{
	OnToggled.Broadcast(CurrentSkill.SkillID);
}
