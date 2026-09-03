#include "Ship/ShipObjectiveConsole.h"

#include "Engine/GameInstance.h"
#include "Mission/MissionObjectiveSubsystem.h"

AShipObjectiveConsole::AShipObjectiveConsole()
{
    FixtureType = EShipFixtureType::Terminal;
    bToggleOnInteract = false;
    SystemName = TEXT("District Objective Console");
}

void AShipObjectiveConsole::OnInteract_Implementation(APawn* InteractingPawn)
{
    if ((bSingleUse && bObjectiveResolved) || !CanInteractWithFixture())
    {
        return;
    }

    Super::OnInteract_Implementation(InteractingPawn);
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            bObjectiveResolved = Missions->CompleteObjective(ObjectiveId);
        }
    }
}
