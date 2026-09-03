#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../Bloom/BloomCorruptible.h"
#include "ShipSystemActor.generated.h"

class UShipPowerNodeComponent;

UENUM(BlueprintType)
enum class EShipSystemType : uint8
{
    Door,
    LifeSupport,
    Navigation,
    Lighting,
    Comms,
    Cryo,
    Sensors,
    JumpDrive,
    Collector,
    EscapePod,
    SelfDestruct,
    Armor
};

UCLASS(Abstract)
class GINNUNGAGAP_API AShipSystemActor : public AActor, public IBloomCorruptible
{
    GENERATED_BODY()

public:
    AShipSystemActor();
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship System")
    EShipSystemType SystemType = EShipSystemType::Door;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship System")
    FString SystemName;

    UPROPERTY(BlueprintReadOnly, Category = "Ship System")
    bool bIsCorrupted = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ship System")
    TObjectPtr<UShipPowerNodeComponent> PowerNode;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ship System")
    TObjectPtr<class UStaticMeshComponent> VisualMesh;

    UFUNCTION(BlueprintPure, Category = "Ship System")
    bool IsOperational() const;

    virtual void OnBloomCorruption_Implementation() override;
    virtual void OnBloomPurged_Implementation() override;
    virtual bool CanBeBloomCorrupted_Implementation() const override;

protected:
    virtual void ApplyCorruptionEffects();
    virtual void RemoveCorruptionEffects();
};
