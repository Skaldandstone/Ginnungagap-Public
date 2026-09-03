#include "Threats/ShipboardThreat.h"

#include "AI/PatrollingEnemyController.h"
#include "CoopSurvivalCharacter.h"
#include "Components/CapsuleComponent.h"
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

AShipboardThreat::AShipboardThreat()
{
    bReplicates = true;
}

void AShipboardThreat::BeginPlay()
{
    Super::BeginPlay();
    ConfigureArchetype(Archetype);
}

void AShipboardThreat::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (!HasAuthority() || IsDead() || IsPlayerControlled())
    {
        return;
    }

    TimeUntilNextAttack = FMath::Max(0.0f, TimeUntilNextAttack - DeltaTime);
    if (TimeUntilNextAttack > 0.0f)
    {
        return;
    }

    AActor* Target = FindAttackTarget();
    if (!Target)
    {
        return;
    }

    UGameplayStatics::ApplyDamage(Target, Tuning.DamagePerAttack, GetController(), this, nullptr);
    ReceiveThreatAttack(Target, Tuning.CombatRole);
    TimeUntilNextAttack = AttackInterval;
}

void AShipboardThreat::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AShipboardThreat, Archetype);
}

void AShipboardThreat::ConfigureArchetype(EThreatArchetype NewArchetype)
{
    Archetype = NewArchetype;
    Tuning = GetArchetypeTuning(Archetype);
    if (UTeamAffiliationComponent* Affiliation = GetTeamAffiliationComponent())
    {
        const EAntagonistFaction VersusFaction = Tuning.Faction == EThreatFaction::Pirates
            ? EAntagonistFaction::Pirates
            : Tuning.Faction == EThreatFaction::Rebels
                ? EAntagonistFaction::Rebels
                : EAntagonistFaction::Alien;
        Affiliation->SetAffiliation(EVersusTeam::IndependentAI, VersusFaction);
    }
    MaxHealth = Tuning.MaxHealth;
    Health = MaxHealth;
    DamagePerSecond = Tuning.DamagePerAttack / FMath::Max(0.1f, Tuning.AttackInterval);
    AttackRange = Tuning.AttackRange;
    AttackInterval = Tuning.AttackInterval;

    Tags.Remove(TEXT("Threat.Faction.Pirates"));
    Tags.Remove(TEXT("Threat.Faction.Rebels"));
    Tags.Remove(TEXT("Threat.Faction.Alien"));
    Tags.Remove(TEXT("Threat.Body.Bipedal"));
    Tags.Remove(TEXT("Threat.Body.Quadrupedal"));
    Tags.Remove(TEXT("Threat.Body.Arachnoped"));
    Tags.AddUnique(Tuning.Faction == EThreatFaction::Pirates ? TEXT("Threat.Faction.Pirates")
        : Tuning.Faction == EThreatFaction::Rebels ? TEXT("Threat.Faction.Rebels")
        : TEXT("Threat.Faction.Alien"));
    Tags.AddUnique(Tuning.BodyPlan == EThreatBodyPlan::Bipedal ? TEXT("Threat.Body.Bipedal")
        : Tuning.BodyPlan == EThreatBodyPlan::Quadrupedal ? TEXT("Threat.Body.Quadrupedal")
        : TEXT("Threat.Body.Arachnoped"));

    if (APatrollingEnemyController* ThreatController = Cast<APatrollingEnemyController>(GetController()))
    {
        ThreatController->DetectionRange = Tuning.DetectionRange;
        ThreatController->PatrolSpeed = Tuning.PatrolSpeed;
        ThreatController->ChaseSpeed = Tuning.ChaseSpeed;
    }
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->MaxWalkSpeed = Tuning.PatrolSpeed;
    }

    ApplyArchetypeVisuals();
    ForceNetUpdate();
}

FThreatArchetypeTuning AShipboardThreat::GetArchetypeTuning(EThreatArchetype ForArchetype)
{
    FThreatArchetypeTuning Result;
    switch (ForArchetype)
    {
    case EThreatArchetype::PirateBreacher:
        Result.DisplayName = NSLOCTEXT("Threats", "PirateBreacher", "Pirate Breacher");
        Result.Faction = EThreatFaction::Pirates;
        Result.CombatRole = EThreatCombatRole::Breacher;
        Result.MaxHealth = 125.0f;
        Result.DamagePerAttack = 18.0f;
        Result.AttackRange = 175.0f;
        Result.AttackInterval = 1.1f;
        Result.ChaseSpeed = 470.0f;
        break;
    case EThreatArchetype::PirateGunner:
        Result.DisplayName = NSLOCTEXT("Threats", "PirateGunner", "Pirate Gunner");
        Result.Faction = EThreatFaction::Pirates;
        Result.CombatRole = EThreatCombatRole::Gunner;
        Result.MaxHealth = 90.0f;
        Result.DamagePerAttack = 9.0f;
        Result.AttackRange = 900.0f;
        Result.AttackInterval = 0.8f;
        Result.ChaseSpeed = 390.0f;
        Result.DetectionRange = 1900.0f;
        break;
    case EThreatArchetype::RebelSaboteur:
        Result.DisplayName = NSLOCTEXT("Threats", "RebelSaboteur", "Rebel Saboteur");
        Result.Faction = EThreatFaction::Rebels;
        Result.CombatRole = EThreatCombatRole::Saboteur;
        Result.MaxHealth = 80.0f;
        Result.DamagePerAttack = 12.0f;
        Result.AttackRange = 525.0f;
        Result.AttackInterval = 1.0f;
        Result.PatrolSpeed = 340.0f;
        Result.ChaseSpeed = 520.0f;
        break;
    case EThreatArchetype::RebelHeavy:
        Result.DisplayName = NSLOCTEXT("Threats", "RebelHeavy", "Rebel Heavy");
        Result.Faction = EThreatFaction::Rebels;
        Result.CombatRole = EThreatCombatRole::Heavy;
        Result.MaxHealth = 220.0f;
        Result.DamagePerAttack = 25.0f;
        Result.AttackRange = 260.0f;
        Result.AttackInterval = 1.5f;
        Result.PatrolSpeed = 210.0f;
        Result.ChaseSpeed = 325.0f;
        break;
    case EThreatArchetype::AlienBipedHunter:
        Result.DisplayName = NSLOCTEXT("Threats", "AlienBipedHunter", "Biped Hunter");
        Result.Faction = EThreatFaction::Alien;
        Result.BodyPlan = EThreatBodyPlan::Bipedal;
        Result.CombatRole = EThreatCombatRole::Hunter;
        Result.MaxHealth = 145.0f;
        Result.DamagePerAttack = 20.0f;
        Result.AttackRange = 190.0f;
        Result.AttackInterval = 0.95f;
        Result.ChaseSpeed = 560.0f;
        Result.DetectionRange = 2100.0f;
        break;
    case EThreatArchetype::AlienQuadrupedStalker:
        Result.DisplayName = NSLOCTEXT("Threats", "AlienQuadruped", "Quadruped Stalker");
        Result.Faction = EThreatFaction::Alien;
        Result.BodyPlan = EThreatBodyPlan::Quadrupedal;
        Result.CombatRole = EThreatCombatRole::Stalker;
        Result.MaxHealth = 105.0f;
        Result.DamagePerAttack = 16.0f;
        Result.AttackRange = 155.0f;
        Result.AttackInterval = 0.65f;
        Result.PatrolSpeed = 390.0f;
        Result.ChaseSpeed = 690.0f;
        Result.DetectionRange = 1750.0f;
        break;
    case EThreatArchetype::AlienArachnopedAmbusher:
        Result.DisplayName = NSLOCTEXT("Threats", "AlienArachnoped", "Arachnoped Ambusher");
        Result.Faction = EThreatFaction::Alien;
        Result.BodyPlan = EThreatBodyPlan::Arachnoped;
        Result.CombatRole = EThreatCombatRole::Ambusher;
        Result.MaxHealth = 70.0f;
        Result.DamagePerAttack = 24.0f;
        Result.AttackRange = 145.0f;
        Result.AttackInterval = 1.35f;
        Result.PatrolSpeed = 310.0f;
        Result.ChaseSpeed = 610.0f;
        Result.DetectionRange = 1300.0f;
        break;
    }
    return Result;
}

void AShipboardThreat::OnRep_Archetype()
{
    Tuning = GetArchetypeTuning(Archetype);
    MaxHealth = Tuning.MaxHealth;
    AttackRange = Tuning.AttackRange;
    AttackInterval = Tuning.AttackInterval;
    ApplyArchetypeVisuals();
}

AActor* AShipboardThreat::FindAttackTarget() const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    AActor* NearestTarget = nullptr;
    float NearestDistanceSq = FMath::Square(AttackRange);
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

        const float DistanceSq = FVector::DistSquared(GetActorLocation(), Candidate->GetActorLocation());
        AController* ThreatController = GetController();
        if (DistanceSq <= NearestDistanceSq
            && (!ThreatController || ThreatController->LineOfSightTo(Candidate)))
        {
            NearestDistanceSq = DistanceSq;
            NearestTarget = Candidate;
        }
    }
    return NearestTarget;
}

void AShipboardThreat::ApplyArchetypeVisuals()
{
    const bool bHuman = Tuning.Faction != EThreatFaction::Alien;
    GetMesh()->SetVisibility(bHuman, true);
    ProxyVisualMesh->SetVisibility(!bHuman, true);

    if (bHuman)
    {
        if (USkeletalMesh* HumanMesh = LoadObject<USkeletalMesh>(nullptr,
            TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")))
        {
            GetMesh()->SetSkeletalMesh(HumanMesh);
            GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -90.0f));
            GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
        }
        if (UMaterialInterface* SuitMaterial = LoadObject<UMaterialInterface>(nullptr,
            TEXT("/Game/Assets/Materials/M_SpaceSuit_Damaged.M_SpaceSuit_Damaged")))
        {
            GetMesh()->SetMaterial(0, SuitMaterial);
        }
        GetCapsuleComponent()->SetCapsuleSize(42.0f, 92.0f);
        return;
    }

    const TCHAR* MeshPath = TEXT("/Game/Assets/Models/Bloom/SM_Bloom_Puppeteer_Proxy.SM_Bloom_Puppeteer_Proxy");
    FVector VisualScale(1.0f);
    if (Tuning.BodyPlan == EThreatBodyPlan::Quadrupedal)
    {
        MeshPath = TEXT("/Game/Assets/Models/Bloom/SM_Bloom_Crawler_Proxy.SM_Bloom_Crawler_Proxy");
        VisualScale = FVector(1.1f, 1.1f, 0.9f);
        GetCapsuleComponent()->SetCapsuleSize(55.0f, 58.0f);
    }
    else if (Tuning.BodyPlan == EThreatBodyPlan::Arachnoped)
    {
        MeshPath = TEXT("/Game/Assets/Models/Bloom/Expansion/SM_Bloom_CeilingStalker_Proxy.SM_Bloom_CeilingStalker_Proxy");
        VisualScale = FVector(0.9f);
        GetCapsuleComponent()->SetCapsuleSize(48.0f, 55.0f);
    }
    else
    {
        GetCapsuleComponent()->SetCapsuleSize(44.0f, 105.0f);
    }

    if (UStaticMesh* AlienMesh = LoadObject<UStaticMesh>(nullptr, MeshPath))
    {
        ProxyVisualMesh->SetStaticMesh(AlienMesh);
        ProxyVisualMesh->SetRelativeScale3D(VisualScale);
    }
}
