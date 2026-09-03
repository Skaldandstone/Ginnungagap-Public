#pragma once

#include "CoreMinimal.h"
#include "../AstrophysicsHazardComponent.h"
#include "../Bloom/BloomDirector.h"
#include "StarSystemTypes.generated.h"

UENUM(BlueprintType)
enum class EHazardCategory : uint8
{
    BlackHole,
    ExcessiveGravityWell,
    SolarRadiationStorm,
    CosmicRadiationBelt,
    MicroDebrisField,
    ThermalExtreme,
    MicrogravityShear
};

UENUM(BlueprintType)
enum class EStarSystemResourceType : uint8
{
    NavigationFuel,
    StructuralAlloy,
    CryoCoolant,
    LifeSupportFilters,
    SensorComponents,
    PowerCells
};

UENUM(BlueprintType)
enum class EResourceAcquisitionMethod : uint8
{
    ShipSystemReactivation,
    EVARetrieval,
    DroneDispatch
};

UENUM(BlueprintType)
enum class ESystemPointOfInterestType : uint8
{
    Unknown,
    Arrival,
    CelestialBody,
    Phenomenon,
    Hazard,
    Resource
};

/** Astronomical placement used by the strategic system map. Values are never Unreal world units. */
USTRUCT(BlueprintType)
struct FSystemMapCoordinate
{
    GENERATED_BODY()

    /** Semi-major axis or representative distance from the primary star. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System Map", meta = (ClampMin = "0.0"))
    double OrbitalRadiusAU = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System Map", meta = (ClampMin = "0.0", ClampMax = "360.0", Units = "Degrees"))
    double TrueAnomalyDegrees = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System Map", meta = (ClampMin = "-90.0", ClampMax = "90.0", Units = "Degrees"))
    double InclinationDegrees = 0.0;
};

/** A streamed kilometer-scale gameplay bubble anchored to an astronomical system-map location. */
USTRUCT(BlueprintType)
struct FLocalOperationsVolumeDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations")
    FName VolumeID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations")
    FSystemMapCoordinate SystemAnchor;

    /** Playable diameter, not radius. The existing generated exterior is 60 km across. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations", meta = (ClampMin = "1.0", Units = "Kilometers"))
    double DiameterKm = 60.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations")
    FName LevelAsset;
};

USTRUCT(BlueprintType)
struct FSystemPointOfInterest
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    FName Name;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    ESystemPointOfInterestType Type = ESystemPointOfInterestType::Unknown;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    FVector WorldLocation = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    float SensorSignature = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    bool bCriticalResource = false;

    /** Strategic-map coordinate. Do not derive this from WorldLocation. */
    UPROPERTY(BlueprintReadOnly, Category = "System Map")
    FSystemMapCoordinate SystemMapCoordinate;

    /** Optional streamed gameplay bubble entered when this POI is selected. */
    UPROPERTY(BlueprintReadOnly, Category = "Local Operations")
    FName LocalOperationsVolumeID;
};

USTRUCT(BlueprintType)
struct FHazardEntry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hazard")
    EHazardCategory Category = EHazardCategory::MicroDebrisField;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hazard")
    float Severity = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hazard")
    FPhysicsEnvironmentState EnvironmentPreset;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Hazard")
    EBloomHazardType MappedBloomHazardType = EBloomHazardType::Radiation;
};

USTRUCT(BlueprintType)
struct FResourceEntry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource")
    EStarSystemResourceType ResourceType = EStarSystemResourceType::NavigationFuel;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource")
    int32 Quantity = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource")
    TArray<EResourceAcquisitionMethod> AvailableMethods;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Resource")
    bool bCriticallyNeeded = false;
};

USTRUCT(BlueprintType)
struct FStarSystemData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System")
    FGuid SystemID;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System")
    FString DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System")
    int32 DangerTier = 1;

    /** Strategic display extent measured from the primary star. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System Map", meta = (ClampMin = "1.0"))
    double SystemMapExtentAU = 30.0;

    /** Streamable kilometer-scale locations available inside this astronomical system. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Local Operations")
    TArray<FLocalOperationsVolumeDefinition> LocalOperationsVolumes;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System")
    TArray<FHazardEntry> Hazards;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System")
    TArray<FResourceEntry> Resources;
};

USTRUCT(BlueprintType)
struct FJumpCandidate
{
    GENERATED_BODY()

    // What the player sees on the jump console - may be redacted or falsified.
    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    FStarSystemData DisplayedData;

    // Ground truth applied on arrival. Deliberately NOT BlueprintReadOnly/ReadWrite so no
    // widget can bind to it and leak the outcome before the jump completes.
    UPROPERTY()
    FStarSystemData ActualData;

    UPROPERTY(BlueprintReadOnly, Category = "Jump")
    bool bIsFalsified = false;
};
