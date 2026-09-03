#include "LevelSetup/QuickDemoPowerStation.h"

#include "Components/PointLightComponent.h"
#include "Engine/PointLight.h"
#include "EngineUtils.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "Ship/ModularShipRoom.h"

AQuickDemoPowerStation::AQuickDemoPowerStation()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "RestoreMainBus", "Restore the ship main bus");
    Activity.DurationSeconds = 8.0f;
    Activity.PuzzleSteps = 6;
    RemainingUses = 1;
}

bool AQuickDemoPowerStation::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, TEXT("QD_RestorePower"));
}

void AQuickDemoPowerStation::OnActivityCompleted_Implementation(APawn* Player)
{
    Super::OnActivityCompleted_Implementation(Player);

    if (!HasAuthority())
    {
        return;
    }

    // What comes back is the emergency bus, and it comes back red. The beat sheet has always said
    // "lights recover to an emergency-red state"; this station used to bring the corridors up cool
    // white (0.72, 0.88, 1.0) and drop every room into Nominal's cold blue, so the moment read as
    // the ship being fine. It is not fine. Same colour as the room state so the corridor fixtures
    // and the rooms agree.
    for (TActorIterator<APointLight> It(GetWorld()); It; ++It)
    {
        APointLight* Light = *It;
        if (Light && Light->ActorHasTag(UtilityLightTag))
        {
            if (UPointLightComponent* Component = Light->GetComponentByClass<UPointLightComponent>())
            {
                Component->SetVisibility(true);
                Component->SetIntensity(RestoredLightIntensity);
                Component->SetLightColor(RestoredLightColor);
            }
        }
    }

    for (TActorIterator<AModularShipRoom> It(GetWorld()); It; ++It)
    {
        AModularShipRoom* Room = *It;
        if (Room && Room->ActorHasTag(TEXT("QuickDemoShipRoom")))
        {
            Room->SetEmergencyPower(true);
            Room->SetPowered(true);
        }
    }

    AQuickDemoMissionDirector::CompleteActiveObjective(this, TEXT("QD_RestorePower"));
}
