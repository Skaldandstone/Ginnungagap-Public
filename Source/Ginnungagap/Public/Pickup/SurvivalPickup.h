#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/Interactable.h"
#include "SurvivalPickup.generated.h"

UENUM(BlueprintType)
enum class EPickupType : uint8
{
    Oxygen,
    Health
};

UCLASS()
class GINNUNGAGAP_API ASurvivalPickup : public AActor, public IInteractable
{
    GENERATED_BODY()

public:
    ASurvivalPickup();
    virtual void OnConstruction(const FTransform& Transform) override;

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;

    UPROPERTY(Replicated, EditAnywhere, BlueprintReadWrite, Category="Pickup")
    EPickupType PickupType;

    UPROPERTY(Replicated, EditAnywhere, BlueprintReadWrite, Category="Pickup")
    float Amount = 25.0f;

    UFUNCTION()
    void OnOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

    UPROPERTY(VisibleAnywhere)
    class USphereComponent* CollisionSphere;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Pickup")
    TObjectPtr<class UStaticMeshComponent> VisualMesh;
};
