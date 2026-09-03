#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "PreGameLoadoutWidget.generated.h"

class UButton;
class UExpeditionLoadoutSubsystem;
class USkillPayloadPickerWidget;
class USkillTreeWidget;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPreGameDeployRequested);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPreGameBackRequested);

/** Combined operator certification and equipment screen shown immediately before deployment. */
UCLASS()
class GINNUNGAGAP_API UPreGameLoadoutWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UPROPERTY(BlueprintAssignable, Category="Pre-Game")
	FOnPreGameDeployRequested OnDeployRequested;

	UPROPERTY(BlueprintAssignable, Category="Pre-Game")
	FOnPreGameBackRequested OnBackRequested;

protected:
	/** Replace this class to redesign skill/class selection without changing the loadout workflow. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Pre-Game|Skills")
	TSubclassOf<USkillTreeWidget> SkillTreeWidgetClass;

	/** Payload picker. Separate from the tree because buying a skill and bringing it are
	    different decisions made at different times. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Pre-Game|Skills")
	TSubclassOf<USkillPayloadPickerWidget> PayloadPickerWidgetClass;

	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<USkillTreeWidget> SkillTreeWidget;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<USkillPayloadPickerWidget> PayloadPickerWidget;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> OperatorText;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> RoleText;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> SupplyText;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> StatsText;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UTextBlock> StatusText;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> HelmetVisorButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> ThermalPlatingButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> RadiationShieldButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> PressureSealButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> ArmorPlatingButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> OxygenFilterButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> BackButton;
	UPROPERTY(meta=(BindWidgetOptional)) TObjectPtr<UButton> DeployButton;

	UPROPERTY() TObjectPtr<UExpeditionLoadoutSubsystem> LoadoutSubsystem;

	UFUNCTION() void OnHelmetVisorClicked();
	UFUNCTION() void OnThermalPlatingClicked();
	UFUNCTION() void OnRadiationShieldClicked();
	UFUNCTION() void OnPressureSealClicked();
	UFUNCTION() void OnArmorPlatingClicked();
	UFUNCTION() void OnOxygenFilterClicked();
	UFUNCTION() void OnBackClicked();
	UFUNCTION() void OnDeployClicked();

	void BuildFallbackLayout();
	void ToggleEquipment(uint8 EquipmentTypeValue);
	void RefreshEquipmentDisplay();
	void StyleEquipmentButton(UButton* Button, uint8 EquipmentTypeValue) const;
};
