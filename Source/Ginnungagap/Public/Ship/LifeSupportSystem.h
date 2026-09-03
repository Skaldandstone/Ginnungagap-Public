#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "LifeSupportSystem.generated.h"

class ACoopSurvivalCharacter;

UCLASS()
class GINNUNGAGAP_API ALifeSupportSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ALifeSupportSystem();

    virtual void Tick(float DeltaTime) override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Life Support")
    float OxygenDrainMultiplierWhenFailed = 4.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Life Support")
    float DrainRampUpSeconds = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Life Support|Atmosphere")
    float CarbonDioxideStatusStartsAtRamp = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Life Support")
    float RepairDuration = 4.0f;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    void FinishRepair();
    bool IsCharacterProtectedByCryo(const ACoopSurvivalCharacter* Character) const;

    float TimeSinceFailureStarted = 0.0f;
    bool bIsRepairing = false;
    FTimerHandle RepairTimerHandle;
};
