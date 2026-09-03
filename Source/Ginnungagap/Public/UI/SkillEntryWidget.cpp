#include "UI/SkillEntryWidget.h"
#include "Progression/ClassSkillTreeSubsystem.h"
#include "Engine/GameInstance.h"
#include "Progression/PlayerClass.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void USkillEntryWidget::NativeConstruct()
{
	Super::NativeConstruct();
	BuildFallbackLayout();

	if (UGameInstance* GI = GetGameInstance())
	{
		SkillTreeSubsystem = GI->GetSubsystem<UClassSkillTreeSubsystem>();
	}

	if (UnlockButton)
	{
		UnlockButton->OnClicked.AddDynamic(this, &USkillEntryWidget::OnUnlockButtonClicked);
	}
}

void USkillEntryWidget::NativeDestruct()
{
	if (UnlockButton) UnlockButton->OnClicked.RemoveDynamic(this, &USkillEntryWidget::OnUnlockButtonClicked);
	Super::NativeDestruct();
}

void USkillEntryWidget::BuildFallbackLayout()
{
	if (!WidgetTree || WidgetTree->RootWidget) return;
	UBorder* Card = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SkillCard"));
	Card->SetBrushColor(FLinearColor(0.025f, 0.055f, 0.068f, 1.0f));
	Card->SetPadding(FMargin(16.0f, 12.0f));
	WidgetTree->RootWidget = Card;
	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SkillRow"));
	Card->SetContent(Row);

	USizeBox* IconSize = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("SkillIconSize"));
	IconSize->SetWidthOverride(44.0f); IconSize->SetHeightOverride(44.0f);
	SkillIcon = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("SkillIcon"));
	SkillIcon->SetColorAndOpacity(FLinearColor(0.18f, 0.72f, 0.82f, 0.28f)); IconSize->AddChild(SkillIcon);
	if (UHorizontalBoxSlot* IconSlot = Row->AddChildToHorizontalBox(IconSize)) IconSlot->SetPadding(FMargin(0, 2, 14, 0));

	auto Text = [this](const TCHAR* Name, int32 Size, FLinearColor Color)
	{
		UTextBlock* Result = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Result->SetFont(FSlateFontInfo(Result->GetFont().FontObject, Size));
		Result->SetColorAndOpacity(FSlateColor(Color));
		return Result;
	};
	UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SkillCopy"));
	SkillNameText = Text(TEXT("SkillNameText"), 16, FLinearColor(0.88f, 0.94f, 0.95f));
	TierText = Text(TEXT("TierText"), 10, FLinearColor(0.30f, 0.86f, 1.0f));
	DescriptionText = Text(TEXT("DescriptionText"), 12, FLinearColor(0.58f, 0.66f, 0.69f));
	DescriptionText->SetAutoWrapText(true);
	CostText = Text(TEXT("CostText"), 11, FLinearColor(0.82f, 0.66f, 0.30f));
	Copy->AddChildToVerticalBox(SkillNameText); Copy->AddChildToVerticalBox(TierText);
	if (UVerticalBoxSlot* DescriptionSlot = Copy->AddChildToVerticalBox(DescriptionText)) DescriptionSlot->SetPadding(FMargin(0, 5, 0, 6));
	Copy->AddChildToVerticalBox(CostText);
	if (UHorizontalBoxSlot* CopySlot = Row->AddChildToHorizontalBox(Copy))
	{
		CopySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); CopySlot->SetVerticalAlignment(VAlign_Center);
	}

	UnlockButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("UnlockButton"));
	UnlockButton->SetBackgroundColor(FLinearColor(0.05f, 0.28f, 0.32f, 1.0f));
	UnlockButtonText = Text(TEXT("UnlockButtonText"), 11, FLinearColor(0.88f, 0.96f, 0.96f));
	UnlockButtonText->SetText(FText::FromString(TEXT("UNLOCK"))); UnlockButton->AddChild(UnlockButtonText);
	if (UHorizontalBoxSlot* ButtonSlot = Row->AddChildToHorizontalBox(UnlockButton))
	{
		ButtonSlot->SetPadding(FMargin(14, 6, 0, 6)); ButtonSlot->SetVerticalAlignment(VAlign_Center);
	}
}

void USkillEntryWidget::SetSkillData(const FClassSkill& InSkill, EPressureSuitRole InRole,
	const FClassSkillsArray& InOwned, int32 InAvailablePoints, int32 InBankedCurrency)
{
	CurrentSkill = InSkill;
	CurrentRole = InRole;
	OwnedSkills = InOwned;
	AvailableSkillPoints = InAvailablePoints;
	BankedCurrency = InBankedCurrency;

	UpdateUI();
	RefreshUnlockButton();
}

void USkillEntryWidget::UpdateUI()
{
	// DisplayName and Description are FText from the catalogue now, so they carry through
	// localisation instead of being flattened to raw strings here.
	if (SkillNameText)
	{
		SkillNameText->SetText(CurrentSkill.DisplayName);
	}

	if (TierText)
	{
		TierText->SetText(FText::FromString(FString::Printf(TEXT("Tier %d"), CurrentSkill.Tier)));
	}

	if (DescriptionText)
	{
		DescriptionText->SetText(CurrentSkill.Description);
	}

	const int32 OwnedRank = SkillTreeSubsystem
		? SkillTreeSubsystem->GetOwnedRank(CurrentSkill.SkillID, OwnedSkills) : 0;
	const bool bAtMaxRank = OwnedRank >= CurrentSkill.MaxRank;

	if (RankText)
	{
		// Whether a skill is carried kit or learned habit changes how the player should read it:
		// an active is only worth buying if they intend to spend one of three loadout slots on it.
		const FString Kind = CurrentSkill.Activation == ESkillActivation::Active
			? TEXT("ACTIVE") : TEXT("PASSIVE");
		RankText->SetText(FText::FromString(
			FString::Printf(TEXT("%s  //  RANK %d / %d"), *Kind, OwnedRank, CurrentSkill.MaxRank)));
	}

	if (CostText)
	{
		if (bAtMaxRank)
		{
			CostText->SetText(FText::FromString(TEXT("Fully trained")));
		}
		else if (SkillTreeSubsystem && !SkillTreeSubsystem->ArePrerequisitesMet(CurrentSkill.SkillID, OwnedSkills))
		{
			// Name what is blocking rather than just greying out, so the tree reads as a path
			// rather than an arbitrary refusal.
			TArray<FString> Missing = SkillTreeSubsystem->GetMissingPrerequisites(CurrentSkill.SkillID, OwnedSkills);
			TArray<FString> MissingNames;
			for (const FString& MissingID : Missing)
			{
				MissingNames.Add(SkillTreeSubsystem->GetSkillByID(MissingID).DisplayName.ToString());
			}
			CostText->SetText(FText::FromString(TEXT("Requires: ") + FString::Join(MissingNames, TEXT(", "))));
		}
		else
		{
			const int32 PointCost = SkillTreeSubsystem
				? SkillTreeSubsystem->GetNextRankCost(CurrentSkill.SkillID, OwnedSkills) : 0;
			const int32 CurrencyCost = SkillTreeSubsystem
				? SkillTreeSubsystem->GetNextRankCurrencyCost(CurrentSkill.SkillID, OwnedSkills) : 0;
			CostText->SetText(FText::FromString(
				FString::Printf(TEXT("Points: %d   Credits: %d"), PointCost, CurrencyCost)));
		}
	}
}

void USkillEntryWidget::RefreshUnlockButton()
{
	if (!UnlockButton)
		return;

	const int32 OwnedRank = SkillTreeSubsystem
		? SkillTreeSubsystem->GetOwnedRank(CurrentSkill.SkillID, OwnedSkills) : 0;
	const bool bAtMaxRank = OwnedRank >= CurrentSkill.MaxRank;
	const bool bPrerequisitesMet = SkillTreeSubsystem
		&& SkillTreeSubsystem->ArePrerequisitesMet(CurrentSkill.SkillID, OwnedSkills);
	const bool bCanUnlock = CanUnlockSkill();

	UnlockButton->SetIsEnabled(bCanUnlock);

	if (bAtMaxRank)
	{
		UnlockButton->SetToolTipText(FText::FromString(TEXT("Fully trained")));
		UnlockButton->SetBackgroundColor(FLinearColor(0.08f, 0.18f, 0.17f, 1.0f));
		if (UnlockButtonText) UnlockButtonText->SetText(FText::FromString(TEXT("MAX")));
	}
	else if (!bPrerequisitesMet)
	{
		UnlockButton->SetToolTipText(FText::FromString(TEXT("Earlier training required first")));
		UnlockButton->SetBackgroundColor(FLinearColor(0.09f, 0.11f, 0.12f, 1.0f));
		if (UnlockButtonText) UnlockButtonText->SetText(FText::FromString(TEXT("LOCKED")));
	}
	else if (!bCanUnlock)
	{
		UnlockButton->SetToolTipText(FText::FromString(TEXT("Not enough points or credits")));
		UnlockButton->SetBackgroundColor(FLinearColor(0.09f, 0.11f, 0.12f, 1.0f));
		if (UnlockButtonText) UnlockButtonText->SetText(FText::FromString(TEXT("LOCKED")));
	}
	else
	{
		UnlockButton->SetBackgroundColor(FLinearColor(0.05f, 0.28f, 0.32f, 1.0f));
		if (UnlockButtonText)
		{
			UnlockButtonText->SetText(FText::FromString(OwnedRank > 0 ? TEXT("RANK UP") : TEXT("UNLOCK")));
		}
	}
}

bool USkillEntryWidget::CanUnlockSkill() const
{
	if (!SkillTreeSubsystem)
	{
		return false;
	}

	// Points route and currency route share the catalogue's legality check, so the button can
	// never offer a purchase the subsystem would then refuse.
	if (SkillTreeSubsystem->CanUnlockSkill(CurrentRole, CurrentSkill.SkillID, OwnedSkills, AvailableSkillPoints))
	{
		return true;
	}

	const int32 CurrencyCost = SkillTreeSubsystem->GetNextRankCurrencyCost(CurrentSkill.SkillID, OwnedSkills);
	const int32 RankCost = SkillTreeSubsystem->GetNextRankCost(CurrentSkill.SkillID, OwnedSkills);
	return BankedCurrency >= CurrencyCost
		&& SkillTreeSubsystem->CanUnlockSkill(CurrentRole, CurrentSkill.SkillID, OwnedSkills, RankCost);
}

void USkillEntryWidget::OnUnlockButtonClicked()
{
	if (!CanUnlockSkill())
		return;

	OnSkillUnlocked.Broadcast(CurrentSkill.SkillID);
}
