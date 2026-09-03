#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RetrievalDroneActor.generated.h"

class AResourceNodeActor;

UENUM(BlueprintType)
enum class EDroneState : uint8
{
    Docked,
    OutboundTravel,
    Collecting,
    ReturnTravel,
    Returned,
    Lost
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDroneStateChanged, EDroneState, NewState);

UCLASS()
class GINNUNGAGAP_API ARetrievalDroneActor : public AActor
{
    GENERATED_BODY()

public:
    ARetrievalDroneActor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Drone")
    TObjectPtr<class UStaticMeshComponent> VisualMesh;

    UPROPERTY(BlueprintReadOnly, Category = "Drone")
    EDroneState CurrentState = EDroneState::Docked;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Drone")
    float OutboundTravelDuration = 6.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Drone")
    float CollectingDuration = 3.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Drone")
    float ReturnTravelDuration = 6.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Drone")
    float BaseLossChance = 0.05f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Drone")
    float LossChancePerSeverity = 0.15f;

    // Assigns the drone to a node and starts the round trip. HazardSeverity (0..1) scales the loss chance.
    UFUNCTION(BlueprintCallable, Category = "Drone")
    bool DispatchTo(AResourceNodeActor* TargetNode, float HazardSeverity);

    /** Recovers a lost/returned drone to a safe docked state after physical servicing. */
    UFUNCTION(BlueprintCallable, Category = "Drone")
    void RepairAndRecall();

    UFUNCTION(BlueprintPure, Category = "Drone")
    float GetStateProgress() const;

    UPROPERTY(BlueprintAssignable, Category = "Drone")
    FOnDroneStateChanged OnDroneStateChanged;

private:
    void BeginCollecting();
    void BeginReturnTravel();
    void FinishReturn();
    void SetDroneState(EDroneState NewState);

    UPROPERTY()
    TWeakObjectPtr<AResourceNodeActor> AssignedTargetNode;

    bool bWillBeLost = false;
    FTimerHandle StateTimerHandle;
};
