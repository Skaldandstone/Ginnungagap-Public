#pragma once

#include "CoreMinimal.h"
#include "Activities/ActivityStation.h"
#include "MaintenanceActivityStations.generated.h"

class UItemDefinition;

UENUM(BlueprintType)
enum class EMaintenanceActivityEffect : uint8
{
    RepairHull,
    SuppressFire,
    SealBreach,
    ReplaceComponent,
    FabricateItem,
    CalibrateSensor,
    Decontaminate,
    StabilizePatient,
    RerouteBreaker,
    ToggleMechanicalOverride,

    // Appended rather than inserted: these values are serialized into placed stations, so
    // reordering would silently repurpose every one already in a map.
    RepairSuit
};

/** Shared completion plumbing; the ten subclasses below provide grounded designer-ready presets. */
UCLASS(Abstract, Blueprintable)
class GINNUNGAGAP_API AMaintenanceActivityStation : public AActivityStation
{
    GENERATED_BODY()

public:
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Activity|Outcome")
    TObjectPtr<AActor> TargetActor;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category="Activity|Outcome")
    EMaintenanceActivityEffect CompletionEffect = EMaintenanceActivityEffect::RepairHull;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Outcome", meta=(ClampMin="0.0"))
    float EffectStrength = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Resources")
    TObjectPtr<UItemDefinition> RequiredItem;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Resources", meta=(ClampMin="0"))
    int32 RequiredItemCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Fabrication")
    TObjectPtr<UItemDefinition> FabricatedItem;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Fabrication", meta=(ClampMin="1"))
    int32 FabricatedItemCount = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Construction")
    TSubclassOf<AActor> ConstructedActorClass;

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;

protected:
    void ConfigurePreset(EPlayerActivityType Type, EActivityMechanic Mechanic, const FText& Name, float Duration, int32 Steps = 5);
};

UCLASS(Blueprintable)
class GINNUNGAGAP_API AHullPatchingStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: AHullPatchingStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API AFireSuppressionStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: AFireSuppressionStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API APipeSealingStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: APipeSealingStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API AComponentReplacementStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: AComponentReplacementStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API AFabricationStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: AFabricationStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API ASensorCalibrationStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: ASensorCalibrationStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API ADecontaminationStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: ADecontaminationStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API AMedicalStabilizationStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: AMedicalStabilizationStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API ABreakerReroutingStation : public AMaintenanceActivityStation
{ GENERATED_BODY() public: ABreakerReroutingStation(); };

UCLASS(Blueprintable)
class GINNUNGAGAP_API AMechanicalOverrideStation : public AMaintenanceActivityStation
{
    GENERATED_BODY()

public:
    AMechanicalOverrideStation();

    /** The panel refuses anyone not sealed in a pressure suit: what is beyond the door has no air. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Maintenance")
    bool bRequiresPressureSuit = false;

    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
};
