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

    /**
     * Something else has set the movement mode (the magnetic suit letting go, a respawn): apply
     * the ship's gravity again on the next tick rather than remembering it was already applied.
     */
    void Reassert() { bUnderPseudoGravity = false; }

private:
    bool bUnderPseudoGravity = false;
};
