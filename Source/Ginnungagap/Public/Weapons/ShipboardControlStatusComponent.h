#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Weapons/ShipboardWeaponTypes.h"
#include "ShipboardControlStatusComponent.generated.h"

class UCharacterMovementComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FShipboardControlEffectChanged, EWeaponControlEffect, ActiveEffect);

/** Replicated runtime state applied by restraint and less-lethal projectile payloads. */
UCLASS(ClassGroup = (Weapons), BlueprintType, meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UShipboardControlStatusComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UShipboardControlStatusComponent();

    /** Finds an existing receiver or creates a transient replicated receiver on the authoritative target. */
    static UShipboardControlStatusComponent* FindOrCreate(AActor* TargetActor);

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Weapon|Control")
    void ApplyControlEffect(EWeaponControlEffect Effect, float DurationSeconds, float MovementMultiplier);

    UFUNCTION(BlueprintPure, Category = "Weapon|Control")
    bool IsControlEffectActive() const { return ActiveEffect != EWeaponControlEffect::None; }

    UFUNCTION(BlueprintPure, Category = "Weapon|Control")
    bool IsMarked() const { return ActiveEffect == EWeaponControlEffect::Mark; }

    UFUNCTION(BlueprintPure, Category = "Weapon|Control")
    EWeaponControlEffect GetActiveEffect() const { return ActiveEffect; }

    UFUNCTION(BlueprintPure, Category = "Weapon|Control")
    float GetRemainingDurationSeconds() const;

    UPROPERTY(BlueprintAssignable, Category = "Weapon|Control")
    FShipboardControlEffectChanged OnControlEffectChanged;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION()
    void OnRep_ControlState();

    UFUNCTION()
    void ClearControlEffect();

    void CaptureMovementBaseline();
    void EnforceMovementState();
    void RestoreMovementState();
    UCharacterMovementComponent* FindCharacterMovement() const;

    UPROPERTY(ReplicatedUsing = OnRep_ControlState, BlueprintReadOnly, Category = "Weapon|Control")
    EWeaponControlEffect ActiveEffect = EWeaponControlEffect::None;

    UPROPERTY(ReplicatedUsing = OnRep_ControlState, BlueprintReadOnly, Category = "Weapon|Control")
    float EffectEndTimeSeconds = 0.0f;

    UPROPERTY(ReplicatedUsing = OnRep_ControlState, BlueprintReadOnly, Category = "Weapon|Control")
    float ActiveMovementMultiplier = 1.0f;

    float BaselineMaxWalkSpeed = 0.0f;
    bool bMovementBaselineCaptured = false;
    FTimerHandle ExpirationTimer;
};
