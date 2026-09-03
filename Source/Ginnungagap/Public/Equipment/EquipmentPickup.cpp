// Copyright Epic Games, Inc. All Rights Reserved.

#include "EquipmentPickup.h"
#include "CoopSurvivalCharacter.h"
#include "Equipment/EquipmentComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"

AEquipmentPickup::AEquipmentPickup()
{
    PrimaryActorTick.bCanEverTick = true;

    // Equipment is explicitly collected through the interaction trace. The base
    // survival pickup overlaps pawns and would otherwise consume this actor as an
    // oxygen/health pickup before the player could equip it.
    if (CollisionSphere)
    {
        CollisionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
        CollisionSphere->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    }
}

void AEquipmentPickup::BeginPlay()
{
    Super::BeginPlay();
}

void AEquipmentPickup::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    RotatePickup(DeltaTime);
}

void AEquipmentPickup::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!InteractingPawn)
    {
        return;
    }

    ACoopSurvivalCharacter* PlayerCharacter = Cast<ACoopSurvivalCharacter>(InteractingPawn);
    if (!PlayerCharacter)
    {
        return;
    }

    UEquipmentComponent* EquipmentComp = PlayerCharacter->FindComponentByClass<UEquipmentComponent>();
    if (EquipmentComp && EquipmentComp->EquipItem(EquipmentItem))
    {
        Destroy();
    }
}

void AEquipmentPickup::RotatePickup(float DeltaTime)
{
    FRotator DeltaRotation(
        PickupRotationSpeed.Y * DeltaTime,
        PickupRotationSpeed.Z * DeltaTime,
        PickupRotationSpeed.X * DeltaTime
    );
    AddActorLocalRotation(DeltaRotation);
}

void AEquipmentPickup::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    const TCHAR* Path = nullptr;
    switch (EquipmentItem.Type)
    {
    case EEquipmentType::HelmetVisor: Path = TEXT("/Game/Assets/Models/Equipment/SM_Tool_BioScanner.SM_Tool_BioScanner"); break;
    case EEquipmentType::ThermalPlating: Path = TEXT("/Game/Assets/Models/Equipment/SM_Tool_FireExtinguisher.SM_Tool_FireExtinguisher"); break;
    case EEquipmentType::RadiationShield: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_SampleCanister.SM_Pickup_SampleCanister"); break;
    case EEquipmentType::PressureSeal: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_OxygenCanister.SM_Pickup_OxygenCanister"); break;
    case EEquipmentType::ArmorPlating: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_RepairPartsCase.SM_Pickup_RepairPartsCase"); break;
    case EEquipmentType::OxygenFilter: Path = TEXT("/Game/Assets/Models/Pickups/SM_Pickup_PowerCell.SM_Pickup_PowerCell"); break;
    }
    if (VisualMesh && Path) VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Path));
}
