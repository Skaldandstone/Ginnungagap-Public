#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "StarSystemTypes.h"
#include "ShipResourceInventorySubsystem.generated.h"

class AShipHelmSystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnShipResourceChanged, EStarSystemResourceType, ResourceType, int32, NewAmount, int32, Delta);

UCLASS()
class GINNUNGAGAP_API UShipResourceInventorySubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable, Category = "Resources")
    FOnShipResourceChanged OnResourceChanged;

    UFUNCTION(BlueprintCallable, Category = "Resources")
    void AddResource(EStarSystemResourceType ResourceType, int32 Amount);

    UFUNCTION(BlueprintCallable, Category = "Resources")
    bool TrySpendResource(EStarSystemResourceType ResourceType, int32 Amount);

    UFUNCTION(BlueprintCallable, Category = "Resources")
    int32 GetResourceAmount(EStarSystemResourceType ResourceType) const;

    UFUNCTION(BlueprintCallable, Category = "Resources")
    bool TrySpendForHeadingCorrection(AShipHelmSystem* Helm, float ReductionFraction = 1.0f, int32 FuelCost = 10);

protected:
    UPROPERTY()
    TMap<EStarSystemResourceType, int32> ResourceAmounts;
};
