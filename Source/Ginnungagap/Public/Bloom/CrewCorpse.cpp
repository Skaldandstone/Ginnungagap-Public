#include "CrewCorpse.h"
#include "../Ship/ZeroGGravityComponent.h"
#include "../AI/PatrollingEnemyController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "AIController.h"
#include "Components/SkeletalMeshComponent.h"

ACrewCorpse::ACrewCorpse()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoPossessAI = EAutoPossessAI::Disabled;

    ZeroGGravityComponent = CreateDefaultSubobject<UZeroGGravityComponent>(TEXT("ZeroGGravityComponent"));

    // Possessed corpses must remain dangerous to every crew member in co-op, not just player 0,
    // and should respect line-of-sight/team-hostility like every other patrolling threat.
    PossessionControllerClass = APatrollingEnemyController::StaticClass();
}

void ACrewCorpse::BeginPlay()
{
    Super::BeginPlay();

    if (USkeletalMeshComponent* CorpseMesh = GetMesh())
    {
        CorpseMesh->SetSimulatePhysics(true);
        CorpseMesh->SetCollisionEnabled(ECollisionEnabled::PhysicsOnly);
    }

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->DisableMovement();
    }
}

void ACrewCorpse::OnBloomPossession_Implementation()
{
    if (bIsPossessed)
    {
        return;
    }

    bIsPossessed = true;

    if (USkeletalMeshComponent* CorpseMesh = GetMesh())
    {
        CorpseMesh->SetSimulatePhysics(false);
        CorpseMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    }

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->SetDefaultMovementMode();
    }

    if (PossessionControllerClass)
    {
        if (UWorld* World = GetWorld())
        {
            FActorSpawnParameters SpawnParams;
            SpawnParams.Owner = this;
            AAIController* SpawnedController = World->SpawnActor<AAIController>(PossessionControllerClass, GetActorLocation(), GetActorRotation(), SpawnParams);
            if (SpawnedController)
            {
                SpawnedController->Possess(this);
            }
        }
    }
}

bool ACrewCorpse::CanBeBloomPossessed_Implementation() const
{
    return !bIsPossessed;
}
