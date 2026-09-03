#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../Interfaces/Interactable.h"
#include "StarSystemTypes.h"
#include "ResourceNodeActor.generated.h"

class AShipSystemActor;
class AResourceNodeActor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnResourceNodeDepleted, AResourceNodeActor*, ResourceNode);

UCLASS()
class GINNUNGAGAP_API AResourceNodeActor : public AActor, public IInteractable
{
    GENERATED_BODY()

public:
    AResourceNodeActor();
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Resource Node")
    TObjectPtr<class UStaticMeshComponent> VisualMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource Node")
    EResourceAcquisitionMethod RequiredMethod = EResourceAcquisitionMethod::EVARetrieval;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource Node")
    EStarSystemResourceType ResourceType = EStarSystemResourceType::NavigationFuel;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource Node")
    int32 Quantity = 10;

    UPROPERTY(BlueprintReadOnly, Category = "Resource Node|Operations")
    int32 GeneratedResourceIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Category = "Resource Node|Operations")
    bool bShipOnStation = false;

    UFUNCTION(BlueprintCallable, Category = "Resource Node|Operations")
    void SetShipOnStation(bool bOnStation);

    UPROPERTY(BlueprintAssignable, Category = "Resource Node|Operations")
    FOnResourceNodeDepleted OnResourceNodeDepleted;

    UFUNCTION(BlueprintCallable, Category = "Resource Node|Operations")
    void DepleteResourceNode();

    UFUNCTION(BlueprintImplementableEvent, Category = "Resource Node|Operations")
    void OnShipStationStateChanged(bool bOnStation);

    // Required for EResourceAcquisitionMethod::ShipSystemReactivation - e.g. an ADormantCollectorSystem.
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Resource Node")
    TObjectPtr<AShipSystemActor> RequiredSystem;

    UFUNCTION(BlueprintCallable, Category = "Resource Node")
    bool CanBeCollectedBy(APawn* Character) const;

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
};
