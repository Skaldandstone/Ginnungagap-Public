#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/PlayerClass.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/ScrollBox.h"
#include "Components/VerticalBox.h"
#include "SkillTreeWidget.generated.h"

class UClassSkillTreeSubsystem;
class USkillEntryWidget;
class URunOutcomeSubsystem;

UCLASS()
class GINNUNGAGAP_API USkillTreeWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	void RefreshSkillTree();

	UFUNCTION(BlueprintCallable, Category = "Skills")
	void SelectRole(EPressureSuitRole SelectedClass);

protected:
	UPROPERTY()
	UClassSkillTreeSubsystem* SkillTreeSubsystem;

	UPROPERTY()
	URunOutcomeSubsystem* RunOutcomeSubsystem;

	UPROPERTY()
	EPressureSuitRole CurrentSelectedRole = GinnungagapDefaults::StartingSuitRole;

	// UI Elements
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* RoleNameText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* PointsText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* CurrencyText;

	UPROPERTY(meta = (BindWidgetOptional))
	UScrollBox* SkillScrollBox;

	// Class selection buttons
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* SecurityButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* CrewButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* EngineeringButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* MedicalButton;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skills")
	TSubclassOf<USkillEntryWidget> SkillEntryWidgetClass;

	UFUNCTION()
	void OnSecurityClicked();

	UFUNCTION()
	void OnCrewClicked();

	UFUNCTION()
	void OnEngineeringClicked();

	UFUNCTION()
	void OnMedicalClicked();

	UFUNCTION()
	void OnSkillUnlocked(const FString& SkillID);

	void PopulateSkillsForRole();
	void UpdateRoleDisplay();
	void UpdatePointsDisplay();
	void RefreshAllSkillEntries();
	void BuildFallbackLayout();
	void RefreshRoleTabStyles();
	float PointsRefreshTimer = 0.0f;
};
