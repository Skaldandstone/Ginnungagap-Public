#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "InteractionComponent.generated.h"

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UInteractionComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UInteractionComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "Interaction")
    void TryInteract();

    UFUNCTION(Server, Reliable)
    void ServerTryInteract(AActor* Target);

    UFUNCTION(BlueprintCallable, Category = "Interaction")
    bool HasFocusedInteractable() const;

    UFUNCTION(BlueprintPure, Category = "Interaction")
    AActor* GetFocusedInteractable() const { return FocusedInteractable; }

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Interaction")
    float InteractionRange = 250.0f;

protected:
    UPROPERTY(BlueprintReadOnly, Category = "Interaction")
    TObjectPtr<AActor> FocusedInteractable;

private:
    void UpdateFocusedInteractable();
    bool IsValidInteractionTarget(const AActor* Target, const APawn* OwnerPawn) const;
};
