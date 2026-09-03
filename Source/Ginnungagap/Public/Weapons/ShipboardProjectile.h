#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Weapons/ShipboardWeaponTypes.h"
#include "ShipboardProjectile.generated.h"

class UProjectileMovementComponent;
class UPrimitiveComponent;
class USphereComponent;
class UStaticMeshComponent;

/** Server-authoritative physical round used by civilian and improvised projectile weapons. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipboardProjectile : public AActor
{
    GENERATED_BODY()

public:
    AShipboardProjectile();

    void InitializeProjectile(const FWeaponFiringProfile& InProfile, const FVector& Direction,
        AActor* InSourceWeapon, AActor* InOperator);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<USphereComponent> Collision;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<UStaticMeshComponent> Visual;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Projectile")
    TObjectPtr<UProjectileMovementComponent> Movement;

protected:
    UFUNCTION()
    void HandleImpact(UPrimitiveComponent* HitComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit);

    void ApplyImpact(const FHitResult& Hit);

    FWeaponFiringProfile Profile;
    TWeakObjectPtr<AActor> SourceWeapon;
    TWeakObjectPtr<AActor> OperatorActor;
};
