// Copyright Epic Games, Inc. All Rights Reserved.

#include "AstrophysicsHazardComponent.h"

UAstrophysicsHazardComponent::UAstrophysicsHazardComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UAstrophysicsHazardComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UAstrophysicsHazardComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

float UAstrophysicsHazardComponent::ComputeRadiationDoseSv(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float ShieldingFactor) const
{
    // Base dose scales with solar flux; solar storms multiply it; shielding reduces it.
    float DoseRate = EnvironmentState.SolarRadiationFlux * (EnvironmentState.bSolarStormActive ? 5.0f : 1.0f);
    float ShieldedDose = DoseRate * FMath::Clamp(1.0f - ShieldingFactor, 0.0f, 1.0f);
    return ShieldedDose * DeltaTime;
}

float UAstrophysicsHazardComponent::ComputePressureFailure(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float SuitIntegrity) const
{
    // If ambient pressure is below the vacuum threshold, degrade proportional to how compromised the suit is.
    if (EnvironmentState.bVacuumZone || EnvironmentState.AmbientPressureKPa < VacuumPressureThresholdKPa)
    {
        float IntegrityDeficit = FMath::Clamp(1.0f - SuitIntegrity, 0.0f, 1.0f);
        return IntegrityDeficit * DeltaTime;
    }
    return 0.0f;
}

float UAstrophysicsHazardComponent::ComputeMicrogravityInstability(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float Stability) const
{
    if (EnvironmentState.bMicrogravityZone)
    {
        float StabilityDeficit = FMath::Clamp(MicrogravityThreshold - Stability, 0.0f, 1.0f);
        return StabilityDeficit * DeltaTime;
    }
    return 0.0f;
}

float UAstrophysicsHazardComponent::ComputeThermalStress(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float Insulation) const
{
    float TempDeltaAboveThreshold = FMath::Max(0.0f, EnvironmentState.TemperatureC - ThermalThresholdC);
    float InsulatedStress = TempDeltaAboveThreshold * FMath::Clamp(1.0f - Insulation, 0.0f, 1.0f);
    return InsulatedStress * DeltaTime * 0.01f;
}