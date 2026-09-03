#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PlayerHallucinationActor.generated.h"

class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EPlayerHallucinationType : uint8
{
    BloomGrowth,
    BloomApparition,
    PhantomMovement,
    PhantomSound,
    FalseInfection
};

/** A non-replicated, collision-free visual that only exists for the hallucinating player. */
UCLASS(NotPlaceable, Transient)
class GINNUNGAGAP_API APlayerHallucinationActor : public AActor
{
    GENERATED_BODY()

public:
    APlayerHallucinationActor();
    virtual void Tick(float DeltaTime) override;

    void Configure(EPlayerHallucinationType Type, float Severity, float LifetimeSeconds);

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    float HallucinationSeverity = 0.0f;
    float AgeSeconds = 0.0f;
    float TotalLifetimeSeconds = 2.0f;
};
