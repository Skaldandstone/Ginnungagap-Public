#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/PlayerClass.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "SkillEntryWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSkillUnlocked, const FString&, SkillID);

class UClassSkillTreeSubsystem;

UCLASS()
class GINNUNGAGAP_API USkillEntryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	void SetSkillData(const FClassSkill& InSkill, EPressureSuitRole InRole, const FClassSkillsArray& InOwned,
		int32 AvailablePoints, int32 BankedCurrency);

	UPROPERTY(BlueprintAssignable, Category = "Skills")
	FOnSkillUnlocked OnSkillUnlocked;

protected:
	UPROPERTY()
	FClassSkill CurrentSkill;

	UPROPERTY()
	FClassSkillsArray OwnedSkills;

	UPROPERTY()
	EPressureSuitRole CurrentRole = EPressureSuitRole::Scientist;

	UPROPERTY()
	int32 AvailableSkillPoints = 0;

	UPROPERTY()
	int32 BankedCurrency = 0;

	UPROPERTY()
	UClassSkillTreeSubsystem* SkillTreeSubsystem;

	// UI Elements
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* SkillNameText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* TierText;

	/** Rank readout and the passive/active tag, so a node's kind is legible before purchase. */
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* RankText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* DescriptionText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* CostText;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* UnlockButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UImage* SkillIcon;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* UnlockButtonText;

	UFUNCTION()
	void OnUnlockButtonClicked();

	void UpdateUI();
	void RefreshUnlockButton();
	bool CanUnlockSkill() const;
	void BuildFallbackLayout();
};
