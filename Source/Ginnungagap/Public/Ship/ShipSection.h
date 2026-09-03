#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ShipSection.generated.h"

class UBoxComponent;
class UShipDamageComponent;

UENUM(BlueprintType)
enum class EShipSectionType : uint8
{
    Deck,
    Corridor,
    Airlock,
    CargoBay,
    EngineRoom,
    Bridge,
    CrewQuarters,
    MedBay
};

/** Stable placement intent consumed by encounter, infestation, activity and repair systems. */
UENUM(BlueprintType)
enum class EShipGameplayHardpointType : uint8
{
    Doorway,
    Body,
    Obstacle,
    BloomGrowth,
    Activity,
    DamageRepair
};

/**
 * Lightweight, serializable placement marker kept on a room or corridor section. Hardpoints avoid
 * paying for hundreds of TargetPoint actors on ship-scale interiors while still giving gameplay
 * systems stable IDs, transforms and clearance requirements.
 */
USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipGameplayHardpoint
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint")
    FName HardpointId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint")
    EShipGameplayHardpointType HardpointType = EShipGameplayHardpointType::Activity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint")
    FVector RelativeLocation = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint")
    FRotator RelativeRotation = FRotator::ZeroRotator;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint", meta = (ClampMin = "0.0"))
    float ClearanceRadius = 100.0f;

    /** Socket, mount, wall, floor or narrative-purpose hint. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Hardpoint")
    FName ContextTag = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Ship Hardpoint")
    bool bReserved = false;

    bool IsValid(FString* OutError = nullptr) const;
};

USTRUCT(BlueprintType)
struct FSectionConnection
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Section Connection")
    TObjectPtr<class AShipSection> Target = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Section Connection")
    TObjectPtr<class ABulkheadDoor> Door = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Section Connection")
    float TransferCoefficient = 1.0f;
};

UCLASS()
class GINNUNGAGAP_API AShipSection : public AActor
{
    GENERATED_BODY()

public:
    AShipSection();

    virtual void BeginPlay() override;
    virtual void EndPlay(EEndPlayReason::Type EndPlayReason) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ship Section")
    TObjectPtr<UBoxComponent> SectionBounds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Ship Section")
    TObjectPtr<UShipDamageComponent> DamageState;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship Section")
    int32 SectionID = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship Section")
    EShipSectionType SectionType = EShipSectionType::Corridor;

    /** Aggregate art/lighting volumes can opt out when smaller fitted rooms own navigation. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Section")
    bool bRegisterWithNavigation = true;

    UPROPERTY(BlueprintReadOnly, Category = "Ship Section")
    float Contamination = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship Section")
    float DiffusionRate = 0.1f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Ship Section")
    float NaturalDecayRate = 0.01f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Section")
    TArray<FSectionConnection> Connections;

    /** Stable placement slots for bodies, blockers, Bloom, activities and damage-control work. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship Section|Gameplay Hardpoints")
    TArray<FShipGameplayHardpoint> GameplayHardpoints;

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    void AddContamination(float Amount);

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    bool IsContaminated(float Threshold = 0.01f) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    bool ContainsPoint(const FVector& Point) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    bool IsConnectedTo(const AShipSection* Other) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    float GetTransferRateTo(const AShipSection* Other) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section")
    bool IsTraversableTo(const AShipSection* Other, bool bRespectSealedDoors = true) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section|Gameplay Hardpoints")
    bool AddGameplayHardpoint(const FShipGameplayHardpoint& Hardpoint);

    UFUNCTION(BlueprintPure, Category = "Ship Section|Gameplay Hardpoints")
    TArray<FShipGameplayHardpoint> GetGameplayHardpoints(EShipGameplayHardpointType HardpointType,
        bool bOnlyAvailable = true) const;

    UFUNCTION(BlueprintPure, Category = "Ship Section|Gameplay Hardpoints")
    bool GetGameplayHardpointWorldTransform(FName HardpointId, FTransform& OutTransform) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Section|Gameplay Hardpoints")
    bool SetGameplayHardpointReserved(FName HardpointId, bool bReserved);
};
