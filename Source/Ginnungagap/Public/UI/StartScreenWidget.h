#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "StartScreenWidget.generated.h"

class UBorder;
class UImage;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnStartGameClicked);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnContinueGameClicked);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnQuitClicked);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSettingsClicked);

UCLASS()
class GINNUNGAGAP_API UStartScreenWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UFUNCTION(BlueprintCallable, Category="Menu")
	void SetTitleGateEnabled(bool bEnabled) { bRequireTitleGate = bEnabled; }
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void SetStatusMessage(const FText& Message, bool bIsError = false);

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnStartGameClicked OnStartGameClicked;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnContinueGameClicked OnContinueGameClicked;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnQuitClicked OnQuitClicked;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnSettingsClicked OnSettingsRequested;

	UPROPERTY(BlueprintAssignable, Category="Menu")
	FOnStartGameClicked OnTitleGateCompleted;

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* NewGameButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* ContinueButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* SettingsButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* QuitButton;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* TitleText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* VersionText;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* StatusText;

	UPROPERTY(Transient)
	TObjectPtr<UImage> BackdropImage;

	UPROPERTY(Transient)
	TObjectPtr<UImage> BackdropGlowImage;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> MenuPanel;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> AccentRail;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> TitleGate;

	/** The one hot element on the screen: the ship's emergency readout along the bottom edge. */
	UPROPERTY(Transient)
	TObjectPtr<UBorder> EmergencyStrip;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> EmergencyLamp;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> EmergencyTicker;

	/**
	 * The gate title as a baked plate: GINNUNGAGAP in ceramic plating the Bloom has taken left to
	 * right, built by tools/build_title_bloom_plate.py from the threat family's own layering
	 * (host, fibre, crystal, tendril, core, haze). Two layers: the matter, and the emissive layer
	 * NativeTick breathes over it. Falls back to plain text when the textures are absent.
	 */
	UPROPERTY(Transient)
	TObjectPtr<UImage> TitlePlate;

	UPROPERTY(Transient)
	TObjectPtr<UImage> TitleGlow;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> TitleFallbackText;

	/** Master switch for the native title-screen ambience. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Menu|Motion")
	bool bAnimateBackground = true;

	/** Scales drift and zoom without affecting the initial menu fade. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Menu|Motion", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float BackgroundMotionStrength = 0.65f;

	UFUNCTION()
	void OnNewGameClicked();

	UFUNCTION()
	void OnContinueClicked();

	UFUNCTION()
	void OnSettingsClicked();

	UFUNCTION()
	void HandleQuitClicked();

	void UpdateContinueButtonState();
	void BuildFallbackLayout();
	void ActivateMainMenu();
	void DisarmQuit();
	void DisarmNewGame();
	bool bQuitArmed = false;
	bool bNewGameArmed = false;
	FTimerHandle QuitArmTimer;
	FTimerHandle NewGameArmTimer;
	float IntroElapsed = 0.0f;
	float AmbientElapsed = 0.0f;
	bool bRequireTitleGate = true;
	bool bTitleGateActive = false;
};
