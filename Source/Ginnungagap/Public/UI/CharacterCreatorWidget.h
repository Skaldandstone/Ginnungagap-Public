#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Meta/CharacterProfile.h"
#include "CharacterCreatorWidget.generated.h"

class UButton;
class UComboBoxString;
class UEditableTextBox;
class UTextBlock;
class UImage;
class UTextureRenderTarget2D;
class ASceneCapture2D;
class ACoopSurvivalCharacter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCharacterIdentityConfirmed, const FCharacterProfile&, CharacterDraft);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCharacterCreatorBackRequested);

UCLASS()
class GINNUNGAGAP_API UCharacterCreatorWidget : public UUserWidget
{
	GENERATED_BODY()
public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
	UPROPERTY(BlueprintAssignable, Category="Character Creation") FOnCharacterIdentityConfirmed OnIdentityConfirmed;
	UPROPERTY(BlueprintAssignable, Category="Character Creation") FOnCharacterCreatorBackRequested OnBackRequested;
private:
	void BuildFallbackLayout();
	void PopulateOptions();
	void RefreshDraft();
	void CreateCharacterPreview();
	void RefreshCharacterPreview();
	void DestroyCharacterPreview();
	UFUNCTION() void OnConfirmClicked();
	UFUNCTION() void OnBackClicked();
	UFUNCTION() void OnNameChanged(const FText& Text);
	UFUNCTION() void OnOptionChanged(FString Item, ESelectInfo::Type SelectionType);
	UFUNCTION() void OnRotateLeftClicked();
	UFUNCTION() void OnRotateRightClicked();
	UPROPERTY(Transient) TObjectPtr<UEditableTextBox> CharacterNameInput;
	UPROPERTY(Transient) TObjectPtr<UComboBoxString> BodyCombo;
	UPROPERTY(Transient) TObjectPtr<UComboBoxString> FaceCombo;
	UPROPERTY(Transient) TObjectPtr<UComboBoxString> SkinCombo;
	UPROPERTY(Transient) TObjectPtr<UComboBoxString> HairCombo;
	UPROPERTY(Transient) TObjectPtr<UComboBoxString> VoiceCombo;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SummaryText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ValidationText;
	UPROPERTY(Transient) TObjectPtr<UImage> CharacterPreviewImage;
	UPROPERTY(Transient) TObjectPtr<UButton> ConfirmButton;
	UPROPERTY(Transient) TObjectPtr<UButton> BackButton;
	UPROPERTY(Transient) TObjectPtr<UButton> RotateLeftButton;
	UPROPERTY(Transient) TObjectPtr<UButton> RotateRightButton;
	UPROPERTY(Transient) TObjectPtr<ACoopSurvivalCharacter> PreviewCharacter;
	UPROPERTY(Transient) TObjectPtr<ASceneCapture2D> PreviewCapture;
	UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> PreviewRenderTarget;
	FCharacterProfile Draft;
};
