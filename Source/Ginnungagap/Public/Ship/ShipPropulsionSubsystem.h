#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShipPropulsionSubsystem.generated.h"

UCLASS()
class GINNUNGAGAP_API UShipPropulsionSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;
    UFUNCTION(BlueprintCallable, Category = "Ship Propulsion")
    void SetShipThrust(FVector Direction, float Acceleration);

    UFUNCTION(BlueprintCallable, Category = "Ship Propulsion")
    void StopShipThrust();

    UFUNCTION(BlueprintCallable, Category = "Ship Propulsion")
    void HaltShipMotion();

    UFUNCTION(BlueprintCallable, Category = "Ship Propulsion")
    FVector GetPseudoGravity() const;

    UFUNCTION(BlueprintCallable, Category = "Ship Propulsion")
    bool IsShipThrusting() const;

    UFUNCTION(BlueprintPure, Category = "Ship Propulsion")
    FVector GetShipVelocity() const { return ShipVelocity; }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Propulsion")
    float MaximumTravelSpeed = 75000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Propulsion")
    float CoastingDragPerSecond = 0.015f;

protected:
    UPROPERTY(BlueprintReadOnly, Category = "Ship Propulsion")
    FVector ThrustAcceleration = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "Ship Propulsion")
    FVector ShipVelocity = FVector::ZeroVector;
};
