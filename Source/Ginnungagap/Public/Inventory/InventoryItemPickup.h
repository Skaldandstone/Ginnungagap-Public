#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/Interactable.h"
#include "InventoryItemPickup.generated.h"

class UItemDefinition;
class USphereComponent;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnInventoryPickupCollected, UItemDefinition*, Item, int32, Quantity);

/** Replicated physical stack that transfers atomically into a player's inventory. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AInventoryItemPickup : public AActor, public IInteractable
{
    GENERATED_BODY()

public:
    AInventoryItemPickup();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
    virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const override;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Pickup")
    void ConfigurePickup(UItemDefinition* NewItem, int32 NewQuantity);

    UFUNCTION(BlueprintPure, Category = "Pickup")
    bool CanBeCollectedBy(const APawn* InteractingPawn) const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
    TObjectPtr<USphereComponent> CollisionSphere;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Pickup")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(ReplicatedUsing = OnRep_PickupState, EditAnywhere, BlueprintReadOnly, Category = "Pickup")
    TObjectPtr<UItemDefinition> ItemDefinition = nullptr;

    UPROPERTY(ReplicatedUsing = OnRep_PickupState, EditAnywhere, BlueprintReadOnly, Category = "Pickup", meta = (ClampMin = "1"))
    int32 Quantity = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Pickup", meta = (ClampMin = "25.0"))
    float InteractionRadiusCm = 95.0f;

    UPROPERTY(BlueprintAssignable, Category = "Pickup")
    FOnInventoryPickupCollected OnCollected;

protected:
    UFUNCTION()
    void OnRep_PickupState();

    void RefreshPresentation();
};
