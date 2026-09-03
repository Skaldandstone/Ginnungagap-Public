#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ShipCheckpointVolume.generated.h"

class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FShipCheckpointReached, AShipCheckpointVolume*, Checkpoint, APawn*, PlayerPawn);

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipCheckpointVolume : public AActor
{
    GENERATED_BODY()

public:
    AShipCheckpointVolume();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Checkpoint")
    TObjectPtr<UBoxComponent> Trigger;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Checkpoint")
    FName CheckpointId = TEXT("DistrictCheckpoint");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Checkpoint")
    FVector RespawnOffset = FVector(300.0f, 0.0f, 100.0f);

    UPROPERTY(BlueprintReadOnly, Category="Checkpoint")
    bool bActivated = false;

    UPROPERTY(BlueprintAssignable, Category="Checkpoint")
    FShipCheckpointReached OnCheckpointReached;

protected:
    UFUNCTION()
    void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);
};
