// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/SkillPayloadPickerWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/GameInstance.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "Progression/ClassSkillTreeSubsystem.h"
#include "UI/SkillPayloadEntryWidget.h"

void USkillPayloadPickerWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildFallbackLayout();

	if (UGameInstance* GameInstance = GetGameInstance())
	{
		SkillTreeSubsystem = GameInstance->GetSubsystem<UClassSkillTreeSubsystem>();
		RunOutcomeSubsystem = GameInstance->GetSubsystem<URunOutcomeSubsystem>();
	}

	if (!EntryWidgetClass)
	{
		EntryWidgetClass = USkillPayloadEntryWidget::StaticClass();
	}

	RefreshPayload();
}

void USkillPayloadPickerWidget::NativeConstruct()
{
	Super::NativeConstruct();
	// Focus needs the Slate tree, which exists only once the widget is constructed.
}

void USkillPayloadPickerWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}

	UBorder* Root = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PayloadRoot"));
	Root->SetBrushColor(FLinearColor(0.012f, 0.027f, 0.035f, 0.98f));
	Root->SetPadding(FMargin(18.0f));
	WidgetTree->RootWidget = Root;

	UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass(), TEXT("PayloadStack"));
	Root->SetContent(Stack);

	auto MakeText = [this](const TCHAR* Name, const TCHAR* Copy, int32 Size, FLinearColor Color)
	{
		UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Text->SetText(FText::FromString(Copy));
		Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
		Text->SetColorAndOpacity(FSlateColor(Color));
		return Text;
	};

	HeaderText = MakeText(TEXT("HeaderText"), TEXT("PAYLOAD"), 18, FLinearColor(0.88f, 0.94f, 0.95f));
	SlotSummaryText = MakeText(TEXT("SlotSummaryText"), TEXT("0 / 3 selected"), 11,
		FLinearColor(0.30f, 0.86f, 1.0f));

	Stack->AddChildToVerticalBox(HeaderText);
	if (UVerticalBoxSlot* SummarySlot = Stack->AddChildToVerticalBox(SlotSummaryText))
	{
		SummarySlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 12.0f));
	}

	AvailableList = WidgetTree->ConstructWidget<UVerticalBox>(
		UVerticalBox::StaticClass(), TEXT("AvailableList"));
	if (UVerticalBoxSlot* ListSlot = Stack->AddChildToVerticalBox(AvailableList))
	{
		ListSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
}

void USkillPayloadPickerWidget::RefreshPayload()
{
	if (RunOutcomeSubsystem)
	{
		CurrentRole = RunOutcomeSubsystem->GetPlayerRole();
		WorkingSkills = RunOutcomeSubsystem->GetRoleSkills(CurrentRole);
	}

	RebuildAvailableList();
}

void USkillPayloadPickerWidget::RebuildAvailableList()
{
	if (!AvailableList || !SkillTreeSubsystem)
	{
		return;
	}

	AvailableList->ClearChildren();

	const TArray<FClassSkill> Available =
		SkillTreeSubsystem->GetAvailableActiveSkills(CurrentRole, WorkingSkills);
	const int32 Selected = WorkingSkills.EquippedActiveSkills.Num();
	const bool bSlotsFull = Selected >= FClassProgression::MaxEquippedActiveSkills;

	if (SlotSummaryText)
	{
		SlotSummaryText->SetText(FText::FromString(FString::Printf(TEXT("%d / %d selected"),
			Selected, FClassProgression::MaxEquippedActiveSkills)));
	}

	if (Available.Num() == 0)
	{
		// Say why the list is empty. A blank panel here would read as a broken screen rather than
		// as "you have not unlocked any procedures yet".
		UTextBlock* Empty = WidgetTree->ConstructWidget<UTextBlock>(
			UTextBlock::StaticClass(), TEXT("NoActivesText"));
		Empty->SetText(FText::FromString(TEXT("No active procedures unlocked for this role yet.")));
		Empty->SetFont(FSlateFontInfo(Empty->GetFont().FontObject, 11));
		Empty->SetColorAndOpacity(FSlateColor(FLinearColor(0.67f, 0.75f, 0.77f)));
		AvailableList->AddChildToVerticalBox(Empty);
		return;
	}

	// Equipped first, so what you are bringing stays together at the top as the list changes.
	TArray<FClassSkill> Ordered = Available;
	Ordered.Sort([this](const FClassSkill& A, const FClassSkill& B)
	{
		const bool bAEquipped = WorkingSkills.EquippedActiveSkills.Contains(A.SkillID);
		const bool bBEquipped = WorkingSkills.EquippedActiveSkills.Contains(B.SkillID);
		if (bAEquipped != bBEquipped)
		{
			return bAEquipped;
		}
		return A.Tier < B.Tier;
	});

	for (const FClassSkill& Skill : Ordered)
	{
		USkillPayloadEntryWidget* Entry = CreateWidget<USkillPayloadEntryWidget>(this, EntryWidgetClass);
		if (!Entry)
		{
			continue;
		}

		const bool bEquipped = WorkingSkills.EquippedActiveSkills.Contains(Skill.SkillID);
		Entry->SetEntryData(Skill, SkillTreeSubsystem->GetOwnedRank(Skill.SkillID, WorkingSkills),
			bEquipped, bSlotsFull);
		Entry->OnToggled.AddDynamic(this, &USkillPayloadPickerWidget::OnEntryToggled);

		if (UVerticalBoxSlot* EntrySlot = AvailableList->AddChildToVerticalBox(Entry))
		{
			EntrySlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 6.0f));
		}
	}
}

void USkillPayloadPickerWidget::OnEntryToggled(const FString& SkillID)
{
	if (WorkingSkills.EquippedActiveSkills.Contains(SkillID))
	{
		UnequipSkill(SkillID);
	}
	else
	{
		EquipSkill(SkillID);
	}
}

bool USkillPayloadPickerWidget::EquipSkill(const FString& SkillID)
{
	if (!SkillTreeSubsystem
		|| !SkillTreeSubsystem->CanEquipActiveSkill(CurrentRole, SkillID, WorkingSkills))
	{
		return false;
	}

	TArray<FString> Proposed = WorkingSkills.EquippedActiveSkills;
	Proposed.Add(SkillID);
	return CommitPayload(Proposed);
}

bool USkillPayloadPickerWidget::UnequipSkill(const FString& SkillID)
{
	if (!WorkingSkills.EquippedActiveSkills.Contains(SkillID))
	{
		return false;
	}

	TArray<FString> Proposed = WorkingSkills.EquippedActiveSkills;
	Proposed.Remove(SkillID);
	return CommitPayload(Proposed);
}

bool USkillPayloadPickerWidget::CommitPayload(const TArray<FString>& NewPayload)
{
	if (!RunOutcomeSubsystem)
	{
		return false;
	}

	// The subsystem validates the whole set and persists it. The local copy is only updated on
	// success, so a refused change cannot leave the screen showing a payload the run will not use.
	if (!RunOutcomeSubsystem->SetEquippedActiveSkills(CurrentRole, NewPayload))
	{
		return false;
	}

	WorkingSkills.EquippedActiveSkills = NewPayload;
	RebuildAvailableList();
	OnPayloadChanged.Broadcast();
	return true;
}
