#pragma once

#include "CoreMinimal.h"
#include "Ship/ShipInteractiveFixture.h"
#include "ShipObjectiveConsole.generated.h"

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipObjectiveConsole : public AShipInteractiveFixture
{
    GENERATED_BODY()

public:
    AShipObjectiveConsole();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    FName ObjectiveId = TEXT("RestoreDistrictSystems");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    bool bSingleUse = true;

    UPROPERTY(BlueprintReadOnly, Category="Mission")
    bool bObjectiveResolved = false;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
};
