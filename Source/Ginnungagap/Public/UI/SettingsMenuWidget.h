#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SettingsMenuWidget.generated.h"

class UButton;
class USlider;
class UTextBlock;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSettingsBackRequested);

UCLASS()
class GINNUNGAGAP_API USettingsMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnSettingsBackRequested OnBackRequested;

protected:
	UPROPERTY(meta = (BindWidgetOptional)) USlider* QualitySlider;
	UPROPERTY(meta = (BindWidgetOptional)) USlider* ResolutionScaleSlider;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* QualityValueText;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* ResolutionValueText;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* WindowModeButton;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* WindowModeValueText;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* VSyncButton;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* VSyncValueText;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* FrameRateButton;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* FrameRateValueText;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* DefaultsButton;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* ApplyButton;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* BackButton;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* StatusText;

	UFUNCTION() void OnQualityChanged(float Value);
	UFUNCTION() void OnResolutionScaleChanged(float Value);
	UFUNCTION() void OnWindowModeClicked();
	UFUNCTION() void OnVSyncClicked();
	UFUNCTION() void OnFrameRateClicked();
	UFUNCTION() void OnDefaultsClicked();
	UFUNCTION() void OnApplyClicked();
	UFUNCTION() void OnBackClicked();

	void BuildFallbackLayout();
	void LoadCurrentSettings();
	void RefreshValueLabels();
	void RestoreUnconfirmedSettings();
	float PendingFrameRateLimit = 60.0f;
	bool bPendingVSync = false;
	bool bAwaitingConfirmation = false;
	float ConfirmationDeadline = 0.0f;
	FTimerHandle ConfirmationTimer;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
};
