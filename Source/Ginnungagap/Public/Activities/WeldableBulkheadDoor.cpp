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

    // A door welded shut in an earlier emergency is not a wall: the same tool path, run the other
    // way, cuts the seam and the door is a door again.
    CuttingActivity.Type = EPlayerActivityType::Welding;
    CuttingActivity.Mechanic = EActivityMechanic::ToolPath;
    CuttingActivity.DisplayName = NSLOCTEXT("Activities", "CutDoorSeam", "Cut emergency weld");
    CuttingActivity.DurationSeconds = 10.0f;
    CuttingActivity.ToolPathTolerance = 0.22f;
    CuttingActivity.MaxRange = 220.0f;
    CuttingActivity.bBloomSensitive = true;
}

void AWeldableBulkheadDoor::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!InteractingPawn) return;
    if (bWeldedShut)
    {
        if (UPlayerActivityComponent* Activity = InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
            Activity->StartActivity(this, CuttingActivity);
        return;
    }
    // Close first: welding an open or moving door cannot produce a pressure seal.
    if (!bIsSealed)
    {
        if (CanBeSealed()) Seal();
        else return;
    }
    if (UPlayerActivityComponent* Activity = InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
        Activity->StartActivity(this, IPlayerActivitySource::Execute_GetActivityDefinition(this, InteractingPawn));
}

FPlayerActivityDefinition AWeldableBulkheadDoor::GetActivityDefinition_Implementation(APawn* Player) const
{
    return bWeldedShut ? CuttingActivity : WeldingActivity;
}

bool AWeldableBulkheadDoor::CanStartActivity_Implementation(APawn* Player) const
{
    if (!Player || bIsCorrupted) return false;
    return bWeldedShut || bIsSealed;
}

void AWeldableBulkheadDoor::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority()) return;
    if (bWeldedShut)
    {
        // Cut free, and open: nobody cuts a seam to leave the door shut.
        CutEmergencyWeld();
        Super::Unseal();
        return;
    }
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
