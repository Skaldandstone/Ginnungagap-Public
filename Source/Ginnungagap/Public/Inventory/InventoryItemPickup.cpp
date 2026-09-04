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

    // Measured across the deck, not to the pawn's centre: a supply lies on the floor a metre below
    // the pawn's origin, and the straight-line check refused the E press silently at any distance
    // the prompt was visible from. The prompt (the eye-line, 2.5 m) is the real reach.
    const float MaxDistance = InteractionRadiusCm + InteractingPawn->GetSimpleCollisionRadius() + 120.0f;
    return FVector::DistSquared2D(InteractingPawn->GetActorLocation(), GetActorLocation()) <= FMath::Square(MaxDistance);
}

FText AInventoryItemPickup::GetInteractionPrompt_Implementation(APawn* Viewer) const
{
    if (!ItemDefinition)
    {
        return FText::GetEmpty();
    }
    const FText Name = ItemDefinition->DisplayName.IsEmpty() ? FText::FromName(ItemDefinition->ItemId) : ItemDefinition->DisplayName;
    const UInventoryComponent* Inventory = Viewer ? Viewer->FindComponentByClass<UInventoryComponent>() : nullptr;
    if (Inventory && !Inventory->CanAddItem(ItemDefinition, Quantity))
    {
        return FText::Format(NSLOCTEXT("Pickup", "NoRoom", "{0} (no room)"), Name);
    }
    if (Quantity > 1)
    {
        return FText::Format(NSLOCTEXT("Pickup", "TakeMany", "Take {0} x{1}"), Name, FText::AsNumber(Quantity));
    }
    return FText::Format(NSLOCTEXT("Pickup", "Take", "Take {0}"), Name);
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
