// Copyright Epic Games, Inc. All Rights Reserved.

#include "AI/HorrorEnemy.h"
#include "AI/PatrollingEnemyController.h"
#include "Ship/ZeroGGravityComponent.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "Versus/TeamAffiliationComponent.h"

AHorrorEnemy::AHorrorEnemy()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;
    AIControllerClass = APatrollingEnemyController::StaticClass();
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

    ZeroGGravityComponent = CreateDefaultSubobject<UZeroGGravityComponent>(TEXT("ZeroGGravityComponent"));
    TeamAffiliationComponent = CreateDefaultSubobject<UTeamAffiliationComponent>(TEXT("TeamAffiliationComponent"));
    TeamAffiliationComponent->Team = EVersusTeam::IndependentAI;
    TeamAffiliationComponent->Faction = EAntagonistFaction::Bloom;
    ProxyVisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProxyVisualMesh"));
    ProxyVisualMesh->SetupAttachment(GetCapsuleComponent());
    ProxyVisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProxyVisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/Assets/Models/Bloom/SM_Bloom_Puppeteer_Proxy.SM_Bloom_Puppeteer_Proxy")));
}

float AHorrorEnemy::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    const float AppliedDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    if (!HasAuthority() || AppliedDamage <= 0.0f || Health <= 0.0f)
    {
        return AppliedDamage;
    }

    Health = FMath::Clamp(Health - AppliedDamage, 0.0f, MaxHealth);
    ReceiveHealthChanged(Health, MaxHealth);
    if (Health <= 0.0f)
    {
        HandleKilled(DamageCauser);
    }
    return AppliedDamage;
}

void AHorrorEnemy::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AHorrorEnemy, Health);
}

void AHorrorEnemy::OnRep_Health()
{
    ReceiveHealthChanged(Health, MaxHealth);
}

void AHorrorEnemy::HandleKilled(AActor* DamageCauser)
{
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetCharacterMovement()->DisableMovement();
    ReceiveKilled(DamageCauser);
    OnEnemyKilled.Broadcast();
    SetLifeSpan(5.0f);
}

void AHorrorEnemy::BeginPlay()
{
    Super::BeginPlay();
}

void AHorrorEnemy::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}

void AHorrorEnemy::ReceiveHazardExposure(EBloomHazardType HazardType, float Amount)
{
    UWorld* World = GetWorld();
    if (!World || !World->GetGameInstance())
    {
        return;
    }

    UBloomDirector* Director = World->GetGameInstance()->GetSubsystem<UBloomDirector>();
    if (!Director)
    {
        return;
    }

    const float Effectiveness = Director->GetHazardEffectiveness(HazardType);
    const float DamageAmount = Amount * (1.0f - Effectiveness);

    Health = FMath::Clamp(Health - DamageAmount, 0.0f, MaxHealth);

    Director->RegisterHazardExposure(HazardType, Amount);
}
