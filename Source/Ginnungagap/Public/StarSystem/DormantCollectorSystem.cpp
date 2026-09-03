#include "DormantCollectorSystem.h"
#include "../Bloom/BloomDirector.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"

ADormantCollectorSystem::ADormantCollectorSystem()
{
    SystemType = EShipSystemType::Collector;
}

void ADormantCollectorSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!CanBeginReactivation())
    {
        return;
    }

    bIsReactivating = true;
    GetWorldTimerManager().SetTimer(ReactivationTimerHandle, this, &ADormantCollectorSystem::FinishReactivation, ReactivationDuration, false);
}

bool ADormantCollectorSystem::CanBeginReactivation() const
{
    return !bIsCorrupted && !bIsReactivating && !bIsReactivated;
}

void ADormantCollectorSystem::FinishReactivation()
{
    bIsReactivating = false;

    if (bIsCorrupted)
    {
        return;
    }

    bIsReactivated = true;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            Director->RegisterPlayerAction(EBloomPlayerActionType::ReactivatedShipSystem);
        }
    }
}

void ADormantCollectorSystem::ApplyCorruptionEffects()
{
    GetWorldTimerManager().ClearTimer(ReactivationTimerHandle);
    bIsReactivating = false;
    bIsReactivated = false;
}

void ADormantCollectorSystem::RemoveCorruptionEffects()
{
    // Stays deactivated after purging - a player must manually reactivate it, mirroring ABulkheadDoor.
}
