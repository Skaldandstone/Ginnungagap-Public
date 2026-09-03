#include "ShipSystemActor.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "Components/StaticMeshComponent.h"

AShipSystemActor::AShipSystemActor()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    PowerNode = CreateDefaultSubobject<UShipPowerNodeComponent>(TEXT("PowerNode"));
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    RootComponent = VisualMesh;
}

void AShipSystemActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (!VisualMesh || VisualMesh->GetStaticMesh()) return;
    const TCHAR* Path = nullptr;
    switch (SystemType)
    {
    case EShipSystemType::Cryo: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_CryoPod.SM_System_CryoPod"); break;
    case EShipSystemType::LifeSupport: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_LifeSupport.SM_System_LifeSupport"); break;
    case EShipSystemType::Sensors: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_SensorConsole.SM_System_SensorConsole"); break;
    // Navigation had no case, so every helm ever placed spawned invisible: collision and
    // interaction prompt present, nothing to see. Deliberately not the jump console mesh even
    // though both are bridge stations -- two identical consoles side by side in the CIC would
    // read as one duplicated actor rather than two different jobs.
    case EShipSystemType::Navigation: Path = TEXT("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal.SM_Prop_WallTerminal"); break;
    // The remaining four had no case either, for the same reason Navigation did not: nothing in
    // any map places one, so nobody ever saw them spawn with nothing to draw. Filled in now rather
    // than left as a trap for whoever places the first door or comms panel and spends an afternoon
    // wondering why their actor has collision and an interaction prompt and no geometry.
    //
    // Lighting and Comms share the wall terminal because both are panels on a bulkhead; a door is
    // structural and takes the bulkhead mesh the production doors already use; self destruct takes
    // the jump console, being the other console someone stands at to commit to something.
    case EShipSystemType::Lighting: Path = TEXT("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal.SM_Prop_WallTerminal"); break;
    case EShipSystemType::Comms: Path = TEXT("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal.SM_Prop_WallTerminal"); break;
    case EShipSystemType::Door: Path = TEXT("/Game/Assets/Ships/Production/Meshes/SM_Kit_BulkheadDoor.SM_Kit_BulkheadDoor"); break;
    case EShipSystemType::SelfDestruct: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_JumpConsole.SM_System_JumpConsole"); break;
    case EShipSystemType::JumpDrive: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_JumpConsole.SM_System_JumpConsole"); break;
    case EShipSystemType::EscapePod: Path = TEXT("/Game/Assets/Models/ShipSystems/SM_System_EscapePod.SM_System_EscapePod"); break;
    case EShipSystemType::Collector: Path = TEXT("/Game/Assets/Models/Drones/SM_Drone_Repair.SM_Drone_Repair"); break;
    case EShipSystemType::Armor: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_RepairPartsCase.SM_Pickup_RepairPartsCase"); break;
    default: break;
    }
    if (Path) VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Path));
}

bool AShipSystemActor::IsOperational() const
{
    return !bIsCorrupted && (!PowerNode || PowerNode->IsPowered());
}

void AShipSystemActor::OnBloomCorruption_Implementation()
{
    if (bIsCorrupted)
    {
        return;
    }

    bIsCorrupted = true;
    ApplyCorruptionEffects();
}

void AShipSystemActor::OnBloomPurged_Implementation()
{
    if (!bIsCorrupted)
    {
        return;
    }

    bIsCorrupted = false;
    RemoveCorruptionEffects();
}

bool AShipSystemActor::CanBeBloomCorrupted_Implementation() const
{
    return !bIsCorrupted;
}

void AShipSystemActor::ApplyCorruptionEffects()
{
    // Subclasses override to define what corruption does to this system.
}

void AShipSystemActor::RemoveCorruptionEffects()
{
    // Subclasses override to define recovery behavior.
}
