#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "Components/CanvasPanel.h"
#include "Meta/CharacterProfile.h"
#include "StatusEffects/PlayerPsychosisComponent.h"
#include "SurvivalHUDWidget.generated.h"

class ACoopSurvivalCharacter;
class UCharacterProfileSubsystem;
class ASensorArraySystem;
class UBorder;
class UScaleBox;
class USizeBox;
class UActivityMinigameWidget;
class USkillAbilityBarWidget;

UCLASS()
class GINNUNGAGAP_API USurvivalHUDWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void SetCharacterReference(ACoopSurvivalCharacter* InCharacter);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void UpdateDisplay();

    /**
     * A single ship-wide line under the standing warnings, for a moment rather than a state: a
     * biomass signature, a hull event, something the ship wants the crew to know once. Holds for
     * Seconds, pulsing with the other alerts, then collapses.
     */
    UFUNCTION(BlueprintCallable, Category = "HUD")
    void ShowAlertLine(const FText& Line, float Seconds = 6.0f);

    UFUNCTION(BlueprintPure, Category = "HUD")
    bool IsAlertLineVisible() const { return AlertLineSecondsRemaining > 0.0f; }

protected:
    UPROPERTY(BlueprintReadWrite, Category = "HUD")
    TObjectPtr<ACoopSurvivalCharacter> OwningCharacter;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
    float UpdateInterval = 0.1f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
    float LifeSupportCriticalDrainMultiplierThreshold = 1.5f;

    // Widget-implementable events for UI updates. Each has a native default implementation built
    // from the widget tree constructed in NativeConstruct(), so no WBP override is required, but
    // one can still be authored later to replace the native visuals.
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetHealth(float HealthPercent);
    virtual void SetHealth_Implementation(float HealthPercent);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetOxygen(float OxygenLevelPercent);
    virtual void SetOxygen_Implementation(float OxygenLevelPercent);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetRadiation(float RadiationSv);
    virtual void SetRadiation_Implementation(float RadiationSv);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetSuitIntegrity(float SuitIntegrityPercent);
    virtual void SetSuitIntegrity_Implementation(float SuitIntegrityPercent);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetStability(float StabilityPercent);
    virtual void SetStability_Implementation(float StabilityPercent);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetArmorStatus(float ArmorIntegrity, bool bIsCorrupted);
    virtual void SetArmorStatus_Implementation(float ArmorIntegrity, bool bIsCorrupted);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void OnPlayerDeath(float RespawnCountdown);
    virtual void OnPlayerDeath_Implementation(float RespawnCountdown);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void OnPlayerRespawn();
    virtual void OnPlayerRespawn_Implementation();

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetContaminationReading(float Concentration);
    virtual void SetContaminationReading_Implementation(float Concentration);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetInteractionPrompt(const FString& Prompt);

    /** Reads whatever the player is looking at and asks it what to say. */
    void RefreshInteractionPrompt();
    virtual void SetInteractionPrompt_Implementation(const FString& Prompt);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetJumpWarning(bool bActive, float SecondsRemaining);
    virtual void SetJumpWarning_Implementation(bool bActive, float SecondsRemaining);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetLifeSupportCritical(bool bCritical);
    virtual void SetLifeSupportCritical_Implementation(bool bCritical);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetSelfDestructWarning(bool bActive, float SecondsRemaining);
    virtual void SetSelfDestructWarning_Implementation(bool bActive, float SecondsRemaining);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void ShowRunOutcome(uint8 Outcome, int32 CurrencyEarned, int32 TotalBankedCurrency);
    virtual void ShowRunOutcome_Implementation(uint8 Outcome, int32 CurrencyEarned, int32 TotalBankedCurrency);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "HUD")
    void SetCharacterName(const FString& NewName);
    virtual void SetCharacterName_Implementation(const FString& NewName);

    UFUNCTION()
    void OnCharacterProfileChanged(const FCharacterProfile& NewProfile);

    UFUNCTION()
    void OnPsychosisVoiceReceived(EPsychosisVoiceIntent Intent, const FText& Line, FVector PerceivedLocation, float Severity);

    void RefreshAllStats();
    float TimeSinceLastUpdate = 0.0f;

private:
    void BuildWidgetTree();

    UPROPERTY()
    TObjectPtr<UCanvasPanel> RootCanvas;

    UPROPERTY()
    TObjectPtr<UBorder> InteractionPromptPanel;

    UPROPERTY()
    TObjectPtr<UProgressBar> HealthBar;

    UPROPERTY()
    TObjectPtr<UProgressBar> OxygenBar;

    UPROPERTY()
    TObjectPtr<UProgressBar> SuitIntegrityBar;

    UPROPERTY()
    TObjectPtr<UProgressBar> StabilityBar;

    UPROPERTY()
    TObjectPtr<UProgressBar> ArmorBar;

    UPROPERTY()
    TObjectPtr<UTextBlock> RadiationText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ContaminationText;

    UPROPERTY()
    TObjectPtr<UTextBlock> StatusEffectsText;

    UPROPERTY()
    TObjectPtr<UTextBlock> InteractionPromptText;

    UPROPERTY()
    TObjectPtr<UTextBlock> JumpWarningText;

    UPROPERTY()
    TObjectPtr<UTextBlock> LifeSupportWarningText;

    UPROPERTY()
    TObjectPtr<UTextBlock> DeathText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SelfDestructWarningText;

    UPROPERTY()
    TObjectPtr<UTextBlock> AlertLineText;

    float AlertLineSecondsRemaining = 0.0f;

    UPROPERTY()
    TObjectPtr<UTextBlock> RunOutcomeText;

    UPROPERTY()
    TObjectPtr<UBorder> RunOutcomePanel;

    UPROPERTY()
    TObjectPtr<UTextBlock> CharacterNameText;

    UPROPERTY()
    TObjectPtr<UTextBlock> NavigationContactText;

    UPROPERTY()
    TObjectPtr<UTextBlock> DemoTitleText;

    UPROPERTY()
    TObjectPtr<UTextBlock> VisorStatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> VisorReticleText;

    UPROPERTY()
    TObjectPtr<UTextBlock> PsychosisGhostReticleText;

    UPROPERTY()
    TObjectPtr<UTextBlock> PsychosisVoiceLeftText;

    UPROPERTY()
    TObjectPtr<UTextBlock> PsychosisVoiceCenterText;

    UPROPERTY()
    TObjectPtr<UTextBlock> PsychosisVoiceRightText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ObjectiveText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ControlsText;

    UPROPERTY()
    TObjectPtr<UTextBlock> MagneticSuitText;

    UPROPERTY()
    TObjectPtr<UProgressBar> ThrusterFuelBar;

    UPROPERTY()
    TObjectPtr<UTextBlock> HealthLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> OxygenLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> SuitLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> StabilityLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> ArmorLabel;

    UPROPERTY()
    TObjectPtr<UTextBlock> HealthValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> OxygenValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SuitValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> StabilityValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ArmorValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ThrusterValueText;

    UPROPERTY()
    TObjectPtr<UTextBlock> CompassText;

    UPROPERTY()
    TObjectPtr<UActivityMinigameWidget> ActivityMinigameWidget;

    UPROPERTY()
    TObjectPtr<USkillAbilityBarWidget> AbilityBarWidget;

    UPROPERTY()
    TObjectPtr<ASensorArraySystem> CachedSensorArray;

    bool bHasShownRunOutcome = false;
    float AlertPulseTime = 0.0f;
    float PsychosisVoiceSecondsRemaining = 0.0f;
};
