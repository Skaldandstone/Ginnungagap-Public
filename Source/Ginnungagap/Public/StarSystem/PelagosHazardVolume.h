#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PelagosArrivalDefinition.h"
#include "PelagosHazardVolume.generated.h"

class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPelagosHazardContact, FName, HazardId, AActor*, AffectedActor);

UCLASS(Blueprintable)
class GINNUNGAGAP_API APelagosHazardVolume : public AActor
{
    GENERATED_BODY()

public:
    APelagosHazardVolume();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Pelagos")
    TObjectPtr<UBoxComponent> HazardBounds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    FPelagosHazardDefinition Definition;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos", meta=(ClampMin="0.05"))
    float DamageInterval = 0.5f;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosHazardContact OnHazardEntered;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosHazardContact OnHazardExited;

protected:
    UFUNCTION()
    void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

    UFUNCTION()
    void HandleEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex);

private:
    TSet<TWeakObjectPtr<AActor>> OverlappingActors;
    float DamageAccumulator = 0.0f;
};
