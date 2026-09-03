#pragma once

#include "CoreMinimal.h"
#include "Ship/ProductionBulkheadDoor.h"
#include "Activities/PlayerActivitySource.h"
#include "WeldableBulkheadDoor.generated.h"

/** Emergency bulkhead that can be permanently seam-welded until explicitly cut free. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AWeldableBulkheadDoor : public AProductionBulkheadDoor, public IPlayerActivitySource
{
    GENERATED_BODY()

public:
    AWeldableBulkheadDoor();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Welding")
    FPlayerActivityDefinition WeldingActivity;

    UPROPERTY(ReplicatedUsing=OnRep_WeldedShut, BlueprintReadOnly, Category="Welding")
    bool bWeldedShut = false;

    UFUNCTION(BlueprintCallable, Category="Welding")
    void CutEmergencyWeld();

    virtual void Unseal() override;
    virtual bool IsPassable() const override;

    UFUNCTION(BlueprintImplementableEvent, Category="Welding")
    void OnWeldStateChanged(bool bIsWelded);

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
    virtual FPlayerActivityDefinition GetActivityDefinition_Implementation(APawn* Player) const override;
    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    UFUNCTION()
    void OnRep_WeldedShut();
};
