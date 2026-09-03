#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BTTask_MoveToPatrolPoint.generated.h"

UCLASS()
class GINNUNGAGAP_API UBTTask_MoveToPatrolPoint : public UBTTaskNode
{
    GENERATED_BODY()

public:
    UBTTask_MoveToPatrolPoint();

    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
    virtual void TickTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Task")
    float AcceptanceRadius = 100.0f;
};
