#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Ship/ShipSection.h"
#include "Ship/ModularShipRoom.h"
#include "Activities/ActivityPopulationTypes.h"
#include "ProceduralShipBuilder.generated.h"

class UStaticMesh;
class UMaterialInterface;
class USkeletalMesh;
class AActivityStation;
class ABulkheadDoor;

// Builds a medium, textured military corvette interior entirely in code.  The runtime-built
// level keeps the sample map source-control friendly while still providing a complete playable
// deck with bridge, CIC, engineering, cargo, medical, crew and escape spaces.
UCLASS()
class GINNUNGAGAP_API AProceduralShipBuilder : public AActor
{
    GENERATED_BODY()

public:
    AProceduralShipBuilder();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship")
    bool bSpawnOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship")
    float HubRadius = 2400.0f;

    UFUNCTION(BlueprintCallable, Category = "Procedural Ship")
    void BuildShip();

    /** Editable room recipes; populated with the corvette layout by default. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Modules")
    TArray<FShipRoomModuleDefinition> RoomModules;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Modules")
    TArray<FShipRoomConnectionDefinition> RoomConnections;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Procedural Ship|Modules")
    TArray<TObjectPtr<AModularShipRoom>> SpawnedRooms;

    /** Every horizontal graph edge is materialized as a navigable, damageable corridor section. */
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Procedural Ship|Modules")
    TArray<TObjectPtr<AShipSection>> SpawnedCorridors;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Modules", meta = (ClampMin = "220.0"))
    float CorridorWidth = 360.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Modules", meta = (ClampMin = "300.0"))
    float CorridorHeight = 600.0f;

    UFUNCTION(BlueprintPure, Category = "Procedural Ship|Modules")
    AModularShipRoom* FindBuiltRoom(FName RoomCode) const;

    UFUNCTION(BlueprintCallable, Category = "Procedural Ship|Modules")
    bool ValidateLayout(TArray<FString>& OutErrors) const;

    UFUNCTION(BlueprintPure, Category = "Procedural Ship|Modules")
    bool HasBuiltShip() const { return bHasBuiltShip; }

    /** Seeded, room-aware distribution of repair, scan, wiring and operations stations. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities")
    bool bPopulateActivityStations = true;

    /** Stable seed makes a generated ship reproducible for saves and network sessions. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities")
    int32 ActivityPopulationSeed = 731942;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float ActivitySpawnChance = 0.82f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities",
        meta = (ClampMin = "0", ClampMax = "6"))
    int32 MinActivitiesPerRoom = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities",
        meta = (ClampMin = "0", ClampMax = "8"))
    int32 MaxActivitiesPerRoom = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities",
        meta = (ClampMin = "100.0"))
    float MinimumActivitySpacing = 240.0f;

    /** Optional imported meshes from Activity_UI_Kit.blend; code-built proxies are used while null. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities|Art")
    TObjectPtr<UStaticMesh> BioscanStationMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Procedural Ship|Activities|Art")
    TObjectPtr<UStaticMesh> RewiringPanelMesh;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Procedural Ship|Activities")
    TArray<TObjectPtr<AActivityStation>> SpawnedActivityStations;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Procedural Ship|Activities")
    TArray<FProceduralActivitySpawnRecord> ActivityPopulationManifest;

    UFUNCTION(BlueprintCallable, Category = "Procedural Ship|Activities")
    void PopulateActivityStations();

    UFUNCTION(BlueprintPure, Category = "Procedural Ship|Activities")
    AActivityStation* FindActivityStationById(FName StationId) const;

    UFUNCTION(BlueprintPure, Category = "Procedural Ship|Activities")
    TArray<AActivityStation*> GetActivityStationsForRoom(FName RoomCode) const;

    UFUNCTION(BlueprintCallable, Category = "Procedural Ship|Activities")
    bool ValidateActivityPopulation(TArray<FString>& OutErrors) const;

    UFUNCTION(BlueprintPure, Category = "Procedural Ship|Activities")
    FString GetActivityPopulationSummary() const;

protected:
    virtual void BeginPlay() override;

private:
    AModularShipRoom* SpawnRoomModule(int32 SectionID, FName RoomCode, const FText& DisplayName,
        EShipRoomArchetype Archetype, EShipSectionType SectionType, const FVector& Location, const FVector& BoxExtent);
    void SpawnBoxRoom(AShipSection* Section);
    ABulkheadDoor* ConnectSections(AShipSection* A, AShipSection* B, const FVector& DoorLocation,
        const FRotator& DoorRotation, float TransferCoefficient = 1.0f);
    bool ConnectRoomModules(AModularShipRoom* A, EShipRoomSocket ASocket, AModularShipRoom* B,
        EShipRoomSocket BSocket, float TransferCoefficient);
    UStaticMeshComponent* AddBox(AActor* OwningActor, const FVector& RelativeLocation, const FVector& BoxSize,
        UMaterialInterface* Material, bool bCollision = true);
    UStaticMeshComponent* AddPrimitive(AActor* OwningActor, UStaticMesh* Mesh, const FVector& RelativeLocation,
        const FVector& Size, const FRotator& Rotation, UMaterialInterface* Material, bool bCollision = true);
    UStaticMeshComponent* AddAuthoredProp(AActor* OwningActor, const TCHAR* AssetPath,
        const FVector& RelativeLocation, const FRotator& Rotation = FRotator::ZeroRotator,
        const FVector& Scale = FVector::OneVector);
    void AddRoomDetails(AShipSection* Section, const FString& RoomName, const FLinearColor& AccentColor);
    void AddShipProps(AShipSection* Section, const FString& RoomName);
    void AddAuthoredCryoRoom(AModularShipRoom* CryoBay);
    void AddBloomCluster(AShipSection* Section, const FVector& RelativeLocation, const FRotator& Rotation, float Scale);
    void SpawnCrewCorpse(AShipSection* Section, const FVector& RelativeLocation, const FRotator& Rotation, bool bBloomCovered);
    AShipSection* AddCorridor(const FVector& Start, const FVector& End, int32 SectionID, FName CorridorCode);
    void PopulateRoomGameplayHardpoints(AModularShipRoom* Room);
    void PopulateCorridorGameplayHardpoints(AShipSection* Corridor, FName CorridorCode, float Length);
    TArray<TSubclassOf<AActivityStation>> GetActivityClassesForRoom(EShipRoomArchetype Archetype) const;
    bool FindActivitySpawnTransform(AModularShipRoom* Room, bool bWallMounted,
        EShipGameplayHardpointType RequestedType, FRandomStream& Random,
        const TArray<FVector>& OccupiedLocations, FTransform& OutTransform, FName& OutHardpointId) const;
    void ConfigureSpawnedActivity(AActivityStation* Station, AModularShipRoom* Room, FRandomStream& Random,
        int32 SlotIndex, EActivityStationMount MountType) const;
    float CalculateRoomBloomPressure(const AModularShipRoom* Room) const;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CylinderMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> SphereMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CryoRoomShellMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CryoRoomMachineryMesh;

    UPROPERTY()
    TObjectPtr<USkeletalMesh> CrewMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> HullMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> DeckMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> AccentMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> SpaceSuitMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> BloomMaterial;

    bool bHasBuiltShip = false;
};
