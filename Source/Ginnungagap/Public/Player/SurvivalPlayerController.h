#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SurvivalPlayerController.generated.h"

class USurvivalHUDWidget;
class UProgressionMenuWidget;
class UAntagonistActivityWidget;

UCLASS()
class GINNUNGAGAP_API ASurvivalPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    ASurvivalPlayerController();

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "HUD")
    TSubclassOf<USurvivalHUDWidget> HUDWidgetClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "HUD")
    TSubclassOf<UProgressionMenuWidget> ProgressionMenuClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "HUD|Versus")
    TSubclassOf<UAntagonistActivityWidget> AntagonistActivityWidgetClass;

    /** The live survival HUD, or null before BeginPlay has created it. */
    UFUNCTION(BlueprintPure, Category = "HUD")
    USurvivalHUDWidget* GetHUDWidget() const { return HUDWidget; }

    /** What the Interact binding does, for tests that press the key path rather than call into stations. */
    void PressInteract() { OnInteract(); }

protected:
    virtual void BeginPlay() override;
    virtual void OnPossess(APawn* InPawn) override;

    UPROPERTY(BlueprintReadOnly, Category = "HUD")
    TObjectPtr<USurvivalHUDWidget> HUDWidget;

    UPROPERTY(BlueprintReadOnly, Category = "HUD")
    TObjectPtr<UProgressionMenuWidget> ProgressionMenu;

    UPROPERTY(BlueprintReadOnly, Category = "HUD|Versus")
    TObjectPtr<UAntagonistActivityWidget> AntagonistActivityWidget;

private:
    // Input callbacks
    void OnMove_Forward(float Value);
    void OnMove_Right(float Value);
    void OnLook_Up(float Value);
    void OnLook_Right(float Value);
    void OnJumpPressed();
    void OnJumpReleased();
    void OnInteract();

    /** Changes which way the player intends to get past the obstruction they are looking at. */
    void OnCycleApproach();
    void OnActivitySecondary();
    void OnActivityTertiary();
    void OnActivityQuaternary();
    void OnActivityCancel();
    void OnToggleProgressionMenu();
    void OnRestartDemo();
    void OnToggleView();
    void SetupAntagonistActivityWidget(APawn* InPawn);

public:
    virtual void SetupInputComponent() override;

    /**
     * Developer console command: reseeds the run so it can be reproduced exactly.
     *
     * Pass the seed printed in the log of the run being investigated. Passing 0 draws a fresh one.
     * Reseeding mid-run resets every channel, so this is a "start this run again" control rather
     * than something to reach for partway through.
     */
    UFUNCTION(Exec)
    void SeedRun(int32 Seed);

    /** Developer console command: prints the seed this run is using. */
    UFUNCTION(Exec)
    void ShowRunSeed();

    /** Developer console command: cycles through hallucination types on the local player. */
    UFUNCTION(Exec)
    void TestPsychosisEpisode();

    /** Developer console command: adds severe jump psychosis so the scheduler can be observed. */
    UFUNCTION(Exec)
    void EnablePsychosisTestMode();

    /** Developer console command: performs a local suit-telemetry reality check. */
    UFUNCTION(Exec)
    void PsychosisRealityCheck();

private:
    int32 PsychosisTestEpisodeIndex = 0;
};
