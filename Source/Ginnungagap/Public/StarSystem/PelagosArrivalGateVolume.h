#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PelagosArrivalDefinition.h"
#include "PelagosArrivalGateVolume.generated.h"

class APelagosOrbitalArrivalDirector;
class UBoxComponent;

UENUM(BlueprintType)
enum class EPelagosGateAction : uint8
{
    AdvanceState,
    RequestDock,
    BeginFinalApproach,
    ConfirmSoftCapture,
    ConfirmHardDock,
    ReleaseDock
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPelagosGateTriggered, FName, GateId, AActor*, TriggeringActor);

UCLASS(Blueprintable)
class GINNUNGAGAP_API APelagosArrivalGateVolume : public AActor
{
    GENERATED_BODY()

public:
    APelagosArrivalGateVolume();

    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Pelagos")
    TObjectPtr<UBoxComponent> TriggerVolume;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    FName GateId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    EPelagosGateAction Action = EPelagosGateAction::AdvanceState;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    EPelagosArrivalState RequiredState = EPelagosArrivalState::JumpExit;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    FName DockId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    FName RouteId = TEXT("PlayerArrival");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    FName RequiredActorTag = TEXT("PlayerShip");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    bool bDisableAfterSuccess = true;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosGateTriggered OnGateTriggered;

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    void SetGateEnabled(bool bEnabled);

protected:
    UFUNCTION()
    void HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
        const FHitResult& SweepResult);

private:
    APelagosOrbitalArrivalDirector* ResolveDirector() const;
};
