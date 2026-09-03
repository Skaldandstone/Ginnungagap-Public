#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/PlayerClass.h"
#include "SkillPayloadPickerWidget.generated.h"

class UClassSkillTreeSubsystem;
class URunOutcomeSubsystem;
class USkillPayloadEntryWidget;
class UTextBlock;
class UVerticalBox;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPayloadChanged);

/**
 * Pre-run payload screen: choose which of the unlocked actives to bring.
 *
 * Commits through URunOutcomeSubsystem::SetEquippedActiveSkills, which validates the whole set
 * before accepting any of it. Nothing here decides legality itself -- the catalogue does, so this
 * screen cannot drift from what the run will honour.
 */
UCLASS()
class GINNUNGAGAP_API USkillPayloadPickerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;

	/** Re-reads the role and its owned skills, then rebuilds the list. */
	UFUNCTION(BlueprintCallable, Category = "Payload")
	void RefreshPayload();

	UFUNCTION(BlueprintCallable, Category = "Payload")
	bool EquipSkill(const FString& SkillID);

	UFUNCTION(BlueprintCallable, Category = "Payload")
	bool UnequipSkill(const FString& SkillID);

	/** Currently committed payload, in slot order. */
	UFUNCTION(BlueprintPure, Category = "Payload")
	TArray<FString> GetPayload() const { return WorkingSkills.EquippedActiveSkills; }

	UPROPERTY(BlueprintAssignable, Category = "Payload")
	FOnPayloadChanged OnPayloadChanged;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Payload")
	TSubclassOf<USkillPayloadEntryWidget> EntryWidgetClass;

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> HeaderText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> SlotSummaryText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UVerticalBox> AvailableList;

	UPROPERTY()
	TObjectPtr<UClassSkillTreeSubsystem> SkillTreeSubsystem;

	UPROPERTY()
	TObjectPtr<URunOutcomeSubsystem> RunOutcomeSubsystem;

	UPROPERTY()
	EPressureSuitRole CurrentRole = EPressureSuitRole::Scientist;

	UFUNCTION()
	void OnEntryToggled(const FString& SkillID);

	void BuildFallbackLayout();
	void RebuildAvailableList();

	/** Persists a payload, returning false when the subsystem refuses the set. */
	bool CommitPayload(const TArray<FString>& NewPayload);

	/** Working copy of the role's owned ranks and payload. */
	FClassSkillsArray WorkingSkills;
};
