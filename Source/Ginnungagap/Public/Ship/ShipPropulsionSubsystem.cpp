#include "ShipPropulsionSubsystem.h"
#include "StarSystem/ProceduralStarSystemMap.h"
#include "EngineUtils.h"

void UShipPropulsionSubsystem::Tick(float DeltaTime)
{
    if (!GetWorld() || DeltaTime <= 0.0f)
    {
        return;
    }

    ShipVelocity += ThrustAcceleration * DeltaTime;
    ShipVelocity = ShipVelocity.GetClampedToMaxSize(MaximumTravelSpeed);
    if (ThrustAcceleration.IsNearlyZero())
    {
        ShipVelocity *= FMath::Max(0.0f, 1.0f - CoastingDragPerSecond * DeltaTime);
    }

    const FVector ExteriorTranslation = -ShipVelocity * DeltaTime;
    if (ExteriorTranslation.IsNearlyZero())
    {
        return;
    }

    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->ActorHasTag(TEXT("GeneratedSystemContent")))
        {
            continue;
        }
        if (AProceduralStarSystemMap* SystemMap = Cast<AProceduralStarSystemMap>(Actor))
        {
            SystemMap->TranslateSystem(ExteriorTranslation);
        }
        else
        {
            Actor->AddActorWorldOffset(ExteriorTranslation, false);
        }
    }
}

TStatId UShipPropulsionSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UShipPropulsionSubsystem, STATGROUP_Tickables);
}

void UShipPropulsionSubsystem::SetShipThrust(FVector Direction, float Acceleration)
{
    ThrustAcceleration = Direction.GetSafeNormal() * Acceleration;
}

void UShipPropulsionSubsystem::StopShipThrust()
{
    ThrustAcceleration = FVector::ZeroVector;
}

void UShipPropulsionSubsystem::HaltShipMotion()
{
    ThrustAcceleration = FVector::ZeroVector;
    ShipVelocity = FVector::ZeroVector;
}

FVector UShipPropulsionSubsystem::GetPseudoGravity() const
{
    return -ThrustAcceleration;
}

bool UShipPropulsionSubsystem::IsShipThrusting() const
{
    return !ThrustAcceleration.IsNearlyZero();
}
