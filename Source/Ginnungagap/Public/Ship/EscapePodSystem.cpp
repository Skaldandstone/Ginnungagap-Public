#include "EscapePodSystem.h"
#include "../CoopSurvivalCharacter.h"

AEscapePodSystem::AEscapePodSystem()
{
    SystemType = EShipSystemType::EscapePod;
}

bool AEscapePodSystem::TryEnterPod(ACoopSurvivalCharacter* Character)
{
    if (!Character || bIsOccupied || !IsFunctioning())
    {
        return false;
    }

    bIsOccupied = true;
    OccupyingCharacter = Character;
    return true;
}

void AEscapePodSystem::ExitPod()
{
    bIsOccupied = false;
    OccupyingCharacter = nullptr;
}

void AEscapePodSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (bIsCorrupted)
    {
        return;
    }

    ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(InteractingPawn);
    if (!Character)
    {
        return;
    }

    if (bIsOccupied && OccupyingCharacter.Get() == Character)
    {
        ExitPod();
    }
    else
    {
        TryEnterPod(Character);
    }
}

void AEscapePodSystem::ApplyCorruptionEffects()
{
    // Occupant fate is resolved by URunOutcomeSubsystem at self-destruct detonation time, not here.
}

void AEscapePodSystem::RemoveCorruptionEffects()
{
}
