#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "Weapons/ShipboardWeaponTypes.h"
#include "WeaponMountComponent.generated.h"

class AShipboardWeapon;
class ATraversalClearanceVolume;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMountedWeaponChanged, AShipboardWeapon*, Weapon);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWeaponClearanceBlocked, AActor*, BlockingActor,
    AShipboardWeapon*, Weapon);

/** Operator-neutral socket used by player grips, aerial drones, and robotic drones. */
UCLASS(ClassGroup = (Weapons), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UWeaponMountComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    UWeaponMountComponent();

    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Mount")
    bool MountWeapon(AShipboardWeapon* Weapon);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Mount")
    AShipboardWeapon* ReleaseWeapon(bool bEnablePhysics = true);

    UFUNCTION(BlueprintCallable, Category = "Weapon|Mount")
    bool FireWeapon(const FVector& AimOrigin, const FVector& AimDirection);

    UFUNCTION(BlueprintCallable, Category = "Weapon|Mount")
    bool FireAlongMountForward();

    UFUNCTION(BlueprintCallable, Category = "Weapon|Mount")
    void SetUnsafeModificationInstalled(bool bInstalled);

    UFUNCTION(BlueprintPure, Category = "Weapon|Mount")
    AShipboardWeapon* GetMountedWeapon() const { return MountedWeapon; }

    /** Sweeps the mounted weapon's oriented envelope and evaluates active passage constraints. */
    UFUNCTION(BlueprintCallable, Category = "Weapon|Traversal")
    bool CanMoveMountedWeapon(const FVector& WorldMovementDirection, float ProbeDistanceCm,
        FHitResult& OutBlockingHit);

    UFUNCTION(BlueprintPure, Category = "Weapon|Traversal")
    bool CanFitPassage(const ATraversalClearanceVolume* Passage, bool bTestFolded = false) const;

    UFUNCTION(BlueprintCallable, Category = "Weapon|Traversal")
    void SetMountedWeaponFolded(bool bFolded);

    void HandleClearanceVolumeExited(const ATraversalClearanceVolume* Passage);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Mount")
    EWeaponOperatorType OperatorType = EWeaponOperatorType::Player;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Mount")
    bool bSpawnDefaultWeapon = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Mount", meta = (EditCondition = "bSpawnDefaultWeapon"))
    TSubclassOf<AShipboardWeapon> DefaultWeaponClass;

    UPROPERTY(ReplicatedUsing = OnRep_MountedWeapon, BlueprintReadOnly, Category = "Weapon|Mount")
    TObjectPtr<AShipboardWeapon> MountedWeapon;

    UPROPERTY(BlueprintAssignable, Category = "Weapon|Mount")
    FOnMountedWeaponChanged OnMountedWeaponChanged;

    UPROPERTY(BlueprintAssignable, Category = "Weapon|Traversal")
    FOnWeaponClearanceBlocked OnWeaponClearanceBlocked;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal", meta = (ClampMin = "0.0"))
    float EnvelopeCollisionSkinCm = 2.0f;

private:
    UFUNCTION(Server, Reliable)
    void ServerFireWeapon(FVector_NetQuantize AimOrigin, FVector_NetQuantizeNormal AimDirection);

    UFUNCTION(Server, Reliable)
    void ServerSetUnsafeModificationInstalled(bool bInstalled);

    UFUNCTION(Server, Reliable)
    void ServerSetTraversalFolded(bool bFolded);

    UFUNCTION()
    void OnRep_MountedWeapon();

    void AttachMountedWeapon();
    bool TryAutomaticFoldForPassage(ATraversalClearanceVolume* Passage);

    UPROPERTY(Transient)
    TWeakObjectPtr<ATraversalClearanceVolume> AutomaticFoldSource;

    bool bWasFoldedBeforeAutomaticFold = false;
};
