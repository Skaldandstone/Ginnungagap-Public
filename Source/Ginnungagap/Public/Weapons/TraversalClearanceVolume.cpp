#include "Weapons/TraversalClearanceVolume.h"

#include "Components/BoxComponent.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/WeaponMountComponent.h"

ATraversalClearanceVolume::ATraversalClearanceVolume()
{
    PrimaryActorTick.bCanEverTick = false;

    ApproachVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("ApproachVolume"));
    RootComponent = ApproachVolume;
    ApproachVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ApproachVolume->SetCollisionObjectType(ECC_WorldDynamic);
    ApproachVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    ApproachVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    ApproachVolume->SetCollisionResponseToChannel(ECC_PhysicsBody, ECR_Overlap);
    ApproachVolume->SetGenerateOverlapEvents(true);
    ApproachVolume->ShapeColor = FColor(255, 128, 0);
}

void ATraversalClearanceVolume::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApproachVolume->SetBoxExtent(FVector(
        ApproachDepthCm * 0.5f,
        ClearWidthCm * 0.5f + ApproachPaddingCm,
        ClearHeightCm * 0.5f + ApproachPaddingCm));
}

void ATraversalClearanceVolume::NotifyActorEndOverlap(AActor* OtherActor)
{
    Super::NotifyActorEndOverlap(OtherActor);
    if (OtherActor)
    {
        if (UWeaponMountComponent* Mount = OtherActor->FindComponentByClass<UWeaponMountComponent>())
        {
            Mount->HandleClearanceVolumeExited(this);
        }
    }
}

bool ATraversalClearanceVolume::CanWeaponTraverse(const AShipboardWeapon* Weapon, bool bTestFolded) const
{
    return !Weapon || Weapon->FitsPassageAperture(GetActorTransform(), ClearWidthCm, ClearHeightCm, bTestFolded);
}

bool ATraversalClearanceVolume::ShouldBlockMovement(const AActor* Operator, const AShipboardWeapon* Weapon,
    const FVector& WorldMovementDirection) const
{
    if (!Operator || !Weapon || CanWeaponTraverse(Weapon, Weapon->bTraversalFolded))
    {
        return false;
    }

    const FVector LocalPosition = GetActorTransform().InverseTransformPosition(Operator->GetActorLocation());
    const FVector LocalDirection = GetActorTransform().InverseTransformVectorNoScale(WorldMovementDirection.GetSafeNormal());

    // An oversized operator may always retreat toward the side from which it approached. Only the
    // component of movement carrying it toward the aperture's center plane is rejected.
    if (FMath::Abs(LocalPosition.X) <= 2.0f)
    {
        return FMath::Abs(LocalDirection.X) > KINDA_SMALL_NUMBER;
    }
    return LocalPosition.X * LocalDirection.X < -KINDA_SMALL_NUMBER;
}

void ATraversalClearanceVolume::BroadcastRejected(AActor* Operator, AShipboardWeapon* Weapon)
{
    OnTraversalRejected.Broadcast(Operator, Weapon);
}
