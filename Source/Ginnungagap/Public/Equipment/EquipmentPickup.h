#pragma once

#include "CoreMinimal.h"
#include "Pickup/SurvivalPickup.h"
#include "Equipment/EquipmentSystem.h"
#include "EquipmentPickup.generated.h"

UCLASS()
class GINNUNGAGAP_API AEquipmentPickup : public ASurvivalPickup
{
    GENERATED_BODY()

public:
    AEquipmentPickup();
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Equipment")
    FEquipmentItem EquipmentItem;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Equipment")
    FVector PickupRotationSpeed = FVector(0.0f, 0.0f, 90.0f); // Degrees per second

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

private:
    void RotatePickup(float DeltaTime);
};
