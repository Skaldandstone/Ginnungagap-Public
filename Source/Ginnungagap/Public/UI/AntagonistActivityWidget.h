#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Versus/AntagonistActivityTypes.h"
#include "AntagonistActivityWidget.generated.h"

class UAntagonistActivityComponent;
class UCanvasPanel;
class UProgressBar;
class UTextBlock;

UCLASS()
class GINNUNGAGAP_API UAntagonistActivityWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;

	UFUNCTION(BlueprintCallable, Category="Versus|Activities")
	void SetActivityComponent(UAntagonistActivityComponent* NewComponent);

	UFUNCTION(BlueprintCallable, Category="Versus|Activities")
	void UpdateFromSnapshot(const FAntagonistActivitySnapshot& Snapshot);

protected:
	UFUNCTION()
	void HandleActivityChanged(const FAntagonistActivitySnapshot& Snapshot);

private:
	void BuildWidgetTree();
	FLinearColor GetFactionColor(EAntagonistFaction Faction) const;
	FString BuildMechanicReadout(const FAntagonistActivitySnapshot& Snapshot) const;

	UPROPERTY() TObjectPtr<UAntagonistActivityComponent> ActivityComponent;
	UPROPERTY() TObjectPtr<UCanvasPanel> RootCanvas;
	UPROPERTY() TObjectPtr<UTextBlock> TitleText;
	UPROPERTY() TObjectPtr<UTextBlock> MotivationText;
	UPROPERTY() TObjectPtr<UTextBlock> MechanicText;
	UPROPERTY() TObjectPtr<UTextBlock> InputText;
	UPROPERTY() TObjectPtr<UProgressBar> ProgressBar;
	UPROPERTY() TObjectPtr<UProgressBar> ResourceBarA;
	UPROPERTY() TObjectPtr<UProgressBar> ResourceBarB;
	UPROPERTY() TObjectPtr<UProgressBar> ResourceBarC;
};

