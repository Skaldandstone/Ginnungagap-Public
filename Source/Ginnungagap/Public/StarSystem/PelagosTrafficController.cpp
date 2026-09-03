#include "StarSystem/PelagosTrafficController.h"

#include "Engine/World.h"
#include "StarSystem/PelagosArrivalDefinition.h"
#include "TimerManager.h"

APelagosTrafficController::APelagosTrafficController()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(false);
}

void APelagosTrafficController::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority() && bAutoStart)
    {
        StartTraffic();
    }
}

void APelagosTrafficController::StartTraffic()
{
    if (!HasAuthority() || !GetWorld())
    {
        return;
    }
    GetWorldTimerManager().SetTimer(SpawnTimer, this,
        &APelagosTrafficController::HandleSpawnTimer, SpawnInterval, true, 0.25f);
}

void APelagosTrafficController::StopTraffic()
{
    GetWorldTimerManager().ClearTimer(SpawnTimer);
}

bool APelagosTrafficController::SpawnNextTrafficActor()
{
    PruneTrafficActors();
    if (!HasAuthority() || !ArrivalDefinition || !TrafficActorClass || !GetWorld()
        || ArrivalDefinition->TrafficSpawns.IsEmpty()
        || ActiveTrafficActors.Num() >= ArrivalDefinition->MaxActiveTraffic)
    {
        return false;
    }

    const int32 SpawnIndex = NextSpawnIndex % ArrivalDefinition->TrafficSpawns.Num();
    const FPelagosTrafficSpawnDefinition& Spawn = ArrivalDefinition->TrafficSpawns[SpawnIndex];
    NextSpawnIndex = (SpawnIndex + 1) % ArrivalDefinition->TrafficSpawns.Num();

    AActor* SpawnedActor = GetWorld()->SpawnActor<AActor>(TrafficActorClass, Spawn.SpawnTransform);
    if (!SpawnedActor)
    {
        return false;
    }

    SpawnedActor->Tags.AddUnique(TEXT("PelagosTraffic"));
    SpawnedActor->Tags.AddUnique(Spawn.RouteId);
    ActiveTrafficActors.Add(SpawnedActor);
    OnTrafficSpawned.Broadcast(Spawn.SpawnId, SpawnedActor);
    return true;
}

int32 APelagosTrafficController::GetActiveTrafficCount() const
{
    int32 ValidActorCount = 0;
    for (const TObjectPtr<AActor>& Actor : ActiveTrafficActors)
    {
        if (IsValid(Actor)) ++ValidActorCount;
    }
    return ValidActorCount;
}

void APelagosTrafficController::HandleSpawnTimer()
{
    SpawnNextTrafficActor();
}

void APelagosTrafficController::PruneTrafficActors()
{
    ActiveTrafficActors.RemoveAll([](const TObjectPtr<AActor>& Actor)
    {
        return !IsValid(Actor);
    });
}
