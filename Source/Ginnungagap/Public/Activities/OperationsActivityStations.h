#pragma once

#include "CoreMinimal.h"
#include "Activities/ActivityStation.h"
#include "OperationsActivityStations.generated.h"

UENUM(BlueprintType)
enum class EOperationsActivityEffect : uint8
{
    RepressurizeAirlock,
    ServiceScrubber,
    BalanceCoolant,
    RecoverBattery,
    StartReactor,
    RepairDrone,
    ServiceTurret,
    PatchSuit,
    ContainSample,
    PurgeBloom
};

UCLASS(Abstract, Blueprintable)
class GINNUNGAGAP_API AOperationsActivityStation : public AActivityStation
{
    GENERATED_BODY()

public:
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Activity|Outcome")
    TObjectPtr<AActor> TargetActor;

    UPROPERTY(VisibleDefaultsOnly, BlueprintReadOnly, Category="Activity|Outcome")
    EOperationsActivityEffect CompletionEffect = EOperationsActivityEffect::RepressurizeAirlock;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Outcome", meta=(ClampMin="0.0", ClampMax="1.0"))
    float EffectStrength = 0.5f;

    /** Persistent result for machinery without a dedicated runtime subsystem yet. */
    UPROPERTY(ReplicatedUsing=OnRep_OperationState, BlueprintReadOnly, Category="Activity|Outcome")
    float OperationalValue = 0.0f;

    UPROPERTY(ReplicatedUsing=OnRep_OperationState, BlueprintReadOnly, Category="Activity|Outcome")
    bool bOperationSecured = false;

    UFUNCTION(BlueprintImplementableEvent, Category="Activity|Outcome")
    void OnOperationStateChanged(float NewOperationalValue, bool bSecured);

    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    void ConfigurePreset(EPlayerActivityType Type, EActivityMechanic Mechanic, const FText& Name, float Duration, int32 Steps = 5);

private:
    UFUNCTION()
    void OnRep_OperationState();
};

UCLASS(Blueprintable)
class GINNUNGAGAP_API AAirlockRepressurizationStation : public AOperationsActivityStation
{ GENERATED_BODY() public: AAirlockRepressurizationStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API AOxygenScrubberServiceStation : public AOperationsActivityStation
{ GENERATED_BODY() public: AOxygenScrubberServiceStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ACoolantBalancingStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ACoolantBalancingStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ABatteryRecoveryStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ABatteryRecoveryStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API AReactorStartupStation : public AOperationsActivityStation
{ GENERATED_BODY() public: AReactorStartupStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ADroneRepairStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ADroneRepairStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ATurretServiceStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ATurretServiceStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ASuitPatchingStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ASuitPatchingStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ASampleContainmentStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ASampleContainmentStation(); };
UCLASS(Blueprintable)
class GINNUNGAGAP_API ABloomPurgingStation : public AOperationsActivityStation
{ GENERATED_BODY() public: ABloomPurgingStation(); };
