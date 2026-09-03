// Copyright Epic Games, Inc. All Rights Reserved.

#include "AI/BehaviorTree/BTTask_ChasePlayer.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "AIController.h"
#include "CoopSurvivalCharacter.h"
#include "Kismet/GameplayStatics.h"

UBTTask_ChasePlayer::UBTTask_ChasePlayer()
{
    NodeName = TEXT("Chase Player");
    bNotifyTick = true;
}

EBTNodeResult::Type UBTTask_ChasePlayer::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
    AccumulatedDamageTime = 0.0f;

    AAIController* AIController = OwnerComp.GetAIOwner();
    if (!AIController)
    {
        return EBTNodeResult::Failed;
    }

    ACoopSurvivalCharacter* PlayerCharacter = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerCharacter(AIController, 0));
    if (!PlayerCharacter)
    {
        return EBTNodeResult::Failed;
    }

    AIController->MoveToActor(PlayerCharacter, AttackRange * 0.5f);

    return EBTNodeResult::InProgress;
}

void UBTTask_ChasePlayer::TickTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
    Super::TickTask(OwnerComp, NodeMemory, DeltaSeconds);

    AAIController* AIController = OwnerComp.GetAIOwner();
    if (!AIController)
    {
        FinishLatentTask(OwnerComp, EBTNodeResult::Failed);
        return;
    }

    APawn* ControlledPawn = AIController->GetPawn();
    ACoopSurvivalCharacter* PlayerCharacter = Cast<ACoopSurvivalCharacter>(UGameplayStatics::GetPlayerCharacter(AIController, 0));

    if (!ControlledPawn || !PlayerCharacter)
    {
        FinishLatentTask(OwnerComp, EBTNodeResult::Failed);
        return;
    }

    float Distance = FVector::Dist(ControlledPawn->GetActorLocation(), PlayerCharacter->GetActorLocation());

    if (Distance <= AttackRange)
    {
        AccumulatedDamageTime += DeltaSeconds;
        if (AccumulatedDamageTime >= 1.0f)
        {
            AccumulatedDamageTime -= 1.0f;
            PlayerCharacter->HealthPercent = FMath::Clamp(PlayerCharacter->HealthPercent - DamagePerSecond, 0.0f, 100.0f);
        }
    }
    else
    {
        AIController->MoveToActor(PlayerCharacter, AttackRange * 0.5f);
    }
}