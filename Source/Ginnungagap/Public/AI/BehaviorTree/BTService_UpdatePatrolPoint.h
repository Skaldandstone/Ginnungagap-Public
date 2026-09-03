#pragma once

#include "CoreMinimal.h"
#include "BehaviorTree/BTService.h"
#include "BTService_UpdatePatrolPoint.generated.h"

UCLASS()
class GINNUNGAGAP_API UBTService_UpdatePatrolPoint : public UBTService
{
    GENERATED_BODY()

public:
    UBTService_UpdatePatrolPoint();

    virtual void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float DeltaSeconds) override;
};
