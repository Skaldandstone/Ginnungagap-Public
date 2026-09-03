#pragma once

#include "CoreMinimal.h"
#include "Bloom/BloomCorruptible.h"
#include "GameFramework/Actor.h"
#include "Interfaces/Interactable.h"
#include "ShipboardRobotArchetypes.generated.h"

class UBoxComponent;
class UPointLightComponent;
class USceneComponent;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EShipboardRobotRole : uint8
{
    Maintenance,
    Utility,
    Cargo,
    Security
};

UENUM(BlueprintType)
enum class EShipboardRobotState : uint8
{
    Standby,
    Working,
    Disabled,
    Corrupted
};

USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipboardRobotCapabilities
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
    float WorkRate = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
    float RepairOutput = 0.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot", meta = (Units = "kg"))
    float CarryCapacityKg = 0.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot", meta = (Units = "cm"))
    float SensorRangeCm = 1500.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
    float PowerDrainPerWorkUnit = 0.01f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
    FShipboardRobotStateChanged,
    EShipboardRobotState,
    PreviousState,
    EShipboardRobotState,
    NewState);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
    FShipboardRobotResourcesChanged,
    float,
    IntegrityFraction,
    float,
    BatteryFraction);

/**
 * Clean shipboard robot master. The rigid visual parts remain separate so each
 * chassis can later receive a Control Rig without using a RealityScan shell as
 * its animation source.
 */
UCLASS(Abstract, Blueprintable)
class GINNUNGAGAP_API AShipboardRobotBase : public AActor, public IBloomCorruptible, public IInteractable
{
    GENERATED_BODY()

public:
    AShipboardRobotBase();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<USceneComponent> AssemblyRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UBoxComponent> CollisionBounds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Feedback")
    TObjectPtr<UPointLightComponent> StatusLight;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
    EShipboardRobotRole RobotRole = EShipboardRobotRole::Maintenance;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Robot")
    bool bOperational = true;

    UPROPERTY(BlueprintReadOnly, Replicated, Category = "Robot")
    bool bWorking = false;

    UPROPERTY(BlueprintReadOnly, Replicated, Category = "Robot|Bloom")
    bool bBloomCorrupted = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Resources", meta = (ClampMin = "1.0"))
    float MaxIntegrity = 100.0f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, ReplicatedUsing = OnRep_Resources, Category = "Robot|Resources")
    float CurrentIntegrity = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_Resources, Category = "Robot|Resources", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float BatteryCharge = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
    FShipboardRobotCapabilities Capabilities;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, ReplicatedUsing = OnRep_RobotState, Category = "Robot")
    EShipboardRobotState RobotState = EShipboardRobotState::Standby;

    UPROPERTY(BlueprintAssignable, Category = "Robot")
    FShipboardRobotStateChanged OnRobotStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Robot|Resources")
    FShipboardRobotResourcesChanged OnRobotResourcesChanged;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot")
    void SetOperational(bool bNewOperational);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot")
    void SetWorking(bool bNewWorking);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot|Resources")
    float ApplyRobotDamage(float DamageAmount);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot|Resources")
    float RepairRobot(float RepairAmount, bool bReactivate = false);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot|Resources")
    float ConsumePower(float RequestedCharge);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot|Resources")
    float RechargeRobot(float ChargeAmount, bool bReactivate = false);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot")
    float AdvanceWork(float WorkUnits);

    UFUNCTION(BlueprintPure, Category = "Robot")
    bool CanPerformWork() const;

    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
        class AController* EventInstigator, AActor* DamageCauser) override;

    virtual void OnInteract_Implementation(APawn* InstigatorPawn) override;

    virtual void OnBloomCorruption_Implementation() override;
    virtual void OnBloomPurged_Implementation() override;
    virtual bool CanBeBloomCorrupted_Implementation() const override;

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

    void RefreshRobotState();
    void UpdateStatusLight();

    UFUNCTION()
    void OnRep_RobotState(EShipboardRobotState PreviousState);

    UFUNCTION()
    void OnRep_Resources();

    bool bWasWorkingBeforeCorruption = false;

    UFUNCTION(BlueprintImplementableEvent, Category = "Robot")
    void ReceiveOperationalStateChanged(bool bIsOperational);

    UFUNCTION(BlueprintImplementableEvent, Category = "Robot")
    void ReceiveRobotStateChanged(EShipboardRobotState PreviousState, EShipboardRobotState NewState);

    UFUNCTION(BlueprintImplementableEvent, Category = "Robot|Resources")
    void ReceiveRobotResourcesChanged(float IntegrityFraction, float BatteryFraction);

    UFUNCTION(BlueprintImplementableEvent, Category = "Robot|Bloom")
    void ReceiveBloomStateChanged(bool bIsCorrupted);
};

/** Low, stable maintenance chassis built from JACK limbs and a dedicated Fab scanner/tool package. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ACompactMaintenanceRobot : public AShipboardRobotBase
{
    GENERATED_BODY()

public:
    ACompactMaintenanceRobot();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Chassis;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> SensorHead;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontLeftLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontRightLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearLeftLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearRightLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> ToolArm;
};

/** Tall inspection and manipulation chassis derived directly from the Fab JACK kit. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ATallUtilityRobot : public AShipboardRobotBase
{
    GENERATED_BODY()

public:
    ATallUtilityRobot();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Body;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Head;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> LeftArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RightArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> LeftLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RightLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> ChestDisplay;
};

/** Broad powered cargo chassis using JACK parts, equipment pods, and a mechanical cargo crane. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AHeavyCargoRobot : public AShipboardRobotBase
{
    GENERATED_BODY()

public:
    AHeavyCargoRobot();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Body;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Head;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> LeftArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RightArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> LeftLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RightLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> LeftCargoPod;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RightCargoPod;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> IndustrialTool;
};

/** Low magnetic crawler with four articulated surface clamps, a scanner mast, and a response arm. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ASecuritySentryRobot : public AShipboardRobotBase
{
    GENERATED_BODY()

public:
    ASecuritySentryRobot();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> Chassis;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> ArmorBody;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontLeftClamp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontRightClamp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearLeftClamp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearRightClamp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontLeftMagPad;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> FrontRightMagPad;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearLeftMagPad;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> RearRightMagPad;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> SensorHead;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> ResponseArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Assembly")
    TObjectPtr<UStaticMeshComponent> PowerPod;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Magnetic Anchoring", meta = (ClampMin = "0.0", Units = "N"))
    float MagneticClampStrengthNewtons = 18000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Robot|Magnetic Anchoring")
    bool bMagneticAnchorsEngaged = true;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Robot|Magnetic Anchoring")
    void SetMagneticAnchorsEngaged(bool bEngaged);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
