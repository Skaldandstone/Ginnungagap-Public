#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Activities/PlayerActivityTypes.h"
#include "ActivityMinigameWidget.generated.h"

class UBorder;
class UCanvasPanel;
class UProgressBar;
class UTextBlock;

/** Native, asset-free first playable UX for layered bioscan and electrical-panel activities. */
UCLASS()
class GINNUNGAGAP_API UActivityMinigameWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;

    UFUNCTION(BlueprintCallable, Category="Activity UI")
    void UpdateFromSnapshot(const FPlayerActivitySnapshot& Snapshot);

    UFUNCTION(BlueprintPure, Category="Activity UI")
    bool IsShowingMinigame() const { return bShowingMinigame; }

private:
    void BuildWidgetTree();
    void UpdateGenomeLayout(const FPlayerActivitySnapshot& Snapshot);
    void UpdateRewiringLayout(const FPlayerActivitySnapshot& Snapshot);
    static FString InputToken(EActivityInput Input, bool bGenomeSymbol);
    static FString PhaseLabel(EActivityProcedurePhase Phase);

    UPROPERTY() TObjectPtr<UCanvasPanel> RootCanvas;
    UPROPERTY() TObjectPtr<UBorder> BackgroundPanel;
    UPROPERTY() TObjectPtr<UTextBlock> TitleText;
    UPROPERTY() TObjectPtr<UTextBlock> PhaseText;
    UPROPERTY() TObjectPtr<UTextBlock> StageRailText;
    UPROPERTY() TObjectPtr<UTextBlock> PrimaryPanelText;
    UPROPERTY() TObjectPtr<UTextBlock> SecondaryPanelText;
    UPROPERTY() TObjectPtr<UTextBlock> MetricsText;
    UPROPERTY() TObjectPtr<UTextBlock> InputPromptText;
    UPROPERTY() TObjectPtr<UTextBlock> ConnectionLampsText;
    UPROPERTY() TObjectPtr<UProgressBar> MainProgressBar;
    UPROPERTY() TObjectPtr<UProgressBar> ConsumableBar;
    UPROPERTY() TObjectPtr<UProgressBar> ConfidenceBar;
    UPROPERTY() TObjectPtr<UProgressBar> LoadBar;
    UPROPERTY() TObjectPtr<UProgressBar> InterferenceBar;

    bool bShowingMinigame = false;
};
