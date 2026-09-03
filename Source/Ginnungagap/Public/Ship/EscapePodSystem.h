#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "EscapePodSystem.generated.h"

class ACoopSurvivalCharacter;

UCLASS()
class GINNUNGAGAP_API AEscapePodSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    AEscapePodSystem();

    UPROPERTY(BlueprintReadOnly, Category = "Escape Pod")
    bool bIsOccupied = false;

    UPROPERTY()
    TWeakObjectPtr<ACoopSurvivalCharacter> OccupyingCharacter;

    UFUNCTION(BlueprintCallable, Category = "Escape Pod")
    bool TryEnterPod(ACoopSurvivalCharacter* Character);

    UFUNCTION(BlueprintCallable, Category = "Escape Pod")
    void ExitPod();

    UFUNCTION(BlueprintCallable, Category = "Escape Pod")
    bool IsFunctioning() const { return !bIsCorrupted; }

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;
};
