#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Weapons/ShipboardWeaponTypes.h"
#include "ShipboardWeapon.generated.h"

class UBoxComponent;
class UShipboardWeaponDefinition;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnShipboardWeaponFired, const FHitResult&, Hit, bool, bUnsafeMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWeaponModificationChanged, bool, bUnsafeMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWeaponUpgradeLevelChanged, int32, NewLevel, int32, MaxLevel);

/** A physical tool-weapon instance that can move unchanged between a player and a drone. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipboardWeapon : public AActor
{
    GENERATED_BODY()

public:
    AShipboardWeapon();

    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category = "Weapon")
    bool TryFire(const FVector& AimOrigin, const FVector& AimDirection, FHitResult& OutHit);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Mounting")
    void SetMountedState(AActor* NewOperator, EWeaponOperatorType NewOperatorType);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Modification")
    void SetUnsafeModificationInstalled(bool bInstalled);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Upgrade")
    bool TryInstallNextUpgrade();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Upgrade")
    void SetUpgradeLevel(int32 NewUpgradeLevel);

    UFUNCTION(BlueprintPure, Category = "Weapon|Upgrade")
    int32 GetMaxUpgradeLevel() const;

    UFUNCTION(BlueprintPure, Category = "Weapon")
    FWeaponFiringProfile GetActiveFiringProfile() const;

    UFUNCTION(BlueprintPure, Category = "Weapon")
    FWeaponCollisionEnvelope GetCollisionEnvelope() const;

    UFUNCTION(BlueprintPure, Category = "Weapon|Shield")
    bool IsRescueShieldActive() const { return bRescueShieldActive; }

    UFUNCTION(BlueprintPure, Category = "Weapon|Mounting")
    bool IsCompatibleWith(EWeaponOperatorType CandidateOperator) const;

    UFUNCTION(BlueprintPure, Category = "Weapon|Traversal")
    bool FitsOpening(const FVector& OpeningFullExtentsCm) const;

    UFUNCTION(BlueprintPure, Category = "Weapon|Traversal")
    bool FitsPassageAperture(const FTransform& PassageTransform, float ClearWidthCm, float ClearHeightCm, bool bTestFolded = false) const;

    UFUNCTION(BlueprintPure, Category = "Weapon|Traversal")
    FVector GetTraversalHalfExtents() const;

    UFUNCTION(BlueprintPure, Category = "Weapon|Traversal")
    FVector GetTraversalEnvelopeWorldCenter() const;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Traversal")
    void SetTraversalFolded(bool bFolded);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
    TObjectPtr<USceneComponent> Muzzle;

    /** Query-only representation used by traversal volumes and drone route planners. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Traversal")
    TObjectPtr<UBoxComponent> EnvelopeVolume;

    /** Enabled only while a rescue-shield firing profile is active. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon|Shield")
    TObjectPtr<UBoxComponent> RescueShieldVolume;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
    TObjectPtr<UShipboardWeaponDefinition> Definition;

    /** Actor-local defaults allow usable C++/Blueprint weapons before a Data Asset is authored. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Defaults")
    FWeaponFiringProfile SafeProfile;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Defaults")
    FWeaponFiringProfile UnsafeModifiedProfile;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Defaults")
    FWeaponCollisionEnvelope CollisionEnvelope;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Mounting")
    bool bPlayerCompatible = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Mounting")
    bool bAerialDroneCompatible = true;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon|Mounting")
    bool bRoboticDroneCompatible = true;

    UPROPERTY(ReplicatedUsing = OnRep_UnsafeModification, BlueprintReadOnly, Category = "Weapon|Modification")
    bool bUnsafeModificationInstalled = false;

    UPROPERTY(ReplicatedUsing = OnRep_UpgradeLevel, BlueprintReadOnly, Category = "Weapon|Upgrade")
    int32 UpgradeLevel = 0;

    UPROPERTY(ReplicatedUsing = OnRep_TraversalFolded, BlueprintReadOnly, Category = "Weapon|Traversal")
    bool bTraversalFolded = false;

    UPROPERTY(ReplicatedUsing = OnRep_RescueShieldActive, BlueprintReadOnly, Category = "Weapon|Shield")
    bool bRescueShieldActive = false;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Weapon|Mounting")
    TObjectPtr<AActor> OperatorActor;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Weapon|Mounting")
    EWeaponOperatorType OperatorType = EWeaponOperatorType::Unmounted;

    UPROPERTY(BlueprintAssignable, Category = "Weapon")
    FOnShipboardWeaponFired OnWeaponFired;

    UPROPERTY(BlueprintAssignable, Category = "Weapon")
    FOnWeaponModificationChanged OnModificationChanged;

    UPROPERTY(BlueprintAssignable, Category = "Weapon|Upgrade")
    FOnWeaponUpgradeLevelChanged OnUpgradeLevelChanged;

protected:
    UFUNCTION()
    void OnRep_UnsafeModification();

    UFUNCTION()
    void OnRep_UpgradeLevel();

    UFUNCTION()
    void OnRep_TraversalFolded();

    UFUNCTION()
    void OnRep_RescueShieldActive();

    UFUNCTION()
    void ClearRescueShield();

    UFUNCTION(NetMulticast, Unreliable)
    void MulticastFireCosmetics(FVector_NetQuantize TraceEnd, bool bHit, bool bUnsafeMode);

    UFUNCTION(BlueprintImplementableEvent, Category = "Weapon|Presentation")
    void ReceiveFireCosmetics(FVector TraceEnd, bool bHit, bool bUnsafeMode);

    void RefreshFromDefinition();
    void ApplyImpact(const FWeaponFiringProfile& Profile, const FVector& AimDirection, const FHitResult& Hit);
    void ApplyRecoil(const FWeaponFiringProfile& Profile, const FVector& AimDirection);

    /**
     * Publishes the shot to the stealth perception system. Attributed to the operator rather than
     * to the weapon actor, so hostility checks and "ignore my own noise" resolve against the
     * crew member who pulled the trigger.
     */
    void ReportFiringNoise(const FWeaponFiringProfile& Profile) const;
    bool FirePhysicalProjectiles(const FVector& AimOrigin, const FVector& AimDirection,
        const FWeaponFiringProfile& Profile);
    bool ActivateRescueShield(const FWeaponFiringProfile& Profile);

    double LastFireTimeSeconds = -DBL_MAX;
    FTimerHandle RescueShieldTimer;
};
