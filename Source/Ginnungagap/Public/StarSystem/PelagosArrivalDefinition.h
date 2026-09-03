#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "PelagosArrivalDefinition.generated.h"

UENUM(BlueprintType)
enum class EPelagosArrivalState : uint8
{
    Inactive,
    JumpExit,
    SensorAcquisition,
    IFFChallenge,
    ControlHandoff,
    TrafficContact,
    DockRequest,
    DockAssignment,
    FinalApproach,
    SoftCapture,
    HardDock,
    ServicesAvailable,
    ArrivalComplete,
    Departure
};

UENUM(BlueprintType)
enum class EPelagosDockState : uint8
{
    Available,
    Reserved,
    Occupied,
    Faulted,
    EmergencyOnly
};

UENUM(BlueprintType)
enum class EPelagosHazardType : uint8
{
    SolarShear,
    IonWake,
    DebrisField,
    NoBurnZone,
    EmergencyClearLane
};

UENUM(BlueprintType)
enum class EPelagosServiceType : uint8
{
    Fuel,
    Repair,
    Medical,
    Cargo,
    Customs,
    Crew,
    Upgrade,
    Market,
    Navigation,
    Salvage
};

USTRUCT(BlueprintType)
struct FPelagosDockDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    FName DockId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    FTransform DockTransform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    FTransform ApproachTransform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    float CaptureRadius = 2200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    bool bSupportsLargeShips = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Dock")
    bool bEmergencyDock = false;
};

USTRUCT(BlueprintType)
struct FPelagosArrivalRouteDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Route")
    FName RouteId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Route")
    TArray<FVector> ControlPoints;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Route", meta=(ClampMin="1.0"))
    float SpeedLimit = 220.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Route")
    float ClearanceRadius = 1800.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Route")
    bool bPlayerRoute = false;
};

USTRUCT(BlueprintType)
struct FPelagosTrafficSpawnDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic")
    FName SpawnId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic")
    FName RouteId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic")
    FTransform SpawnTransform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic", meta=(ClampMin="1"))
    int32 LocalCapacity = 2;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic", meta=(ClampMin="0.0"))
    float MinimumRespawnDelay = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic")
    bool bAllowsLargeShips = false;
};

USTRUCT(BlueprintType)
struct FPelagosHazardDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard")
    FName HazardId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard")
    EPelagosHazardType HazardType = EPelagosHazardType::DebrisField;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard")
    FTransform Transform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard")
    FVector Extent = FVector(5000.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard", meta=(ClampMin="0.0", ClampMax="1.0"))
    float Severity = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazard", meta=(ClampMin="0.0"))
    float DamagePerSecond = 0.0f;
};

USTRUCT(BlueprintType)
struct FPelagosServiceDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Service")
    FName ServiceId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Service")
    EPelagosServiceType ServiceType = EPelagosServiceType::Repair;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Service")
    FTransform InteractionTransform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Service", meta=(ClampMin="0.0"))
    float InteractionRadius = 1500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Service")
    bool bRequiresHardDock = true;
};

UCLASS(BlueprintType)
class GINNUNGAGAP_API UPelagosArrivalDefinition : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Identity")
    FName DestinationId = TEXT("Pelagos");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Identity")
    FText DisplayName = NSLOCTEXT("Pelagos", "OrbitalArrivalName", "Pelagos Orbital Arrival");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Arrival")
    FTransform PlayerArrivalTransform;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Arrival")
    TArray<FPelagosArrivalRouteDefinition> Routes;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Docking")
    TArray<FPelagosDockDefinition> Docks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic")
    TArray<FPelagosTrafficSpawnDefinition> TrafficSpawns;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Hazards")
    TArray<FPelagosHazardDefinition> Hazards;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Services")
    TArray<FPelagosServiceDefinition> Services;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic", meta=(ClampMin="0"))
    int32 MaxActiveTraffic = 24;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Traffic", meta=(ClampMin="0"))
    int32 MaxTrafficNearDocks = 5;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Missions", meta=(ClampMin="0"))
    int32 MaxConcurrentMissions = 8;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Arrival")
    bool bAutoStartOnJumpArrival = true;
};
