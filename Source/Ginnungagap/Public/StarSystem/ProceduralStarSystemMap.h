#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StarSystemTypes.h"
#include "ProceduralStarSystemMap.generated.h"

class UInstancedStaticMeshComponent;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UDirectionalLightComponent;
class UNiagaraComponent;
class UPCGComponent;
class AActor;

UENUM(BlueprintType)
enum class ESystemPhenomenon : uint8
{
    GoldenGiant,
    BlueWhiteStar,
    BinaryStars,
    VioletDwarf,
    IonNebula,
    GravityAnomaly,
    FracturedWorld
};

UENUM(BlueprintType)
enum class ESystemVisualQualityTier : uint8
{
    Low,
    Medium,
    High,
    Cinematic
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FSystemVisualSeedReadySignature, int32, SystemSeed,
    ESystemPhenomenon, Phenomenon);

/**
 * Runtime-built local operations volume around the ship.
 *
 * Despite the legacy class name, this actor is not an astronomical solar-system map. It realizes
 * one kilometer-scale encounter bubble selected from the AU-scale strategic system map.
 */
UCLASS(BlueprintType)
class GINNUNGAGAP_API AProceduralStarSystemMap : public AActor
{
    GENERATED_BODY()

public:
    AProceduralStarSystemMap();
    virtual void Tick(float DeltaTime) override;

    /** Legacy Unreal-unit radius used to place actors inside the local operations volume. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Local Operations|Scale", meta = (Units = "Centimeters"))
    float MapRadius = 3000000.0f;

    /** Full playable diameter. BuildSystem converts this to MapRadius in centimeters. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Local Operations|Scale", meta = (ClampMin = "1.0", ClampMax = "500.0", Units = "Kilometers"))
    float LocalOperationsDiameterKm = 60.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Star System|Generation", meta = (ClampMin = "3", ClampMax = "12"))
    int32 MinCelestialBodies = 4;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Star System|Generation", meta = (ClampMin = "3", ClampMax = "12"))
    int32 MaxCelestialBodies = 8;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Star System|Generation", meta = (ClampMin = "0", ClampMax = "1000"))
    int32 BaseDebrisCount = 180;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Motion", meta = (ClampMin = "0.0", ClampMax = "1000.0"))
    float AstronomicalTimeScale = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Motion")
    bool bAnimateCelestialBodies = true;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    FStarSystemData GeneratedSystem;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    TArray<FSystemPointOfInterest> PointsOfInterest;

    UPROPERTY(BlueprintReadOnly, Category = "Star System")
    ESystemPhenomenon DominantPhenomenon = ESystemPhenomenon::GoldenGiant;

    UPROPERTY(BlueprintReadOnly, Category = "Star System|Visuals")
    FLinearColor StellarLightColor = FLinearColor::White;

    UPROPERTY(BlueprintReadOnly, Category = "Star System|Visuals")
    float StellarLightIntensity = 4.0f;

    /** Prefer Celestial Vault, PCG, Niagara, and volume materials over the legacy skydome. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Unreal Native")
    bool bUseUnrealNativeVisualPipeline = true;

    /** Transitional escape hatch for old maps. New system maps should leave this disabled. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Unreal Native")
    bool bUseLegacyCosmicSky = false;

    /** Changes presentation density only; system identity and gameplay points remain unchanged. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Unreal Native")
    ESystemVisualQualityTier VisualQualityTier = ESystemVisualQualityTier::High;

    /** Clear radius around arrival and gameplay-critical points. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Unreal Native", meta = (Units = "Centimeters", ClampMin = "1000.0"))
    float VisualExclusionRadiusCm = 120000.0f;

    /** Optional exterior landmark meshes. Exactly zero or one is selected per generated system. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Fab Landmarks")
    TArray<TObjectPtr<UStaticMesh>> LandmarkMeshes;

    /** Optional exterior landmark actors, such as a self-contained portal Blueprint. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Fab Landmarks")
    TArray<TSubclassOf<AActor>> LandmarkActorClasses;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Fab Landmarks", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LandmarkSpawnChance = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Star System|Visuals|Fab Landmarks", meta = (Units = "Centimeters", ClampMin = "1000.0"))
    float LandmarkTargetDiameterCm = 30000.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Star System|Visuals|Fab Landmarks")
    FName SelectedLandmarkId = NAME_None;

    /** Blueprint visual directors bind here to trigger PCG generation and Niagara reseeding. */
    UPROPERTY(BlueprintAssignable, Category = "Star System|Visuals|Unreal Native")
    FSystemVisualSeedReadySignature OnSystemVisualSeedReady;

    UFUNCTION(BlueprintCallable, Category = "Star System")
    void BuildSystem(const FStarSystemData& SystemData, const FVector& ShipLocation);

    /** Stable seed exposed to PCG graphs, Niagara systems, and Blueprint visual directors. */
    UFUNCTION(BlueprintPure, Category = "Star System|Visuals|Unreal Native")
    int32 GetVisualGenerationSeed() const { return GenerationSeed; }

    /** Produces an independent deterministic seed for a named visual layer. */
    UFUNCTION(BlueprintPure, Category = "Star System|Visuals|Unreal Native")
    int32 GetVisualLayerSeed(FName LayerName) const;

    /** Reseeds and regenerates every assigned Unreal-native visual layer. */
    UFUNCTION(BlueprintCallable, Category = "Star System|Visuals|Unreal Native")
    void RefreshUnrealNativeVisuals();

    /** Runtime PCG attachment point for the reusable asteroid/debris graph. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Star System|Visuals|Unreal Native")
    TObjectPtr<UPCGComponent> AsteroidPCG;

    /** Niagara attachment point for radiation, charged dust, and stellar wind. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Star System|Visuals|Unreal Native")
    TObjectPtr<UNiagaraComponent> RadiationDustFX;

    /** Niagara attachment point for localized nebula wisps and volume particles. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Star System|Visuals|Unreal Native")
    TObjectPtr<UNiagaraComponent> NebulaFX;

    /** Samples a reproducible exterior gameplay point, well clear of the ship and central star. */
    FVector SampleGameplayLocation(int32 Salt) const;

    UFUNCTION(BlueprintPure, Category = "Star System")
    FVector GetHazardLocation(int32 HazardIndex) const;

    UFUNCTION(BlueprintPure, Category = "Star System")
    FVector GetResourceLocation(int32 ResourceIndex) const;

    UFUNCTION(BlueprintCallable, Category = "Star System")
    void OverrideResourceLocation(int32 ResourceIndex, const FVector& WorldLocation);

    UFUNCTION(BlueprintCallable, Category = "Procedural System|Gameplay")
    void DeactivateResourceContact(int32 ResourceIndex);

    UFUNCTION(BlueprintPure, Category = "Procedural System|Gameplay")
    int32 GetActiveResourceContactCount() const;

    UFUNCTION(BlueprintPure, Category = "Procedural System|Gameplay")
    int32 GetRecoveredResourceContactCount() const;

    UFUNCTION(BlueprintPure, Category = "Procedural System|Gameplay")
    bool IsResourceSweepComplete() const;

    UFUNCTION(BlueprintCallable, Category = "Star System")
    void TranslateSystem(const FVector& WorldOffset);

private:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> CelestialBodies;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> VolcanicPlanets;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> IcePlanets;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> GasGiants;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> Moons;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> Stars;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> CosmicSky;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> Phenomena;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> Atmospheres;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UDirectionalLightComponent> StellarLight;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> DebrisField;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> LargeDebrisFieldA;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> LargeDebrisFieldB;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> LandmarkMesh;

    UPROPERTY(Transient)
    TObjectPtr<AActor> SpawnedLandmarkActor;

    UPROPERTY()
    TObjectPtr<UStaticMesh> SphereMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> RockMesh;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInterface>> StarMaterials;

    UPROPERTY()
    TArray<TObjectPtr<UMaterialInterface>> PlanetMaterials;

    int32 GenerationSeed = 0;
    FVector SystemCenter = FVector::ZeroVector;

    TArray<FVector> HazardLocations;
    TArray<FVector> ResourceLocations;
    TSet<int32> StationaryResourceIndices;

    struct FRotatingInstance
    {
        TObjectPtr<UInstancedStaticMeshComponent> Component;
        int32 InstanceIndex = INDEX_NONE;
        FTransform BaseTransform;
        FVector RotationAxis = FVector::UpVector;
        float DegreesPerSecond = 0.0f;
        float AccumulatedDegrees = 0.0f;
        bool bOrbitLocation = false;
        FVector OrbitCenter = FVector::ZeroVector;
        int32 PointOfInterestIndex = INDEX_NONE;
    };

    TArray<FRotatingInstance> RotatingInstances;

    struct FDriftingInstance
    {
        TObjectPtr<UInstancedStaticMeshComponent> Component;
        int32 InstanceIndex = INDEX_NONE;
        FTransform BaseTransform;
        FVector Velocity = FVector::ZeroVector;
        FVector AccumulatedOffset = FVector::ZeroVector;
        int32 PointOfInterestIndex = INDEX_NONE;
    };

    TArray<FDriftingInstance> DriftingInstances;

    int32 AddDebrisInstance(const FTransform& Transform, int32 VariationKey);
};
