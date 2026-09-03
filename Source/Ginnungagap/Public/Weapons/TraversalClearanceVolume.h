#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TraversalClearanceVolume.generated.h"

class AShipboardWeapon;
class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnTraversalClearanceRejected,
    AActor*, Operator, AShipboardWeapon*, MountedWeapon);

/**
 * Authorable approach volume for a hatch, duct, squeeze gap, or blocked passage.
 * Local X is the travel axis; ClearWidth and ClearHeight describe its actual aperture.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ATraversalClearanceVolume : public AActor
{
    GENERATED_BODY()

public:
    ATraversalClearanceVolume();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

    UFUNCTION(BlueprintPure, Category = "Traversal|Clearance")
    bool CanWeaponTraverse(const AShipboardWeapon* Weapon, bool bTestFolded = false) const;

    UFUNCTION(BlueprintPure, Category = "Traversal|Clearance")
    bool ShouldBlockMovement(const AActor* Operator, const AShipboardWeapon* Weapon,
        const FVector& WorldMovementDirection) const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Traversal|Clearance")
    TObjectPtr<UBoxComponent> ApproachVolume;

    /** Clear aperture width along local Y. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance", meta = (ClampMin = "1.0"))
    float ClearWidthCm = 90.0f;

    /** Clear aperture height along local Z. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance", meta = (ClampMin = "1.0"))
    float ClearHeightCm = 90.0f;

    /** Total approach-zone depth. It must extend far enough to detect the weapon before the aperture. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance", meta = (ClampMin = "10.0"))
    float ApproachDepthCm = 180.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance", meta = (ClampMin = "0.0"))
    float ApproachPaddingCm = 30.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance")
    bool bAllowAutomaticWeaponFolding = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Traversal|Clearance")
    bool bRestoreWeaponAfterExit = true;

    UPROPERTY(BlueprintAssignable, Category = "Traversal|Clearance")
    FOnTraversalClearanceRejected OnTraversalRejected;

    void BroadcastRejected(AActor* Operator, AShipboardWeapon* Weapon);
};
