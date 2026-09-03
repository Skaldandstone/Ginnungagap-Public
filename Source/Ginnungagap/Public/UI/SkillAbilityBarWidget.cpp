// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/SkillAbilityBarWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "CoopSurvivalCharacter.h"
#include "Engine/GameInstance.h"
#include "Progression/ClassSkillComponent.h"
#include "Progression/ClassSkillTreeSubsystem.h"

namespace
{
	// Ready, spent, and running are the three states a player has to tell apart at a glance while
	// something is trying to kill them, so they are separated by hue rather than brightness.
	const FLinearColor ReadyColor(0.05f, 0.28f, 0.32f, 0.92f);
	const FLinearColor ActiveColor(0.10f, 0.52f, 0.38f, 0.95f);
	const FLinearColor CoolingColor(0.07f, 0.09f, 0.11f, 0.88f);
	const FLinearColor EmptyColor(0.04f, 0.05f, 0.06f, 0.55f);
	const FLinearColor TriggerFlashColor(0.30f, 0.86f, 1.0f, 0.98f);
}

void USkillAbilityBarWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (UGameInstance* GameInstance = GetGameInstance())
	{
		SkillTreeSubsystem = GameInstance->GetSubsystem<UClassSkillTreeSubsystem>();
	}

	// The HUD may construct before possession completes, so fall back to the local pawn rather
	// than relying solely on SetCharacterReference having already been called.
	if (!OwningCharacter)
	{
		if (const APlayerController* PC = GetOwningPlayer())
		{
			SetCharacterReference(Cast<ACoopSurvivalCharacter>(PC->GetPawn()));
		}
	}

	RefreshSlots();
}

void USkillAbilityBarWidget::NativeDestruct()
{
	if (SkillComponent)
	{
		SkillComponent->OnActiveSkillTriggered.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillTriggered);
		SkillComponent->OnActiveSkillExpired.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillExpired);
		SkillComponent->OnSkillsChanged.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillsChanged);
	}
	Super::NativeDestruct();
}

void USkillAbilityBarWidget::SetCharacterReference(ACoopSurvivalCharacter* InCharacter)
{
	if (OwningCharacter == InCharacter)
	{
		return;
	}

	if (SkillComponent)
	{
		SkillComponent->OnActiveSkillTriggered.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillTriggered);
		SkillComponent->OnActiveSkillExpired.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillExpired);
		SkillComponent->OnSkillsChanged.RemoveDynamic(this, &USkillAbilityBarWidget::HandleSkillsChanged);
	}

	OwningCharacter = InCharacter;
	SkillComponent = InCharacter ? InCharacter->GetSkillComponent() : nullptr;

	if (SkillComponent)
	{
		SkillComponent->OnActiveSkillTriggered.AddDynamic(this, &USkillAbilityBarWidget::HandleSkillTriggered);
		SkillComponent->OnActiveSkillExpired.AddDynamic(this, &USkillAbilityBarWidget::HandleSkillExpired);
		SkillComponent->OnSkillsChanged.AddDynamic(this, &USkillAbilityBarWidget::HandleSkillsChanged);
	}

	RefreshSlots();
}

void USkillAbilityBarWidget::BuildFallbackLayout()
{
	// Same early-return contract as the other native widgets: an authored WBP supplies its own
	// root, and this only builds when nothing else has.
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}

	SlotRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SlotRow"));
	WidgetTree->RootWidget = SlotRow;

	SlotVisuals.Empty();
	for (int32 SlotIndex = 0; SlotIndex < FClassProgression::MaxEquippedActiveSkills; ++SlotIndex)
	{
		const FString SlotName = FString::Printf(TEXT("Slot%d"), SlotIndex);

		FAbilitySlotVisual Visual;
		Visual.Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), *SlotName);
		Visual.Frame->SetBrushColor(EmptyColor);
		Visual.Frame->SetPadding(FMargin(10.0f, 6.0f));

		UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
			UVerticalBox::StaticClass(), *(SlotName + TEXT("Stack")));
		Visual.Frame->SetContent(Stack);

		auto MakeText = [this, &SlotName](const TCHAR* Suffix, int32 Size, FLinearColor Color)
		{
			UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
				UTextBlock::StaticClass(), *(SlotName + Suffix));
			Text->SetFont(FSlateFontInfo(Text->GetFont().FontObject, Size));
			Text->SetColorAndOpacity(FSlateColor(Color));
			return Text;
		};

		Visual.KeyText = MakeText(TEXT("Key"), 11, FLinearColor(0.30f, 0.86f, 1.0f));
		Visual.NameText = MakeText(TEXT("Name"), 12, FLinearColor(0.88f, 0.94f, 0.95f));
		Visual.StateText = MakeText(TEXT("State"), 10, FLinearColor(0.67f, 0.75f, 0.77f));

		Visual.CooldownBar = WidgetTree->ConstructWidget<UProgressBar>(
			UProgressBar::StaticClass(), *(SlotName + TEXT("Cooldown")));
		Visual.CooldownBar->SetPercent(0.0f);

		Stack->AddChildToVerticalBox(Visual.KeyText);
		Stack->AddChildToVerticalBox(Visual.NameText);
		Stack->AddChildToVerticalBox(Visual.StateText);
		if (UVerticalBoxSlot* BarSlot = Stack->AddChildToVerticalBox(Visual.CooldownBar))
		{
			BarSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 0.0f));
		}

		if (UHorizontalBoxSlot* FrameSlot = SlotRow->AddChildToHorizontalBox(Visual.Frame))
		{
			FrameSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
		}

		SlotVisuals.Add(Visual);
	}
}

void USkillAbilityBarWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (TriggerFlashRemaining > 0.0f)
	{
		TriggerFlashRemaining = FMath::Max(0.0f, TriggerFlashRemaining - InDeltaTime);
	}

	// Polled rather than event-driven: a cooldown sweep is continuous, and nothing fires an event
	// per frame to drive it.
	RefreshSlots();
}

void USkillAbilityBarWidget::RefreshSlots()
{
	if (!SkillComponent || !SkillTreeSubsystem)
	{
		return;
	}

	for (int32 SlotIndex = 0; SlotIndex < SlotVisuals.Num(); ++SlotIndex)
	{
		const FAbilitySlotVisual& Visual = SlotVisuals[SlotIndex];
		if (!Visual.Frame)
		{
			continue;
		}

		if (Visual.KeyText)
		{
			Visual.KeyText->SetText(FText::FromString(
				SlotKeyLabels.IsValidIndex(SlotIndex) ? SlotKeyLabels[SlotIndex] : FString()));
		}

		const FString SkillID = SkillComponent->GetSkillInSlot(SlotIndex);
		if (SkillID.IsEmpty())
		{
			// An empty slot reads as deliberately empty rather than broken, so a player who has
			// not filled their payload can tell the difference.
			Visual.Frame->SetBrushColor(EmptyColor);
			if (Visual.NameText) Visual.NameText->SetText(FText::FromString(TEXT("-- EMPTY --")));
			if (Visual.StateText) Visual.StateText->SetText(FText::GetEmpty());
			if (Visual.CooldownBar) Visual.CooldownBar->SetPercent(0.0f);
			continue;
		}

		const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
		if (Visual.NameText)
		{
			Visual.NameText->SetText(Skill.DisplayName);
		}

		const bool bActive = SkillComponent->IsSkillActive(SkillID);
		const float Cooldown = SkillComponent->GetRemainingCooldown(SkillID);
		const int32 Charges = SkillComponent->GetChargesRemaining(SkillID);
		const bool bOutOfCharges = Charges == 0;

		FString State;
		if (bActive)
		{
			State = FString::Printf(TEXT("ACTIVE %.0fs"), SkillComponent->GetRemainingDuration(SkillID));
		}
		else if (bOutOfCharges)
		{
			State = TEXT("SPENT");
		}
		else if (Cooldown > 0.0f)
		{
			State = FString::Printf(TEXT("%.0fs"), Cooldown);
		}
		else
		{
			State = TEXT("READY");
		}

		// -1 means the skill is limited by cooldown alone, so no count is shown at all rather than
		// a misleading number.
		if (Charges >= 0)
		{
			State += FString::Printf(TEXT("  [%d]"), Charges);
		}

		if (Visual.StateText)
		{
			Visual.StateText->SetText(FText::FromString(State));
		}

		if (Visual.CooldownBar)
		{
			// Sweeps down from full to empty as the cooldown clears, so the bar drains toward
			// readiness rather than filling toward it.
			const float Fraction = Skill.CooldownSeconds > 0.0f
				? FMath::Clamp(Cooldown / Skill.CooldownSeconds, 0.0f, 1.0f)
				: 0.0f;
			Visual.CooldownBar->SetPercent(Fraction);
		}

		FLinearColor FrameColor = ReadyColor;
		if (bActive)
		{
			FrameColor = ActiveColor;
		}
		else if (Cooldown > 0.0f || bOutOfCharges)
		{
			FrameColor = CoolingColor;
		}

		if (TriggerFlashRemaining > 0.0f && bActive)
		{
			FrameColor = FMath::Lerp(FrameColor, TriggerFlashColor, TriggerFlashRemaining / 0.35f);
		}

		Visual.Frame->SetBrushColor(FrameColor);
	}
}

void USkillAbilityBarWidget::HandleSkillTriggered(const FString& SkillID)
{
	TriggerFlashRemaining = 0.35f;
	RefreshSlots();
}

void USkillAbilityBarWidget::HandleSkillExpired(const FString& SkillID)
{
	RefreshSlots();
}

void USkillAbilityBarWidget::HandleSkillsChanged()
{
	RefreshSlots();
}
