#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StarSystemTypes.h"
#include "PelagosArrivalDefinition.h"
#include "PelagosOrbitalArrivalDirector.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPelagosArrivalStateChanged, EPelagosArrivalState, PreviousState, EPelagosArrivalState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPelagosDockStateChanged, FName, DockId, EPelagosDockState, NewState);

UCLASS(Blueprintable)
class GINNUNGAGAP_API APelagosOrbitalArrivalDirector : public AActor
{
    GENERATED_BODY()

public:
    APelagosOrbitalArrivalDirector();

    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Pelagos")
    TObjectPtr<UPelagosArrivalDefinition> ArrivalDefinition;

    UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_ArrivalState, Category="Pelagos")
    EPelagosArrivalState ArrivalState = EPelagosArrivalState::Inactive;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Pelagos")
    FName ReservedDockId;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Pelagos")
    FName ActiveRouteId;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosArrivalStateChanged OnArrivalStateChanged;

    UPROPERTY(BlueprintAssignable, Category="Pelagos")
    FPelagosDockStateChanged OnDockStateChanged;

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    void NotifyJumpArrival(const FStarSystemData& SystemData);

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool AdvanceArrivalState();

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool RequestDock(FName RequestedDockId, bool bLargeShip, bool bEmergency);

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool BeginFinalApproach(FName RouteId);

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool ConfirmSoftCapture(FName DockId);

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool ConfirmHardDock(FName DockId);

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool ReleaseDock(FName DockId);

    UFUNCTION(BlueprintPure, Category="Pelagos")
    EPelagosDockState GetDockState(FName DockId) const;

    UFUNCTION(BlueprintPure, Category="Pelagos")
    bool GetDockDefinition(FName DockId, FPelagosDockDefinition& OutDock) const;

    UFUNCTION(BlueprintPure, Category="Pelagos")
    bool GetRouteDefinition(FName RouteId, FPelagosArrivalRouteDefinition& OutRoute) const;

    UFUNCTION(BlueprintCallable, Category="Pelagos")
    bool SetDockOperationalState(FName DockId, EPelagosDockState NewState);

    UFUNCTION(BlueprintPure, Category="Pelagos")
    bool IsArrivalComplete() const { return ArrivalState == EPelagosArrivalState::ArrivalComplete; }

    static bool IsValidStateTransition(EPelagosArrivalState From, EPelagosArrivalState To);

private:
    UFUNCTION()
    void OnRep_ArrivalState(EPelagosArrivalState PreviousState);

    void SetArrivalState(EPelagosArrivalState NewState);
    int32 FindDockIndex(FName DockId) const;
    int32 FindRouteIndex(FName RouteId) const;

    UPROPERTY(Replicated)
    TArray<EPelagosDockState> DockStates;
};
