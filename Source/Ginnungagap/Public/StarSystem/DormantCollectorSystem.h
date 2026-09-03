#pragma once

#include "CoreMinimal.h"
#include "../Ship/ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "DormantCollectorSystem.generated.h"

UCLASS()
class GINNUNGAGAP_API ADormantCollectorSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ADormantCollectorSystem();

    UPROPERTY(BlueprintReadOnly, Category = "Collector")
    bool bIsReactivated = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Collector")
    float ReactivationDuration = 5.0f;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

    UFUNCTION(BlueprintPure, Category = "Collector")
    bool CanBeginReactivation() const;

    UFUNCTION(BlueprintPure, Category = "Collector")
    bool IsReactivating() const { return bIsReactivating; }

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    void FinishReactivation();

    bool bIsReactivating = false;
    FTimerHandle ReactivationTimerHandle;
};
