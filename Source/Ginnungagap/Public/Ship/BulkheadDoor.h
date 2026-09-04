#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "BulkheadDoor.generated.h"

class AShipSection;
class USceneComponent;

UCLASS()
class GINNUNGAGAP_API ABulkheadDoor : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ABulkheadDoor();

    /** Explicit placement handles on both sides of every room-threshold bulkhead. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bulkhead Door|Hardpoints")
    TObjectPtr<USceneComponent> RoomSideHardpoint;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bulkhead Door|Hardpoints")
    TObjectPtr<USceneComponent> CorridorSideHardpoint;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Bulkhead Door|Hardpoints")
    TObjectPtr<AShipSection> RoomSection;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Bulkhead Door|Hardpoints")
    TObjectPtr<AShipSection> CorridorSection;

    UPROPERTY(BlueprintReadOnly, Category = "Bulkhead Door")
    bool bIsSealed = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bulkhead Door")
    float SealedLeakFactor = 0.05f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bulkhead Door")
    float SealPowerDrawPerSecond = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bulkhead Door")
    float CycleDuration = 2.0f;

    /** A locked door does not cycle from its own panel; something else (an override station) releases it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bulkhead Door")
    bool bLocked = false;

    /** Why, in the words the prompt shows: "override from the CIC access panel". */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bulkhead Door")
    FText LockedReason;

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    void SetLocked(bool bInLocked);

    virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const override;

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    virtual void Seal();

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    virtual void Unseal();

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    bool CanBeSealed() const;

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    float GetTransferMultiplier() const;

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door")
    virtual bool IsPassable() const;

    UFUNCTION(BlueprintCallable, Category = "Bulkhead Door|Hardpoints")
    void ConfigureThresholdSides(AShipSection* InRoomSection, AShipSection* InCorridorSection);

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    void FinishCycle();

    bool bIsCycling = false;
    FTimerHandle CycleTimerHandle;
};
