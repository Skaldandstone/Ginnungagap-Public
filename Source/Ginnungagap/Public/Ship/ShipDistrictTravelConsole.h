#pragma once

#include "CoreMinimal.h"
#include "Ship/ShipInteractiveFixture.h"
#include "ShipDistrictTravelConsole.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FShipDistrictTravelDenied);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FShipDistrictTravelStarted, FName, DestinationMap);

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipDistrictTravelConsole : public AShipInteractiveFixture
{
    GENERATED_BODY()

public:
    AShipDistrictTravelConsole();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="District Travel")
    FName DestinationMapName = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="District Travel")
    FText DestinationDisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="District Travel")
    bool bRequireResolvedObjectives = true;

    UPROPERTY(BlueprintReadOnly, Category="District Travel")
    bool bTravelInProgress = false;

    UPROPERTY(BlueprintAssignable, Category="District Travel")
    FShipDistrictTravelDenied OnTravelDenied;

    UPROPERTY(BlueprintAssignable, Category="District Travel")
    FShipDistrictTravelStarted OnTravelStarted;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

    UFUNCTION(BlueprintPure, Category="District Travel")
    bool CanTravel() const;
};
