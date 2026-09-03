#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Meta/CharacterProfile.h"
#include "FirstLaunchCharacterCreationWidget.generated.h"

class UTextBlock;
class UEditableTextBox;
class UButton;
class UImage;
class UTextureRenderTarget2D;
class ASceneCapture2D;
class ACoopSurvivalCharacter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnCharacterCreated, const FString&, CharacterName, ECharacterAppearance, Appearance, EPressureSuitRole, SuitRole);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FOnCharacterCreatedWithPreset, const FString&, CharacterName,
	ECharacterAppearance, Appearance, EPressureSuitRole, SuitRole, FName, MetaHumanPresetId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCharacterCreationBackRequested);

UCLASS()
class GINNUNGAGAP_API UFirstLaunchCharacterCreationWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	void SetCharacterDraft(const FCharacterProfile& InDraft) { CharacterDraft = InDraft; }

	UPROPERTY(BlueprintAssignable, Category = "Character Creation")
	FOnCharacterCreated OnCharacterCreated;

	/** Extended event for new character-creator flows; the legacy three-parameter event remains supported. */
	UPROPERTY(BlueprintAssignable, Category = "Character Creation")
	FOnCharacterCreatedWithPreset OnCharacterCreatedWithPreset;

	UPROPERTY(BlueprintAssignable, Category = "Character Creation")
	FOnCharacterCreationBackRequested OnBackRequested;

protected:
	// Optional like every other binding in this screen. BuildFallbackLayout constructs both of
	// these itself and every use site null-checks them, so requiring them only meant an authored
	// Blueprint that had not rebuilt the whole screen failed to compile -- which is exactly what
	// WBP_FirstLaunchCharacterCreation was doing.
	UPROPERTY(meta = (BindWidgetOptional))
	UEditableTextBox* CharacterNameInput;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* ConfirmButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* ScienceRoleButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* EngineeringRoleButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* MedicalRoleButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* SecurityRoleButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* RotatePreviewLeftButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* RotatePreviewRightButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UImage* SuitPreviewImage;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* SelectedSuitRoleText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* SelectedMetaHumanText;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* PreviousMetaHumanButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* NextMetaHumanButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* ValidationText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* CharacterCountText;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* BackButton;

	UPROPERTY()
	ECharacterAppearance SelectedAppearance = ECharacterAppearance::Default;

	UPROPERTY(BlueprintReadOnly, Category="Character Creation")
	EPressureSuitRole SelectedSuitRole = GinnungagapDefaults::StartingSuitRole;
	FCharacterProfile CharacterDraft;

	UPROPERTY(BlueprintReadOnly, Category="Character Creation")
	FName SelectedMetaHumanPresetId = TEXT("PlayerFace01");

	UFUNCTION()
	void OnConfirmClicked();

	UFUNCTION(BlueprintCallable, Category="Character Creation")
	void OnAppearanceSelected(ECharacterAppearance Appearance);

	UFUNCTION(BlueprintCallable, Category="Character Creation")
	void OnSuitRoleSelected(EPressureSuitRole SuitRole);

	UFUNCTION(BlueprintCallable, Category="Character Creation")
	bool OnMetaHumanPresetSelected(FName PresetId);

	UFUNCTION() void OnScienceRoleClicked();
	UFUNCTION() void OnEngineeringRoleClicked();
	UFUNCTION() void OnMedicalRoleClicked();
	UFUNCTION() void OnSecurityRoleClicked();
	UFUNCTION() void OnRotatePreviewLeft();
	UFUNCTION() void OnRotatePreviewRight();
	UFUNCTION() void OnPreviousMetaHumanClicked();
	UFUNCTION() void OnNextMetaHumanClicked();
	UFUNCTION() void OnBackClicked();
	UFUNCTION() void OnCharacterNameChanged(const FText& Text);

	UFUNCTION()
	void UpdateAppearanceUI();
	void BuildFallbackLayout();
	void CreateSuitPreview();
	void RefreshSuitPreview();
	void SelectAdjacentMetaHuman(int32 Direction);
	void DestroySuitPreview();

	UPROPERTY(Transient)
	TObjectPtr<ACoopSurvivalCharacter> PreviewCharacter;

	UPROPERTY(Transient)
	TObjectPtr<ASceneCapture2D> PreviewCapture;

	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> PreviewRenderTarget;

	void ValidateAndCreateCharacter();
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
};
