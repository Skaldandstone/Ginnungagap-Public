#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShipDamageControlSubsystem.generated.h"

class UShipDamageComponent;
class AShipSection;

UCLASS()
class GINNUNGAGAP_API UShipDamageControlSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    void RegisterDamageComponent(UShipDamageComponent* Component);
    void UnregisterDamageComponent(UShipDamageComponent* Component);

    UFUNCTION(BlueprintPure, Category = "Damage Control")
    TArray<AShipSection*> GetDamagedSections(float MinimumDangerScore = 0.01f) const;

    UFUNCTION(BlueprintPure, Category = "Damage Control")
    AShipSection* GetMostCriticalSection() const;

private:
    UPROPERTY() TArray<TObjectPtr<UShipDamageComponent>> DamageComponents;
};

