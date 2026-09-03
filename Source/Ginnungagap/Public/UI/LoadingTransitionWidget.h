#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Meta/CharacterProfile.h"
#include "UI/MapCustomizationWidget.h"
#include "LoadingTransitionWidget.generated.h"

class UTextBlock;

/** Briefing frame displayed before blocking map travel begins. */
UCLASS()
class GINNUNGAGAP_API ULoadingTransitionWidget : public UUserWidget
{
	GENERATED_BODY()
public:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
	void Configure(const FCharacterProfile& Character, const FGameCustomization& Customization, EGameMode GameMode);
private:
	void BuildFallbackLayout();
	void RefreshText();
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CharacterText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ExpeditionText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;
	FCharacterProfile CharacterProfile;
	FGameCustomization GameCustomization;
	EGameMode SelectedMode = EGameMode::SinglePlayerSurvival;
	float ElapsedSeconds = 0.0f;
};
