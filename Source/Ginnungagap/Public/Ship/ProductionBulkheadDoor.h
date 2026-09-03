#pragma once

#include "CoreMinimal.h"
#include "Ship/BulkheadDoor.h"
#include "ProductionBulkheadDoor.generated.h"

class UMaterialInterface;
class UPointLightComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * A bulkhead with a frame, a lintel and two leaves that actually open.
 *
 * The first version of this class shipped every door in the demo as a wall: its "frame" was a
 * full-size door mesh with BlockAll, its "panels" were wall sections scaled to 200 cm each and
 * opened 135 cm -- not far enough for a 200 cm leaf to clear a 250 cm gap -- and the Blueprint
 * added a leaf that was never attached. The doorway audit found 0 of 96 passable; the placement
 * script's fix was to hide all of it and let the greybox gap be the door.
 *
 * This version derives its geometry from the gap it is placed in and from the meshes it is given:
 * the frame is scaled so its opening is DoorwayWidth by DoorwayHeight, each leaf is scaled to
 * cover exactly half the opening and slides its own width plus a margin into the wall, and the
 * lintel fills whatever is left between the frame top and the ceiling. Nothing here blocks the
 * opening except the leaves, and only while sealed.
 *
 * Meshes default to the Modular_Scifi_Mechanic_Base door frame and leaves the rest of the
 * dressing already uses, so a door reads as part of the same kit as the wall it sits in.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AProductionBulkheadDoor : public ABulkheadDoor
{
    GENERATED_BODY()

public:
    AProductionBulkheadDoor();

    virtual void Tick(float DeltaSeconds) override;
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;
    virtual void Seal() override;
    virtual void Unseal() override;

    /** The gap in the wall this door sits in, in the door's own space (X along the wall, Z up). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="50.0"))
    float DoorwayWidth = 250.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="50.0"))
    float DoorwayHeight = 270.0f;

    /** Interior height above the walkable floor; the lintel fills from the frame top to here. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="0.0"))
    float CeilingHeight = 410.0f;

    /** Where the walkable floor is above the actor origin. The generator places doors 10 cm under a 20 cm floor slab's centre. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry")
    float FloorOffset = 20.0f;

    /** Extra travel past its own width, so an open leaf sits fully inside the wall. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="0.0"))
    float LeafSlideMargin = 8.0f;

    /** The frame mesh's own opening, so a different gap scales it to fit. Measured from SM_DOOR_FRAME_01_INSIDE. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="1.0"))
    float FrameNativeOpeningWidth = 271.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Geometry", meta=(ClampMin="1.0"))
    float FrameNativeOpeningHeight = 270.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMesh> FrameMeshAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMesh> LeftLeafMeshAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMesh> RightLeafMeshAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMesh> LintelMeshAsset;

    /** The old single-panel field. Honoured only when no leaf assets are set, for saved instances. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMesh> PanelMeshAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UMaterialInterface> DoorMaterial;

    /** Off by default: the kit meshes carry their own materials, and the greybox hull material flattens them. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    bool bApplyDoorMaterial = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    float VisualMoveSpeed = 4.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMeshComponent> FrameMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMeshComponent> LeftPanel;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMeshComponent> RightPanel;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UStaticMeshComponent> LintelMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Bulkhead Visuals")
    TObjectPtr<UPointLightComponent> SealIndicator;

    /** 0 closed, 1 open, from where the leaves actually are. */
    UFUNCTION(BlueprintPure, Category="Bulkhead Visuals")
    float GetLeafOpenFraction() const;

private:
    void ApplyGeometry();
    void SnapLeavesToState();
    FVector LeafTarget(bool bLeft) const;

    float LeftClosedX = 0.0f;
    float RightClosedX = 0.0f;
    float LeafOpenTravel = 0.0f;
    float LeafZ = 0.0f;
};
