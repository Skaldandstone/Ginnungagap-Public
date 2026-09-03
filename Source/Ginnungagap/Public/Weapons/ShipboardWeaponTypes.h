#pragma once

#include "CoreMinimal.h"
#include "ShipboardWeaponTypes.generated.h"

UENUM(BlueprintType)
enum class EWeaponOperatorType : uint8
{
    Unmounted UMETA(DisplayName = "Unmounted"),
    Player UMETA(DisplayName = "Player"),
    AerialDrone UMETA(DisplayName = "Aerial Drone"),
    RoboticDrone UMETA(DisplayName = "Robotic Drone")
};

UENUM(BlueprintType)
enum class EWeaponEnvelopeClass : uint8
{
    Compact,
    Standard,
    Long,
    Bulky,
    Emplaced
};

UENUM(BlueprintType)
enum class EWeaponDeliveryMode : uint8
{
    Trace UMETA(DisplayName = "Instant Trace"),
    Projectile UMETA(DisplayName = "Physical Projectile"),
    RescueShield UMETA(DisplayName = "Timed Rescue Shield")
};

UENUM(BlueprintType)
enum class EWeaponUpgradeResource : uint8
{
    StructuralAlloy,
    SensorComponents,
    PowerCells
};

UENUM(BlueprintType)
enum class EWeaponControlEffect : uint8
{
    None,
    Stagger,
    Restrain,
    ConductiveStun,
    Mark,
    AdhesiveSlow,
    AcousticDisorient,
    FlashDazzle
};

/** Physical firing behavior shared by player-held and autonomous mounts. */
USTRUCT(BlueprintType)
struct FWeaponFiringProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon", meta = (ClampMin = "0.0"))
    float MaxRangeCm = 75.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon", meta = (ClampMin = "0.0"))
    float TraceRadiusCm = 4.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon", meta = (ClampMin = "0.0"))
    float BiologicalDamage = 45.0f;

    /** Impulse imparted to the struck body, in Unreal's kg*cm/s convention. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Physics", meta = (ClampMin = "0.0"))
    float ImpactImpulse = 18000.0f;

    /** Equal-and-opposite impulse applied to an unbraced operator. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Physics", meta = (ClampMin = "0.0"))
    float RecoilImpulse = 2500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon", meta = (ClampMin = "0.0"))
    float CooldownSeconds = 0.65f;

    /**
     * Noise this shot makes, on the stealth system's abstract 0..1 scale (see
     * UNoisePerceptionSubsystem). Per-profile rather than per-weapon so a weapon's safe and unsafe
     * modes can differ: an unsafe extended bolt should carry further than a contained one.
     * Defaults high because discharging a weapon is the least subtle thing a player can do.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float FiringNoiseLoudness = 0.9f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Delivery")
    EWeaponDeliveryMode DeliveryMode = EWeaponDeliveryMode::Trace;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Delivery", meta = (ClampMin = "1.0", EditCondition = "DeliveryMode == EWeaponDeliveryMode::Projectile"))
    float ProjectileSpeedCmPerSecond = 4500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Delivery", meta = (ClampMin = "0.0", EditCondition = "DeliveryMode == EWeaponDeliveryMode::Projectile"))
    float ProjectileGravityScale = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Delivery", meta = (ClampMin = "1", ClampMax = "32"))
    int32 ProjectilesPerShot = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Delivery", meta = (ClampMin = "0.0", ClampMax = "45.0", Units = "Degrees"))
    float SpreadHalfAngleDegrees = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Shield", meta = (ClampMin = "0.0", Units = "Seconds", EditCondition = "DeliveryMode == EWeaponDeliveryMode::RescueShield"))
    float ShieldDurationSeconds = 0.0f;

    /** Local half-extents of the temporary projectile-blocking shield volume. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Shield", meta = (ClampMin = "0.0", EditCondition = "DeliveryMode == EWeaponDeliveryMode::RescueShield"))
    FVector ShieldHalfExtentsCm = FVector(6.0f, 42.0f, 68.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Control")
    EWeaponControlEffect ControlEffect = EWeaponControlEffect::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Control", meta = (ClampMin = "0.0", Units = "Seconds", EditCondition = "ControlEffect != EWeaponControlEffect::None"))
    float ControlDurationSeconds = 0.0f;

    /** Movement multiplier enforced while an active movement-affecting control payload is present. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Control", meta = (ClampMin = "0.0", ClampMax = "1.0", EditCondition = "ControlEffect != EWeaponControlEffect::None"))
    float ControlMovementMultiplier = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Environment")
    bool bCanDamageHull = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Environment", meta = (ClampMin = "0.0", ClampMax = "1.0", EditCondition = "bCanDamageHull"))
    float HullImpactSeverity = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Environment", meta = (ClampMin = "0.0", ClampMax = "1.0", EditCondition = "bCanDamageHull"))
    float BreachSeverity = 0.0f;
};

/** One permanent, ordered improvement installed after the base weapon configuration. */
USTRUCT(BlueprintType)
struct FWeaponUpgradeStage
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade")
    FName UpgradeId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade", meta = (MultiLine = true))
    FText Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade")
    FWeaponFiringProfile FiringProfile;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade")
    EWeaponUpgradeResource CostResource = EWeaponUpgradeResource::StructuralAlloy;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Upgrade", meta = (ClampMin = "0"))
    int32 ResourceCost = 0;
};

/** Traversal footprint used by hatches, ducts, squeeze volumes, and drone navigation. */
USTRUCT(BlueprintType)
struct FWeaponCollisionEnvelope
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal")
    EWeaponEnvelopeClass EnvelopeClass = EWeaponEnvelopeClass::Compact;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal", meta = (ClampMin = "0.0"))
    FVector HalfExtentsCm = FVector(35.0f, 12.0f, 12.0f);

    /** Offset from the weapon actor origin to the center of its oriented traversal box. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal")
    FVector CenterOffsetCm = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal")
    bool bCanFoldForTraversal = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon|Traversal", meta = (EditCondition = "bCanFoldForTraversal", ClampMin = "0.0"))
    FVector FoldedHalfExtentsCm = FVector(20.0f, 10.0f, 10.0f);

    FVector GetHalfExtents(bool bFolded) const
    {
        return bFolded && bCanFoldForTraversal ? FoldedHalfExtentsCm : HalfExtentsCm;
    }

    /** Tests an oriented weapon against a rectangular aperture whose travel axis is local X. */
    bool FitsPassageAperture(const FQuat& WeaponRotation, const FQuat& PassageRotation,
        float ClearWidthCm, float ClearHeightCm, bool bFolded) const
    {
        const FVector Extents = GetHalfExtents(bFolded);
        const FVector WeaponAxes[] = {
            WeaponRotation.GetAxisX(), WeaponRotation.GetAxisY(), WeaponRotation.GetAxisZ()
        };
        const FVector PassageRight = PassageRotation.GetAxisY();
        const FVector PassageUp = PassageRotation.GetAxisZ();

        float ProjectedHalfWidth = 0.0f;
        float ProjectedHalfHeight = 0.0f;
        for (int32 Axis = 0; Axis < 3; ++Axis)
        {
            ProjectedHalfWidth += FMath::Abs(FVector::DotProduct(PassageRight, WeaponAxes[Axis])) * Extents[Axis];
            ProjectedHalfHeight += FMath::Abs(FVector::DotProduct(PassageUp, WeaponAxes[Axis])) * Extents[Axis];
        }
        return ProjectedHalfWidth * 2.0f <= ClearWidthCm
            && ProjectedHalfHeight * 2.0f <= ClearHeightCm;
    }
};
