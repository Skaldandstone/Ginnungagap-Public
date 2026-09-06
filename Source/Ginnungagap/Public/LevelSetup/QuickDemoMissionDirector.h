#pragma once

#include "CoreMinimal.h"
#include "Activities/ActivityStation.h"
#include "Activities/MaintenanceActivityStations.h"
#include "Equipment/EquipmentSystem.h"
#include "GameFramework/Actor.h"
#include "Meta/CharacterProfile.h"
#include "Mission/MissionTypes.h"
#include "QuickDemoMissionDirector.generated.h"

class UBoxComponent;
class USceneComponent;
class UTextRenderComponent;

/** Registers and coordinates the authored four-deck quick-demo objective chain. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoMissionDirector : public AActor
{
    GENERATED_BODY()

public:
    AQuickDemoMissionDirector();

    static bool IsObjectiveActive(const UObject* WorldContext, FName ObjectiveId);
    static bool CompleteActiveObjective(const UObject* WorldContext, FName ObjectiveId);

    /**
     * Whether this director resumes a saved checkpoint when the level loads.
     *
     * Defaults to true, which is the behaviour every existing map already relies on. Turned off on
     * the demo map, because a level that exists to be recorded in one take should begin at the
     * beginning: restoring left whoever launched it looking at objectives another session had
     * already ticked off, with the beacons pointing at nothing.
     *
     * This is deliberately narrow. Whether the game wants checkpoints on load at all, and what
     * should invalidate one, is a larger question tracked in TRO-264 and not answered here.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo|Checkpoint")
    bool bRestoreCheckpointOnStart = true;

    /**
     * Seconds between the CIC console finishing and the cut to the title screen.
     *
     * The beat sheet ends on the console booting, a beat to let that read, then title. Zero would
     * cut mid-animation; this is a hold, not a mechanic, so it stays a plain EditAnywhere number
     * rather than something a scenario needs to reason about.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    float TitleCutDelaySeconds = 2.5f;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

public:
    /**
     * The emergency bus: every utility light and practical aboard comes up dull red-amber and
     * flickers, with the odd dropout and a slow beacon pulse, from the moment power is restored.
     * Called live by the power station and again on a checkpoint restore.
     */
    UFUNCTION(BlueprintCallable, Category="Quick Demo")
    void BringUpEmergencyLighting();

private:
    void TickEmergencyFlicker();
    /** The arcing damage: a torn box sparking whatever the bus is doing. Harsh, fast, from the first frame. */
    void TickArcFlicker();
    UPROPERTY(Transient)
    TArray<TObjectPtr<class UPointLightComponent>> ArcLights;
    TArray<float> ArcBaseIntensity;
    FTimerHandle ArcFlickerTimer;

    UPROPERTY(Transient)
    TArray<TObjectPtr<class UPointLightComponent>> EmergencyLights;
    TArray<float> EmergencyBaseIntensity;
    FTimerHandle EmergencyFlickerTimer;
    float EmergencyClock = 0.0f;
    TArray<float> EmergencyDropoutUntil;

public:

private:
    /** The chain's definitions, identical on every machine. */
    void DefineObjectives(class UMissionObjectiveSubsystem* Missions);

    /** Objectives the server has completed, in order; clients mirror them into their own subsystem. */
    UPROPERTY(ReplicatedUsing=OnRep_CompletedObjectives)
    TArray<FName> ReplicatedCompletedObjectives;

    UFUNCTION()
    void OnRep_CompletedObjectives();

    UFUNCTION()
    void HandleObjectiveChanged(FName ObjectiveId, EMissionObjectiveState NewState);

    void RestoreCheckpointState();
    void ApplyRestoredWorldState(const TArray<FName>& CompletedObjectiveIds);
    void ShowTitleCut();

    bool bRestoringCheckpoint = false;
    FTimerHandle TitleCutTimer;
};

/** In-world, non-lighting breadcrumb that is visible only for its active objective. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoObjectiveBeacon : public AActor
{
    GENERATED_BODY()

public:
    AQuickDemoObjectiveBeacon();
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Quick Demo")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Quick Demo")
    TObjectPtr<UTextRenderComponent> MarkerText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FName ObjectiveId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FText MarkerLabel = NSLOCTEXT("QuickDemo", "DefaultBeaconLabel", "OBJECTIVE");

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    UFUNCTION()
    void HandleObjectiveChanged(FName ChangedObjectiveId, EMissionObjectiveState NewState);

    void RefreshVisibility();
    bool bMarkerActive = false;
};

/** One-shot room volume used for workshop and CIC arrival objectives. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoObjectiveTrigger : public AActor
{
    GENERATED_BODY()

public:
    AQuickDemoObjectiveTrigger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Quick Demo")
    TObjectPtr<UBoxComponent> TriggerBounds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FName ObjectiveId = NAME_None;

private:
    UFUNCTION()
    void OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);
};

/** A cryo-bay suit rack that equips a pressure-rated starter suit. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoSuitStation : public AActivityStation
{
    GENERATED_BODY()

public:
    AQuickDemoSuitStation();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FEquipmentItem StarterSuit;

    /** Visible class variant stocked in this cryo-bay recess. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    EPressureSuitRole SuitRole = GinnungagapDefaults::StartingSuitRole;

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    /**
     * The suit itself, hanging from a rail in front of the locker: the Space Marshal the crew will
     * wear, in its rest pose, so the rack reads as a rack and not a cabinet with a prompt. Taken
     * down (hidden everywhere) the first time a crew member suits up here.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Quick Demo|Rack")
    TObjectPtr<class USkeletalMeshComponent> RackSuit;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Quick Demo|Rack")
    TObjectPtr<class UStaticMeshComponent> RackRail;

    /** The wall harness the suit hangs in: the salvage tool rack, bolted to the locker front behind the suit. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Quick Demo|Rack")
    TObjectPtr<class UStaticMeshComponent> RackBacking;

    UPROPERTY(ReplicatedUsing = OnRep_SuitTaken, BlueprintReadOnly, Category = "Quick Demo|Rack")
    bool bSuitTaken = false;

    UFUNCTION()
    void OnRep_SuitTaken();
};

/** Hull-patching activity that removes the demo vacuum zone when complete. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoBreachStation : public AHullPatchingStation
{
    GENERATED_BODY()

public:
    AQuickDemoBreachStation();

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
};

/** Mechanical override for the CIC door, gated behind the breach objective. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoCICAccessStation : public AMechanicalOverrideStation
{
    GENERATED_BODY()

public:
    AQuickDemoCICAccessStation();

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
};

/**
 * The workshop bench the second objective sends the player to.
 *
 * That objective told them to "recover its basic field equipment" and there was nothing there to
 * recover -- no station, no pickups, no way to leave the workshop better equipped than they
 * arrived. This makes the instruction true.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoWorkshopBench : public AComponentReplacementStation
{
    GENERATED_BODY()

public:
    AQuickDemoWorkshopBench();

    /**
     * Handed over on completion.
     *
     * Defaulted in the constructor to the pressure-bottle fastener tool. The comment here used to
     * say "unset by default so a scenario picks its own", which read as a design stance and was in
     * practice the reason the bench granted nothing at all: no scenario ever picked one. Still
     * EditAnywhere, so overriding remains the point -- it just is no longer mandatory.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo|Workshop")
    TSubclassOf<class AShipboardWeapon> GrantedWeaponClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo|Workshop")
    TObjectPtr<class UShipboardWeaponDefinition> GrantedWeaponDefinition;

    /** Supplies stocked on the bench, so the inventory verbs have something to act on. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo|Workshop")
    TArray<TObjectPtr<class UItemDefinition>> GrantedItems;

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
};

/**
 * A bench for putting worn gear back together.
 *
 * Equipment protection scales continuously with durability and nothing in the map restored it, so
 * a run was a one-way slide with nowhere to undo it. Repeatable on purpose: degradation is
 * continuous, so its counter has to be available more than once.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoSuitRepairBench : public AMaintenanceActivityStation
{
    GENERATED_BODY()

public:
    AQuickDemoSuitRepairBench();
};

/** Final tactical-console boot activity inside CIC. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoCICConsole : public ASensorCalibrationStation
{
    GENERATED_BODY()

public:
    AQuickDemoCICConsole();

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
};
