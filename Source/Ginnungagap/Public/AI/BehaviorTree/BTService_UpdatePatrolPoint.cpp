// Copyright Epic Games, Inc. All Rights Reserved.

#include "AI/BehaviorTree/BTService_UpdatePatrolPoint.h"
#include "BehaviorTree/BehaviorTreeComponent.h"

UBTService_UpdatePatrolPoint::UBTService_UpdatePatrolPoint()
{
    NodeName = TEXT("Update Patrol Point");
    Interval = 1.0f;
}

void UBTService_UpdatePatrolPoint::TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds)
{
    Super::TickNode(OwnerComp, NodeMemory, DeltaSeconds);

    // TODO: select/update the current patrol target on the blackboard.
    // This needs a blackboard key (e.g. a Vector or Object key for the patrol point)
    // exposed on this class before real patrol logic can be written here.
}