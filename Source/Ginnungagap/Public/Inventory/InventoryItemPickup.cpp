#include "Inventory/InventoryItemPickup.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/ItemDefinition.h"
#include "Net/UnrealNetwork.h"

AInventoryItemPickup::AInventoryItemPickup()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(true);

    CollisionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionSphere"));
    SetRootComponent(CollisionSphere);
    CollisionSphere->InitSphereRadius(InteractionRadiusCm);
    CollisionSphere->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    CollisionSphere->SetCollisionObjectType(ECC_WorldDynamic);
    CollisionSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
    CollisionSphere->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    CollisionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(CollisionSphere);
    VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AInventoryItemPickup::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    CollisionSphere->SetSphereRadius(InteractionRadiusCm);
    RefreshPresentation();
}

void AInventoryItemPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AInventoryItemPickup, ItemDefinition);
    DOREPLIFETIME(AInventoryItemPickup, Quantity);
}

void AInventoryItemPickup::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!HasAuthority() || !CanBeCollectedBy(InteractingPawn))
    {
        return;
    }

    UInventoryComponent* Inventory = InteractingPawn->FindComponentByClass<UInventoryComponent>();
    if (Inventory && Inventory->AddItem(ItemDefinition, Quantity))
    {
        OnCollected.Broadcast(ItemDefinition, Quantity);
        Destroy();
    }
}

void AInventoryItemPickup::ConfigurePickup(UItemDefinition* NewItem, int32 NewQuantity)
{
    if (!HasAuthority())
    {
        return;
    }

    ItemDefinition = NewItem;
    Quantity = FMath::Max(1, NewQuantity);
    RefreshPresentation();
    ForceNetUpdate();
}

bool AInventoryItemPickup::CanBeCollectedBy(const APawn* InteractingPawn) const
{
    if (!InteractingPawn || !ItemDefinition || Quantity <= 0)
    {
        return false;
    }

    const UInventoryComponent* Inventory = InteractingPawn->FindComponentByClass<UInventoryComponent>();
    if (!Inventory || !Inventory->CanAddItem(ItemDefinition, Quantity))
    {
        return false;
    }

    const float MaxDistance = InteractionRadiusCm + InteractingPawn->GetSimpleCollisionRadius();
    return FVector::DistSquared(InteractingPawn->GetActorLocation(), GetActorLocation()) <= FMath::Square(MaxDistance);
}

void AInventoryItemPickup::OnRep_PickupState()
{
    RefreshPresentation();
}

void AInventoryItemPickup::RefreshPresentation()
{
    if (!VisualMesh)
    {
        return;
    }

    VisualMesh->SetStaticMesh(ItemDefinition ? ItemDefinition->WorldMesh : nullptr);
    VisualMesh->SetRelativeScale3D(ItemDefinition ? ItemDefinition->WorldMeshScale : FVector(1.0f));
}
