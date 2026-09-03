#include "Activities/WeldableBulkheadDoor.h"
#include "Activities/PlayerActivityComponent.h"
#include "Net/UnrealNetwork.h"

AWeldableBulkheadDoor::AWeldableBulkheadDoor()
{
    WeldingActivity.Type = EPlayerActivityType::Welding;
    WeldingActivity.Mechanic = EActivityMechanic::ToolPath;
    WeldingActivity.DisplayName = NSLOCTEXT("Activities", "WeldDoorSeam", "Emergency seam weld");
    WeldingActivity.DurationSeconds = 8.0f;
    WeldingActivity.ToolPathTolerance = 0.22f;
    WeldingActivity.MaxRange = 220.0f;
    WeldingActivity.bBloomSensitive = true;
}

void AWeldableBulkheadDoor::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!InteractingPawn || bWeldedShut) return;
    // Close first: welding an open or moving door cannot produce a pressure seal.
    if (!bIsSealed)
    {
        if (CanBeSealed()) Seal();
        else return;
    }
    if (UPlayerActivityComponent* Activity = InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
        Activity->StartActivity(this, IPlayerActivitySource::Execute_GetActivityDefinition(this, InteractingPawn));
}

FPlayerActivityDefinition AWeldableBulkheadDoor::GetActivityDefinition_Implementation(APawn* Player) const { return WeldingActivity; }

bool AWeldableBulkheadDoor::CanStartActivity_Implementation(APawn* Player) const
{
    return Player && bIsSealed && !bWeldedShut && !bIsCorrupted;
}

void AWeldableBulkheadDoor::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority()) return;
    bWeldedShut = true;
    Seal();
    OnWeldStateChanged(true);
}

void AWeldableBulkheadDoor::CutEmergencyWeld()
{
    if (!HasAuthority() || !bWeldedShut) return;
    bWeldedShut = false;
    OnWeldStateChanged(false);
}

void AWeldableBulkheadDoor::Unseal()
{
    if (!bWeldedShut) Super::Unseal();
}

bool AWeldableBulkheadDoor::IsPassable() const { return !bWeldedShut && Super::IsPassable(); }

void AWeldableBulkheadDoor::OnRep_WeldedShut() { OnWeldStateChanged(bWeldedShut); }

void AWeldableBulkheadDoor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AWeldableBulkheadDoor, bWeldedShut);
}
