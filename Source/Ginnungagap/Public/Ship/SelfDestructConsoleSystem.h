#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "SelfDestructConsoleSystem.generated.h"

UCLASS()
class GINNUNGAGAP_API ASelfDestructConsoleSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ASelfDestructConsoleSystem();

    /** Opt-in fallback for C++-only demo stations that have no confirmation Blueprint. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Self Destruct")
    bool bArmOnInteractForNativeDemo = false;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

    UFUNCTION(BlueprintCallable, Category = "Self Destruct Console")
    bool ConfirmArm();

    UFUNCTION(BlueprintCallable, Category = "Self Destruct Console")
    bool ConfirmCancel();

    UFUNCTION(BlueprintImplementableEvent, Category = "Self Destruct Console")
    void OnSelfDestructConsoleOpened();

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;
};
