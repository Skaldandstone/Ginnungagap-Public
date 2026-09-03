#include "Weapons/ShipboardWeapon.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"
#include "Ship/ShipDamageComponent.h"
#include "Stealth/NoisePerceptionSubsystem.h"
#include "StarSystem/ShipResourceInventorySubsystem.h"
#include "StarSystem/StarSystemTypes.h"
#include "Weapons/ShipboardWeaponDefinition.h"
#include "Weapons/ShipboardProjectile.h"
#include "Weapons/ShipboardControlStatusComponent.h"
#include "Versus/TeamAffiliationComponent.h"
#include "TimerManager.h"

AShipboardWeapon::AShipboardWeapon()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(true);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;

    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(SceneRoot);
    VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    Muzzle = CreateDefaultSubobject<USceneComponent>(TEXT("Muzzle"));
    Muzzle->SetupAttachment(SceneRoot);
    Muzzle->SetRelativeLocation(FVector(40.0f, 0.0f, 0.0f));

    EnvelopeVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("EnvelopeVolume"));
    EnvelopeVolume->SetupAttachment(SceneRoot);
    EnvelopeVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    EnvelopeVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    EnvelopeVolume->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Overlap);
    EnvelopeVolume->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
    EnvelopeVolume->SetGenerateOverlapEvents(true);

    RescueShieldVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("RescueShieldVolume"));
    RescueShieldVolume->SetupAttachment(SceneRoot);
    RescueShieldVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RescueShieldVolume->SetCollisionObjectType(ECC_WorldDynamic);
    RescueShieldVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    RescueShieldVolume->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Block);
    RescueShieldVolume->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    RescueShieldVolume->SetGenerateOverlapEvents(false);

    UnsafeModifiedProfile = SafeProfile;
    UnsafeModifiedProfile.MaxRangeCm = 110.0f;
    UnsafeModifiedProfile.BiologicalDamage = 80.0f;
    UnsafeModifiedProfile.ImpactImpulse = 32000.0f;
    UnsafeModifiedProfile.RecoilImpulse = 6500.0f;
    UnsafeModifiedProfile.CooldownSeconds = 0.9f;
    UnsafeModifiedProfile.bCanDamageHull = true;
    UnsafeModifiedProfile.HullImpactSeverity = 0.04f;
    UnsafeModifiedProfile.BreachSeverity = 0.08f;
    // An uncontained discharge carries further than a contained one, so the unsafe modification
    // trades stealth for power rather than being strictly better.
    UnsafeModifiedProfile.FiringNoiseLoudness = 1.0f;
}

void AShipboardWeapon::BeginPlay()
{
    Super::BeginPlay();
    RefreshFromDefinition();
}

void AShipboardWeapon::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AShipboardWeapon, bUnsafeModificationInstalled);
    DOREPLIFETIME(AShipboardWeapon, UpgradeLevel);
    DOREPLIFETIME(AShipboardWeapon, bTraversalFolded);
    DOREPLIFETIME(AShipboardWeapon, bRescueShieldActive);
    DOREPLIFETIME(AShipboardWeapon, OperatorActor);
    DOREPLIFETIME(AShipboardWeapon, OperatorType);
}

bool AShipboardWeapon::TryFire(const FVector& AimOrigin, const FVector& AimDirection, FHitResult& OutHit)
{
    if (!HasAuthority() || AimDirection.IsNearlyZero())
    {
        return false;
    }
    OutHit = FHitResult();

    const FWeaponFiringProfile Profile = GetActiveFiringProfile();
    const double Now = GetWorld()->GetTimeSeconds();
    if (Now - LastFireTimeSeconds < Profile.CooldownSeconds)
    {
        return false;
    }
    LastFireTimeSeconds = Now;

    if (Profile.DeliveryMode == EWeaponDeliveryMode::RescueShield)
    {
        if (!ActivateRescueShield(Profile))
        {
            return false;
        }
        const FVector CosmeticEnd = AimOrigin + AimDirection.GetSafeNormal() * Profile.MaxRangeCm;
        MulticastFireCosmetics(CosmeticEnd, false, bUnsafeModificationInstalled);
        ReportFiringNoise(Profile);
        OnWeaponFired.Broadcast(OutHit, bUnsafeModificationInstalled);
        return true;
    }

    if (Profile.DeliveryMode == EWeaponDeliveryMode::Projectile)
    {
        if (!FirePhysicalProjectiles(AimOrigin, AimDirection, Profile))
        {
            return false;
        }
        ApplyRecoil(Profile, AimDirection.GetSafeNormal());
        const FVector CosmeticEnd = AimOrigin + AimDirection.GetSafeNormal() * Profile.MaxRangeCm;
        MulticastFireCosmetics(CosmeticEnd, false, bUnsafeModificationInstalled);
        ReportFiringNoise(Profile);
        OnWeaponFired.Broadcast(OutHit, bUnsafeModificationInstalled);
        return true;
    }

    const FVector Direction = AimDirection.GetSafeNormal();
    const FVector TraceEnd = AimOrigin + Direction * Profile.MaxRangeCm;
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ShipboardWeaponTrace), true, this);
    QueryParams.AddIgnoredActor(this);
    if (OperatorActor)
    {
        QueryParams.AddIgnoredActor(OperatorActor);
    }

    const FCollisionShape Shape = FCollisionShape::MakeSphere(Profile.TraceRadiusCm);
    const bool bHit = GetWorld()->SweepSingleByChannel(
        OutHit,
        AimOrigin,
        TraceEnd,
        FQuat::Identity,
        ECC_Visibility,
        Shape,
        QueryParams);

    if (bHit)
    {
        ApplyImpact(Profile, Direction, OutHit);
    }
    ApplyRecoil(Profile, Direction);
    MulticastFireCosmetics(bHit ? OutHit.ImpactPoint : TraceEnd, bHit, bUnsafeModificationInstalled);
    ReportFiringNoise(Profile);
    OnWeaponFired.Broadcast(OutHit, bUnsafeModificationInstalled);
    return true;
}

void AShipboardWeapon::ReportFiringNoise(const FWeaponFiringProfile& Profile) const
{
    if (Profile.FiringNoiseLoudness <= 0.0f)
    {
        return;
    }

    const UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UNoisePerceptionSubsystem* Perception = World->GetSubsystem<UNoisePerceptionSubsystem>();
    if (!Perception)
    {
        return;
    }

    // Attribute to the operator so hostility checks and self-ignore resolve against the crew
    // member firing, not the weapon actor. Falls back to the weapon when unmounted (a turret or
    // a shot with no owner still makes noise).
    AActor* NoiseInstigator = OperatorActor ? OperatorActor : const_cast<AShipboardWeapon*>(this);
    Perception->ReportNoise(GetActorLocation(), Profile.FiringNoiseLoudness,
        ENoiseCategory::Weapon, NoiseInstigator);
}

void AShipboardWeapon::SetMountedState(AActor* NewOperator, EWeaponOperatorType NewOperatorType)
{
    if (!HasAuthority())
    {
        return;
    }
    OperatorActor = NewOperator;
    OperatorType = NewOperator ? NewOperatorType : EWeaponOperatorType::Unmounted;
    SetOwner(NewOperator);
}

void AShipboardWeapon::SetUnsafeModificationInstalled(bool bInstalled)
{
    if (!HasAuthority() || bUnsafeModificationInstalled == bInstalled)
    {
        return;
    }
    bUnsafeModificationInstalled = bInstalled;
    OnRep_UnsafeModification();
}

bool AShipboardWeapon::TryInstallNextUpgrade()
{
    if (!HasAuthority() || !Definition || UpgradeLevel >= Definition->UpgradeStages.Num())
    {
        return false;
    }
    const FWeaponUpgradeStage& Stage = Definition->UpgradeStages[UpgradeLevel];
    EStarSystemResourceType ResourceType = EStarSystemResourceType::StructuralAlloy;
    switch (Stage.CostResource)
    {
    case EWeaponUpgradeResource::SensorComponents:
        ResourceType = EStarSystemResourceType::SensorComponents;
        break;
    case EWeaponUpgradeResource::PowerCells:
        ResourceType = EStarSystemResourceType::PowerCells;
        break;
    default:
        break;
    }
    if (Stage.ResourceCost > 0)
    {
        UGameInstance* GameInstance = GetGameInstance();
        UShipResourceInventorySubsystem* Inventory = GameInstance
            ? GameInstance->GetSubsystem<UShipResourceInventorySubsystem>() : nullptr;
        if (!Inventory || !Inventory->TrySpendResource(ResourceType, Stage.ResourceCost))
        {
            return false;
        }
    }
    SetUpgradeLevel(UpgradeLevel + 1);
    return true;
}

void AShipboardWeapon::SetUpgradeLevel(int32 NewUpgradeLevel)
{
    if (!HasAuthority())
    {
        return;
    }
    const int32 ClampedLevel = FMath::Clamp(NewUpgradeLevel, 0, GetMaxUpgradeLevel());
    if (UpgradeLevel == ClampedLevel)
    {
        return;
    }
    UpgradeLevel = ClampedLevel;
    OnRep_UpgradeLevel();
}

int32 AShipboardWeapon::GetMaxUpgradeLevel() const
{
    return Definition ? Definition->GetMaxUpgradeLevel() : 0;
}

FWeaponFiringProfile AShipboardWeapon::GetActiveFiringProfile() const
{
    if (Definition)
    {
        return bUnsafeModificationInstalled
            ? Definition->UnsafeModifiedProfile
            : Definition->GetFiringProfileForUpgradeLevel(UpgradeLevel);
    }
    return bUnsafeModificationInstalled ? UnsafeModifiedProfile : SafeProfile;
}

FWeaponCollisionEnvelope AShipboardWeapon::GetCollisionEnvelope() const
{
    return Definition ? Definition->CollisionEnvelope : CollisionEnvelope;
}

bool AShipboardWeapon::IsCompatibleWith(EWeaponOperatorType CandidateOperator) const
{
    const bool bPlayer = Definition ? Definition->bPlayerCompatible : bPlayerCompatible;
    const bool bAerial = Definition ? Definition->bAerialDroneCompatible : bAerialDroneCompatible;
    const bool bRobotic = Definition ? Definition->bRoboticDroneCompatible : bRoboticDroneCompatible;
    switch (CandidateOperator)
    {
    case EWeaponOperatorType::Player: return bPlayer;
    case EWeaponOperatorType::AerialDrone: return bAerial;
    case EWeaponOperatorType::RoboticDrone: return bRobotic;
    default: return true;
    }
}

bool AShipboardWeapon::FitsOpening(const FVector& OpeningFullExtentsCm) const
{
    const FVector FullWeaponExtents = GetTraversalHalfExtents() * 2.0f;
    return FullWeaponExtents.X <= OpeningFullExtentsCm.X
        && FullWeaponExtents.Y <= OpeningFullExtentsCm.Y
        && FullWeaponExtents.Z <= OpeningFullExtentsCm.Z;
}

bool AShipboardWeapon::FitsPassageAperture(const FTransform& PassageTransform, float ClearWidthCm,
    float ClearHeightCm, bool bTestFolded) const
{
    return GetCollisionEnvelope().FitsPassageAperture(
        GetActorQuat(), PassageTransform.GetRotation(), ClearWidthCm, ClearHeightCm, bTestFolded);
}

FVector AShipboardWeapon::GetTraversalHalfExtents() const
{
    return GetCollisionEnvelope().GetHalfExtents(bTraversalFolded);
}

FVector AShipboardWeapon::GetTraversalEnvelopeWorldCenter() const
{
    const FWeaponCollisionEnvelope Envelope = GetCollisionEnvelope();
    return GetActorTransform().TransformPosition(Envelope.CenterOffsetCm);
}

void AShipboardWeapon::SetTraversalFolded(bool bFolded)
{
    if (!HasAuthority())
    {
        return;
    }
    const bool bNewFolded = bFolded && GetCollisionEnvelope().bCanFoldForTraversal;
    if (bTraversalFolded == bNewFolded)
    {
        return;
    }
    bTraversalFolded = bNewFolded;
    OnRep_TraversalFolded();
}

void AShipboardWeapon::OnRep_UnsafeModification()
{
    OnModificationChanged.Broadcast(bUnsafeModificationInstalled);
}

void AShipboardWeapon::OnRep_UpgradeLevel()
{
    OnUpgradeLevelChanged.Broadcast(UpgradeLevel, GetMaxUpgradeLevel());
}

void AShipboardWeapon::OnRep_TraversalFolded()
{
    const FWeaponCollisionEnvelope Envelope = GetCollisionEnvelope();
    EnvelopeVolume->SetRelativeLocation(Envelope.CenterOffsetCm);
    EnvelopeVolume->SetBoxExtent(Envelope.GetHalfExtents(bTraversalFolded));
}

void AShipboardWeapon::OnRep_RescueShieldActive()
{
    RescueShieldVolume->SetCollisionEnabled(
        bRescueShieldActive ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
}

void AShipboardWeapon::ClearRescueShield()
{
    if (!HasAuthority())
    {
        return;
    }
    bRescueShieldActive = false;
    OnRep_RescueShieldActive();
    ForceNetUpdate();
}

void AShipboardWeapon::MulticastFireCosmetics_Implementation(FVector_NetQuantize TraceEnd, bool bHit, bool bUnsafeMode)
{
    ReceiveFireCosmetics(TraceEnd, bHit, bUnsafeMode);
}

void AShipboardWeapon::RefreshFromDefinition()
{
    if (Definition && Definition->WeaponMesh)
    {
        VisualMesh->SetStaticMesh(Definition->WeaponMesh);
        VisualMesh->SetRelativeTransform(Definition->WeaponMeshTransform);
        Muzzle->SetRelativeLocation(Definition->MuzzleOffset);
    }
    const FWeaponCollisionEnvelope Envelope = GetCollisionEnvelope();
    EnvelopeVolume->SetRelativeLocation(Envelope.CenterOffsetCm);
    EnvelopeVolume->SetBoxExtent(Envelope.GetHalfExtents(bTraversalFolded));
}

bool AShipboardWeapon::FirePhysicalProjectiles(const FVector& AimOrigin, const FVector& AimDirection,
    const FWeaponFiringProfile& Profile)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }
    const FVector Forward = AimDirection.GetSafeNormal();
    const FVector SpawnLocation = Muzzle ? Muzzle->GetComponentLocation() : AimOrigin;
    const float SpreadRadians = FMath::DegreesToRadians(Profile.SpreadHalfAngleDegrees);
    bool bSpawnedAny = false;
    for (int32 Index = 0; Index < FMath::Max(1, Profile.ProjectilesPerShot); ++Index)
    {
        const FVector ShotDirection = SpreadRadians > 0.0f
            ? FMath::VRandCone(Forward, SpreadRadians)
            : Forward;
        const FTransform SpawnTransform(ShotDirection.Rotation(), SpawnLocation);
        AShipboardProjectile* Projectile = World->SpawnActorDeferred<AShipboardProjectile>(
            AShipboardProjectile::StaticClass(), SpawnTransform, this, Cast<APawn>(OperatorActor),
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
        if (!Projectile)
        {
            continue;
        }
        Projectile->InitializeProjectile(Profile, ShotDirection, this, OperatorActor);
        UGameplayStatics::FinishSpawningActor(Projectile, SpawnTransform);
        bSpawnedAny = true;
    }
    return bSpawnedAny;
}

bool AShipboardWeapon::ActivateRescueShield(const FWeaponFiringProfile& Profile)
{
    if (!HasAuthority() || Profile.ShieldDurationSeconds <= 0.0f
        || Profile.ShieldHalfExtentsCm.GetMin() <= 0.0f)
    {
        return false;
    }
    RescueShieldVolume->SetBoxExtent(Profile.ShieldHalfExtentsCm);
    RescueShieldVolume->SetRelativeLocation(FVector(Profile.ShieldHalfExtentsCm.X, 0.0f, 0.0f));
    bRescueShieldActive = true;
    OnRep_RescueShieldActive();
    GetWorldTimerManager().SetTimer(RescueShieldTimer, this,
        &AShipboardWeapon::ClearRescueShield, Profile.ShieldDurationSeconds, false);
    ForceNetUpdate();
    return true;
}

void AShipboardWeapon::ApplyImpact(const FWeaponFiringProfile& Profile, const FVector& AimDirection, const FHitResult& Hit)
{
    if (AActor* HitActor = Hit.GetActor())
    {
        AController* InstigatorController = nullptr;
        if (const APawn* OperatorPawn = Cast<APawn>(OperatorActor))
        {
            InstigatorController = OperatorPawn->GetController();
        }
        const bool bAlliedCharacter = OperatorActor
            && !UTeamAffiliationComponent::AreActorsHostile(OperatorActor, HitActor)
            && UTeamAffiliationComponent::FindAffiliation(HitActor);
        if (!bAlliedCharacter)
        {
            UGameplayStatics::ApplyPointDamage(HitActor, Profile.BiologicalDamage, AimDirection, Hit,
                InstigatorController, this, UDamageType::StaticClass());
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
    }

    if (UPrimitiveComponent* HitComponent = Hit.GetComponent())
    {
        if (HitComponent->IsSimulatingPhysics())
        {
            HitComponent->AddImpulseAtLocation(AimDirection * Profile.ImpactImpulse, Hit.ImpactPoint);
        }
    }
}

void AShipboardWeapon::ApplyRecoil(const FWeaponFiringProfile& Profile, const FVector& AimDirection)
{
    if (!OperatorActor || Profile.RecoilImpulse <= 0.0f)
    {
        return;
    }
    const FVector Recoil = -AimDirection * Profile.RecoilImpulse;
    if (ACharacter* Character = Cast<ACharacter>(OperatorActor))
    {
        if (UCharacterMovementComponent* Movement = Character->GetCharacterMovement())
        {
            Movement->AddImpulse(Recoil, false);
        }
    }
    else if (UPrimitiveComponent* RootPrimitive = Cast<UPrimitiveComponent>(OperatorActor->GetRootComponent()))
    {
        if (RootPrimitive->IsSimulatingPhysics())
        {
            RootPrimitive->AddImpulseAtLocation(Recoil, GetActorLocation());
        }
    }
}
