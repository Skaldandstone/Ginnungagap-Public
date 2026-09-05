#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "CryoPodSystem.generated.h"

class ACoopSurvivalCharacter;
class UCurveFloat;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCryoPodLidMotionEvent, bool, bOpening);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FCryoPodLidProgressEvent, float, Progress, bool, bOpening);

UCLASS()
class GINNUNGAGAP_API ACryoPodSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ACryoPodSystem();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(BlueprintReadOnly, Category = "Cryo Pod")
    bool bIsOccupied = false;

    UPROPERTY()
    TWeakObjectPtr<ACoopSurvivalCharacter> OccupyingCharacter;

    UFUNCTION(BlueprintCallable, Category = "Cryo Pod")
    bool TryEnterPod(ACoopSurvivalCharacter* Character);

    UFUNCTION(BlueprintCallable, Category = "Cryo Pod")
    void ExitPod();

    UFUNCTION(BlueprintCallable, Category = "Cryo Pod")
    void SetLidOpen(bool bOpen);

    UFUNCTION(BlueprintPure, Category = "Cryo Pod")
    bool IsLidOpen() const { return bLidOpen; }

    UFUNCTION(BlueprintCallable, Category = "Cryo Pod")
    bool IsFunctioning() const { return !bIsCorrupted; }

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
    virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod")
    float RepairDuration = 4.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class USceneComponent> PodRakePivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class USceneComponent> LidPivot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> BedInsert;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> DetailTrim;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> HingeAssembly;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> Restraints;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> StatusLights;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> LidFrame;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> LidGlass;

    /**
     * The vertical stasis pod from Fab ("Sci-Fi Cryo Stasis Pod - Sleep Chamber", one mesh, glass
     * door in the base colour's alpha). When its mesh is present it is the pod's whole look: the
     * generated bed, lid, trim and lights are hidden and the sleeper stands inside behind the
     * glass. The door faces the actor's +X. Lid open/shut still drives state and lights; there
     * is no moving door on this mesh.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UStaticMeshComponent> VerticalPod;

    /**
     * The standing tube the crew wake in: a base the sleeper stands on, three ribs, and a glass
     * cylinder with a cap that lifts clear when the pod releases. The tube stays on the deck; only
     * the glass rises, and the sleeper is seen through it the whole time. Replaces the one-piece
     * Fab pod, which was opaque (the sleeper vanished inside it) and had to lift whole to open.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Tube")
    TObjectPtr<class UStaticMeshComponent> TubeBase;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Tube")
    TObjectPtr<class UStaticMeshComponent> TubeGlass;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Tube")
    TObjectPtr<class UStaticMeshComponent> TubeCap;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Tube")
    TArray<TObjectPtr<class UStaticMeshComponent>> TubeRibs;

    UFUNCTION(BlueprintPure, Category = "Cryo Pod|Visual")
    bool UsesVerticalPod() const;

    /** Resting state. Closed by default; a level opens the pods whose occupants got out. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_LidOpen, Category = "Cryo Pod")
    bool bLidOpen = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Lid", meta = (ClampMin = "0.05", Units = "s"))
    float LidAnimationDuration = 1.25f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Lid", meta = (ClampMin = "-110.0", ClampMax = "0.0", Units = "deg"))
    float LidOpenAngle = -24.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Cryo Pod|Lid")
    float LidAnimationAlpha = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Lid")
    TObjectPtr<UCurveFloat> LidAnimationCurve;

    UPROPERTY(BlueprintAssignable, Category = "Cryo Pod|Lid")
    FCryoPodLidMotionEvent OnLidMotionStarted;

    UPROPERTY(BlueprintAssignable, Category = "Cryo Pod|Lid")
    FCryoPodLidProgressEvent OnLidMotionProgress;

    UPROPERTY(BlueprintAssignable, Category = "Cryo Pod|Lid")
    FCryoPodLidMotionEvent OnLidMotionFinished;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    float PodRakeAngle = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    float PodRakeLift = 0.0f;

    /**
     * Recolours the status panel to whatever the pod currently is.
     *
     * The pod has had three authored status materials and a state model for as long as it has
     * existed, and nothing connected them: the lights were a mesh with no material at all. Cyan
     * for a working occupied pod, amber for a working empty one, red for a corrupted pod.
     */
    UFUNCTION(BlueprintCallable, Category = "Cryo Pod|Visual")
    void RefreshStatusLights();

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UMaterialInterface> StatusOccupiedMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UMaterialInterface> StatusIdleMaterial;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Cryo Pod|Visual")
    TObjectPtr<class UMaterialInterface> StatusFaultMaterial;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    UFUNCTION()
    void OnRep_LidOpen();

    void BeginLidMotion();
    void ApplyLidPose();
    void FinishRepair();

    bool bIsRepairing = false;
    FTimerHandle RepairTimerHandle;
};
