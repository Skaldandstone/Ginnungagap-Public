#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ShipPowerNodeComponent.generated.h"

UENUM(BlueprintType)
enum class EShipPowerNodeRole : uint8
{
    Generator,
    Storage,
    Consumer
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnShipPowerStateChanged, bool, bPowered);

UCLASS(ClassGroup = (Ship), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UShipPowerNodeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UShipPowerNodeComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category = "Ship Power")
    void SetNodeOnline(bool bNewOnline);

    UFUNCTION(BlueprintCallable, Category = "Ship Power")
    void SetDamageFraction(float NewDamageFraction);

    UFUNCTION(BlueprintPure, Category = "Ship Power")
    float GetEffectiveGeneration() const;

    UFUNCTION(BlueprintPure, Category = "Ship Power")
    float GetEffectiveDemand() const;

    UFUNCTION(BlueprintPure, Category = "Ship Power")
    bool IsPowered() const { return bPowered; }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power")
    EShipPowerNodeRole Role = EShipPowerNodeRole::Consumer;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power")
    FName BusId = TEXT("Main");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0"))
    int32 Priority = 50;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float GenerationUnits = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float DemandUnits = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float StorageCapacityUnits = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float StoredPowerUnits = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float MaxChargeRate = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0"))
    float MaxDischargeRate = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Power", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MinimumPowerFraction = 1.0f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Ship Power")
    bool bOnline = true;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Ship Power", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float DamageFraction = 0.0f;

    UPROPERTY(ReplicatedUsing = OnRep_PowerState, BlueprintReadOnly, Category = "Ship Power")
    bool bPowered = true;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Ship Power")
    float AllocatedPowerUnits = 0.0f;

    UPROPERTY(BlueprintAssignable, Category = "Ship Power")
    FOnShipPowerStateChanged OnPowerStateChanged;

    void ApplyAllocation(float NewAllocatedPower, bool bNewPowered);
    void NotifyGridDirty();

private:
    UFUNCTION()
    void OnRep_PowerState();
};

