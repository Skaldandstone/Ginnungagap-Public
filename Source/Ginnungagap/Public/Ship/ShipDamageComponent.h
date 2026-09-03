#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipDamageComponent.generated.h"

UENUM(BlueprintType)
enum class EShipDamageType : uint8
{
    HullImpact,
    Breach,
    Fire,
    Electrical
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnShipDamageStateChanged);

UCLASS(ClassGroup = (Ship), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UShipDamageComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UShipDamageComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category = "Damage Control")
    void ApplyShipDamage(EShipDamageType DamageType, float Severity);

    UFUNCTION(BlueprintCallable, Category = "Damage Control")
    bool RepairHull(float RepairAmount);

    UFUNCTION(BlueprintCallable, Category = "Damage Control")
    bool SealBreach(float RepairAmount);

    UFUNCTION(BlueprintCallable, Category = "Damage Control")
    bool SuppressFire(float SuppressionAmount);

    UFUNCTION(BlueprintCallable, Category = "Damage Control")
    bool RepairElectricalFault(float RepairAmount);

    UFUNCTION(BlueprintPure, Category = "Damage Control")
    bool HasCriticalDamage() const;

    UFUNCTION(BlueprintPure, Category = "Damage Control")
    float GetDangerScore() const;

    UPROPERTY(ReplicatedUsing = OnRep_DamageState, BlueprintReadOnly, Category = "Damage Control")
    float HullIntegrity = 1.0f;

    UPROPERTY(ReplicatedUsing = OnRep_DamageState, BlueprintReadOnly, Category = "Damage Control")
    float BreachSeverity = 0.0f;

    UPROPERTY(ReplicatedUsing = OnRep_DamageState, BlueprintReadOnly, Category = "Damage Control")
    float FireIntensity = 0.0f;

    UPROPERTY(ReplicatedUsing = OnRep_DamageState, BlueprintReadOnly, Category = "Damage Control")
    float ElectricalFaultSeverity = 0.0f;

    UPROPERTY(ReplicatedUsing = OnRep_DamageState, BlueprintReadOnly, Category = "Damage Control")
    float AtmospherePercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage Control", meta = (ClampMin = "0.0"))
    float BreachAtmosphereLossPerSecond = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage Control", meta = (ClampMin = "0.0"))
    float FireAtmosphereLossPerSecond = 3.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage Control", meta = (ClampMin = "0.0"))
    float FireHullDamagePerSecond = 0.01f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Damage Control", meta = (ClampMin = "0.0"))
    float PassiveRepressurizationPerSecond = 4.0f;

    UPROPERTY(BlueprintAssignable, Category = "Damage Control")
    FOnShipDamageStateChanged OnDamageStateChanged;

private:
    UFUNCTION()
    void OnRep_DamageState();

    void NotifyChanged();
    void UpdateAffectedShipSystems();
};

