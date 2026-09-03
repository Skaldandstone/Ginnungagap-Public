#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BTTask_ChasePlayer.generated.h"

class ACoopSurvivalCharacter;

UCLASS()
class GINNUNGAGAP_API UBTTask_ChasePlayer : public UBTTaskNode
{
    GENERATED_BODY()

public:
    UBTTask_ChasePlayer();

    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
    virtual void TickTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task")
    float AttackRange = 150.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Task")
    float DamagePerSecond = 10.0f;

private:
    float AccumulatedDamageTime = 0.0f;
};
