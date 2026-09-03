#include "ProceduralStarSystemMap.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Components/DirectionalLightComponent.h"
#include "NiagaraComponent.h"
#include "PCGComponent.h"
#include "UObject/ConstructorHelpers.h"

AProceduralStarSystemMap::AProceduralStarSystemMap()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.05f;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SystemRoot"));
    SetRootComponent(SceneRoot);

    CelestialBodies = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("CelestialBodies"));
    CelestialBodies->SetupAttachment(SceneRoot);
    CelestialBodies->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    VolcanicPlanets = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("VolcanicPlanets"));
    VolcanicPlanets->SetupAttachment(SceneRoot);
    VolcanicPlanets->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    IcePlanets = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("IcePlanets"));
    IcePlanets->SetupAttachment(SceneRoot);
    IcePlanets->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    GasGiants = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("GasGiants"));
    GasGiants->SetupAttachment(SceneRoot);
    GasGiants->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    Moons = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Moons"));
    Moons->SetupAttachment(SceneRoot);
    Moons->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    Stars = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Stars"));
    Stars->SetupAttachment(SceneRoot);
    Stars->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    CosmicSky = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CosmicSky"));
    CosmicSky->SetupAttachment(SceneRoot);
    CosmicSky->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CosmicSky->SetCastShadow(false);

    Phenomena = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Phenomena"));
    Phenomena->SetupAttachment(SceneRoot);
    Phenomena->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    Atmospheres = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Atmospheres"));
    Atmospheres->SetupAttachment(SceneRoot);
    Atmospheres->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Atmospheres->SetCastShadow(false);

    StellarLight = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("StellarLight"));
    StellarLight->SetupAttachment(SceneRoot);
    StellarLight->SetCastShadows(false);

    DebrisField = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("DebrisField"));
    DebrisField->SetupAttachment(SceneRoot);
    DebrisField->SetCollisionEnabled(ECollisionEnabled::QueryOnly);

    LargeDebrisFieldA = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LargeDebrisFieldA"));
    LargeDebrisFieldA->SetupAttachment(SceneRoot);
    LargeDebrisFieldA->SetCollisionEnabled(ECollisionEnabled::QueryOnly);

    LargeDebrisFieldB = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("LargeDebrisFieldB"));
    LargeDebrisFieldB->SetupAttachment(SceneRoot);
    LargeDebrisFieldB->SetCollisionEnabled(ECollisionEnabled::QueryOnly);

    LandmarkMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("OptionalSystemLandmark"));
    LandmarkMesh->SetupAttachment(SceneRoot);
    LandmarkMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    LandmarkMesh->SetVisibility(false, true);

    AsteroidPCG = CreateDefaultSubobject<UPCGComponent>(TEXT("AsteroidPCG"));
    AsteroidPCG->GenerationTrigger = EPCGComponentGenerationTrigger::GenerateOnDemand;
    AsteroidPCG->bActivated = true;

    RadiationDustFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("RadiationDustFX"));
    RadiationDustFX->SetupAttachment(SceneRoot);
    RadiationDustFX->SetAutoActivate(false);

    NebulaFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("NebulaFX"));
    NebulaFX->SetupAttachment(SceneRoot);
    NebulaFX->SetAutoActivate(false);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Celestial_Planet.SM_Celestial_Planet"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> MoonFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Celestial_Moon.SM_Celestial_Moon"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> StarFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Celestial_Star.SM_Celestial_Star"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> RockFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Debris.SM_Asteroid_Debris"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> LargeRockAFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Large_A.SM_Asteroid_Large_A"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> LargeRockBFinder(TEXT("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Large_B.SM_Asteroid_Large_B"));
    SphereMesh = SphereFinder.Object;
    RockMesh = RockFinder.Object;
    CelestialBodies->SetStaticMesh(SphereMesh);
    VolcanicPlanets->SetStaticMesh(SphereMesh);
    IcePlanets->SetStaticMesh(SphereMesh);
    GasGiants->SetStaticMesh(SphereMesh);
    Moons->SetStaticMesh(MoonFinder.Succeeded() ? MoonFinder.Object : SphereMesh);
    Stars->SetStaticMesh(StarFinder.Succeeded() ? StarFinder.Object : SphereMesh);
    CosmicSky->SetStaticMesh(SphereMesh);
    Phenomena->SetStaticMesh(SphereMesh);
    Atmospheres->SetStaticMesh(SphereMesh);
    CosmicSky->SetRelativeScale3D(FVector(90000.0f));
    CosmicSky->SetVisibility(false, true);
    DebrisField->SetStaticMesh(RockMesh);
    LargeDebrisFieldA->SetStaticMesh(LargeRockAFinder.Succeeded() ? LargeRockAFinder.Object : RockMesh);
    LargeDebrisFieldB->SetStaticMesh(LargeRockBFinder.Succeeded() ? LargeRockBFinder.Object : RockMesh);

    auto LoadMaterial = [](const TCHAR* Path) { return LoadObject<UMaterialInterface>(nullptr, Path); };
    StarMaterials = {
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Star_Gold.M_Star_Gold")),
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Star_Blue.M_Star_Blue")),
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Star_Violet.M_Star_Violet"))};
    PlanetMaterials = {
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Planet_Ocean.M_Planet_Ocean")),
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Planet_Volcanic.M_Planet_Volcanic")),
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Planet_Ice.M_Planet_Ice")),
        LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Planet_GasGiant.M_Planet_GasGiant"))};
    if (PlanetMaterials.Num() == 4)
    {
        CelestialBodies->SetMaterial(0, PlanetMaterials[0]);
        VolcanicPlanets->SetMaterial(0, PlanetMaterials[1]);
        IcePlanets->SetMaterial(0, PlanetMaterials[2]);
        GasGiants->SetMaterial(0, PlanetMaterials[3]);
        Moons->SetMaterial(0, PlanetMaterials[2]);
    }
    CosmicSky->SetMaterial(0, LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_SpaceSky_CosmicRift.M_SpaceSky_CosmicRift")));
    Phenomena->SetMaterial(0, LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Phenomenon_Anomaly.M_Phenomenon_Anomaly")));
    Atmospheres->SetMaterial(0, LoadMaterial(TEXT("/Game/Assets/SpaceSystems/Materials/M_Atmosphere_Additive.M_Atmosphere_Additive")));
    Tags.Add(TEXT("GeneratedStarSystemMap"));
    Tags.Add(TEXT("GeneratedSystemContent"));
}

int32 AProceduralStarSystemMap::AddDebrisInstance(const FTransform& Transform, int32 VariationKey)
{
    UInstancedStaticMeshComponent* Target = DebrisField;
    switch (FMath::Abs(VariationKey) % 7)
    {
    case 0:
        Target = LargeDebrisFieldA;
        break;
    case 1:
        Target = LargeDebrisFieldB;
        break;
    default:
        break;
    }
    return Target->AddInstance(Transform);
}

void AProceduralStarSystemMap::TranslateSystem(const FVector& WorldOffset)
{
    AddActorWorldOffset(WorldOffset, false);
    SystemCenter += WorldOffset;
    int32 ResourcePointIndex = 0;
    for (FSystemPointOfInterest& Point : PointsOfInterest)
    {
        const bool bStationaryResource = Point.Type == ESystemPointOfInterestType::Resource && StationaryResourceIndices.Contains(ResourcePointIndex);
        if (!bStationaryResource)
        {
            Point.WorldLocation += WorldOffset;
        }
        if (Point.Type == ESystemPointOfInterestType::Resource)
        {
            ++ResourcePointIndex;
        }
    }
    for (FVector& Location : HazardLocations)
    {
        Location += WorldOffset;
    }
    for (int32 Index = 0; Index < ResourceLocations.Num(); ++Index)
    {
        if (!StationaryResourceIndices.Contains(Index))
        {
            ResourceLocations[Index] += WorldOffset;
        }
    }
}

void AProceduralStarSystemMap::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (!bAnimateCelestialBodies || AstronomicalTimeScale <= 0.0f)
    {
        return;
    }

    for (FRotatingInstance& Body : RotatingInstances)
    {
        if (!Body.Component || Body.InstanceIndex == INDEX_NONE)
        {
            continue;
        }
        Body.AccumulatedDegrees = FMath::Fmod(Body.AccumulatedDegrees + Body.DegreesPerSecond * AstronomicalTimeScale * DeltaTime, 360.0f);
        FTransform AnimatedTransform = Body.BaseTransform;
        const FQuat MotionRotation(Body.RotationAxis.GetSafeNormal(), FMath::DegreesToRadians(Body.AccumulatedDegrees));
        AnimatedTransform.SetRotation(MotionRotation * Body.BaseTransform.GetRotation());
        if (Body.bOrbitLocation)
        {
            const FVector OrbitalOffset = Body.BaseTransform.GetLocation() - Body.OrbitCenter;
            const FVector AnimatedLocation = Body.OrbitCenter + MotionRotation.RotateVector(OrbitalOffset);
            AnimatedTransform.SetLocation(AnimatedLocation);
            if (PointsOfInterest.IsValidIndex(Body.PointOfInterestIndex))
            {
                PointsOfInterest[Body.PointOfInterestIndex].WorldLocation = SystemCenter + AnimatedLocation;
            }
        }
        Body.Component->UpdateInstanceTransform(Body.InstanceIndex, AnimatedTransform, false, true, true);
    }
    for (FDriftingInstance& Body : DriftingInstances)
    {
        if (!Body.Component || Body.InstanceIndex == INDEX_NONE)
        {
            continue;
        }
        Body.AccumulatedOffset += Body.Velocity * AstronomicalTimeScale * DeltaTime;
        FTransform AnimatedTransform = Body.BaseTransform;
        AnimatedTransform.AddToTranslation(Body.AccumulatedOffset);
        Body.Component->UpdateInstanceTransform(Body.InstanceIndex, AnimatedTransform, false, true, true);
        if (PointsOfInterest.IsValidIndex(Body.PointOfInterestIndex))
        {
            PointsOfInterest[Body.PointOfInterestIndex].WorldLocation = SystemCenter + AnimatedTransform.GetLocation();
        }
    }
}

void AProceduralStarSystemMap::BuildSystem(const FStarSystemData& SystemData, const FVector& ShipLocation)
{
    // One Unreal unit is one centimeter. This actor represents only the selected local encounter
    // bubble; astronomical AU coordinates remain in FStarSystemData and are never converted into
    // world-space actor positions.
    MapRadius = LocalOperationsDiameterKm * 100000.0f * 0.5f;
    GeneratedSystem = SystemData;
    SystemCenter = ShipLocation;
    SetActorLocation(SystemCenter);
    CelestialBodies->ClearInstances();
    VolcanicPlanets->ClearInstances();
    IcePlanets->ClearInstances();
    GasGiants->ClearInstances();
    Moons->ClearInstances();
    Stars->ClearInstances();
    Phenomena->ClearInstances();
    Atmospheres->ClearInstances();
    DebrisField->ClearInstances();
    LargeDebrisFieldA->ClearInstances();
    LargeDebrisFieldB->ClearInstances();
    PointsOfInterest.Reset();
    HazardLocations.Reset();
    ResourceLocations.Reset();
    StationaryResourceIndices.Reset();
    RotatingInstances.Reset();
    DriftingInstances.Reset();
    SelectedLandmarkId = NAME_None;
    LandmarkMesh->SetVisibility(false, true);
    LandmarkMesh->SetStaticMesh(nullptr);
    if (SpawnedLandmarkActor)
    {
        SpawnedLandmarkActor->Destroy();
        SpawnedLandmarkActor = nullptr;
    }

    GenerationSeed = HashCombine(GetTypeHash(SystemData.SystemID), GetTypeHash(SystemData.DisplayName));
    CosmicSky->SetVisibility(!bUseUnrealNativeVisualPipeline || bUseLegacyCosmicSky, true);
    FRandomStream Random(GenerationSeed);
    // The strongest real hazard drives the system silhouette, so the vista foreshadows mechanics.
    DominantPhenomenon = static_cast<ESystemPhenomenon>(static_cast<uint32>(GenerationSeed) % 7);
    float StrongestSeverity = -1.0f;
    for (const FHazardEntry& Hazard : SystemData.Hazards)
    {
        if (Hazard.Severity <= StrongestSeverity)
        {
            continue;
        }
        StrongestSeverity = Hazard.Severity;
        switch (Hazard.Category)
        {
        case EHazardCategory::BlackHole:
        case EHazardCategory::ExcessiveGravityWell:
        case EHazardCategory::MicrogravityShear:
            DominantPhenomenon = ESystemPhenomenon::GravityAnomaly;
            break;
        case EHazardCategory::SolarRadiationStorm:
            DominantPhenomenon = ESystemPhenomenon::BlueWhiteStar;
            break;
        case EHazardCategory::CosmicRadiationBelt:
            DominantPhenomenon = ESystemPhenomenon::IonNebula;
            break;
        case EHazardCategory::MicroDebrisField:
            DominantPhenomenon = ESystemPhenomenon::FracturedWorld;
            break;
        case EHazardCategory::ThermalExtreme:
            DominantPhenomenon = ESystemPhenomenon::GoldenGiant;
            break;
        }
    }
    auto RandomRotation = [&Random]()
    {
        return FRotator(Random.FRandRange(-180.0f, 180.0f), Random.FRandRange(-180.0f, 180.0f), Random.FRandRange(-180.0f, 180.0f));
    };

    // The primary sits far enough away to read as a backdrop while leaving the arrival area playable.
    const FVector StarDirection = Random.VRand();
    const FVector StarLocation = StarDirection * MapRadius * 0.82f;
    FVector PhenomenonAnchor = StarLocation;
    const float StarScale = Random.FRandRange(220.0f, 520.0f);
    const int32 StarMaterialIndex = DominantPhenomenon == ESystemPhenomenon::BlueWhiteStar ? 1
        : (DominantPhenomenon == ESystemPhenomenon::VioletDwarf || DominantPhenomenon == ESystemPhenomenon::GravityAnomaly ? 2 : 0);
    if (StarMaterials.IsValidIndex(StarMaterialIndex) && StarMaterials[StarMaterialIndex])
    {
        Stars->SetMaterial(0, StarMaterials[StarMaterialIndex]);
    }
    Stars->AddInstance(FTransform(FRotator::ZeroRotator, StarLocation, FVector(StarScale)));
    StellarLightColor = StarMaterialIndex == 1 ? FLinearColor(0.32f, 0.55f, 1.0f)
        : (StarMaterialIndex == 2 ? FLinearColor(0.55f, 0.18f, 1.0f) : FLinearColor(1.0f, 0.48f, 0.16f));
    StellarLightIntensity = DominantPhenomenon == ESystemPhenomenon::BinaryStars ? 8.0f : 4.5f;
    StellarLight->SetLightColor(StellarLightColor);
    StellarLight->SetIntensity(StellarLightIntensity);
    StellarLight->SetRelativeRotation((-StarLocation).Rotation());
    // Nested shells give the primary a corona with depth instead of a single hard emissive edge.
    Atmospheres->AddInstance(FTransform(FRotator::ZeroRotator, StarLocation, FVector(StarScale * 1.025f)));
    Atmospheres->AddInstance(FTransform(FRotator::ZeroRotator, StarLocation, FVector(StarScale * 1.075f)));
    Atmospheres->AddInstance(FTransform(FRotator::ZeroRotator, StarLocation, FVector(StarScale * 1.16f)));
    if (DominantPhenomenon == ESystemPhenomenon::BinaryStars)
    {
        const FVector CompanionLocation = StarLocation + FVector(StarScale * 90.0f, 0.0f, StarScale * 20.0f);
        const float CompanionScale = StarScale * 0.62f;
        Stars->AddInstance(FTransform(FRotator::ZeroRotator, CompanionLocation, FVector(CompanionScale)));
        Atmospheres->AddInstance(FTransform(FRotator::ZeroRotator, CompanionLocation, FVector(CompanionScale * 1.08f)));
    }

    FSystemPointOfInterest ArrivalPoint;
    ArrivalPoint.Name = TEXT("Jump Arrival");
    ArrivalPoint.Type = ESystemPointOfInterestType::Arrival;
    ArrivalPoint.WorldLocation = SystemCenter;
    ArrivalPoint.SensorSignature = 1.0f;
    PointsOfInterest.Add(ArrivalPoint);

    auto AddPhenomenonPoint = [this](const TCHAR* Name, const FVector& LocalLocation, float Signature)
    {
        FSystemPointOfInterest Point;
        Point.Name = FName(Name);
        Point.Type = ESystemPointOfInterestType::Phenomenon;
        Point.WorldLocation = SystemCenter + LocalLocation;
        Point.SensorSignature = Signature;
        PointsOfInterest.Add(Point);
    };

    if (DominantPhenomenon == ESystemPhenomenon::IonNebula)
    {
        const FVector NebulaCenter = Random.VRand() * MapRadius * 0.36f;
        PhenomenonAnchor = NebulaCenter;
        for (int32 CloudIndex = 0; CloudIndex < 7; ++CloudIndex)
        {
            const FVector CloudLocation = NebulaCenter + Random.VRand() * Random.FRandRange(50000.0f, 280000.0f);
            const FVector CloudScale(Random.FRandRange(700.0f, 1800.0f), Random.FRandRange(400.0f, 1200.0f), Random.FRandRange(500.0f, 1500.0f));
            const FTransform CloudTransform(RandomRotation(), CloudLocation, CloudScale);
            const int32 CloudInstance = Phenomena->AddInstance(CloudTransform);
            FRotatingInstance& Motion = RotatingInstances.AddDefaulted_GetRef();
            Motion.Component = Phenomena;
            Motion.InstanceIndex = CloudInstance;
            Motion.BaseTransform = CloudTransform;
            Motion.RotationAxis = Random.VRand();
            Motion.DegreesPerSecond = Random.FRandRange(0.002f, 0.012f);
        }
        AddPhenomenonPoint(TEXT("Ionized Nebula Core"), NebulaCenter, 0.92f);
    }
    else if (DominantPhenomenon == ESystemPhenomenon::GravityAnomaly)
    {
        const FVector AnomalyCenter = -StarDirection * MapRadius * 0.42f;
        PhenomenonAnchor = AnomalyCenter;
        Phenomena->AddInstance(FTransform(FRotator::ZeroRotator, AnomalyCenter, FVector(620.0f)));
        Phenomena->AddInstance(FTransform(FRotator::ZeroRotator, AnomalyCenter, FVector(880.0f, 880.0f, 70.0f)));
        AddPhenomenonPoint(TEXT("Gravitational Lens"), AnomalyCenter, 1.0f);
    }

    const int32 BodyCount = Random.RandRange(MinCelestialBodies, MaxCelestialBodies);
    TArray<FVector> BodyLocations;
    for (int32 Index = 0; Index < BodyCount; ++Index)
    {
        const float OrbitRadius = FMath::Lerp(MapRadius * 0.18f, MapRadius * 0.72f, (Index + 1.0f) / (BodyCount + 1.0f));
        const float Angle = Random.FRandRange(0.0f, 2.0f * PI);
        const float Inclination = Random.FRandRange(-0.16f, 0.16f);
        const FVector Position(FMath::Cos(Angle) * OrbitRadius, FMath::Sin(Angle) * OrbitRadius, OrbitRadius * Inclination);
        int32 PlanetFamily = static_cast<int32>((static_cast<uint32>(GenerationSeed) + Index) % 4);
        if (DominantPhenomenon == ESystemPhenomenon::FracturedWorld && Index == 0)
        {
            PlanetFamily = 1;
        }
        const float BodyScale = PlanetFamily == 3 ? Random.FRandRange(62.0f, 125.0f) : Random.FRandRange(18.0f, 85.0f);
        const float PolarScale = PlanetFamily == 3
            ? Random.FRandRange(0.86f, 0.94f)
            : Random.FRandRange(0.965f, 1.015f);
        BodyLocations.Add(Position);
        UInstancedStaticMeshComponent* PlanetComponent = PlanetFamily == 1 ? VolcanicPlanets
            : (PlanetFamily == 2 ? IcePlanets : (PlanetFamily == 3 ? GasGiants : CelestialBodies));
        const FTransform PlanetTransform(RandomRotation(), Position, FVector(BodyScale, BodyScale, BodyScale * PolarScale));
        const int32 PlanetInstance = PlanetComponent->AddInstance(PlanetTransform);
        FRotatingInstance& Motion = RotatingInstances.AddDefaulted_GetRef();
        Motion.Component = PlanetComponent;
        Motion.InstanceIndex = PlanetInstance;
        Motion.BaseTransform = PlanetTransform;
        Motion.RotationAxis = FVector(Random.FRandRange(-0.22f, 0.22f), Random.FRandRange(-0.22f, 0.22f), 1.0f).GetSafeNormal();
        Motion.DegreesPerSecond = PlanetFamily == 3 ? Random.FRandRange(0.015f, 0.035f) : Random.FRandRange(0.035f, 0.09f);
        // Most volcanic bodies are airless; rare retained atmospheres remain a seeded exception.
        const bool bHasAtmosphere = PlanetFamily != 1 || Random.FRand() < 0.22f;
        if (bHasAtmosphere)
        {
            const float AtmosphereScale = BodyScale * Random.FRandRange(1.025f, PlanetFamily == 3 ? 1.045f : 1.075f);
            Atmospheres->AddInstance(FTransform(FRotator::ZeroRotator, Position,
                FVector(AtmosphereScale, AtmosphereScale, AtmosphereScale * PolarScale)));
        }

        // Compact moon groups give the player parallax and readable scale when approaching a planet.
        const int32 MoonCount = PlanetFamily == 3
            ? Random.RandRange(1, 3)
            : (((Index + GenerationSeed) & 1) == 0 ? Random.RandRange(0, 2) : 0);
        const FVector MoonPlaneNormal = Random.VRand();
        const FVector MoonPlaneX = FVector::CrossProduct(MoonPlaneNormal, FVector::UpVector).GetSafeNormal(
            UE_SMALL_NUMBER, FVector::ForwardVector);
        const FVector MoonPlaneY = FVector::CrossProduct(MoonPlaneNormal, MoonPlaneX).GetSafeNormal();
        for (int32 MoonIndex = 0; MoonIndex < MoonCount; ++MoonIndex)
        {
            const float MoonAngle = Random.FRandRange(0.0f, 2.0f * PI);
            const float MoonOrbitRadius = BodyScale * (150.0f + MoonIndex * 85.0f + Random.FRandRange(0.0f, 45.0f));
            const FVector MoonPosition = Position +
                (MoonPlaneX * FMath::Cos(MoonAngle) + MoonPlaneY * FMath::Sin(MoonAngle)) * MoonOrbitRadius;
            const float MoonScale = FMath::Max(3.5f, BodyScale * Random.FRandRange(0.09f, 0.22f));
            UInstancedStaticMeshComponent* MoonComponent = Moons;
            const FTransform MoonTransform(RandomRotation(), MoonPosition, FVector(MoonScale));
            const int32 MoonInstance = MoonComponent->AddInstance(MoonTransform);
            FRotatingInstance& MoonMotion = RotatingInstances.AddDefaulted_GetRef();
            MoonMotion.Component = MoonComponent;
            MoonMotion.InstanceIndex = MoonInstance;
            MoonMotion.BaseTransform = MoonTransform;
            MoonMotion.RotationAxis = MoonPlaneNormal;
            MoonMotion.DegreesPerSecond = Random.FRandRange(0.004f, 0.018f);
            MoonMotion.bOrbitLocation = true;
            MoonMotion.OrbitCenter = Position;

            if (MoonIndex == 0 || MoonScale >= 10.0f)
            {
                FSystemPointOfInterest MoonPoint;
                MoonPoint.Name = FName(*FString::Printf(TEXT("Moon %02d-%c"), Index + 1, TCHAR('A' + MoonIndex)));
                MoonPoint.Type = ESystemPointOfInterestType::CelestialBody;
                MoonPoint.WorldLocation = SystemCenter + MoonPosition;
                MoonPoint.SensorSignature = FMath::Clamp(MoonScale / 35.0f, 0.18f, 0.62f);
                PointsOfInterest.Add(MoonPoint);
                MoonMotion.PointOfInterestIndex = PointsOfInterest.Num() - 1;
            }
        }

        // Stone rings read clearly at ship scale and avoid a single opaque disk around the planet.
        if ((Index + GenerationSeed) % 3 == 0)
        {
            const int32 RingPieces = 28 + Random.RandRange(0, 18);
            for (int32 Piece = 0; Piece < RingPieces; ++Piece)
            {
                const float RingAngle = (2.0f * PI * Piece / RingPieces) + Random.FRandRange(-0.035f, 0.035f);
                const float RingRadius = BodyScale * Random.FRandRange(85.0f, 125.0f);
                const FVector RingOffset(FMath::Cos(RingAngle) * RingRadius, FMath::Sin(RingAngle) * RingRadius, Random.FRandRange(-BodyScale * 4.0f, BodyScale * 4.0f));
                const FVector RingScale(Random.FRandRange(0.8f, 4.0f));
                AddDebrisInstance(FTransform(RandomRotation(), Position + RingOffset, RingScale), GenerationSeed + Index * 53 + Piece);
            }
        }

        if (DominantPhenomenon == ESystemPhenomenon::FracturedWorld && Index == 0)
        {
            for (int32 Fragment = 0; Fragment < 36; ++Fragment)
            {
                const FVector FragmentOffset = Random.VRand() * Random.FRandRange(BodyScale * 65.0f, BodyScale * 180.0f);
                AddDebrisInstance(FTransform(RandomRotation(), Position + FragmentOffset, FVector(Random.FRandRange(2.0f, 14.0f))), GenerationSeed + Fragment);
            }
            AddPhenomenonPoint(TEXT("Fractured Planet"), Position, 0.86f);
        }

        FSystemPointOfInterest BodyPoint;
        static const TCHAR* FamilyNames[] = {TEXT("Ocean World"), TEXT("Volcanic World"), TEXT("Ice World"), TEXT("Gas Giant")};
        BodyPoint.Name = FName(*FString::Printf(TEXT("%s %02d"), FamilyNames[PlanetFamily], Index + 1));
        BodyPoint.Type = ESystemPointOfInterestType::CelestialBody;
        BodyPoint.WorldLocation = SystemCenter + Position;
        BodyPoint.SensorSignature = FMath::GetMappedRangeValueClamped(FVector2D(18.0f, 85.0f), FVector2D(0.35f, 1.0f), BodyScale);
        PointsOfInterest.Add(BodyPoint);
    }

    // A broad belt creates a readable orbital plane across the full map and a dense traversal landmark.
    const bool bBrokenBelt = DominantPhenomenon == ESystemPhenomenon::GravityAnomaly ||
        DominantPhenomenon == ESystemPhenomenon::FracturedWorld;
    const float BeltRadius = Random.FRandRange(MapRadius * 0.34f, MapRadius * 0.58f);
    const int32 BeltRockCount = 150 + SystemData.DangerTier * 28;
    const FRotator BeltTilt(Random.FRandRange(-13.0f, 13.0f), Random.FRandRange(-180.0f, 180.0f), 0.0f);
    const FQuat BeltRotation = BeltTilt.Quaternion();
    for (int32 RockIndex = 0; RockIndex < BeltRockCount; ++RockIndex)
    {
        const float NormalizedArc = static_cast<float>(RockIndex) / FMath::Max(1, BeltRockCount - 1);
        float BeltAngle = NormalizedArc * 2.0f * PI + Random.FRandRange(-0.025f, 0.025f);
        if (bBrokenBelt && RockIndex > BeltRockCount / 3 && RockIndex < BeltRockCount / 2)
        {
            BeltAngle += Random.FRandRange(0.35f, 0.8f);
        }
        const float RadialScatter = Random.FRandRange(-MapRadius * 0.035f, MapRadius * 0.035f);
        const FVector FlatPosition(FMath::Cos(BeltAngle) * (BeltRadius + RadialScatter),
            FMath::Sin(BeltAngle) * (BeltRadius + RadialScatter), Random.FRandRange(-14000.0f, 14000.0f));
        const FVector BeltPosition = BeltRotation.RotateVector(FlatPosition);
        const FVector RockScale(Random.FRandRange(1.2f, 9.0f), Random.FRandRange(0.8f, 5.5f), Random.FRandRange(0.9f, 6.5f));
        AddDebrisInstance(FTransform(RandomRotation(), BeltPosition, RockScale), GenerationSeed + RockIndex);
    }
    FSystemPointOfInterest BeltPoint;
    BeltPoint.Name = bBrokenBelt ? TEXT("Shattered Orbital Belt") : TEXT("Primary Asteroid Belt");
    BeltPoint.Type = ESystemPointOfInterestType::Phenomenon;
    BeltPoint.WorldLocation = SystemCenter + BeltRotation.RotateVector(FVector(BeltRadius, 0.0f, 0.0f));
    BeltPoint.SensorSignature = FMath::Clamp(0.4f + BeltRockCount / 500.0f, 0.4f, 0.9f);
    PointsOfInterest.Add(BeltPoint);

    // Comet groups use stretched additive atmosphere shells as tails, avoiding bespoke particle assets.
    const int32 CometCount = 1 + (FMath::Abs(GenerationSeed) % 3);
    for (int32 CometIndex = 0; CometIndex < CometCount; ++CometIndex)
    {
        const FVector CometDirection = Random.VRand().GetSafeNormal();
        const FVector CometPosition = CometDirection * Random.FRandRange(MapRadius * 0.58f, MapRadius * 0.82f);
        const float NucleusScale = Random.FRandRange(4.0f, 10.0f);
        const FTransform NucleusTransform(RandomRotation(), CometPosition, FVector(NucleusScale));
        const int32 NucleusInstance = IcePlanets->AddInstance(NucleusTransform);

        const FVector TailDirection = (CometPosition - StarLocation).GetSafeNormal();
        const FQuat TailRotation = FRotationMatrix::MakeFromX(TailDirection).ToQuat();
        const float TailLength = Random.FRandRange(120.0f, 320.0f);
        const FVector TailCenter = CometPosition + TailDirection * NucleusScale * TailLength * 50.0f;
        const FTransform TailTransform(TailRotation, TailCenter,
            FVector(NucleusScale * TailLength, NucleusScale * Random.FRandRange(1.8f, 3.4f), NucleusScale * Random.FRandRange(1.8f, 3.4f)));
        const int32 TailInstance = Atmospheres->AddInstance(TailTransform);
        const FVector CometVelocity = -CometDirection * Random.FRandRange(12.0f, 38.0f);
        const int32 NucleusMotionIndex = DriftingInstances.AddDefaulted();
        DriftingInstances[NucleusMotionIndex].Component = IcePlanets;
        DriftingInstances[NucleusMotionIndex].InstanceIndex = NucleusInstance;
        DriftingInstances[NucleusMotionIndex].BaseTransform = NucleusTransform;
        DriftingInstances[NucleusMotionIndex].Velocity = CometVelocity;
        FDriftingInstance& TailMotion = DriftingInstances.AddDefaulted_GetRef();
        TailMotion.Component = Atmospheres;
        TailMotion.InstanceIndex = TailInstance;
        TailMotion.BaseTransform = TailTransform;
        TailMotion.Velocity = CometVelocity;

        if (CometIndex == 0)
        {
            FSystemPointOfInterest CometPoint;
            CometPoint.Name = CometCount > 1 ? TEXT("Outer Comet Group") : TEXT("Long-Period Comet");
            CometPoint.Type = ESystemPointOfInterestType::Phenomenon;
            CometPoint.WorldLocation = SystemCenter + CometPosition;
            CometPoint.SensorSignature = 0.48f;
            PointsOfInterest.Add(CometPoint);
            DriftingInstances[NucleusMotionIndex].PointOfInterestIndex = PointsOfInterest.Num() - 1;
        }
    }

    auto CreateGameplayPoint = [this, &Random](ESystemPointOfInterestType Type, int32 Index, float Signature, bool bCriticalResource)
    {
        const float Angle = Random.FRandRange(0.0f, 2.0f * PI);
        const float Radius = Random.FRandRange(MapRadius * 0.14f, MapRadius * 0.58f);
        const FVector LocalLocation(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, Random.FRandRange(-MapRadius * 0.08f, MapRadius * 0.08f));
        FSystemPointOfInterest Point;
        const FString PointName = Type == ESystemPointOfInterestType::Hazard
            ? FString::Printf(TEXT("Hazard Region %02d"), Index + 1)
            : (bCriticalResource
                ? FString::Printf(TEXT("Priority Resource %02d"), Index + 1)
                : FString::Printf(TEXT("Resource Contact %02d"), Index + 1));
        Point.Name = FName(*PointName);
        Point.Type = Type;
        Point.WorldLocation = SystemCenter + LocalLocation;
        Point.SensorSignature = Signature;
        Point.bCriticalResource = bCriticalResource;
        PointsOfInterest.Add(Point);
        return Point.WorldLocation;
    };

    for (int32 Index = 0; Index < SystemData.Hazards.Num(); ++Index)
    {
        const FHazardEntry& Hazard = SystemData.Hazards[Index];
        FVector LocalLocation;
        switch (Hazard.Category)
        {
        case EHazardCategory::SolarRadiationStorm:
        case EHazardCategory::ThermalExtreme:
            LocalLocation = StarLocation + Random.VRand() * Random.FRandRange(180000.0f, 520000.0f);
            break;
        case EHazardCategory::BlackHole:
        case EHazardCategory::ExcessiveGravityWell:
        case EHazardCategory::MicrogravityShear:
        case EHazardCategory::CosmicRadiationBelt:
            LocalLocation = PhenomenonAnchor + Random.VRand() * Random.FRandRange(60000.0f, 280000.0f);
            break;
        case EHazardCategory::MicroDebrisField:
            LocalLocation = BodyLocations.Num() > 0
                ? BodyLocations[Index % BodyLocations.Num()] + Random.VRand() * Random.FRandRange(40000.0f, 180000.0f)
                : Random.VRand() * MapRadius * 0.4f;
            break;
        default:
            LocalLocation = Random.VRand() * Random.FRandRange(MapRadius * 0.14f, MapRadius * 0.58f);
            break;
        }

        FSystemPointOfInterest HazardPoint;
        HazardPoint.Name = FName(*FString::Printf(TEXT("Hazard Region %02d"), Index + 1));
        HazardPoint.Type = ESystemPointOfInterestType::Hazard;
        HazardPoint.WorldLocation = SystemCenter + LocalLocation;
        HazardPoint.SensorSignature = Hazard.Severity;
        PointsOfInterest.Add(HazardPoint);
        HazardLocations.Add(HazardPoint.WorldLocation);
    }
    for (int32 Index = 0; Index < SystemData.Resources.Num(); ++Index)
    {
        const float Signature = FMath::Clamp(SystemData.Resources[Index].Quantity / 100.0f, 0.15f, 1.0f);
        ResourceLocations.Add(CreateGameplayPoint(ESystemPointOfInterestType::Resource, Index, Signature,
            SystemData.Resources[Index].bCriticallyNeeded));
    }

    const float QualityDensity = VisualQualityTier == ESystemVisualQualityTier::Low ? 0.30f
        : (VisualQualityTier == ESystemVisualQualityTier::Medium ? 0.60f
            : (VisualQualityTier == ESystemVisualQualityTier::Cinematic ? 1.45f : 1.0f));
    const int32 FullDebrisCount = BaseDebrisCount + SystemData.DangerTier * 25 + SystemData.Hazards.Num() * 30;
    const int32 DebrisCount = FMath::RoundToInt(FullDebrisCount * QualityDensity);
    for (int32 Index = 0; Index < DebrisCount; ++Index)
    {
        FVector Position = FVector::ZeroVector;
        bool bSafePosition = false;
        for (int32 Attempt = 0; Attempt < 8 && !bSafePosition; ++Attempt)
        {
            const bool bClustered = HazardLocations.Num() > 0 && Index % 3 == 0;
            if (bClustered)
            {
                const FVector ClusterCenter = HazardLocations[Index % HazardLocations.Num()] - SystemCenter;
                Position = ClusterCenter + Random.VRand() * Random.FRandRange(VisualExclusionRadiusCm, 450000.0f);
            }
            else
            {
                const float Angle = Random.FRandRange(0.0f, 2.0f * PI);
                const float Radius = Random.FRandRange(MapRadius * 0.22f, MapRadius * 0.68f);
                Position = FVector(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, Random.FRandRange(-30000.0f, 30000.0f));
            }

            bSafePosition = Position.SizeSquared() >= FMath::Square(VisualExclusionRadiusCm);
            for (const FSystemPointOfInterest& Point : PointsOfInterest)
            {
                if (FVector::DistSquared(SystemCenter + Position, Point.WorldLocation) < FMath::Square(VisualExclusionRadiusCm))
                {
                    bSafePosition = false;
                    break;
                }
            }
        }
        if (!bSafePosition)
        {
            continue;
        }
        const FVector Scale(Random.FRandRange(0.8f, 8.0f), Random.FRandRange(0.8f, 5.0f), Random.FRandRange(0.8f, 6.0f));
        AddDebrisInstance(FTransform(RandomRotation(), Position, Scale), GenerationSeed + Index * 17);
    }

    // Fab content remains an optional landmark layer. It never affects gameplay generation or the
    // stable system seed, and a system may deliberately contain no landmark at all.
    FRandomStream LandmarkRandom(GetVisualLayerSeed(TEXT("Landmarks")));
    const int32 LandmarkOptionCount = LandmarkMeshes.Num() + LandmarkActorClasses.Num();
    if (LandmarkOptionCount > 0 && LandmarkRandom.FRand() <= LandmarkSpawnChance)
    {
        const int32 Selection = LandmarkRandom.RandRange(0, LandmarkOptionCount - 1);
        FVector LandmarkLocation = LandmarkRandom.VRand().GetSafeNormal()
            * LandmarkRandom.FRandRange(MapRadius * 0.45f, MapRadius * 0.68f);
        for (int32 Attempt = 0; Attempt < 8; ++Attempt)
        {
            bool bClear = LandmarkLocation.SizeSquared() >= FMath::Square(VisualExclusionRadiusCm * 2.0f);
            for (const FSystemPointOfInterest& Point : PointsOfInterest)
            {
                if (FVector::DistSquared(SystemCenter + LandmarkLocation, Point.WorldLocation)
                    < FMath::Square(VisualExclusionRadiusCm * 2.0f))
                {
                    bClear = false;
                    break;
                }
            }
            if (bClear)
            {
                break;
            }
            LandmarkLocation = LandmarkRandom.VRand().GetSafeNormal()
                * LandmarkRandom.FRandRange(MapRadius * 0.45f, MapRadius * 0.68f);
        }

        const FRotator LandmarkRotation(
            LandmarkRandom.FRandRange(-180.0f, 180.0f),
            LandmarkRandom.FRandRange(-180.0f, 180.0f),
            LandmarkRandom.FRandRange(-180.0f, 180.0f));
        if (Selection < LandmarkMeshes.Num() && LandmarkMeshes[Selection])
        {
            UStaticMesh* Mesh = LandmarkMeshes[Selection];
            LandmarkMesh->SetStaticMesh(Mesh);
            const float SourceDiameter = FMath::Max(1.0f, Mesh->GetBounds().BoxExtent.GetMax() * 2.0f);
            LandmarkMesh->SetRelativeTransform(FTransform(
                LandmarkRotation, LandmarkLocation, FVector(LandmarkTargetDiameterCm / SourceDiameter)));
            LandmarkMesh->SetVisibility(true, true);
            SelectedLandmarkId = Mesh->GetFName();
        }
        else if (GetWorld())
        {
            const int32 ActorIndex = Selection - LandmarkMeshes.Num();
            if (LandmarkActorClasses.IsValidIndex(ActorIndex) && LandmarkActorClasses[ActorIndex])
            {
                SpawnedLandmarkActor = GetWorld()->SpawnActor<AActor>(LandmarkActorClasses[ActorIndex],
                    FTransform(LandmarkRotation, SystemCenter + LandmarkLocation));
                if (SpawnedLandmarkActor)
                {
                    SpawnedLandmarkActor->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);
                    SpawnedLandmarkActor->Tags.AddUnique(TEXT("GeneratedSystemLandmark"));
                    SelectedLandmarkId = SpawnedLandmarkActor->GetClass()->GetFName();
                }
            }
        }

        if (!SelectedLandmarkId.IsNone())
        {
            FSystemPointOfInterest LandmarkPoint;
            LandmarkPoint.Name = SelectedLandmarkId;
            LandmarkPoint.Type = ESystemPointOfInterestType::Phenomenon;
            LandmarkPoint.WorldLocation = SystemCenter + LandmarkLocation;
            LandmarkPoint.SensorSignature = 0.82f;
            PointsOfInterest.Add(LandmarkPoint);
        }
    }
    RefreshUnrealNativeVisuals();
    OnSystemVisualSeedReady.Broadcast(GenerationSeed, DominantPhenomenon);
}

int32 AProceduralStarSystemMap::GetVisualLayerSeed(FName LayerName) const
{
    return static_cast<int32>(HashCombineFast(static_cast<uint32>(GenerationSeed), GetTypeHash(LayerName)));
}

void AProceduralStarSystemMap::RefreshUnrealNativeVisuals()
{
    if (!bUseUnrealNativeVisualPipeline)
    {
        AsteroidPCG->CleanupLocal(true);
        RadiationDustFX->DeactivateImmediate();
        NebulaFX->DeactivateImmediate();
        return;
    }

    const bool bEnablePCGAsteroids = VisualQualityTier != ESystemVisualQualityTier::Low;
    AsteroidPCG->Seed = GetVisualLayerSeed(TEXT("Asteroids"));
    if (bEnablePCGAsteroids && AsteroidPCG->GetGraph())
    {
        AsteroidPCG->GenerateLocal(true);
    }
    else
    {
        AsteroidPCG->CleanupLocal(true);
    }

    const float QualityScale = VisualQualityTier == ESystemVisualQualityTier::Low ? 0.35f
        : (VisualQualityTier == ESystemVisualQualityTier::Medium ? 0.65f
            : (VisualQualityTier == ESystemVisualQualityTier::Cinematic ? 1.5f : 1.0f));

    auto SeedNiagaraLayer = [this, QualityScale](UNiagaraComponent* Component, FName LayerName)
    {
        const int32 LayerSeed = GetVisualLayerSeed(LayerName);
        Component->SetRandomSeedOffset(LayerSeed);
        Component->SetVariableInt(TEXT("User.SystemSeed"), LayerSeed);
        Component->SetVariableInt(TEXT("User.SystemPhenomenon"), static_cast<int32>(DominantPhenomenon));
        Component->SetVariableFloat(TEXT("User.SystemRadiusCm"), MapRadius);
        Component->SetVariableFloat(TEXT("User.QualityScale"), QualityScale);
        Component->SetVariableFloat(TEXT("User.ExclusionRadiusCm"), VisualExclusionRadiusCm);
        if (Component->GetAsset())
        {
            Component->ReinitializeSystem();
            Component->Activate(true);
        }
    };

    SeedNiagaraLayer(RadiationDustFX, TEXT("RadiationDust"));
    SeedNiagaraLayer(NebulaFX, TEXT("NebulaVolumes"));
}

FVector AProceduralStarSystemMap::GetHazardLocation(int32 HazardIndex) const
{
    return HazardLocations.IsValidIndex(HazardIndex) ? HazardLocations[HazardIndex] : SampleGameplayLocation(HazardIndex + 1000);
}

FVector AProceduralStarSystemMap::GetResourceLocation(int32 ResourceIndex) const
{
    return ResourceLocations.IsValidIndex(ResourceIndex) ? ResourceLocations[ResourceIndex] : SampleGameplayLocation(ResourceIndex + 2000);
}

void AProceduralStarSystemMap::OverrideResourceLocation(int32 ResourceIndex, const FVector& WorldLocation)
{
    if (!ResourceLocations.IsValidIndex(ResourceIndex))
    {
        return;
    }
    ResourceLocations[ResourceIndex] = WorldLocation;
    StationaryResourceIndices.Add(ResourceIndex);

    int32 SeenResourcePoints = 0;
    for (FSystemPointOfInterest& Point : PointsOfInterest)
    {
        if (Point.Type != ESystemPointOfInterestType::Resource)
        {
            continue;
        }
        if (SeenResourcePoints++ == ResourceIndex)
        {
            Point.WorldLocation = WorldLocation;
            const FString InternalName = Point.bCriticalResource
                ? FString::Printf(TEXT("Priority Internal Resource %02d"), ResourceIndex + 1)
                : FString::Printf(TEXT("Internal Resource %02d"), ResourceIndex + 1);
            Point.Name = FName(*InternalName);
            Point.SensorSignature = 1.0f;
            break;
        }
    }
}

void AProceduralStarSystemMap::DeactivateResourceContact(int32 ResourceIndex)
{
    int32 SeenResourcePoints = 0;
    for (FSystemPointOfInterest& Point : PointsOfInterest)
    {
        if (Point.Type == ESystemPointOfInterestType::Resource && SeenResourcePoints++ == ResourceIndex)
        {
            Point.SensorSignature = 0.0f;
            Point.Name = FName(*FString::Printf(TEXT("Depleted Resource %02d"), ResourceIndex + 1));
            return;
        }
    }
}

int32 AProceduralStarSystemMap::GetActiveResourceContactCount() const
{
    int32 ActiveCount = 0;
    for (const FSystemPointOfInterest& Point : PointsOfInterest)
    {
        if (Point.Type == ESystemPointOfInterestType::Resource && Point.SensorSignature > 0.0f)
        {
            ++ActiveCount;
        }
    }
    return ActiveCount;
}

int32 AProceduralStarSystemMap::GetRecoveredResourceContactCount() const
{
    return FMath::Max(0, GeneratedSystem.Resources.Num() - GetActiveResourceContactCount());
}

bool AProceduralStarSystemMap::IsResourceSweepComplete() const
{
    return GeneratedSystem.Resources.Num() > 0 && GetActiveResourceContactCount() == 0;
}

FVector AProceduralStarSystemMap::SampleGameplayLocation(int32 Salt) const
{
    FRandomStream Random(HashCombine(GenerationSeed, Salt));
    const FVector Direction = Random.VRand();
    return SystemCenter + Direction * Random.FRandRange(MapRadius * 0.12f, MapRadius * 0.55f);
}
