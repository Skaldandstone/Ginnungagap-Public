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

    /**
     * The weld itself, seen: a bead across the leaves while the door is welded, and while anyone
     * is welding or cutting it, a white-hot arc at the torch that flickers, lights the corridor,
     * and dims when the torch drifts off the seam. Nothing here is gameplay state; the bead and
     * the arc read the activity snapshot on every machine.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Welding|Look")
    TObjectPtr<UStaticMeshComponent> WeldSeam;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Welding|Look")
    TObjectPtr<UStaticMeshComponent> WeldArc;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Welding|Look")
    TObjectPtr<class UPointLightComponent> WeldArcLight;

    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Welding")
    FPlayerActivityDefinition WeldingActivity;

    /** The work of cutting a welded seam free again; offered instead of welding while the door is welded shut. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Welding")
    FPlayerActivityDefinition CuttingActivity;

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

    void UpdateWeldLook();
    FTimerHandle WeldLookTimer;
    float LastLookSeconds = 0.0f;

    UPROPERTY()
    TObjectPtr<class UMaterialInstanceDynamic> SeamMaterial;

    UPROPERTY()
    TObjectPtr<class UMaterialInstanceDynamic> ArcMaterial;

    /** How hot the bead reads, 0..1; climbs while worked and cools afterwards. */
    float SeamHeat = 0.0f;
};
