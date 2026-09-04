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
    // Fab meshes for every pickup (the project's own placeholder canisters and cases were the
    // "relics" James saw): the engineering props pack for tanks and cases, the Frontier toolbox
    // tools for the instruments. Tanks are authored lying along Y and are stood up.
    const TCHAR* Path = nullptr;
    FRotator MeshRotation = FRotator::ZeroRotator;
    switch (EquipmentItem.Type)
    {
    case EEquipmentType::HelmetVisor: Path = TEXT("/Game/Frontier_EngineersToolbox/Tools/SM_Frontier_Scanner.SM_Frontier_Scanner"); break;
    case EEquipmentType::ThermalPlating: Path = TEXT("/Game/ModSci_EngiProps/Meshes/SM_NitrogenTank_Covered.SM_NitrogenTank_Covered"); break;
    case EEquipmentType::RadiationShield: Path = TEXT("/Game/ModSci_EngiProps/Meshes/SM_Toolbox.SM_Toolbox"); break;
    case EEquipmentType::PressureSeal: Path = TEXT("/Game/ModSci_EngiProps/Meshes/SM_OxygenTank_B.SM_OxygenTank_B"); MeshRotation = FRotator(0.0f, 0.0f, 90.0f); break;
    case EEquipmentType::ArmorPlating: Path = TEXT("/Game/ModSci_EngiProps/Meshes/SM_WireReel_A.SM_WireReel_A"); break;
    case EEquipmentType::OxygenFilter: Path = TEXT("/Game/ModSci_Engineer/Meshes/SM_ElectricBox_C.SM_ElectricBox_C"); break;
    }
    if (VisualMesh && Path)
    {
        VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Path));
        VisualMesh->SetRelativeRotation(MeshRotation);
    }
}
