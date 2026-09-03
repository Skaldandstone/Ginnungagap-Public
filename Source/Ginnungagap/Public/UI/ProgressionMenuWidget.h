#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "ProgressionMenuWidget.generated.h"

class USkillTreeWidget;
class USettingsMenuWidget;
class UTextBlock;

UCLASS()
class GINNUNGAGAP_API UProgressionMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void OpenMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void CloseMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ToggleMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	bool IsMenuOpen() const { return bIsMenuOpen; }

protected:
	UPROPERTY(meta = (BindWidgetOptional))
	USkillTreeWidget* SkillTreeWidget;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* CloseButton;

	UPROPERTY(meta = (BindWidgetOptional)) UButton* SettingsButton;
	UPROPERTY(meta = (BindWidgetOptional)) UButton* ReturnToTitleButton;
	UPROPERTY(meta = (BindWidgetOptional)) UTextBlock* StatusText;
	UPROPERTY() TObjectPtr<USettingsMenuWidget> SettingsMenu;

	UPROPERTY()
	bool bIsMenuOpen = false;

	UFUNCTION()
	void OnCloseButtonClicked();
	UFUNCTION() void OnSettingsClicked();
	UFUNCTION() void OnSettingsBack();
	UFUNCTION() void OnReturnToTitleClicked();
	void DisarmReturnToTitle();
	void DismissSettingsMenu();
	void BuildFallbackLayout();
	bool bReturnToTitleArmed = false;
	FTimerHandle ReturnToTitleTimer;
};
