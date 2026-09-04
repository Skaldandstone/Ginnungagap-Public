#include "BulkheadDoor.h"
#include "Components/SceneComponent.h"
#include "Ship/ShipSection.h"
#include "TimerManager.h"

ABulkheadDoor::ABulkheadDoor()
{
    SystemType = EShipSystemType::Door;
    RoomSideHardpoint = CreateDefaultSubobject<USceneComponent>(TEXT("RoomSideHardpoint"));
    RoomSideHardpoint->SetupAttachment(RootComponent);
    RoomSideHardpoint->SetRelativeLocation(FVector(-110.0f, 0.0f, 110.0f));
    CorridorSideHardpoint = CreateDefaultSubobject<USceneComponent>(TEXT("CorridorSideHardpoint"));
    CorridorSideHardpoint->SetupAttachment(RootComponent);
    CorridorSideHardpoint->SetRelativeLocation(FVector(110.0f, 0.0f, 110.0f));
}

void ABulkheadDoor::ConfigureThresholdSides(AShipSection* InRoomSection, AShipSection* InCorridorSection)
{
    RoomSection = InRoomSection;
    CorridorSection = InCorridorSection;
    Tags.AddUnique(TEXT("RoomThresholdDoor"));
    if (RoomSection)
    {
        Tags.AddUnique(FName(*FString::Printf(TEXT("RoomSection_%d"), RoomSection->SectionID)));
    }
}

void ABulkheadDoor::Seal()
{
    if (!CanBeSealed())
    {
        return;
    }

    bIsSealed = true;
}

void ABulkheadDoor::Unseal()
{
    bIsSealed = false;
}

bool ABulkheadDoor::CanBeSealed() const
{
    return !bIsCorrupted;
}

float ABulkheadDoor::GetTransferMultiplier() const
{
    return bIsSealed ? SealedLeakFactor : 1.0f;
}

bool ABulkheadDoor::IsPassable() const
{
    return !bIsSealed;
}

void ABulkheadDoor::SetLocked(bool bInLocked)
{
    bLocked = bInLocked;
    ForceNetUpdate();
}

FText ABulkheadDoor::GetInteractionPrompt_Implementation(APawn* Viewer) const
{
    // What the door offers, in words: the HUD otherwise shows the placement label.
    if (bIsCorrupted) return NSLOCTEXT("BulkheadDoor", "Corrupted", "Bulkhead fouled: purge the growth first");
    if (bIsCycling) return NSLOCTEXT("BulkheadDoor", "Cycling", "Bulkhead cycling...");
    if (bLocked && bIsSealed)
    {
        return LockedReason.IsEmpty() ? NSLOCTEXT("BulkheadDoor", "Locked", "Bulkhead locked")
                                      : FText::Format(NSLOCTEXT("BulkheadDoor", "LockedWhy", "Bulkhead locked: {0}"), LockedReason);
    }
    return bIsSealed ? NSLOCTEXT("BulkheadDoor", "Open", "Open bulkhead") : NSLOCTEXT("BulkheadDoor", "Seal", "Seal bulkhead");
}

void ABulkheadDoor::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (bIsCorrupted || bIsCycling || (bLocked && bIsSealed))
    {
        return;
    }

    bIsCycling = true;
    GetWorldTimerManager().SetTimer(CycleTimerHandle, this, &ABulkheadDoor::FinishCycle, CycleDuration, false);
}

void ABulkheadDoor::FinishCycle()
{
    bIsCycling = false;

    if (bIsCorrupted)
    {
        return;
    }

    if (bIsSealed)
    {
        Unseal();
    }
    else
    {
        Seal();
    }
}

void ABulkheadDoor::ApplyCorruptionEffects()
{
    GetWorldTimerManager().ClearTimer(CycleTimerHandle);
    bIsCycling = false;
    bIsSealed = false;
}

void ABulkheadDoor::RemoveCorruptionEffects()
{
    // Door stays open after purging; a player must manually reseal it.
}
