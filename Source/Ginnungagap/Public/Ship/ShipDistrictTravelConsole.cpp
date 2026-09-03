#include "Ship/ShipDistrictTravelConsole.h"

#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Mission/MissionObjectiveSubsystem.h"

AShipDistrictTravelConsole::AShipDistrictTravelConsole()
{
    FixtureType = EShipFixtureType::Terminal;
    bToggleOnInteract = false;
    SystemName = TEXT("Ship District Transit Console");
}

bool AShipDistrictTravelConsole::CanTravel() const
{
    if (DestinationMapName.IsNone() || bTravelInProgress || !CanInteractWithFixture())
    {
        return false;
    }
    if (!bRequireResolvedObjectives)
    {
        return true;
    }

    UGameInstance* GameInstance = GetGameInstance();
    const UMissionObjectiveSubsystem* Missions = GameInstance
        ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    return Missions && Missions->AreRequiredObjectivesResolved();
}

void AShipDistrictTravelConsole::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!CanTravel())
    {
        OnTravelDenied.Broadcast();
        return;
    }

    Super::OnInteract_Implementation(InteractingPawn);
    bTravelInProgress = true;
    OnTravelStarted.Broadcast(DestinationMapName);
    UGameplayStatics::OpenLevel(this, DestinationMapName);
}
