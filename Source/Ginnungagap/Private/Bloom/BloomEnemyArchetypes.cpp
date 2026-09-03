#include "Bloom/BloomEnemyArchetypes.h"

#include "Bloom/BloomDirector.h"
#include "Bloom/PathogenLoadComponent.h"
#include "AI/PatrollingEnemyController.h"
#include "Animation/AnimationAsset.h"
#include "CoopSurvivalCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "Versus/TeamAffiliationComponent.h"

namespace
{
    UStaticMesh* LoadStaticMesh(const TCHAR* AssetPath)
    {
        return LoadObject<UStaticMesh>(nullptr, AssetPath);
    }

    UStaticMeshComponent* CreateVisualPart(
        AActor* Owner,
        const FName Name,
        USceneComponent* Parent,
        UStaticMesh* Mesh,
        UMaterialInterface* MaterialOverride = nullptr,
        const FName Socket = NAME_None)
    {
        UStaticMeshComponent* Component = Owner->CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Component->SetupAttachment(Parent, Socket);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetStaticMesh(Mesh);
        if (MaterialOverride)
        {
            for (int32 MaterialIndex = 0; MaterialIndex < 4; ++MaterialIndex)
            {
                Component->SetMaterial(MaterialIndex, MaterialOverride);
            }
        }
        return Component;
    }

    void ApplyGrowthReveal(
        UStaticMeshComponent* Component,
        const float Progress,
        const float RevealThreshold,
        const FVector& MatureScale)
    {
        if (!Component)
        {
            return;
        }

        const float Reveal = FMath::Clamp(
            (Progress - RevealThreshold) / FMath::Max(KINDA_SMALL_NUMBER, 1.0f - RevealThreshold),
            0.0f,
            1.0f);
        Component->SetVisibility(Reveal > 0.0f, true);
        Component->SetHiddenInGame(Reveal <= 0.0f, true);
        const float SmoothReveal = FMath::SmoothStep(0.0f, 1.0f, Reveal);
        Component->SetRelativeScale3D(MatureScale * FMath::Lerp(0.08f, 1.0f, SmoothReveal));
        Component->SetCustomPrimitiveDataFloat(0, Progress);
    }

    void ApplyScaledTuning(
        AHorrorEnemy* Enemy,
        const float Progress,
        const float SeedHealth,
        const float MatureHealth,
        const float SeedDamage,
        const float MatureDamage,
        const float SeedRange,
        const float MatureRange,
        const float SeedSpeed,
        const float MatureSpeed)
    {
        const float PreviousMaximum = FMath::Max(1.0f, Enemy->MaxHealth);
        const float HealthRatio = FMath::Clamp(Enemy->Health / PreviousMaximum, 0.0f, 1.0f);
        Enemy->MaxHealth = FMath::Lerp(SeedHealth, MatureHealth, Progress);
        Enemy->Health = Enemy->MaxHealth * HealthRatio;
        Enemy->DamagePerSecond = FMath::Lerp(SeedDamage, MatureDamage, Progress);
        Enemy->AttackRange = FMath::Lerp(SeedRange, MatureRange, Progress);
        if (UCharacterMovementComponent* Movement = Enemy->GetCharacterMovement())
        {
            const float CurrentSpeed = FMath::Lerp(SeedSpeed, MatureSpeed, Progress);
            Movement->MaxWalkSpeed = CurrentSpeed;
            if (APatrollingEnemyController* EnemyController =
                Cast<APatrollingEnemyController>(Enemy->GetController()))
            {
                EnemyController->PatrolSpeed = CurrentSpeed * 0.65f;
                EnemyController->ChaseSpeed = CurrentSpeed;
            }
        }
    }
}

AProgressiveBloomEnemy::AProgressiveBloomEnemy()
{
    PathogenLoadComponent = CreateDefaultSubobject<UPathogenLoadComponent>(TEXT("BloomPathogenLoad"));
    PathogenLoadComponent->InfectionState = EInfectionState::Symptomatic;
    PathogenLoadComponent->SubstrateQuality = 100.0f;
    PathogenLoadComponent->PathogenLoad = 100.0f;
    PathogenLoadComponent->ReplicationRate = 0.05f;
    PathogenLoadComponent->SheddingRate = 0.04f;

    AttackPoseRoot = CreateDefaultSubobject<USceneComponent>(TEXT("BloomAttackPoseRoot"));
    AttackPoseRoot->SetupAttachment(GetCapsuleComponent());

    BloomGlowLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("BloomGlowLight"));
    BloomGlowLight->SetupAttachment(AttackPoseRoot);
    BloomGlowLight->SetRelativeLocation(FVector(35.0f, 0.0f, 22.0f));
    BloomGlowLight->SetLightColor(FLinearColor(0.85f, 0.02f, 1.0f));
    BloomGlowLight->SetIntensity(0.0f);
    BloomGlowLight->SetAttenuationRadius(MatureGlowRadius);
    BloomGlowLight->SetCastShadows(false);
    BloomGlowLight->SetVisibility(false);
}

void AProgressiveBloomEnemy::BeginPlay()
{
    Super::BeginPlay();

    if (HasAuthority() && bTrackGlobalBloomStage)
    {
        if (UWorld* World = GetWorld(); World && World->GetGameInstance())
        {
            if (UBloomDirector* Director = World->GetGameInstance()->GetSubsystem<UBloomDirector>())
            {
                Director->OnBloomStageChanged.AddDynamic(this, &AProgressiveBloomEnemy::HandleGlobalBloomStageChanged);
                SetInfectionProgress(CalculateProgressForGlobalStage(Director->GetCurrentStage()));
            }
        }
    }

    RefreshInfectionPresentation();
    TimeUntilNextAttack = AttackInterval;
}

void AProgressiveBloomEnemy::Tick(const float DeltaTime)
{
    Super::Tick(DeltaTime);
    UpdateNativeMotion(DeltaTime);
    UpdateAttackTelegraphLight(DeltaTime);

    if (!HasAuthority() || IsDead() || IsPlayerControlled())
    {
        return;
    }

    TimeUntilNextAttack = FMath::Max(0.0f, TimeUntilNextAttack - DeltaTime);
    AActor* Target = FindAttackTarget();
    if (!Target)
    {
        // A new target always receives at least the full warning window.
        TimeUntilNextAttack = FMath::Max(TimeUntilNextAttack, AttackTelegraphDuration);
        bAttackTelegraphSent = false;
        return;
    }

    if (!bAttackTelegraphSent && TimeUntilNextAttack <= AttackTelegraphDuration)
    {
        bAttackTelegraphSent = true;
        MulticastBeginAttackTelegraph(Target);
    }

    if (TimeUntilNextAttack > 0.0f)
    {
        return;
    }

    const float DamagePerAttack = DamagePerSecond * AttackInterval;
    UGameplayStatics::ApplyDamage(Target, DamagePerAttack, GetController(), this, nullptr);
    if (UPathogenLoadComponent* TargetPathogen = Target->FindComponentByClass<UPathogenLoadComponent>())
    {
        TargetPathogen->ApplyExposure(ContactExposurePerAttack, 1.0f);
    }
    MulticastCommitBloomAttack(Target);
    TimeUntilNextAttack = AttackInterval;
    bAttackTelegraphSent = false;
}

float AProgressiveBloomEnemy::TakeDamage(
    const float DamageAmount,
    FDamageEvent const& DamageEvent,
    AController* EventInstigator,
    AActor* DamageCauser)
{
    const bool bWasDead = IsDead();
    const float AppliedDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    if (HasAuthority() && !bWasDead && IsDead())
    {
        TriggerDeathBurst();
    }
    return AppliedDamage;
}

void AProgressiveBloomEnemy::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld(); World && World->GetGameInstance())
    {
        if (UBloomDirector* Director = World->GetGameInstance()->GetSubsystem<UBloomDirector>())
        {
            Director->OnBloomStageChanged.RemoveDynamic(this, &AProgressiveBloomEnemy::HandleGlobalBloomStageChanged);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void AProgressiveBloomEnemy::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AProgressiveBloomEnemy, InfectionProgress);
}

void AProgressiveBloomEnemy::SetInfectionProgress(const float NewProgress)
{
    if (!HasAuthority())
    {
        return;
    }

    InfectionProgress = FMath::Clamp(NewProgress, 0.0f, 1.0f);
    RefreshInfectionPresentation();
}

EBloomEnemyInfectionPhase AProgressiveBloomEnemy::GetInfectionPhase() const
{
    if (InfectionProgress < 0.25f)
    {
        return EBloomEnemyInfectionPhase::Seeded;
    }
    if (InfectionProgress < 0.55f)
    {
        return EBloomEnemyInfectionPhase::Colonizing;
    }
    if (InfectionProgress < 0.82f)
    {
        return EBloomEnemyInfectionPhase::Puppeteered;
    }
    return EBloomEnemyInfectionPhase::Overgrown;
}

float AProgressiveBloomEnemy::CalculateProgressForGlobalStage(const EBloomStage GlobalStage) const
{
    return static_cast<float>(GlobalStage) / static_cast<float>(EBloomStage::Manifestation);
}

void AProgressiveBloomEnemy::RefreshInfectionPresentation()
{
    if (PathogenLoadComponent)
    {
        PathogenLoadComponent->PathogenLoad =
            PathogenLoadComponent->SubstrateQuality * InfectionProgress;
        PathogenLoadComponent->SheddingRate = FMath::Lerp(0.0f, 0.06f, InfectionProgress);
        PathogenLoadComponent->InfectionState = InfectionProgress < 0.25f
            ? EInfectionState::Exposed
            : InfectionProgress < 0.55f
                ? EInfectionState::Incubating
                : EInfectionState::Symptomatic;
    }
    if (BloomGlowLight)
    {
        const float GlowStrength = FMath::Square(FMath::Clamp(InfectionProgress, 0.0f, 1.0f));
        BloomGlowLight->SetVisibility(GlowStrength > 0.01f);
        BloomGlowLight->SetIntensity(MatureGlowIntensity * GlowStrength);
        BloomGlowLight->SetAttenuationRadius(FMath::Lerp(90.0f, MatureGlowRadius, GlowStrength));
    }
    ApplyProgressiveVisualsAndTuning(InfectionProgress);
    TimeUntilNextAttack = FMath::Min(TimeUntilNextAttack, AttackInterval);
    ReceiveInfectionProgressChanged(InfectionProgress, GetInfectionPhase());
}

void AProgressiveBloomEnemy::ApplyProgressiveVisualsAndTuning(float Progress)
{
}

void AProgressiveBloomEnemy::ApplyNativeAttackPose(float PoseAlpha)
{
}

void AProgressiveBloomEnemy::ApplyNativeDeathPose(float PoseAlpha)
{
}

void AProgressiveBloomEnemy::ApplyFabDeathPose(int32 PoseVariant)
{
}

void AProgressiveBloomEnemy::OnRep_InfectionProgress()
{
    RefreshInfectionPresentation();
}

void AProgressiveBloomEnemy::HandleGlobalBloomStageChanged(const EBloomStage NewStage)
{
    SetInfectionProgress(CalculateProgressForGlobalStage(NewStage));
}

AActor* AProgressiveBloomEnemy::FindAttackTarget() const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    AActor* NearestTarget = nullptr;
    float NearestDistanceSquared = FMath::Square(AttackRange);
    for (TActorIterator<APawn> It(World); It; ++It)
    {
        APawn* Candidate = *It;
        if (!IsValid(Candidate) || Candidate == this
            || !UTeamAffiliationComponent::AreActorsHostile(this, Candidate))
        {
            continue;
        }
        if (const ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Candidate); Crew && Crew->bIsDead)
        {
            continue;
        }
        if (const AHorrorEnemy* Enemy = Cast<AHorrorEnemy>(Candidate); Enemy && Enemy->IsDead())
        {
            continue;
        }

        const float DistanceSquared = FVector::DistSquared(GetActorLocation(), Candidate->GetActorLocation());
        AController* EnemyController = GetController();
        if (DistanceSquared <= NearestDistanceSquared
            && (!EnemyController || EnemyController->LineOfSightTo(Candidate)))
        {
            NearestDistanceSquared = DistanceSquared;
            NearestTarget = Candidate;
        }
    }
    return NearestTarget;
}

void AProgressiveBloomEnemy::UpdateAttackTelegraphLight(const float DeltaTime)
{
    const float BaseGlowStrength = FMath::Square(FMath::Clamp(InfectionProgress, 0.0f, 1.0f));
    if (LocalDeathBurstTimeRemaining > 0.0f)
    {
        const float BurstAlpha = LocalDeathBurstTimeRemaining / 1.25f;
        BloomGlowLight->SetVisibility(true);
        BloomGlowLight->SetIntensity(MatureGlowIntensity * (0.4f + 3.2f * BurstAlpha));
        BloomGlowLight->SetAttenuationRadius(FMath::Lerp(MatureGlowRadius, DeathBurstRadius, BurstAlpha));
        return;
    }
    if (LocalTelegraphTimeRemaining > 0.0f)
    {
        LocalTelegraphTimeRemaining = FMath::Max(0.0f, LocalTelegraphTimeRemaining - DeltaTime);
        const float TelegraphAlpha = 1.0f - LocalTelegraphTimeRemaining
            / FMath::Max(AttackTelegraphDuration, KINDA_SMALL_NUMBER);
        const float Pulse = 1.0f + 1.6f * FMath::SmoothStep(0.0f, 1.0f, TelegraphAlpha);
        BloomGlowLight->SetVisibility(true);
        BloomGlowLight->SetIntensity(MatureGlowIntensity * FMath::Max(0.08f, BaseGlowStrength) * Pulse);
        return;
    }

    BloomGlowLight->SetVisibility(BaseGlowStrength > 0.01f);
    BloomGlowLight->SetIntensity(MatureGlowIntensity * BaseGlowStrength);
}

void AProgressiveBloomEnemy::UpdateNativeMotion(const float DeltaTime)
{
    if (LocalDeathBurstTimeRemaining > 0.0f || LocalDeathPoseAlpha > 0.0f)
    {
        LocalDeathBurstTimeRemaining = FMath::Max(0.0f, LocalDeathBurstTimeRemaining - DeltaTime);
        LocalDeathPoseAlpha = FMath::Min(1.0f, LocalDeathPoseAlpha + DeltaTime / 0.65f);
        ApplyNativeDeathPose(LocalDeathPoseAlpha);
        return;
    }

    if (LocalTelegraphTimeRemaining > 0.0f)
    {
        const float PoseAlpha = 1.0f - LocalTelegraphTimeRemaining
            / FMath::Max(AttackTelegraphDuration, KINDA_SMALL_NUMBER);
        ApplyNativeAttackPose(FMath::SmoothStep(0.0f, 1.0f, PoseAlpha));
        return;
    }

    if (LocalAttackRecoveryTimeRemaining > 0.0f)
    {
        LocalAttackRecoveryTimeRemaining = FMath::Max(0.0f, LocalAttackRecoveryTimeRemaining - DeltaTime);
        ApplyNativeAttackPose(LocalAttackRecoveryTimeRemaining / 0.22f);
        return;
    }

    ApplyNativeAttackPose(0.0f);
}

void AProgressiveBloomEnemy::TriggerDeathBurst()
{
    if (bDeathBurstTriggered)
    {
        return;
    }
    bDeathBurstTriggered = true;

    if (PathogenLoadComponent)
    {
        PathogenLoadComponent->SheddingRate = FMath::Max(PathogenLoadComponent->SheddingRate, 0.24f);
    }

    UWorld* World = GetWorld();
    if (World && DeathBurstExposure > 0.0f && DeathBurstRadius > 0.0f)
    {
        for (TActorIterator<APawn> It(World); It; ++It)
        {
            APawn* Candidate = *It;
            if (!IsValid(Candidate) || Candidate == this
                || !UTeamAffiliationComponent::AreActorsHostile(this, Candidate))
            {
                continue;
            }

            const float Distance = FVector::Dist(GetActorLocation(), Candidate->GetActorLocation());
            if (Distance > DeathBurstRadius)
            {
                continue;
            }
            if (UPathogenLoadComponent* TargetPathogen =
                Candidate->FindComponentByClass<UPathogenLoadComponent>())
            {
                const float Falloff = 1.0f - Distance / DeathBurstRadius;
                TargetPathogen->ApplyExposure(DeathBurstExposure * Falloff, 1.0f);
            }
        }
    }

    MulticastBloomDeathBurst(DeathBurstExposure, DeathBurstRadius, FMath::RandRange(0, 2));
}

void AProgressiveBloomEnemy::MulticastBeginAttackTelegraph_Implementation(AActor* TargetActor)
{
    LocalTelegraphTimeRemaining = AttackTelegraphDuration;
    ReceiveBloomAttackTelegraph(TargetActor, AttackTelegraphDuration);
}

void AProgressiveBloomEnemy::MulticastCommitBloomAttack_Implementation(AActor* TargetActor)
{
    LocalTelegraphTimeRemaining = 0.0f;
    LocalAttackRecoveryTimeRemaining = 0.22f;
    ReceiveBloomAttackCommitted(TargetActor, GetInfectionPhase());
}

void AProgressiveBloomEnemy::MulticastBloomDeathBurst_Implementation(
    const float ExposureAmount,
    const float BurstRadius,
    const int32 FabPoseVariant)
{
    LocalTelegraphTimeRemaining = 0.0f;
    LocalAttackRecoveryTimeRemaining = 0.0f;
    LocalDeathBurstTimeRemaining = 1.25f;
    LocalDeathPoseAlpha = KINDA_SMALL_NUMBER;
    ApplyFabDeathPose(FabPoseVariant);
    ReceiveBloomDeathBurst(ExposureAmount, BurstRadius, FabPoseVariant);
}

ABloomReanimatedCrewEnemy::ABloomReanimatedCrewEnemy()
{
    MatureGlowIntensity = 850.0f;
    MatureGlowRadius = 280.0f;
    AttackInterval = 0.7f;
    ContactExposurePerAttack = 8.0f;
    MaxHealth = 140.0f;
    Health = MaxHealth;
    DamagePerSecond = 14.0f;
    AttackRange = 165.0f;

    ProxyVisualMesh->SetVisibility(false);
    GetCapsuleComponent()->InitCapsuleSize(45.0f, 96.0f);
    GetMesh()->SetupAttachment(AttackPoseRoot);
    GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -96.0f));
    GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    GetMesh()->SetSkeletalMesh(LoadObject<USkeletalMesh>(
        nullptr,
        TEXT("/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02.SKM_PrimaryOversuit_QuinnProjectionShell_I02")));
    BloomGlowLight->SetRelativeLocation(FVector(38.0f, 0.0f, 20.0f));
    BloomGlowLight->SetLightColor(FLinearColor(1.0f, 0.01f, 0.32f));

    UMaterialInterface* BloomMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/Assets/Materials/Production/Instances/MI_Surface_Bloom.MI_Surface_Bloom"));
    UStaticMesh* CompactGrowth = LoadStaticMesh(
        TEXT("/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_13.SM_alien_organism_13"));
    UStaticMesh* CrownGrowthMesh = LoadStaticMesh(
        TEXT("/Game/SF_White_desert/Meshes/Crystals/SM_crystal_03.SM_crystal_03"));
    UStaticMesh* TendrilGrowth = LoadStaticMesh(
        TEXT("/Game/SF_White_desert/Meshes/Crystals/SM_crystal_02.SM_crystal_02"));

    ChestGrowth = CreateVisualPart(this, TEXT("ChestGrowth"), AttackPoseRoot, CompactGrowth, BloomMaterial);
    ChestGrowth->SetRelativeLocation(FVector(29.0f, -4.0f, 20.0f));
    ChestGrowth->SetRelativeRotation(FRotator(0.0f, 70.0f, 0.0f));
    ChestGrowth->SetRelativeScale3D(FVector(0.14f, 0.12f, 0.14f));

    HeadGrowth = CreateVisualPart(this, TEXT("HeadGrowth"), AttackPoseRoot, CrownGrowthMesh, BloomMaterial);
    HeadGrowth->SetRelativeLocation(FVector(30.0f, -3.0f, 66.0f));
    HeadGrowth->SetRelativeRotation(FRotator(90.0f, 8.0f, 0.0f));
    HeadGrowth->SetRelativeScale3D(FVector(0.045f, 0.045f, 0.045f));

    RightArmGrowth = CreateVisualPart(this, TEXT("RightArmGrowth"), AttackPoseRoot, TendrilGrowth, BloomMaterial);
    RightArmGrowth->SetRelativeLocation(FVector(12.0f, -42.0f, 22.0f));
    RightArmGrowth->SetRelativeRotation(FRotator(55.0f, -25.0f, -18.0f));
    RightArmGrowth->SetRelativeScale3D(FVector(0.05f, 0.05f, 0.05f));

    LeftLegGrowth = CreateVisualPart(this, TEXT("LeftLegGrowth"), AttackPoseRoot, TendrilGrowth, BloomMaterial);
    LeftLegGrowth->SetRelativeLocation(FVector(18.0f, 18.0f, -55.0f));
    LeftLegGrowth->SetRelativeRotation(FRotator(72.0f, 18.0f, 8.0f));
    LeftLegGrowth->SetRelativeScale3D(FVector(0.055f, 0.055f, 0.055f));

    FabCorpseMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("FabCorpseMesh"));
    FabCorpseMesh->SetupAttachment(AttackPoseRoot);
    FabCorpseMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    FabCorpseMesh->SetGenerateOverlapEvents(false);
    FabCorpseMesh->SetCanEverAffectNavigation(false);
    FabCorpseMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -96.0f));
    FabCorpseMesh->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    FabCorpseMesh->SetSkeletalMesh(LoadObject<USkeletalMesh>(
        nullptr,
        TEXT("/Game/DeadBodies_Poses_nikoff/Demo/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")));
    FabCorpseMesh->SetVisibility(false, true);
    FabCorpseMesh->SetHiddenInGame(true, true);
#if WITH_EDITOR
    FabCorpseMesh->SetUpdateAnimationInEditor(true);
#endif
    if (BloomMaterial)
    {
        for (int32 MaterialIndex = 0; MaterialIndex < 4; ++MaterialIndex)
        {
            FabCorpseMesh->SetMaterial(MaterialIndex, BloomMaterial);
        }
    }
    FabDeathPoseAssets = {
        LoadObject<UAnimationAsset>(nullptr,
            TEXT("/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_04.AS_DeadBody_Pose_Lie_04")),
        LoadObject<UAnimationAsset>(nullptr,
            TEXT("/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_11.AS_DeadBody_Pose_Lie_11")),
        LoadObject<UAnimationAsset>(nullptr,
            TEXT("/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_17.AS_DeadBody_Pose_Lie_17")),
    };
}

float ABloomReanimatedCrewEnemy::CalculateProgressForGlobalStage(const EBloomStage GlobalStage) const
{
    static constexpr float StageProgress[] = {0.0f, 0.2f, 0.42f, 0.68f, 0.86f, 1.0f};
    return StageProgress[FMath::Clamp(static_cast<int32>(GlobalStage), 0, UE_ARRAY_COUNT(StageProgress) - 1)];
}

void ABloomReanimatedCrewEnemy::ApplyProgressiveVisualsAndTuning(const float Progress)
{
    ApplyGrowthReveal(ChestGrowth, Progress, 0.12f, FVector(0.14f, 0.12f, 0.14f));
    ApplyGrowthReveal(HeadGrowth, Progress, 0.38f, FVector(0.045f));
    ApplyGrowthReveal(RightArmGrowth, Progress, 0.58f, FVector(0.05f));
    ApplyGrowthReveal(LeftLegGrowth, Progress, 0.72f, FVector(0.055f));
    ApplyScaledTuning(
        this, Progress, 85.0f, 140.0f, 6.0f, 14.0f, 120.0f, 165.0f, 215.0f, 365.0f);
    AttackInterval = FMath::Lerp(1.6f, 0.7f, Progress);
    ContactExposurePerAttack = FMath::Lerp(1.5f, 8.0f, Progress);
}

void ABloomReanimatedCrewEnemy::ApplyNativeAttackPose(const float PoseAlpha)
{
    AttackPoseRoot->SetRelativeLocation(FVector(24.0f * PoseAlpha, 0.0f, -3.0f * PoseAlpha));
    AttackPoseRoot->SetRelativeRotation(FRotator(-10.0f * PoseAlpha, 0.0f, 0.0f));
}

void ABloomReanimatedCrewEnemy::ApplyNativeDeathPose(const float PoseAlpha)
{
    if (bUsingFabDeathPose)
    {
        AttackPoseRoot->SetRelativeLocation(FVector::ZeroVector);
        AttackPoseRoot->SetRelativeRotation(FRotator::ZeroRotator);
        return;
    }
    AttackPoseRoot->SetRelativeLocation(FVector(8.0f * PoseAlpha, 0.0f, -48.0f * PoseAlpha));
    AttackPoseRoot->SetRelativeRotation(FRotator(0.0f, 0.0f, 82.0f * PoseAlpha));
}

void ABloomReanimatedCrewEnemy::ApplyFabDeathPose(const int32 PoseVariant)
{
    if (!FabCorpseMesh || FabDeathPoseAssets.IsEmpty())
    {
        return;
    }
    UAnimationAsset* Pose = FabDeathPoseAssets[
        FMath::Clamp(PoseVariant, 0, FabDeathPoseAssets.Num() - 1)];
    if (!Pose)
    {
        return;
    }

    bUsingFabDeathPose = true;
    GetMesh()->SetVisibility(false, true);
    FabCorpseMesh->SetHiddenInGame(false, true);
    FabCorpseMesh->SetVisibility(true, true);
    FabCorpseMesh->PlayAnimation(Pose, false);
    FabCorpseMesh->SetPosition(0.06f, false);
    FabCorpseMesh->TickAnimation(0.0f, false);
    FabCorpseMesh->RefreshBoneTransforms();
    FabCorpseMesh->MarkRenderDynamicDataDirty();
    ChestGrowth->SetVisibility(false, true);
    HeadGrowth->SetVisibility(false, true);
    RightArmGrowth->SetVisibility(false, true);
    LeftLegGrowth->SetVisibility(false, true);
}

void ABloomReanimatedCrewEnemy::PreviewFabDeathPose(const int32 PoseVariant)
{
    ApplyFabDeathPose(PoseVariant);
}

ABloomMechanizedEnemy::ABloomMechanizedEnemy()
{
    MatureGlowIntensity = 1450.0f;
    MatureGlowRadius = 410.0f;
    AttackInterval = 1.25f;
    ContactExposurePerAttack = 14.0f;
    MaxHealth = 320.0f;
    Health = MaxHealth;
    DamagePerSecond = 22.0f;
    AttackRange = 220.0f;

    ProxyVisualMesh->SetVisibility(false);
    GetMesh()->SetVisibility(false);
    GetCapsuleComponent()->InitCapsuleSize(68.0f, 145.0f);
    BloomGlowLight->SetRelativeLocation(FVector(45.0f, 0.0f, 42.0f));
    BloomGlowLight->SetLightColor(FLinearColor(0.32f, 0.04f, 1.0f));

    const TCHAR* JackRoot = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/");
    UStaticMesh* BodyMesh = LoadStaticMesh(*(FString(JackRoot) + TEXT("SM_JACK_BODY.SM_JACK_BODY")));
    UStaticMesh* HeadMesh = LoadStaticMesh(*(FString(JackRoot) + TEXT("SM_JACK_HEAD.SM_JACK_HEAD")));
    UStaticMesh* ArmMesh = LoadStaticMesh(*(FString(JackRoot) + TEXT("SM_JACK_ARM.SM_JACK_ARM")));
    UStaticMesh* LegMesh = LoadStaticMesh(*(FString(JackRoot) + TEXT("SM_JACK_LEG.SM_JACK_LEG")));

    RobotBody = CreateVisualPart(this, TEXT("RobotBody"), AttackPoseRoot, BodyMesh);
    RobotBody->SetRelativeLocation(FVector(0.0f, 0.0f, 30.0f));
    RobotBody->SetRelativeScale3D(FVector(1.15f));

    RobotHead = CreateVisualPart(this, TEXT("RobotHead"), RobotBody, HeadMesh);
    RobotHead->SetRelativeLocation(FVector(0.0f, 0.0f, 74.0f));
    RobotHead->SetRelativeScale3D(FVector(1.1f));

    LeftArm = CreateVisualPart(this, TEXT("LeftArm"), RobotBody, ArmMesh);
    LeftArm->SetRelativeLocation(FVector(0.0f, -54.0f, 8.0f));
    LeftArm->SetRelativeRotation(FRotator(0.0f, 0.0f, -8.0f));
    LeftArm->SetRelativeScale3D(FVector(1.1f));

    RightArm = CreateVisualPart(this, TEXT("RightArm"), RobotBody, ArmMesh);
    RightArm->SetRelativeLocation(FVector(0.0f, 54.0f, 8.0f));
    RightArm->SetRelativeRotation(FRotator(0.0f, 180.0f, 8.0f));
    RightArm->SetRelativeScale3D(FVector(1.1f));

    LeftLeg = CreateVisualPart(this, TEXT("LeftLeg"), AttackPoseRoot, LegMesh);
    LeftLeg->SetRelativeLocation(FVector(0.0f, -27.0f, -74.0f));
    LeftLeg->SetRelativeScale3D(FVector(1.08f));

    RightLeg = CreateVisualPart(this, TEXT("RightLeg"), AttackPoseRoot, LegMesh);
    RightLeg->SetRelativeLocation(FVector(0.0f, 27.0f, -74.0f));
    RightLeg->SetRelativeScale3D(FVector(1.08f, -1.08f, 1.08f));

    UMaterialInterface* BloomMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/Assets/Materials/Production/Instances/MI_Surface_Bloom.MI_Surface_Bloom"));
    UStaticMesh* CompactGrowth = LoadStaticMesh(
        TEXT("/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_13.SM_alien_organism_13"));
    UStaticMesh* CrownGrowthMesh = LoadStaticMesh(
        TEXT("/Game/SF_White_desert/Meshes/Crystals/SM_crystal_01.SM_crystal_01"));
    UStaticMesh* TendrilGrowth = LoadStaticMesh(
        TEXT("/Game/SF_White_desert/Meshes/Crystals/SM_crystal_02.SM_crystal_02"));

    CoreGrowth = CreateVisualPart(this, TEXT("CoreGrowth"), RobotBody, CompactGrowth, BloomMaterial);
    CoreGrowth->SetRelativeLocation(FVector(34.0f, -2.0f, 12.0f));
    CoreGrowth->SetRelativeRotation(FRotator(0.0f, 70.0f, 0.0f));
    CoreGrowth->SetRelativeScale3D(FVector(0.15f, 0.13f, 0.15f));

    CrownGrowth = CreateVisualPart(this, TEXT("CrownGrowth"), RobotHead, CrownGrowthMesh, BloomMaterial);
    CrownGrowth->SetRelativeLocation(FVector(3.0f, 0.0f, 14.0f));
    CrownGrowth->SetRelativeScale3D(FVector(0.038f, 0.038f, 0.038f));

    ArmGrowth = CreateVisualPart(this, TEXT("ArmGrowth"), LeftArm, TendrilGrowth, BloomMaterial);
    ArmGrowth->SetRelativeLocation(FVector(0.0f, -2.0f, -10.0f));
    ArmGrowth->SetRelativeRotation(FRotator(0.0f, 90.0f, -90.0f));
    ArmGrowth->SetRelativeScale3D(FVector(0.065f, 0.065f, 0.065f));
}

float ABloomMechanizedEnemy::CalculateProgressForGlobalStage(const EBloomStage GlobalStage) const
{
    static constexpr float StageProgress[] = {0.0f, 0.05f, 0.22f, 0.48f, 0.76f, 1.0f};
    return StageProgress[FMath::Clamp(static_cast<int32>(GlobalStage), 0, UE_ARRAY_COUNT(StageProgress) - 1)];
}

void ABloomMechanizedEnemy::ApplyProgressiveVisualsAndTuning(const float Progress)
{
    ApplyGrowthReveal(CoreGrowth, Progress, 0.08f, FVector(0.15f, 0.13f, 0.15f));
    ApplyGrowthReveal(ArmGrowth, Progress, 0.42f, FVector(0.065f));
    ApplyGrowthReveal(CrownGrowth, Progress, 0.68f, FVector(0.038f));
    ApplyScaledTuning(
        this, Progress, 180.0f, 320.0f, 10.0f, 22.0f, 155.0f, 220.0f, 105.0f, 225.0f);
    AttackInterval = FMath::Lerp(2.4f, 1.25f, Progress);
    ContactExposurePerAttack = FMath::Lerp(1.0f, 14.0f, Progress);
}

void ABloomMechanizedEnemy::ApplyNativeAttackPose(const float PoseAlpha)
{
    AttackPoseRoot->SetRelativeLocation(FVector(12.0f * PoseAlpha, 0.0f, 0.0f));
    AttackPoseRoot->SetRelativeRotation(FRotator(-3.0f * PoseAlpha, 0.0f, 0.0f));
    RightArm->SetRelativeRotation(FRotator(-68.0f * PoseAlpha, 180.0f, 8.0f));
}

void ABloomMechanizedEnemy::ApplyNativeDeathPose(const float PoseAlpha)
{
    AttackPoseRoot->SetRelativeLocation(FVector(0.0f, 0.0f, -34.0f * PoseAlpha));
    AttackPoseRoot->SetRelativeRotation(FRotator(0.0f, 0.0f, -24.0f * PoseAlpha));
    LeftArm->SetRelativeRotation(FRotator(38.0f * PoseAlpha, 0.0f, -8.0f));
    RightArm->SetRelativeRotation(FRotator(38.0f * PoseAlpha, 180.0f, 8.0f));
}
