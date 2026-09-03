#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AstrophysicsHazardComponent.generated.h"

USTRUCT(BlueprintType)
struct FPhysicsEnvironmentState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float AmbientPressureKPa = 101.325f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float GravityMultiplier = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float SolarRadiationFlux = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float TemperatureC = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bVacuumZone = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bSolarStormActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bMicrogravityZone = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float DustDensity = 0.0f;
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UAstrophysicsHazardComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAstrophysicsHazardComponent();

protected:
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable)
    float ComputeRadiationDoseSv(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float ShieldingFactor) const;

    UFUNCTION(BlueprintCallable)
    float ComputePressureFailure(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float SuitIntegrity) const;

    UFUNCTION(BlueprintCallable)
    float ComputeMicrogravityInstability(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float Stability) const;

    UFUNCTION(BlueprintCallable)
    float ComputeThermalStress(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float Insulation) const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Hazards")
    float RadiationDoseLimitSv = 0.75f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Hazards")
    float VacuumPressureThresholdKPa = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Hazards")
    float MicrogravityThreshold = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Hazards")
    float ThermalThresholdC = 80.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Hazards")
    float BaseOxygenConsumptionPerSecond = 1.0f;
};
