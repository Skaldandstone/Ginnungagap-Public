#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShipPowerGridSubsystem.generated.h"

class UShipPowerNodeComponent;

USTRUCT(BlueprintType)
struct FShipPowerBusSnapshot
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") FName BusId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") float Generation = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") float Demand = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") float ServedDemand = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") float StoredPower = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "Ship Power") int32 UnpoweredConsumers = 0;
};

UCLASS()
class GINNUNGAGAP_API UShipPowerGridSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
    void RegisterNode(UShipPowerNodeComponent* Node);
    void UnregisterNode(UShipPowerNodeComponent* Node);
    void MarkGridDirty() { bGridDirty = true; }

    UFUNCTION(BlueprintCallable, Category = "Ship Power")
    void RecalculateGrid(float DeltaTime = 0.0f);

    UFUNCTION(BlueprintPure, Category = "Ship Power")
    FShipPowerBusSnapshot GetBusSnapshot(FName BusId) const;

    UFUNCTION(BlueprintPure, Category = "Ship Power")
    TArray<FShipPowerBusSnapshot> GetAllBusSnapshots() const;

private:
    UPROPERTY() TArray<TObjectPtr<UShipPowerNodeComponent>> Nodes;
    UPROPERTY() TMap<FName, FShipPowerBusSnapshot> BusSnapshots;
    bool bGridDirty = true;
};

