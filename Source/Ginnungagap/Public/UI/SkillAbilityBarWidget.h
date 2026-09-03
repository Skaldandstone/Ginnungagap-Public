#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/PlayerClass.h"
#include "SkillAbilityBarWidget.generated.h"

class ACoopSurvivalCharacter;
class UClassSkillComponent;
class UClassSkillTreeSubsystem;
class UBorder;
class UHorizontalBox;
class UProgressBar;
class UTextBlock;

/** One payload slot: name, bound key, charge count, and a cooldown sweep. */
USTRUCT()
struct FAbilitySlotVisual
{
	GENERATED_BODY()

	UPROPERTY() TObjectPtr<UBorder> Frame;
	UPROPERTY() TObjectPtr<UTextBlock> KeyText;
	UPROPERTY() TObjectPtr<UTextBlock> NameText;
	UPROPERTY() TObjectPtr<UTextBlock> StateText;
	UPROPERTY() TObjectPtr<UProgressBar> CooldownBar;
};

/**
 * The in-run ability bar: three payload slots showing what can be triggered right now.
 *
 * Reads the skill component every tick rather than subscribing, because cooldowns are continuous
 * and a sweep has to move smoothly regardless of whether an event happened to fire this frame.
 * Delegates still drive the one-shot flourishes.
 */
UCLASS()
class GINNUNGAGAP_API USkillAbilityBarWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION(BlueprintCallable, Category = "HUD|Skills")
	void SetCharacterReference(ACoopSurvivalCharacter* InCharacter);

	/** Keys shown on each slot. Purely a label; the real binding lives in DefaultInput.ini. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "HUD|Skills")
	TArray<FString> SlotKeyLabels = {TEXT("Z"), TEXT("C"), TEXT("G")};

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	TObjectPtr<UHorizontalBox> SlotRow;

	UPROPERTY()
	TObjectPtr<ACoopSurvivalCharacter> OwningCharacter;

	UPROPERTY()
	TObjectPtr<UClassSkillComponent> SkillComponent;

	UPROPERTY()
	TObjectPtr<UClassSkillTreeSubsystem> SkillTreeSubsystem;

	UPROPERTY()
	TArray<FAbilitySlotVisual> SlotVisuals;

	UFUNCTION()
	void HandleSkillTriggered(const FString& SkillID);

	UFUNCTION()
	void HandleSkillExpired(const FString& SkillID);

	UFUNCTION()
	void HandleSkillsChanged();

	void BuildFallbackLayout();
	void RefreshSlots();

	/** Seconds of highlight left after a trigger, so the flash is visible without a timer. */
	float TriggerFlashRemaining = 0.0f;
};
