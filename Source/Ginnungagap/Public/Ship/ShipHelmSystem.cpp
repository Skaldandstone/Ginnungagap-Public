#include "ShipHelmSystem.h"
#include "SensorArraySystem.h"
#include "ShipPropulsionSubsystem.h"
#include "EngineUtils.h"
#include "StarSystem/ResourceNodeActor.h"
#include "HazardZoneActor.h"

AShipHelmSystem::AShipHelmSystem()
{
    SystemType = EShipSystemType::Navigation;
    PrimaryActorTick.bCanEverTick = true;
}

void AShipHelmSystem::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (bIsCorrupted)
    {
        TickNavigationDrift(DeltaTime);
    }

    UpdateTrackedContactSolution();
    if (bHeadingAssistActive)
    {
        if (!CurrentNavigationSolution.bValid || bIsCorrupted)
        {
            EndHeadingAssist();
        }
        else if (UShipPropulsionSubsystem* Propulsion = GetWorld()->GetSubsystem<UShipPropulsionSubsystem>())
        {
            const FVector Velocity = Propulsion->GetShipVelocity();
            const float Speed = Velocity.Size();
            const float StoppingDistance = FMath::Square(Speed) / (2.0f * FMath::Max(1.0f, HeadingAssistAcceleration));
            const FVector ActiveTarget = CurrentNavigationSolution.bUsingSafeDetour
                ? CurrentNavigationSolution.SafeDetourWaypoint
                : IntendedDestination;
            const float ActiveLegRange = FVector::Dist(GetActorLocation(), ActiveTarget);

            if (!CurrentNavigationSolution.bUsingSafeDetour && ActiveLegRange <= ContactArrivalTolerance)
            {
                const FName ArrivedContact = CurrentNavigationSolution.ContactName;
                EndHeadingAssist();
                Propulsion->HaltShipMotion();
                if (LastArrivalContactName != ArrivedContact)
                {
                    LastArrivalContactName = ArrivedContact;
                    OnNavigationContactArrived(ArrivedContact);
                }
            }
            else if (Speed > 1.0f && StoppingDistance >= ActiveLegRange - ContactArrivalTolerance)
            {
                CurrentNavigationSolution.bBraking = true;
                Propulsion->SetShipThrust(-Velocity.GetSafeNormal(), HeadingAssistAcceleration);
            }
            else
            {
                CurrentNavigationSolution.bBraking = false;
                Propulsion->SetShipThrust(CurrentNavigationSolution.DesiredDirection, HeadingAssistAcceleration);
            }
        }
    }
}

FHelmNavigationSolution AShipHelmSystem::UpdateTrackedContactSolution()
{
    CurrentNavigationSolution = FHelmNavigationSolution();
    if (!CachedSensorArray)
    {
        for (TActorIterator<ASensorArraySystem> It(GetWorld()); It; ++It)
        {
            CachedSensorArray = *It;
            break;
        }
    }
    if (!CachedSensorArray || !CachedSensorArray->HasTrackedContact())
    {
        return CurrentNavigationSolution;
    }

    const FSensorContact Contact = CachedSensorArray->GetTrackedContact();
    IntendedDestination = Contact.WorldLocation;
    const FVector ToDestination = IntendedDestination + CurrentHeadingOffset - GetActorLocation();
    CurrentNavigationSolution.bValid = !ToDestination.IsNearlyZero();
    CurrentNavigationSolution.ContactName = Contact.DisplayName;
    CurrentNavigationSolution.ContactType = Contact.Type;
    CurrentNavigationSolution.DesiredDirection = ToDestination.GetSafeNormal();
    CurrentNavigationSolution.RangeKilometers = ToDestination.Size() / 100000.0f;
    CurrentNavigationSolution.HeadingErrorDegrees = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
        FVector::DotProduct(GetActorForwardVector(), CurrentNavigationSolution.DesiredDirection), -1.0f, 1.0f)));
    CurrentNavigationSolution.EstimatedTravelSeconds = CurrentNavigationSolution.RangeKilometers / FMath::Max(0.1f, CruiseSpeedKilometersPerSecond);

    float ClosestClearance = TNumericLimits<float>::Max();
    FVector ClosestHazardLocation = FVector::ZeroVector;
    for (const FSensorContact& SurveyContact : CachedSensorArray->ScanCurrentSystem())
    {
        if (SurveyContact.Type != ESystemPointOfInterestType::Hazard)
        {
            continue;
        }

        const float DestinationDistance = FVector::Dist(SurveyContact.WorldLocation, IntendedDestination);
        CurrentNavigationSolution.bHazardNearDestination |= DestinationDistance <= DestinationHazardWarningRadius;

        const FVector ClosestRoutePoint = FMath::ClosestPointOnSegment(SurveyContact.WorldLocation, GetActorLocation(), IntendedDestination);
        const float RouteClearance = FVector::Dist(SurveyContact.WorldLocation, ClosestRoutePoint);
        if (RouteClearance < ClosestClearance)
        {
            ClosestClearance = RouteClearance;
            CurrentNavigationSolution.ClosestHazardName = SurveyContact.DisplayName;
            CurrentNavigationSolution.ClosestHazardClearanceKilometers = RouteClearance / 100000.0f;
            ClosestHazardLocation = SurveyContact.WorldLocation;
        }
        CurrentNavigationSolution.bRouteIntersectsHazard |= RouteClearance <= DestinationHazardWarningRadius;
    }

    if (CurrentNavigationSolution.bRouteIntersectsHazard && bUseAutomaticSafeDetours)
    {
        const FVector DirectDirection = (IntendedDestination - GetActorLocation()).GetSafeNormal();
        FVector LateralDirection = FVector::CrossProduct(DirectDirection, FVector::UpVector).GetSafeNormal();
        if (LateralDirection.IsNearlyZero())
        {
            LateralDirection = FVector::RightVector;
        }

        // The seedless side choice is stable for a given geometry and avoids route flicker each tick.
        const float Side = FVector::DotProduct(ClosestHazardLocation - GetActorLocation(), GetActorRightVector()) >= 0.0f ? -1.0f : 1.0f;
        CurrentNavigationSolution.SafeDetourWaypoint = ClosestHazardLocation + LateralDirection * Side * DestinationHazardWarningRadius * DetourClearanceMultiplier;
        const float FirstLeg = FVector::Dist(GetActorLocation(), CurrentNavigationSolution.SafeDetourWaypoint);
        const float SecondLeg = FVector::Dist(CurrentNavigationSolution.SafeDetourWaypoint, IntendedDestination);
        CurrentNavigationSolution.DetourTravelSeconds = ((FirstLeg + SecondLeg) / 100000.0f) / FMath::Max(0.1f, CruiseSpeedKilometersPerSecond);
        CurrentNavigationSolution.DesiredDirection = (CurrentNavigationSolution.SafeDetourWaypoint - GetActorLocation()).GetSafeNormal();
        CurrentNavigationSolution.HeadingErrorDegrees = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
            FVector::DotProduct(GetActorForwardVector(), CurrentNavigationSolution.DesiredDirection), -1.0f, 1.0f)));
        CurrentNavigationSolution.bUsingSafeDetour = !CurrentNavigationSolution.DesiredDirection.IsNearlyZero();
    }
    return CurrentNavigationSolution;
}

bool AShipHelmSystem::BeginHeadingAssist()
{
    UpdateTrackedContactSolution();
    bHeadingAssistActive = CurrentNavigationSolution.bValid && !bIsCorrupted &&
        (!CurrentNavigationSolution.bRouteIntersectsHazard || CurrentNavigationSolution.bUsingSafeDetour || bAllowHazardousHeadingAssist);
    return bHeadingAssistActive;
}

void AShipHelmSystem::EndHeadingAssist()
{
    bHeadingAssistActive = false;
    if (UWorld* World = GetWorld())
    {
        if (UShipPropulsionSubsystem* Propulsion = World->GetSubsystem<UShipPropulsionSubsystem>())
        {
            Propulsion->StopShipThrust();
        }
    }
}

void AShipHelmSystem::OnNavigationContactArrived_Implementation(FName ContactName)
{
    if (AResourceNodeActor* PreviousResource = Cast<AResourceNodeActor>(ActiveOperationsTarget))
    {
        PreviousResource->OnResourceNodeDepleted.RemoveDynamic(this, &AShipHelmSystem::HandleResourceNodeDepleted);
        PreviousResource->SetShipOnStation(false);
    }
    ActiveOperationsTarget = nullptr;

    const FVector ContactLocation = IntendedDestination;
    float ClosestDistance = OperationsTargetResolveRadius;
    if (CurrentNavigationSolution.ContactType == ESystemPointOfInterestType::Resource)
    {
        for (TActorIterator<AResourceNodeActor> It(GetWorld()); It; ++It)
        {
            const float Distance = FVector::Dist(It->GetActorLocation(), ContactLocation);
            if (Distance <= ClosestDistance)
            {
                ClosestDistance = Distance;
                ActiveOperationsTarget = *It;
            }
        }
        if (AResourceNodeActor* Resource = Cast<AResourceNodeActor>(ActiveOperationsTarget))
        {
            Resource->OnResourceNodeDepleted.AddUniqueDynamic(this, &AShipHelmSystem::HandleResourceNodeDepleted);
            Resource->SetShipOnStation(true);
        }
    }
    else if (CurrentNavigationSolution.ContactType == ESystemPointOfInterestType::Hazard)
    {
        for (TActorIterator<AHazardZoneActor> It(GetWorld()); It; ++It)
        {
            const float Distance = FVector::Dist(It->GetActorLocation(), ContactLocation);
            if (Distance <= ClosestDistance)
            {
                ClosestDistance = Distance;
                ActiveOperationsTarget = *It;
            }
        }
    }

    OnOperationsTargetChanged.Broadcast(CurrentNavigationSolution.ContactType, ActiveOperationsTarget);
}

void AShipHelmSystem::HandleResourceNodeDepleted(AResourceNodeActor* ResourceNode)
{
    if (ActiveOperationsTarget != ResourceNode)
    {
        return;
    }

    ResourceNode->OnResourceNodeDepleted.RemoveDynamic(this, &AShipHelmSystem::HandleResourceNodeDepleted);
    ActiveOperationsTarget = nullptr;
    LastArrivalContactName = NAME_None;
    OnOperationsTargetChanged.Broadcast(ESystemPointOfInterestType::Resource, nullptr);
}

void AShipHelmSystem::TickNavigationDrift(float DeltaTime)
{
    const FVector RandomDrift = FVector(
        FMath::FRandRange(-1.0f, 1.0f),
        FMath::FRandRange(-1.0f, 1.0f),
        FMath::FRandRange(-1.0f, 1.0f)
    );

    CurrentHeadingOffset += RandomDrift * MaxDriftPerSecond * DeltaTime;
}

void AShipHelmSystem::ConsumeHeadingOffset(float ReductionFraction)
{
    CurrentHeadingOffset *= 1.0f - FMath::Clamp(ReductionFraction, 0.0f, 1.0f);
}

void AShipHelmSystem::ApplyCorruptionEffects()
{
    // Drift accumulation begins in Tick while bIsCorrupted is true.
    EndHeadingAssist();
}

void AShipHelmSystem::RemoveCorruptionEffects()
{
    CurrentHeadingOffset = FVector::ZeroVector;
}
