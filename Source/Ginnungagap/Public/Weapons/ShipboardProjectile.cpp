#include "Weapons/ShipboardProjectile.h"

#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/ProjectileMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"
#include "Ship/ShipDamageComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Weapons/ShipboardControlStatusComponent.h"

AShipboardProjectile::AShipboardProjectile()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(true);

    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
    Collision->InitSphereRadius(1.6f);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Collision->SetCollisionResponseToAllChannels(ECR_Block);
    Collision->SetNotifyRigidBodyCollision(true);
    RootComponent = Collision;
    Collision->OnComponentHit.AddDynamic(this, &AShipboardProjectile::HandleImpact);

    Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
    Visual->SetupAttachment(Collision);
    Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Visual->SetRelativeScale3D(FVector(0.025f, 0.025f, 0.025f));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        Visual->SetStaticMesh(SphereMesh.Object);
    }

    Movement = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("Movement"));
    Movement->UpdatedComponent = Collision;
    Movement->bRotationFollowsVelocity = true;
    Movement->bShouldBounce = false;
    Movement->ProjectileGravityScale = 0.0f;
    InitialLifeSpan = 3.0f;
}

void AShipboardProjectile::InitializeProjectile(const FWeaponFiringProfile& InProfile,
    const FVector& Direction, AActor* InSourceWeapon, AActor* InOperator)
{
    Profile = InProfile;
    SourceWeapon = InSourceWeapon;
    OperatorActor = InOperator;
    SetOwner(InSourceWeapon);
    SetInstigator(Cast<APawn>(InOperator));
    Collision->IgnoreActorWhenMoving(InSourceWeapon, true);
    Collision->IgnoreActorWhenMoving(InOperator, true);
    Movement->InitialSpeed = Profile.ProjectileSpeedCmPerSecond;
    Movement->MaxSpeed = Profile.ProjectileSpeedCmPerSecond;
    Movement->ProjectileGravityScale = Profile.ProjectileGravityScale;
    Movement->Velocity = Direction.GetSafeNormal() * Profile.ProjectileSpeedCmPerSecond;
    const float FlightSeconds = Profile.MaxRangeCm / FMath::Max(Profile.ProjectileSpeedCmPerSecond, 1.0f);
    SetLifeSpan(FMath::Max(0.15f, FlightSeconds * 1.15f));
}

void AShipboardProjectile::HandleImpact(UPrimitiveComponent* HitComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit)
{
    if (!HasAuthority() || !OtherActor || OtherActor == SourceWeapon.Get() || OtherActor == OperatorActor.Get())
    {
        return;
    }
    ApplyImpact(Hit);
    Destroy();
}

void AShipboardProjectile::ApplyImpact(const FHitResult& Hit)
{
    AActor* HitActor = Hit.GetActor();
    if (!HitActor)
    {
        return;
    }
    AController* InstigatorController = nullptr;
    if (const APawn* OperatorPawn = Cast<APawn>(OperatorActor.Get()))
    {
        InstigatorController = OperatorPawn->GetController();
    }
    const bool bAlliedCharacter = OperatorActor.IsValid()
        && !UTeamAffiliationComponent::AreActorsHostile(OperatorActor.Get(), HitActor)
        && UTeamAffiliationComponent::FindAffiliation(HitActor);
    if (!bAlliedCharacter)
    {
        UGameplayStatics::ApplyPointDamage(HitActor, Profile.BiologicalDamage,
            Movement->Velocity.GetSafeNormal(), Hit, InstigatorController,
            SourceWeapon.Get(), UDamageType::StaticClass());
        if (Profile.ControlEffect != EWeaponControlEffect::None)
        {
            if (UShipboardControlStatusComponent* Status =
                UShipboardControlStatusComponent::FindOrCreate(HitActor))
            {
                Status->ApplyControlEffect(Profile.ControlEffect,
                    Profile.ControlDurationSeconds, Profile.ControlMovementMultiplier);
            }
        }
    }

    if (Profile.bCanDamageHull)
    {
        for (AActor* Candidate = HitActor; Candidate; Candidate = Candidate->GetOwner())
        {
            if (UShipDamageComponent* ShipDamage = Candidate->FindComponentByClass<UShipDamageComponent>())
            {
                if (Profile.HullImpactSeverity > 0.0f)
                {
                    ShipDamage->ApplyShipDamage(EShipDamageType::HullImpact, Profile.HullImpactSeverity);
                }
                if (Profile.BreachSeverity > 0.0f)
                {
                    ShipDamage->ApplyShipDamage(EShipDamageType::Breach, Profile.BreachSeverity);
                }
                break;
            }
        }
    }
    if (UPrimitiveComponent* HitPrimitive = Hit.GetComponent();
        HitPrimitive && HitPrimitive->IsSimulatingPhysics())
    {
        HitPrimitive->AddImpulseAtLocation(Movement->Velocity.GetSafeNormal() * Profile.ImpactImpulse, Hit.ImpactPoint);
    }
}
