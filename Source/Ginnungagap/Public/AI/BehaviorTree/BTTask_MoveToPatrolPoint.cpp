// Copyright Epic Games, Inc. All Rights Reserved.

#include "AI/BehaviorTree/BTTask_MoveToPatrolPoint.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "AI/PatrollingEnemyController.h"
#include "Ship/ShipSection.h"
#include "Navigation/PathFollowingComponent.h"

UBTTask_MoveToPatrolPoint::UBTTask_MoveToPatrolPoint()
{
    NodeName = TEXT("Move To Patrol Point");
    bNotifyTick = true;
}

EBTNodeResult::Type UBTTask_MoveToPatrolPoint::ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
    APatrollingEnemyController* PatrolController = Cast<APatrollingEnemyController>(OwnerComp.GetAIOwner());
    if (!PatrolController)
    {
        return EBTNodeResult::Failed;
    }

    if (PatrolController->PatrolSections.Num() > 0)
    {
        AShipSection* Target = PatrolController->GetCurrentPatrolTarget();
        if (!Target && !PatrolController->ComputePathToNextSection())
        {
            return EBTNodeResult::Failed;
        }

        Target = PatrolController->GetCurrentPatrolTarget();
        if (!Target)
        {
            return EBTNodeResult::Failed;
        }

        PatrolController->MoveToLocation(Target->GetActorLocation(), AcceptanceRadius);
        return EBTNodeResult::InProgress;
    }

    if (PatrolController->PatrolPoints.Num() == 0)
    {
        return EBTNodeResult::Failed;
    }

    FVector TargetPoint = PatrolController->PatrolPoints[PatrolController->CurrentPatrolIndex];
    PatrolController->MoveToLocation(TargetPoint, AcceptanceRadius);

    return EBTNodeResult::InProgress;
}

void UBTTask_MoveToPatrolPoint::TickTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
    Super::TickTask(OwnerComp, NodeMemory, DeltaSeconds);

    APatrollingEnemyController* PatrolController = Cast<APatrollingEnemyController>(OwnerComp.GetAIOwner());
    if (!PatrolController)
    {
        FinishLatentTask(OwnerComp, EBTNodeResult::Failed);
        return;
    }

    if (PatrolController->GetMoveStatus() != EPathFollowingStatus::Idle)
    {
        return;
    }

    if (PatrolController->PatrolSections.Num() > 0)
    {
        PatrolController->AdvancePatrolStep();
        FinishLatentTask(OwnerComp, EBTNodeResult::Succeeded);
        return;
    }

    if (PatrolController->PatrolPoints.Num() > 0)
    {
        PatrolController->CurrentPatrolIndex = (PatrolController->CurrentPatrolIndex + 1) % PatrolController->PatrolPoints.Num();
    }
    FinishLatentTask(OwnerComp, EBTNodeResult::Succeeded);
}
