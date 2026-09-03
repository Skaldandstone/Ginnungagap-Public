#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PelagosTrafficController.generated.h"

class UPelagosArrivalDefinition;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPelagosTrafficSpawned, FName, SpawnId, AActor*, TrafficActor);

UCLASS(Blueprintable)
class GINNUNGAGAP_API APelagosTrafficController : public AActor
{
    GENERATED_BODY()

public:
    APelagosTrafficController();

    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    TObjectPtr<UPelagosArrivalDefinition> ArrivalDefinition;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    TSubclassOf<AActor> TrafficActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos", meta=(ClampMin="0.25"))
    float SpawnInterval = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    bool bAutoStart = true;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosTrafficSpawned OnTrafficSpawned;

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    void StartTraffic();

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    void StopTraffic();

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool SpawnNextTrafficActor();

    UFUNCTION(BlueprintPure, Category="Pelagos")
    int32 GetActiveTrafficCount() const;

private:
    void HandleSpawnTimer();
    void PruneTrafficActors();

    UPROPERTY()
    TArray<TObjectPtr<AActor>> ActiveTrafficActors;

    FTimerHandle SpawnTimer;
    int32 NextSpawnIndex = 0;
};
