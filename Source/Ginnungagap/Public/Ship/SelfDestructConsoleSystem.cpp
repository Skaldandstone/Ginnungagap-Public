#include "SelfDestructConsoleSystem.h"
#include "../Meta/RunOutcomeSubsystem.h"
#include "Engine/GameInstance.h"

ASelfDestructConsoleSystem::ASelfDestructConsoleSystem()
{
    SystemType = EShipSystemType::SelfDestruct;
}

void ASelfDestructConsoleSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (bIsCorrupted)
    {
        return;
    }

    OnSelfDestructConsoleOpened();
    if (bArmOnInteractForNativeDemo)
    {
        ConfirmArm();
    }
}

bool ASelfDestructConsoleSystem::ConfirmArm()
{
    if (bIsCorrupted)
    {
        return false;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (URunOutcomeSubsystem* RunOutcome = GI->GetSubsystem<URunOutcomeSubsystem>())
        {
            return RunOutcome->ArmSelfDestruct();
        }
    }

    return false;
}

bool ASelfDestructConsoleSystem::ConfirmCancel()
{
    if (UGameInstance* GI = GetGameInstance())
    {
        if (URunOutcomeSubsystem* RunOutcome = GI->GetSubsystem<URunOutcomeSubsystem>())
        {
            return RunOutcome->CancelSelfDestruct();
        }
    }

    return false;
}

void ASelfDestructConsoleSystem::ApplyCorruptionEffects()
{
    // Corrupted consoles simply refuse interaction (see OnInteract_Implementation); no additional state to unwind.
}

void ASelfDestructConsoleSystem::RemoveCorruptionEffects()
{
}
