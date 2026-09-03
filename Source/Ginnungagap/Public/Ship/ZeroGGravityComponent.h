#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ZeroGGravityComponent.generated.h"

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UZeroGGravityComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UZeroGGravityComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Zero G")
    float GravityScalePerAcceleration = 0.0001f;

private:
    bool bUnderPseudoGravity = false;
};
