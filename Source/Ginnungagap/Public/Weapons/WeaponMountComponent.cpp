#include "Weapons/WeaponMountComponent.h"

#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/TraversalClearanceVolume.h"

UWeaponMountComponent::UWeaponMountComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UWeaponMountComponent::BeginPlay()
{
    Super::BeginPlay();
    if (GetOwner() && GetOwner()->HasAuthority() && bSpawnDefaultWeapon && !MountedWeapon && DefaultWeaponClass)
    {
        FActorSpawnParameters SpawnParameters;
        SpawnParameters.Owner = GetOwner();
        SpawnParameters.Instigator = Cast<APawn>(GetOwner());
        if (AShipboardWeapon* SpawnedWeapon = GetWorld()->SpawnActor<AShipboardWeapon>(
            DefaultWeaponClass, GetComponentTransform(), SpawnParameters))
        {
            MountWeapon(SpawnedWeapon);
        }
    }
}

void UWeaponMountComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UWeaponMountComponent, MountedWeapon);
}

bool UWeaponMountComponent::MountWeapon(AShipboardWeapon* Weapon)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || !Weapon || MountedWeapon || !Weapon->IsCompatibleWith(OperatorType))
    {
        return false;
    }
    MountedWeapon = Weapon;
    Weapon->SetMountedState(GetOwner(), OperatorType);
    AttachMountedWeapon();
    OnMountedWeaponChanged.Broadcast(MountedWeapon);
    return true;
}

AShipboardWeapon* UWeaponMountComponent::ReleaseWeapon(bool bEnablePhysics)
{
    if (!GetOwner() || !GetOwner()->HasAuthority() || !MountedWeapon)
    {
        return nullptr;
    }
    AShipboardWeapon* ReleasedWeapon = MountedWeapon;
    MountedWeapon = nullptr;
    ReleasedWeapon->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    ReleasedWeapon->SetMountedState(nullptr, EWeaponOperatorType::Unmounted);
    if (ReleasedWeapon->VisualMesh)
    {
        ReleasedWeapon->VisualMesh->SetCollisionEnabled(bEnablePhysics ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::QueryOnly);
        ReleasedWeapon->VisualMesh->SetSimulatePhysics(bEnablePhysics);
    }
    OnMountedWeaponChanged.Broadcast(nullptr);
    return ReleasedWeapon;
}

bool UWeaponMountComponent::FireWeapon(const FVector& AimOrigin, const FVector& AimDirection)
{
    if (!MountedWeapon)
    {
        return false;
    }
    if (!GetOwner()->HasAuthority())
    {
        ServerFireWeapon(AimOrigin, AimDirection.GetSafeNormal());
        return true;
    }
    FHitResult Hit;
    return MountedWeapon->TryFire(AimOrigin, AimDirection, Hit);
}

bool UWeaponMountComponent::FireAlongMountForward()
{
    return FireWeapon(GetComponentLocation(), GetForwardVector());
}

void UWeaponMountComponent::SetUnsafeModificationInstalled(bool bInstalled)
{
    if (!MountedWeapon)
    {
        return;
    }
    if (!GetOwner()->HasAuthority())
    {
        ServerSetUnsafeModificationInstalled(bInstalled);
        return;
    }
    MountedWeapon->SetUnsafeModificationInstalled(bInstalled);
}

bool UWeaponMountComponent::CanMoveMountedWeapon(const FVector& WorldMovementDirection, float ProbeDistanceCm,
    FHitResult& OutBlockingHit)
{
    OutBlockingHit = FHitResult();
    AActor* Operator = GetOwner();
    UWorld* World = GetWorld();
    if (!MountedWeapon || !Operator || !World || WorldMovementDirection.IsNearlyZero() || ProbeDistanceCm <= 0.0f)
    {
        return true;
    }

    const FVector Direction = WorldMovementDirection.GetSafeNormal();

    // Passage volumes are directional gates rather than physical blockers. They let an oversized
    // operator back away and optionally fold a compatible tool before entering.
    TArray<AActor*> OverlappingPassages;
    Operator->GetOverlappingActors(OverlappingPassages, ATraversalClearanceVolume::StaticClass());
    for (AActor* Actor : OverlappingPassages)
    {
        ATraversalClearanceVolume* Passage = Cast<ATraversalClearanceVolume>(Actor);
        if (!Passage || Passage->CanWeaponTraverse(MountedWeapon, MountedWeapon->bTraversalFolded))
        {
            continue;
        }
        if (TryAutomaticFoldForPassage(Passage))
        {
            continue;
        }
        if (Passage->ShouldBlockMovement(Operator, MountedWeapon, Direction))
        {
            OutBlockingHit = FHitResult(Passage, Passage->ApproachVolume,
                Operator->GetActorLocation(), -Direction);
            Passage->BroadcastRejected(Operator, MountedWeapon);
            OnWeaponClearanceBlocked.Broadcast(Passage, MountedWeapon);
            return false;
        }
    }

    const FVector Start = MountedWeapon->GetTraversalEnvelopeWorldCenter();
    const FVector End = Start + Direction * ProbeDistanceCm;
    const FVector Extents = MountedWeapon->GetTraversalHalfExtents()
        + FVector(FMath::Max(0.0f, EnvelopeCollisionSkinCm));
    const FCollisionShape Shape = FCollisionShape::MakeBox(Extents);
    FCollisionObjectQueryParams ObjectQuery;
    ObjectQuery.AddObjectTypesToQuery(ECC_WorldStatic);
    ObjectQuery.AddObjectTypesToQuery(ECC_WorldDynamic);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(WeaponTraversalEnvelope), false, Operator);
    QueryParams.AddIgnoredActor(Operator);
    QueryParams.AddIgnoredActor(MountedWeapon);
    TArray<AActor*> AttachedActors;
    Operator->GetAttachedActors(AttachedActors);
    QueryParams.AddIgnoredActors(AttachedActors);

    TArray<FHitResult> Hits;
    World->SweepMultiByObjectType(Hits, Start, End, MountedWeapon->GetActorQuat(),
        ObjectQuery, Shape, QueryParams);
    for (const FHitResult& Hit : Hits)
    {
        if (!Hit.GetActor() || Hit.GetActor()->IsA<ATraversalClearanceVolume>())
        {
            continue;
        }
        // The object query returns every dynamic or static primitive in the envelope's path,
        // including overlap-only volumes -- ship sections, rooms, hazard zones -- that would never
        // stop a tool. An operator is always standing inside one of those, so the envelope read as
        // permanently penetrating and every step forward as "deeper": velocity zeroed each frame,
        // and every armed player crept through the ship at about 20 cm/s. Only something that
        // would actually block the weapon's body counts.
        const UPrimitiveComponent* HitComponent = Hit.GetComponent();
        if (!HitComponent || HitComponent->GetCollisionResponseToChannel(ECC_WorldDynamic) != ECR_Block)
        {
            continue;
        }
        // If already touching something, movement along the depenetration normal is a retreat and
        // must remain possible. Moving deeper or encountering a new obstruction is rejected.
        if (Hit.bStartPenetrating && FVector::DotProduct(Direction, Hit.Normal) > KINDA_SMALL_NUMBER)
        {
            continue;
        }
        OutBlockingHit = Hit;
        OnWeaponClearanceBlocked.Broadcast(Hit.GetActor(), MountedWeapon);
        return false;
    }
    return true;
}

bool UWeaponMountComponent::CanFitPassage(const ATraversalClearanceVolume* Passage, bool bTestFolded) const
{
    return !Passage || !MountedWeapon || Passage->CanWeaponTraverse(MountedWeapon, bTestFolded);
}

void UWeaponMountComponent::SetMountedWeaponFolded(bool bFolded)
{
    if (!MountedWeapon)
    {
        return;
    }
    if (!GetOwner()->HasAuthority())
    {
        ServerSetTraversalFolded(bFolded);
        return;
    }
    MountedWeapon->SetTraversalFolded(bFolded);
}

void UWeaponMountComponent::HandleClearanceVolumeExited(const ATraversalClearanceVolume* Passage)
{
    if (!Passage || AutomaticFoldSource.Get() != Passage)
    {
        return;
    }
    if (Passage->bRestoreWeaponAfterExit && !bWasFoldedBeforeAutomaticFold)
    {
        SetMountedWeaponFolded(false);
    }
    AutomaticFoldSource.Reset();
}

void UWeaponMountComponent::ServerFireWeapon_Implementation(FVector_NetQuantize AimOrigin, FVector_NetQuantizeNormal AimDirection)
{
    // Do not trust an arbitrary client-supplied trace origin. A small allowance covers camera sway
    // and first-person offsets while preventing fire requests from originating across the ship.
    if (FVector::DistSquared(AimOrigin, GetComponentLocation()) > FMath::Square(200.0f))
    {
        return;
    }
    FireWeapon(AimOrigin, AimDirection);
}

void UWeaponMountComponent::ServerSetUnsafeModificationInstalled_Implementation(bool bInstalled)
{
    SetUnsafeModificationInstalled(bInstalled);
}

void UWeaponMountComponent::ServerSetTraversalFolded_Implementation(bool bFolded)
{
    SetMountedWeaponFolded(bFolded);
}

void UWeaponMountComponent::OnRep_MountedWeapon()
{
    AttachMountedWeapon();
    OnMountedWeaponChanged.Broadcast(MountedWeapon);
}

void UWeaponMountComponent::AttachMountedWeapon()
{
    if (!MountedWeapon)
    {
        return;
    }
    MountedWeapon->AttachToComponent(this, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
    MountedWeapon->SetActorRelativeTransform(FTransform::Identity);
    if (MountedWeapon->VisualMesh)
    {
        MountedWeapon->VisualMesh->SetSimulatePhysics(false);
        MountedWeapon->VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
}

bool UWeaponMountComponent::TryAutomaticFoldForPassage(ATraversalClearanceVolume* Passage)
{
    if (!Passage || !Passage->bAllowAutomaticWeaponFolding || !MountedWeapon
        || !MountedWeapon->GetCollisionEnvelope().bCanFoldForTraversal
        || !Passage->CanWeaponTraverse(MountedWeapon, true))
    {
        return false;
    }

    if (AutomaticFoldSource.Get() != Passage)
    {
        bWasFoldedBeforeAutomaticFold = MountedWeapon->bTraversalFolded;
        AutomaticFoldSource = Passage;
    }
    SetMountedWeaponFolded(true);
    return true;
}
