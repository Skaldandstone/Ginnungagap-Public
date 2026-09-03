#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/PlayerClass.h"
#include "SkillPayloadEntryWidget.generated.h"

class UButton;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPayloadEntryToggled, const FString&, SkillID);

/**
 * One selectable active in the payload screen.
 *
 * Exists as its own widget because UButton::OnClicked carries no payload, so a shared handler
 * could not tell which entry was pressed -- the same reason USkillEntryWidget exists for the tree.
 */
UCLASS()
class GINNUNGAGAP_API USkillPayloadEntryWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	/**
	 * @param bInEquipped   whether this skill is currently in the payload
	 * @param bInSlotsFull  payload is full, so an unequipped entry cannot be added right now
	 */
	UFUNCTION(BlueprintCallable, Category = "Payload")
	void SetEntryData(const FClassSkill& InSkill, int32 InRank, bool bInEquipped, bool bInSlotsFull);

	UPROPERTY(BlueprintAssignable, Category = "Payload")
	FOnPayloadEntryToggled OnToggled;

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> NameText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> DetailText;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UTextBlock> ButtonLabel;

	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UButton> ToggleButton;

	UPROPERTY()
	FClassSkill CurrentSkill;

	UPROPERTY()
	int32 CurrentRank = 0;

	UPROPERTY()
	bool bEquipped = false;

	UPROPERTY()
	bool bSlotsFull = false;

	UFUNCTION()
	void OnToggleClicked();

	void BuildFallbackLayout();
	void UpdateUI();
};
