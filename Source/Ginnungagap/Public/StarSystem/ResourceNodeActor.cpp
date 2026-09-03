#include "ResourceNodeActor.h"
#include "DormantCollectorSystem.h"
#include "ShipResourceInventorySubsystem.h"
#include "../Ship/ShipSystemActor.h"
#include "../Ship/ShipNavigationSubsystem.h"
#include "../Bloom/BloomDirector.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Components/StaticMeshComponent.h"
#include "ProceduralStarSystemMap.h"
#include "EngineUtils.h"

AResourceNodeActor::AResourceNodeActor()
{
    PrimaryActorTick.bCanEverTick = false;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    RootComponent = VisualMesh;
}

void AResourceNodeActor::SetShipOnStation(bool bOnStation)
{
    if (bShipOnStation == bOnStation)
    {
        return;
    }
    bShipOnStation = bOnStation;
    OnShipStationStateChanged(bShipOnStation);
}

void AResourceNodeActor::DepleteResourceNode()
{
    SetShipOnStation(false);
    if (GeneratedResourceIndex != INDEX_NONE)
    {
        for (TActorIterator<AProceduralStarSystemMap> It(GetWorld()); It; ++It)
        {
            It->DeactivateResourceContact(GeneratedResourceIndex);
            break;
        }
    }
    OnResourceNodeDepleted.Broadcast(this);
    Destroy();
}

void AResourceNodeActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    const TCHAR* Path = nullptr;
    switch (ResourceType)
    {
    case EStarSystemResourceType::NavigationFuel: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_OxygenCanister.SM_Pickup_OxygenCanister"); break;
    case EStarSystemResourceType::StructuralAlloy: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_RepairPartsCase.SM_Pickup_RepairPartsCase"); break;
    case EStarSystemResourceType::CryoCoolant: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_SampleCanister.SM_Pickup_SampleCanister"); break;
    case EStarSystemResourceType::LifeSupportFilters: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_MedicalInjector.SM_Pickup_MedicalInjector"); break;
    case EStarSystemResourceType::SensorComponents: Path = TEXT("/Game/Assets/Models/Equipment/SM_Tool_BioScanner.SM_Tool_BioScanner"); break;
    case EStarSystemResourceType::PowerCells: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_PowerCell.SM_Pickup_PowerCell"); break;
    }
    if (VisualMesh && Path) VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Path));
}

bool AResourceNodeActor::CanBeCollectedBy(APawn* Character) const
{
    if (!Character)
    {
        return false;
    }

    switch (RequiredMethod)
    {
    case EResourceAcquisitionMethod::EVARetrieval:
    {
        const UWorld* World = GetWorld();
        const UShipNavigationSubsystem* NavSubsystem = World ? World->GetSubsystem<UShipNavigationSubsystem>() : nullptr;
        return NavSubsystem && NavSubsystem->GetSectionContainingLocation(Character->GetActorLocation()) == nullptr;
    }
    case EResourceAcquisitionMethod::ShipSystemReactivation:
    {
        if (!RequiredSystem || RequiredSystem->bIsCorrupted)
        {
            return false;
        }

        if (const ADormantCollectorSystem* Collector = Cast<ADormantCollectorSystem>(RequiredSystem))
        {
            return Collector->bIsReactivated;
        }

        return true;
    }
    case EResourceAcquisitionMethod::DroneDispatch:
    default:
        return false;
    }
}

void AResourceNodeActor::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!CanBeCollectedBy(InteractingPawn))
    {
        return;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UShipResourceInventorySubsystem* Inventory = GI->GetSubsystem<UShipResourceInventorySubsystem>())
        {
            Inventory->AddResource(ResourceType, Quantity);
        }

        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            const EBloomPlayerActionType ActionType = RequiredMethod == EResourceAcquisitionMethod::EVARetrieval
                ? EBloomPlayerActionType::PerformedEVA
                : EBloomPlayerActionType::ReactivatedShipSystem;
            Director->RegisterPlayerAction(ActionType);
        }
    }

    DepleteResourceNode();
}
