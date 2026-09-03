// Copyright Epic Games, Inc. All Rights Reserved.

#include "LevelSetup/ProceduralShipBuilder.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/CryoPodSystem.h"
#include "Ship/LifeSupportSystem.h"
#include "Ship/SensorArraySystem.h"
#include "Ship/JumpConsoleSystem.h"
#include "Ship/EscapePodSystem.h"
#include "Ship/SelfDestructConsoleSystem.h"
#include "Ship/ArmorPlatingSystem.h"
#include "Ship/ModularShipRoom.h"
#include "StarSystem/DormantCollectorSystem.h"
#include "StarSystem/ResourceNodeActor.h"
#include "StarSystem/RetrievalDroneActor.h"
#include "AI/HorrorEnemy.h"
#include "AI/PatrollingEnemyController.h"
#include "Activities/ActivityStation.h"
#include "Activities/MaintenanceActivityStations.h"
#include "Activities/OperationsActivityStations.h"
#include "Bloom/CrewCorpse.h"
#include "CollisionQueryParams.h"
#include "CollisionShape.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/DecalComponent.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/Pawn.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

AProceduralShipBuilder::AProceduralShipBuilder()
{
    PrimaryActorTick.bCanEverTick = false;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("ShipRoot"));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMeshFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMeshFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMeshFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> CrewMeshFinder(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
    CubeMesh = CubeMeshFinder.Object;
    CylinderMesh = CylinderMeshFinder.Object;
    SphereMesh = SphereMeshFinder.Object;
    CrewMesh = CrewMeshFinder.Object;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CryoShellFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell.SM_Room_CryoShell"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CryoMachineryFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/SM_Room_CryoMachinery.SM_Room_CryoMachinery"));
    CryoRoomShellMesh = CryoShellFinder.Object;
    CryoRoomMachineryMesh = CryoMachineryFinder.Object;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> HullFinder(TEXT("/Game/Assets/Materials/M_ShipBulkhead_WornSteel.M_ShipBulkhead_WornSteel"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> DeckFinder(TEXT("/Game/Assets/Materials/M_ShipDeck_NonSlip.M_ShipDeck_NonSlip"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> AccentFinder(TEXT("/Game/Assets/Materials/M_ShipUtility_Hazard.M_ShipUtility_Hazard"));
    HullMaterial = HullFinder.Object;
    DeckMaterial = DeckFinder.Object;
    AccentMaterial = AccentFinder.Object;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SpaceSuitFinder(TEXT("/Game/Assets/Materials/M_SpaceSuit_Damaged.M_SpaceSuit_Damaged"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BloomFinder(TEXT("/Game/Assets/Materials/M_Bloom_AmethystCorruption.M_Bloom_AmethystCorruption"));
    SpaceSuitMaterial = SpaceSuitFinder.Object;
    BloomMaterial = BloomFinder.Object;

    auto AddRoomDefinition = [this](const TCHAR* Code, const TCHAR* Name, EShipRoomArchetype Archetype,
        EShipSectionType Type, const FVector& Offset, const FLinearColor& Color)
    {
        FShipRoomModuleDefinition& Definition = RoomModules.AddDefaulted_GetRef();
        Definition.RoomCode = FName(Code);
        Definition.DisplayName = FText::FromString(Name);
        Definition.Archetype = Archetype;
        Definition.SectionType = Type;
        Definition.RelativeLocation = Offset;
        Definition.AccentColor = Color;
    };

    AddRoomDefinition(TEXT("BRG-01"), TEXT("Bridge"), EShipRoomArchetype::Bridge, EShipSectionType::Bridge, FVector(4800, 0, 0), FLinearColor(0.1f, 0.45f, 1));
    AddRoomDefinition(TEXT("CIC-01"), TEXT("Combat Information Center"), EShipRoomArchetype::Bridge, EShipSectionType::Bridge, FVector(3200, 0, 0), FLinearColor(0.1f, 0.65f, 1));
    AddRoomDefinition(TEXT("SNS-01"), TEXT("Sensor Operations"), EShipRoomArchetype::SensorOperations, EShipSectionType::Bridge, FVector(1600, 900, 0), FLinearColor(0.15f, 0.8f, 1));
    AddRoomDefinition(TEXT("ARM-01"), TEXT("Armory"), EShipRoomArchetype::Armory, EShipSectionType::CargoBay, FVector(1600, -900, 0), FLinearColor(1, 0.5f, 0.05f));
    AddRoomDefinition(TEXT("CMP-01"), TEXT("Central Companionway"), EShipRoomArchetype::Companionway, EShipSectionType::Corridor, FVector(0, 0, 0), FLinearColor(0.15f, 0.65f, 1));
    AddRoomDefinition(TEXT("MED-01"), TEXT("Medical Bay"), EShipRoomArchetype::MedicalBay, EShipSectionType::MedBay, FVector(0, 1400, 0), FLinearColor(0.15f, 1, 0.55f));
    AddRoomDefinition(TEXT("CRW-01"), TEXT("Crew Berthing"), EShipRoomArchetype::CrewBerthing, EShipSectionType::CrewQuarters, FVector(0, -1400, 0), FLinearColor(0.35f, 0.55f, 1));
    AddRoomDefinition(TEXT("DCR-01"), TEXT("Damage Control"), EShipRoomArchetype::DamageControl, EShipSectionType::Deck, FVector(-1600, 900, 0), FLinearColor(1, 0.25f, 0.05f));
    AddRoomDefinition(TEXT("CGO-01"), TEXT("Cargo and Drone Bay"), EShipRoomArchetype::CargoBay, EShipSectionType::CargoBay, FVector(-1600, -900, 0), FLinearColor(1, 0.65f, 0.1f));
    AddRoomDefinition(TEXT("ENG-01"), TEXT("Engineering"), EShipRoomArchetype::Engineering, EShipSectionType::EngineRoom, FVector(-3200, 0, 0), FLinearColor(1, 0.18f, 0.04f));
    AddRoomDefinition(TEXT("RCT-01"), TEXT("Reactor Control"), EShipRoomArchetype::ReactorControl, EShipSectionType::EngineRoom, FVector(-4800, 0, 0), FLinearColor(1, 0.08f, 0.02f));
    AddRoomDefinition(TEXT("ESC-P1"), TEXT("Port Escape Bay"), EShipRoomArchetype::EscapeBay, EShipSectionType::Airlock, FVector(-4000, 1400, 0), FLinearColor(1, 0.75f, 0.1f));
    AddRoomDefinition(TEXT("ESC-S1"), TEXT("Starboard Escape Bay"), EShipRoomArchetype::EscapeBay, EShipSectionType::Airlock, FVector(-4000, -1400, 0), FLinearColor(1, 0.75f, 0.1f));

    auto AddConnection = [this](const TCHAR* RoomA, EShipRoomSocket SocketA,
        const TCHAR* RoomB, EShipRoomSocket SocketB)
    {
        FShipRoomConnectionDefinition& Connection = RoomConnections.AddDefaulted_GetRef();
        Connection.RoomA = FName(RoomA);
        Connection.SocketA = SocketA;
        Connection.RoomB = FName(RoomB);
        Connection.SocketB = SocketB;
    };

    AddConnection(TEXT("BRG-01"), EShipRoomSocket::Aft, TEXT("CIC-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CIC-01"), EShipRoomSocket::AftStarboard, TEXT("SNS-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CIC-01"), EShipRoomSocket::AftPort, TEXT("ARM-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CIC-01"), EShipRoomSocket::Aft, TEXT("CMP-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CMP-01"), EShipRoomSocket::Starboard, TEXT("MED-01"), EShipRoomSocket::Port);
    AddConnection(TEXT("CMP-01"), EShipRoomSocket::Port, TEXT("CRW-01"), EShipRoomSocket::Starboard);
    AddConnection(TEXT("CMP-01"), EShipRoomSocket::AftStarboard, TEXT("DCR-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CMP-01"), EShipRoomSocket::AftPort, TEXT("CGO-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("CMP-01"), EShipRoomSocket::Aft, TEXT("ENG-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("ENG-01"), EShipRoomSocket::Aft, TEXT("RCT-01"), EShipRoomSocket::Forward);
    AddConnection(TEXT("ENG-01"), EShipRoomSocket::AftStarboard, TEXT("ESC-P1"), EShipRoomSocket::Forward);
    AddConnection(TEXT("ENG-01"), EShipRoomSocket::AftPort, TEXT("ESC-S1"), EShipRoomSocket::Forward);
}

void AProceduralShipBuilder::BeginPlay()
{
    Super::BeginPlay();

    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UShipCheckpointSubsystem* Checkpoints = GameInstance->GetSubsystem<UShipCheckpointSubsystem>())
        {
            const FShipCheckpointRecord& Record = Checkpoints->GetCheckpointRecord();
            if (Checkpoints->HasCheckpointForWorld(GetWorld()) && Record.ActivityPopulationSeed != 0)
            {
                ActivityPopulationSeed = Record.ActivityPopulationSeed;
            }
        }
    }

    if (bSpawnOnBeginPlay)
    {
        BuildShip();
    }
}

AModularShipRoom* AProceduralShipBuilder::SpawnRoomModule(int32 SectionID, FName RoomCode,
    const FText& DisplayName, EShipRoomArchetype Archetype, EShipSectionType SectionType,
    const FVector& Location, const FVector& BoxExtent)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    AModularShipRoom* Section = World->SpawnActor<AModularShipRoom>(AModularShipRoom::StaticClass(), Location, FRotator::ZeroRotator);
    if (Section)
    {
        Section->SectionID = SectionID;
        Section->ConfigureRoom(RoomCode, DisplayName, Archetype, SectionType, BoxExtent * 2.0);

        if (RoomCode != TEXT("MED-01"))
        {
            SpawnBoxRoom(Section);
        }
        PopulateRoomGameplayHardpoints(Section);
    }

    return Section;
}

void AProceduralShipBuilder::SpawnBoxRoom(AShipSection* Section)
{
    if (!Section || !Section->SectionBounds || !CubeMesh)
    {
        return;
    }

    const FVector Extent = Section->SectionBounds->GetUnscaledBoxExtent();
    const float T = 24.0f;
    const float DoorHalfWidth = 90.0f;
    const float DoorHeight = 250.0f;

    AddBox(Section, FVector(0, 0, -Extent.Z), FVector(Extent.X * 2, Extent.Y * 2, T), DeckMaterial);
    AddBox(Section, FVector(0, 0, Extent.Z), FVector(Extent.X * 2, Extent.Y * 2, T), HullMaterial);

    // Every wall has a standard naval hatch opening. Corridors overlap these portals, allowing
    // layouts to be changed without rebuilding bespoke wall meshes.
    const float XDoorCenters[] = { -Extent.Y * 0.55f, 0.0f, Extent.Y * 0.55f };
    for (float XSign : { -1.0f, 1.0f })
    {
        float SegmentStart = -Extent.Y;
        for (const float DoorCenter : XDoorCenters)
        {
            const float SegmentEnd = DoorCenter - DoorHalfWidth;
            const float SegmentLength = SegmentEnd - SegmentStart;
            if (SegmentLength > 1.0f)
            {
                AddBox(Section, FVector(XSign * Extent.X, (SegmentStart + SegmentEnd) * 0.5f, 0),
                    FVector(T, SegmentLength, Extent.Z * 2), HullMaterial);
            }
            AddBox(Section, FVector(XSign * Extent.X, DoorCenter, DoorHeight + (Extent.Z - DoorHeight) * .5f),
                FVector(T, DoorHalfWidth * 2, Extent.Z - DoorHeight), HullMaterial);
            SegmentStart = DoorCenter + DoorHalfWidth;
        }
        if (SegmentStart < Extent.Y)
        {
            AddBox(Section, FVector(XSign * Extent.X, (SegmentStart + Extent.Y) * 0.5f, 0),
                FVector(T, Extent.Y - SegmentStart, Extent.Z * 2), HullMaterial);
        }
    }
    const float YSideLength = FMath::Max(50.0f, Extent.X - DoorHalfWidth);
    for (float YSign : { -1.0f, 1.0f })
    {
        AddBox(Section, FVector(DoorHalfWidth + YSideLength * .5f, YSign * Extent.Y, 0), FVector(YSideLength, T, Extent.Z * 2), HullMaterial);
        AddBox(Section, FVector(-DoorHalfWidth - YSideLength * .5f, YSign * Extent.Y, 0), FVector(YSideLength, T, Extent.Z * 2), HullMaterial);
        AddBox(Section, FVector(0, YSign * Extent.Y, DoorHeight + (Extent.Z - DoorHeight) * .5f), FVector(DoorHalfWidth * 2, T, Extent.Z - DoorHeight), HullMaterial);
    }
}

void AProceduralShipBuilder::PopulateRoomGameplayHardpoints(AModularShipRoom* Room)
{
    if (!Room || !Room->SectionBounds)
    {
        return;
    }

    Room->GameplayHardpoints.Reset();
    const FVector Extent = Room->SectionBounds->GetUnscaledBoxExtent();
    const float FloorZ = -Extent.Z + 24.0f;
    int32 Sequence = 0;
    auto Add = [Room, &Sequence](EShipGameplayHardpointType Type, const FVector& Location,
        const FRotator& Rotation, float Clearance, FName Context)
    {
        FShipGameplayHardpoint Hardpoint;
        Hardpoint.HardpointId = FName(*FString::Printf(TEXT("%s-HP-%02d"), *Room->RoomCode.ToString(), Sequence++));
        Hardpoint.HardpointType = Type;
        Hardpoint.RelativeLocation = Location;
        Hardpoint.RelativeRotation = Rotation;
        Hardpoint.ClearanceRadius = Clearance;
        Hardpoint.ContextTag = Context;
        Room->AddGameplayHardpoint(Hardpoint);
    };

    Add(EShipGameplayHardpointType::Body, FVector(-Extent.X * 0.22f, -Extent.Y * 0.10f, FloorZ),
        FRotator(0, 25, 0), 105.0f, TEXT("NarrativeBody"));
    Add(EShipGameplayHardpointType::Body, FVector(Extent.X * 0.18f, Extent.Y * 0.12f, FloorZ),
        FRotator(0, -35, 0), 105.0f, TEXT("NarrativeBody"));
    Add(EShipGameplayHardpointType::Obstacle, FVector(-Extent.X * 0.12f, Extent.Y * 0.28f, FloorZ),
        FRotator::ZeroRotator, 135.0f, TEXT("MoveableBlocker"));
    Add(EShipGameplayHardpointType::Obstacle, FVector(Extent.X * 0.24f, -Extent.Y * 0.28f, FloorZ),
        FRotator(0, 90, 0), 135.0f, TEXT("MoveableBlocker"));
    Add(EShipGameplayHardpointType::BloomGrowth, FVector(-Extent.X * 0.34f, Extent.Y * 0.38f, FloorZ),
        FRotator::ZeroRotator, 115.0f, TEXT("FloorGrowth"));
    Add(EShipGameplayHardpointType::BloomGrowth, FVector(Extent.X * 0.36f, -Extent.Y * 0.38f, FloorZ),
        FRotator::ZeroRotator, 115.0f, TEXT("FloorGrowth"));

    for (const float Side : { -1.0f, 1.0f })
    {
        Add(EShipGameplayHardpointType::Activity,
            FVector(-Extent.X * 0.34f, Side * (Extent.Y - 118.0f), FloorZ + 95.0f),
            FRotator(0, Side < 0.0f ? 90.0f : -90.0f, 0), 100.0f, TEXT("FloorMount"));
        Add(EShipGameplayHardpointType::Activity,
            FVector(Extent.X * 0.34f, Side * (Extent.Y - 52.0f), FloorZ + 175.0f),
            FRotator(0, Side < 0.0f ? 90.0f : -90.0f, 0), 85.0f, TEXT("WallMount"));
        Add(EShipGameplayHardpointType::DamageRepair,
            FVector(Extent.X * 0.12f, Side * (Extent.Y - 48.0f), FloorZ + 170.0f),
            FRotator(0, Side < 0.0f ? 90.0f : -90.0f, 0), 90.0f, TEXT("BulkheadRepair"));
    }
}

UStaticMeshComponent* AProceduralShipBuilder::AddBox(AActor* OwningActor, const FVector& RelativeLocation,
    const FVector& BoxSize, UMaterialInterface* Material, bool bCollision)
{
    return AddPrimitive(OwningActor, CubeMesh, RelativeLocation, BoxSize, FRotator::ZeroRotator, Material, bCollision);
}

UStaticMeshComponent* AProceduralShipBuilder::AddPrimitive(AActor* OwningActor, UStaticMesh* MeshAsset,
    const FVector& RelativeLocation, const FVector& Size, const FRotator& Rotation,
    UMaterialInterface* Material, bool bCollision)
{
    if (!OwningActor || !MeshAsset) return nullptr;
    UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(OwningActor);
    Mesh->SetStaticMesh(MeshAsset);
    Mesh->SetupAttachment(OwningActor->GetRootComponent());
    Mesh->SetRelativeLocation(RelativeLocation);
    Mesh->SetRelativeRotation(Rotation);
    Mesh->SetRelativeScale3D(Size / 100.0f);
    Mesh->SetCollisionEnabled(bCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    Mesh->SetCollisionProfileName(bCollision ? TEXT("BlockAll") : TEXT("NoCollision"));
    if (Material) Mesh->SetMaterial(0, Material);
    Mesh->RegisterComponent();
    return Mesh;
}

UStaticMeshComponent* AProceduralShipBuilder::AddAuthoredProp(AActor* OwningActor, const TCHAR* AssetPath,
    const FVector& RelativeLocation, const FRotator& Rotation, const FVector& Scale)
{
    if (!OwningActor || !AssetPath) return nullptr;
    UStaticMesh* Asset = LoadObject<UStaticMesh>(nullptr, AssetPath);
    if (!Asset) return nullptr;
    UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(OwningActor);
    Mesh->SetStaticMesh(Asset);
    Mesh->SetupAttachment(OwningActor->GetRootComponent());
    Mesh->SetRelativeLocation(RelativeLocation);
    Mesh->SetRelativeRotation(Rotation);
    Mesh->SetRelativeScale3D(Scale);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->SetCollisionProfileName(TEXT("BlockAll"));
    Mesh->RegisterComponent();
    return Mesh;
}

void AProceduralShipBuilder::AddAuthoredCryoRoom(AModularShipRoom* CryoBay)
{
    if (!CryoBay || !CryoRoomShellMesh || !CryoRoomMachineryMesh)
    {
        UE_LOG(LogTemp, Warning, TEXT("CRYO-01 authored meshes are unavailable; retaining the procedural medical shell."));
        return;
    }

    // Blender's module is authored floor-up and with its hatches on local X. MED-01 connects on
    // its port socket, so rotate the module into the room and lower its floor to the section deck.
    const FVector ArtOrigin(0.0f, 0.0f, -300.0f);
    const FRotator ArtRotation(0.0f, 90.0f, 0.0f);
    UStaticMeshComponent* Shell = AddPrimitive(CryoBay, CryoRoomShellMesh, ArtOrigin,
        FVector(100.0f), ArtRotation, nullptr, true);
    UStaticMeshComponent* Machinery = AddPrimitive(CryoBay, CryoRoomMachineryMesh, ArtOrigin,
        FVector(100.0f), ArtRotation, nullptr, true);
    if (Shell) Shell->ComponentTags.Add(TEXT("CRYO-01.Shell"));
    if (Machinery) Machinery->ComponentTags.Add(TEXT("CRYO-01.Machinery"));

    static const float PodX[] = { -384.3f, -136.6f, 112.2f, 359.9f };
    const FTransform ArtTransform(ArtRotation, CryoBay->GetActorLocation() + ArtOrigin);
    UWorld* World = GetWorld();
    for (int32 PodIndex = 0; World && PodIndex < UE_ARRAY_COUNT(PodX); ++PodIndex)
    {
        const FVector PodLocation = ArtTransform.TransformPosition(FVector(PodX[PodIndex], -156.2f, 0.0f));
        ACryoPodSystem* Pod = World->SpawnActor<ACryoPodSystem>(
            ACryoPodSystem::StaticClass(), PodLocation, ArtRotation);
        if (!Pod)
        {
            continue;
        }
        Pod->SystemName = FString::Printf(TEXT("Cryopod %02d"), PodIndex + 1);
        Pod->Tags.Add(TEXT("CRYO-01"));
        Pod->Tags.Add(FName(*FString::Printf(TEXT("CryoPod.%02d"), PodIndex + 1)));
        if (PodIndex >= 2)
        {
            IBloomCorruptible::Execute_OnBloomCorruption(Pod);
        }
    }
}

void AProceduralShipBuilder::AddShipProps(AShipSection* Section, const FString& RoomName)
{
    if (!Section) return;
    const float FloorZ = -220.0f;

    // Common naval fittings: overhead pipe trunks, wall lockers and emergency canisters.
    for (float Y : { -430.0f, 430.0f })
    {
        AddPrimitive(Section, CylinderMesh, FVector(0, Y, 210), FVector(850, 22, 22), FRotator(0, 90, 0), AccentMaterial, false);
        AddPrimitive(Section, CylinderMesh, FVector(0, Y * .94f, 175), FVector(850, 12, 12), FRotator(0, 90, 0), HullMaterial, false);
    }
    AddBox(Section, FVector(-500, 390, -90), FVector(150, 95, 260), AccentMaterial);
    AddPrimitive(Section, CylinderMesh, FVector(500, -400, -150), FVector(65, 65, 190), FRotator::ZeroRotator, AccentMaterial);

    if (RoomName.Contains(TEXT("Bridge")) || RoomName.Contains(TEXT("Information")) || RoomName.Contains(TEXT("Sensor")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Command_HelmChair.SM_Command_HelmChair"), FVector(0,-180,FloorZ), FRotator(0,180,0));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Command_HolographicTable.SM_Command_HolographicTable"), FVector(0,120,FloorZ));
        // The authored holographic table replaces the center greybox console.
        for (float X : { -320.0f, 320.0f })
        {
            AddBox(Section, FVector(X, 100, FloorZ + 80), FVector(210, 130, 120), AccentMaterial);
            AddBox(Section, FVector(X, 145, FloorZ + 165), FVector(190, 24, 90), HullMaterial, false);
        }
        AddBox(Section, FVector(0, -280, FloorZ + 55), FVector(430, 150, 85), DeckMaterial);
    }
    else if (RoomName.Contains(TEXT("Armory")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/Environment/SM_Prop_ToolCabinet.SM_Prop_ToolCabinet"), FVector(-350,430,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/DamageControl/SM_Emergency_RadiationBarrier.SM_Emergency_RadiationBarrier"), FVector(360,-410,FloorZ));
        // The tool cabinet replaces the port-side greybox locker.
        for (float X : { -120.0f, 120.0f, 360.0f })
            AddBox(Section, FVector(X, 360, -75), FVector(180, 120, 290), AccentMaterial);
        for (float X : { -300.0f, 0.0f, 300.0f })
            AddBox(Section, FVector(X, -250, FloorZ + 55), FVector(210, 100, 95), HullMaterial);
    }
    else if (RoomName.Contains(TEXT("Medical")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Medical_DiagnosticArch.SM_Medical_DiagnosticArch"), FVector(0,300,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Medical_SupplyCabinet.SM_Medical_SupplyCabinet"), FVector(-450,-330,FloorZ));
        for (float X : { -330.0f, 0.0f, 330.0f })
        {
            AddBox(Section, FVector(X, 160, FloorZ + 55), FVector(230, 90, 65), HullMaterial);
            AddBox(Section, FVector(X, 205, FloorZ + 105), FVector(220, 18, 75), AccentMaterial, false);
        }
        // The authored supply cabinet replaces the cabinet-shaped greybox here.
        AddPrimitive(Section, CylinderMesh, FVector(430, -340, -135), FVector(55, 55, 220), FRotator::ZeroRotator, AccentMaterial);
        AddPrimitive(Section, CylinderMesh, FVector(500, -340, -135), FVector(55, 55, 220), FRotator::ZeroRotator, AccentMaterial);
    }
    else if (RoomName.Contains(TEXT("Crew")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/Environment/SM_Prop_Bunk.SM_Prop_Bunk"), FVector(-260,320,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/Environment/SM_Prop_GalleyUnit.SM_Prop_GalleyUnit"), FVector(390,-350,FloorZ));
        // Keep two stacked greybox bunks; the other two footprints are now occupied by authored props.
        for (const FVector2D& BunkLocation : { FVector2D(-260,-320), FVector2D(260,320) })
        {
            for (float Z : { -170.0f, 30.0f })
            {
                AddBox(Section, FVector(BunkLocation.X, BunkLocation.Y, Z), FVector(430, 145, 45), DeckMaterial);
            }
        }
    }
    else if (RoomName.Contains(TEXT("Cargo")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Cargo_Pallet.SM_Cargo_Pallet"), FVector(-360,250,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Cargo_HandLoader.SM_Cargo_HandLoader"), FVector(430,-300,FloorZ));
        // Authored cargo gear replaces two of the original crate placeholders.
        for (const FVector& P : { FVector(-350,-220,FloorZ+65), FVector(-80,-260,FloorZ+90), FVector(340,170,FloorZ+75) })
            AddBox(Section, P, FVector(170, 150, 120), AccentMaterial);
        AddPrimitive(Section, CylinderMesh, FVector(470, 350, -135), FVector(85, 85, 220), FRotator::ZeroRotator, HullMaterial);
    }
    else if (RoomName.Contains(TEXT("Engineering")) || RoomName.Contains(TEXT("Reactor")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Engineering_ReactorCoil.SM_Engineering_ReactorCoil"), FVector(-260,0,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Engineering_CoolantPump.SM_Engineering_CoolantPump"), FVector(430,240,FloorZ));
        for (float Y : { -260.0f, 0.0f, 260.0f })
        {
            // The authored reactor coil occupies the center port-machine footprint.
            if (!FMath::IsNearlyZero(Y))
                AddPrimitive(Section, CylinderMesh, FVector(-260, Y, -80), FVector(175, 175, 330), FRotator::ZeroRotator, AccentMaterial);
            AddPrimitive(Section, CylinderMesh, FVector(270, Y, -130), FVector(90, 90, 230), FRotator::ZeroRotator, HullMaterial);
        }
        for (float Z : { -30.0f, 90.0f, 190.0f })
            AddPrimitive(Section, CylinderMesh, FVector(0, -420, Z), FVector(700, 24, 24), FRotator(0, 90, 0), AccentMaterial, false);
    }
    else if (RoomName.Contains(TEXT("Escape")))
    {
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/RoomMachinery/SM_Drone_LaunchCradle.SM_Drone_LaunchCradle"), FVector(0,-200,FloorZ));
        AddAuthoredProp(Section, TEXT("/Game/Assets/Models/DamageControl/SM_Emergency_PortableAirScrubber.SM_Emergency_PortableAirScrubber"), FVector(500,400,FloorZ));
        for (float X : { -360.0f, -120.0f, 120.0f, 360.0f })
        {
            AddBox(Section, FVector(X, 300, FloorZ + 70), FVector(135, 115, 100), DeckMaterial);
            AddBox(Section, FVector(X, 350, FloorZ + 150), FVector(130, 35, 135), AccentMaterial);
        }
        // The authored launch cradle replaces the cylindrical escape-pod placeholder.
    }
    else
    {
        AddBox(Section, FVector(-260, 180, FloorZ + 70), FVector(230, 160, 130), AccentMaterial);
        AddBox(Section, FVector(260, -180, FloorZ + 60), FVector(190, 145, 110), HullMaterial);
    }
}

TArray<TSubclassOf<AActivityStation>> AProceduralShipBuilder::GetActivityClassesForRoom(
    EShipRoomArchetype Archetype) const
{
    TArray<TSubclassOf<AActivityStation>> Pool;
    switch (Archetype)
    {
    case EShipRoomArchetype::Bridge:
        Pool = { ASensorCalibrationStation::StaticClass(), ABreakerReroutingStation::StaticClass(),
            ATurretServiceStation::StaticClass(), AMechanicalOverrideStation::StaticClass() };
        break;
    case EShipRoomArchetype::SensorOperations:
        Pool = { ASensorCalibrationStation::StaticClass(), AComponentReplacementStation::StaticClass(),
            ABloomPurgingStation::StaticClass(), ABreakerReroutingStation::StaticClass() };
        break;
    case EShipRoomArchetype::MedicalBay:
        Pool = { AMedicalStabilizationStation::StaticClass(), ADecontaminationStation::StaticClass(),
            ASampleContainmentStation::StaticClass(), ABloomPurgingStation::StaticClass() };
        break;
    case EShipRoomArchetype::CrewBerthing:
        Pool = { ABreakerReroutingStation::StaticClass(), APipeSealingStation::StaticClass(),
            AFireSuppressionStation::StaticClass(), ASuitPatchingStation::StaticClass() };
        break;
    case EShipRoomArchetype::CargoBay:
        Pool = { ADroneRepairStation::StaticClass(), AComponentReplacementStation::StaticClass(),
            AFabricationStation::StaticClass(), ABreakerReroutingStation::StaticClass() };
        break;
    case EShipRoomArchetype::DamageControl:
        Pool = { AHullPatchingStation::StaticClass(), AFireSuppressionStation::StaticClass(),
            APipeSealingStation::StaticClass(), ABreakerReroutingStation::StaticClass(),
            AMechanicalOverrideStation::StaticClass() };
        break;
    case EShipRoomArchetype::Engineering:
        Pool = { ACoolantBalancingStation::StaticClass(), ABatteryRecoveryStation::StaticClass(),
            AOxygenScrubberServiceStation::StaticClass(), ABreakerReroutingStation::StaticClass(),
            AComponentReplacementStation::StaticClass() };
        break;
    case EShipRoomArchetype::ReactorControl:
        Pool = { AReactorStartupStation::StaticClass(), ACoolantBalancingStation::StaticClass(),
            ABreakerReroutingStation::StaticClass(), ABloomPurgingStation::StaticClass(),
            APipeSealingStation::StaticClass() };
        break;
    case EShipRoomArchetype::EscapeBay:
        Pool = { AAirlockRepressurizationStation::StaticClass(), ASuitPatchingStation::StaticClass(),
            AOxygenScrubberServiceStation::StaticClass(), AMechanicalOverrideStation::StaticClass() };
        break;
    case EShipRoomArchetype::Armory:
        Pool = { ATurretServiceStation::StaticClass(), AComponentReplacementStation::StaticClass(),
            AFabricationStation::StaticClass(), AMechanicalOverrideStation::StaticClass() };
        break;
    case EShipRoomArchetype::Companionway:
    default:
        Pool = { ABreakerReroutingStation::StaticClass(), APipeSealingStation::StaticClass(),
            AMechanicalOverrideStation::StaticClass(), AFireSuppressionStation::StaticClass() };
        break;
    }
    return Pool;
}

bool AProceduralShipBuilder::FindActivitySpawnTransform(AModularShipRoom* Room, bool bWallMounted,
    EShipGameplayHardpointType RequestedType, FRandomStream& Random,
    const TArray<FVector>& OccupiedLocations, FTransform& OutTransform, FName& OutHardpointId) const
{
    if (!Room || !Room->SectionBounds || !GetWorld())
    {
        return false;
    }

    OutHardpointId = NAME_None;
    const FVector Extent = Room->SectionBounds->GetUnscaledBoxExtent();
    const float WallInset = bWallMounted ? 52.0f : 118.0f;
    const float Height = -Extent.Z + (bWallMounted ? 175.0f : 95.0f);
    const FVector CollisionExtent = bWallMounted ? FVector(62.0f, 18.0f, 72.0f)
        : FVector(82.0f, 52.0f, 80.0f);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(ActivityStationPlacement), false);
    QueryParams.AddIgnoredActor(this);

    TArray<FShipGameplayHardpoint> Hardpoints = Room->GetGameplayHardpoints(RequestedType);
    if (Hardpoints.IsEmpty() && RequestedType == EShipGameplayHardpointType::DamageRepair)
    {
        Hardpoints = Room->GetGameplayHardpoints(EShipGameplayHardpointType::Activity);
    }
    for (int32 Index = Hardpoints.Num() - 1; Index > 0; --Index)
    {
        Hardpoints.Swap(Index, Random.RandRange(0, Index));
    }
    for (const FShipGameplayHardpoint& Hardpoint : Hardpoints)
    {
        const bool bHardpointIsWall = Hardpoint.ContextTag == TEXT("WallMount")
            || Hardpoint.ContextTag == TEXT("BulkheadRepair");
        if (bWallMounted != bHardpointIsWall)
        {
            continue;
        }

        FTransform CandidateTransform;
        if (!Room->GetGameplayHardpointWorldTransform(Hardpoint.HardpointId, CandidateTransform))
        {
            continue;
        }
        const FVector WorldLocation = CandidateTransform.GetLocation();
        const bool bTooClose = OccupiedLocations.ContainsByPredicate([this, &WorldLocation](const FVector& Other)
        {
            return FVector::DistSquared2D(WorldLocation, Other) < FMath::Square(MinimumActivitySpacing);
        });
        if (bTooClose || GetWorld()->OverlapBlockingTestByChannel(WorldLocation,
            CandidateTransform.GetRotation(), ECC_WorldStatic,
            FCollisionShape::MakeBox(CollisionExtent), QueryParams))
        {
            continue;
        }

        OutTransform = CandidateTransform;
        OutHardpointId = Hardpoint.HardpointId;
        return true;
    }

    // Backward-compatible fallback for custom Blueprint rooms that predate gameplay hardpoints.
    TArray<FVector> CandidateSlots = {
        FVector(-Extent.X * 0.34f, Extent.Y - WallInset, Height),
        FVector( Extent.X * 0.34f, Extent.Y - WallInset, Height),
        FVector(-Extent.X * 0.34f,-Extent.Y + WallInset, Height),
        FVector( Extent.X * 0.34f,-Extent.Y + WallInset, Height),
        FVector( Extent.X - WallInset,-Extent.Y * 0.34f, Height),
        FVector( Extent.X - WallInset, Extent.Y * 0.34f, Height),
        FVector(-Extent.X + WallInset,-Extent.Y * 0.34f, Height),
        FVector(-Extent.X + WallInset, Extent.Y * 0.34f, Height)
    };

    for (int32 Index = CandidateSlots.Num() - 1; Index > 0; --Index)
    {
        CandidateSlots.Swap(Index, Random.RandRange(0, Index));
    }

    for (const FVector& LocalLocation : CandidateSlots)
    {
        const FVector WorldLocation = Room->GetActorTransform().TransformPosition(LocalLocation);
        const bool bTooClose = OccupiedLocations.ContainsByPredicate([this, &WorldLocation](const FVector& Other)
        {
            return FVector::DistSquared2D(WorldLocation, Other) < FMath::Square(MinimumActivitySpacing);
        });
        if (bTooClose)
        {
            continue;
        }

        FRotator Facing = (Room->GetActorLocation() - WorldLocation).Rotation();
        Facing.Pitch = 0.0f;
        Facing.Roll = 0.0f;
        if (GetWorld()->OverlapBlockingTestByChannel(WorldLocation, Facing.Quaternion(), ECC_WorldStatic,
            FCollisionShape::MakeBox(CollisionExtent), QueryParams))
        {
            continue;
        }

        OutTransform = FTransform(Facing, WorldLocation);
        return true;
    }
    return false;
}

float AProceduralShipBuilder::CalculateRoomBloomPressure(const AModularShipRoom* Room) const
{
    if (!Room)
    {
        return 0.0f;
    }

    float Pressure = FMath::Clamp(Room->GameplayProfile.HazardTier / 5.0f, 0.0f, 1.0f) * 0.2f;
    switch (Room->Archetype)
    {
    case EShipRoomArchetype::DamageControl: Pressure += 0.28f; break;
    case EShipRoomArchetype::CargoBay: Pressure += 0.18f; break;
    case EShipRoomArchetype::Engineering: Pressure += 0.42f; break;
    case EShipRoomArchetype::ReactorControl: Pressure += 0.62f; break;
    case EShipRoomArchetype::EscapeBay: Pressure += 0.12f; break;
    default: break;
    }
    if (Room->RoomCode == TEXT("ESC-S1"))
    {
        Pressure += 0.25f;
    }
    if (Room->OperationalState == EShipRoomOperationalState::BloomCorrupted)
    {
        Pressure = FMath::Max(Pressure, 0.8f);
    }
    return FMath::Clamp(Pressure, 0.0f, 1.0f);
}

void AProceduralShipBuilder::ConfigureSpawnedActivity(AActivityStation* Station, AModularShipRoom* Room,
    FRandomStream& Random, int32 SlotIndex, EActivityStationMount MountType) const
{
    if (!Station || !Room)
    {
        return;
    }

    if (AMaintenanceActivityStation* Maintenance = Cast<AMaintenanceActivityStation>(Station))
    {
        Maintenance->TargetActor = Room;
    }
    if (AOperationsActivityStation* Operation = Cast<AOperationsActivityStation>(Station))
    {
        Operation->TargetActor = Room;
    }

    const float BloomPressure = FMath::Clamp(CalculateRoomBloomPressure(Room)
        + Random.FRandRange(-0.06f, 0.16f), 0.0f, 1.0f);
    Station->Activity.MinimumBloomInterference = BloomPressure;
    Station->Activity.BloomInterferenceScale = Random.FRandRange(0.9f, 1.45f);
    Station->Activity.PuzzleSteps = FMath::Clamp(Station->Activity.PuzzleSteps + Random.RandRange(0, 2), 1, 16);
    Station->Activity.DurationSeconds *= Random.FRandRange(0.9f, 1.2f);
    if (BloomPressure >= 0.65f)
    {
        Station->Activity.AllowedMistakes = FMath::Max(1, Station->Activity.AllowedMistakes - 1);
    }

    const bool bBioscan = Station->Activity.Mechanic == EActivityMechanic::GenomeSequence;
    const bool bRewiring = Station->Activity.Mechanic == EActivityMechanic::CableMatching;

    EActivityStationCondition StationCondition = EActivityStationCondition::Serviceable;
    float ConditionPercent = Random.FRandRange(0.72f, 0.98f);
    const float ConditionRoll = Random.FRand();
    if (BloomPressure >= 0.78f)
    {
        StationCondition = EActivityStationCondition::BloomOverrun;
        ConditionPercent = Random.FRandRange(0.18f, 0.42f);
    }
    else if (BloomPressure >= 0.42f && ConditionRoll < 0.62f)
    {
        StationCondition = EActivityStationCondition::BloomTouched;
        ConditionPercent = Random.FRandRange(0.35f, 0.68f);
    }
    else if (ConditionRoll < 0.12f)
    {
        StationCondition = EActivityStationCondition::Faulted;
        ConditionPercent = Random.FRandRange(0.22f, 0.48f);
    }
    else if (ConditionRoll < 0.38f)
    {
        StationCondition = EActivityStationCondition::Worn;
        ConditionPercent = Random.FRandRange(0.48f, 0.74f);
    }
    else if (ConditionRoll > 0.92f)
    {
        StationCondition = EActivityStationCondition::Pristine;
        ConditionPercent = Random.FRandRange(0.96f, 1.0f);
    }

    EActivityStationRarity StationRarity = EActivityStationRarity::Routine;
    if (StationCondition == EActivityStationCondition::BloomOverrun
        || Station->Activity.Type == EPlayerActivityType::BloomPurging)
    {
        StationRarity = EActivityStationRarity::Anomalous;
    }
    else if (Station->Activity.Type == EPlayerActivityType::ReactorStartup
        || Station->Activity.Type == EPlayerActivityType::MedicalStabilization)
    {
        StationRarity = EActivityStationRarity::Critical;
    }
    else if (bBioscan || bRewiring)
    {
        StationRarity = EActivityStationRarity::Specialized;
    }

    int32 RemainingUses = Random.RandRange(3, 6);
    if (StationRarity == EActivityStationRarity::Specialized) RemainingUses = Random.RandRange(2, 4);
    else if (StationRarity == EActivityStationRarity::Critical) RemainingUses = Random.RandRange(1, 2);
    else if (StationRarity == EActivityStationRarity::Anomalous) RemainingUses = 1;
    Station->CooldownSeconds = Random.FRandRange(8.0f, 22.0f);

    const int32 RoomSeed = HashCombine(ActivityPopulationSeed, GetTypeHash(Room->RoomCode));
    const FName StableId(*FString::Printf(TEXT("%s-ACT-%08X-%02d"), *Room->RoomCode.ToString(),
        static_cast<uint32>(RoomSeed), SlotIndex));
    Station->ConfigureProceduralStation(StableId, Room->RoomCode, RoomSeed, SlotIndex, MountType,
        StationCondition, StationRarity, ConditionPercent, RemainingUses);

    UStaticMesh* VisualMesh = bBioscan ? BioscanStationMesh : (bRewiring ? RewiringPanelMesh : nullptr);
    if (!VisualMesh)
    {
        VisualMesh = CubeMesh;
    }
    Station->Mesh->SetStaticMesh(VisualMesh);
    Station->Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Station->Mesh->SetCollisionProfileName(TEXT("BlockAll"));
    Station->Mesh->SetGenerateOverlapEvents(false);

    if (VisualMesh == CubeMesh)
    {
        const FVector ProxySize = bBioscan ? FVector(180.0f, 85.0f, 180.0f)
            : (bRewiring ? FVector(135.0f, 30.0f, 165.0f) : FVector(125.0f, 65.0f, 135.0f));
        Station->Mesh->SetRelativeScale3D(ProxySize / 100.0f);
        Station->Mesh->SetMaterial(0, BloomPressure >= 0.7f && BloomMaterial ? BloomMaterial
            : (bRewiring && HullMaterial ? HullMaterial : AccentMaterial));
    }
    else
    {
        Station->Mesh->SetRelativeScale3D(FVector::OneVector);
        Station->Mesh->SetRelativeLocation(FVector(0.0f, 0.0f, bBioscan ? -95.0f : -155.0f));
    }

    Station->Tags.AddUnique(TEXT("ProceduralActivity"));
    Station->Tags.AddUnique(Room->RoomCode);
    Station->Tags.AddUnique(bBioscan ? TEXT("BioscanStation")
        : (bRewiring ? TEXT("RewiringPanel") : TEXT("MaintenanceStation")));
    Station->Tags.AddUnique(FName(*FString::Printf(TEXT("BloomTier_%d"), FMath::RoundToInt(BloomPressure * 5.0f))));
}

void AProceduralShipBuilder::PopulateActivityStations()
{
    if (!bPopulateActivityStations || !HasAuthority() || !GetWorld())
    {
        return;
    }

    SpawnedActivityStations.RemoveAll([](const TObjectPtr<AActivityStation>& Station)
    {
        return !IsValid(Station);
    });
    if (!SpawnedActivityStations.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("Activity population skipped; this ship already has %d stations."),
            SpawnedActivityStations.Num());
        return;
    }

    ActivityPopulationManifest.Reset();

    const int32 Minimum = FMath::Clamp(MinActivitiesPerRoom, 0, MaxActivitiesPerRoom);
    const int32 Maximum = FMath::Max(Minimum, MaxActivitiesPerRoom);
    int32 TotalSpawned = 0;
    for (AModularShipRoom* Room : SpawnedRooms)
    {
        if (!Room)
        {
            continue;
        }

        TArray<TSubclassOf<AActivityStation>> Pool = GetActivityClassesForRoom(Room->Archetype);
        if (Pool.IsEmpty())
        {
            continue;
        }

        FRandomStream Random(HashCombine(ActivityPopulationSeed, GetTypeHash(Room->RoomCode)));
        for (int32 Index = Pool.Num() - 1; Index > 0; --Index)
        {
            Pool.Swap(Index, Random.RandRange(0, Index));
        }

        int32 DesiredCount = Minimum;
        for (int32 Extra = Minimum; Extra < Maximum; ++Extra)
        {
            if (Random.FRand() <= ActivitySpawnChance)
            {
                ++DesiredCount;
            }
        }

        TArray<FVector> OccupiedLocations;
        for (int32 StationIndex = 0; StationIndex < DesiredCount; ++StationIndex)
        {
            const TSubclassOf<AActivityStation> StationClass = Pool[StationIndex % Pool.Num()];
            const AActivityStation* Defaults = StationClass->GetDefaultObject<AActivityStation>();
            const bool bWallMounted = Defaults
                && Defaults->Activity.Mechanic == EActivityMechanic::CableMatching;
            EActivityStationMount MountType = bWallMounted ? EActivityStationMount::WallPanel
                : EActivityStationMount::FloorConsole;
            if (Defaults && Defaults->Activity.Mechanic == EActivityMechanic::ToolPath)
            {
                MountType = EActivityStationMount::Workbench;
            }
            const EShipGameplayHardpointType RequestedType = StationClass->IsChildOf(
                AMaintenanceActivityStation::StaticClass())
                ? EShipGameplayHardpointType::DamageRepair
                : EShipGameplayHardpointType::Activity;
            FTransform SpawnTransform;
            FName HardpointId = NAME_None;
            if (!FindActivitySpawnTransform(Room, bWallMounted, RequestedType, Random,
                OccupiedLocations, SpawnTransform, HardpointId))
            {
                UE_LOG(LogTemp, Verbose, TEXT("No clear activity slot remained in %s."), *Room->RoomCode.ToString());
                continue;
            }

            FActorSpawnParameters SpawnParameters;
            SpawnParameters.Owner = Room;
            SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            AActivityStation* Station = GetWorld()->SpawnActor<AActivityStation>(
                StationClass, SpawnTransform, SpawnParameters);
            if (!Station)
            {
                continue;
            }

            ConfigureSpawnedActivity(Station, Room, Random, StationIndex, MountType);
            Station->AttachToActor(Room, FAttachmentTransformRules::KeepWorldTransform);
            if (!HardpointId.IsNone())
            {
                Room->SetGameplayHardpointReserved(HardpointId, true);
            }
            OccupiedLocations.Add(Station->GetActorLocation());
            SpawnedActivityStations.Add(Station);

            FProceduralActivitySpawnRecord& Record = ActivityPopulationManifest.AddDefaulted_GetRef();
            Record.StationId = Station->StationId;
            Record.RoomCode = Room->RoomCode;
            Record.StationClass = StationClass;
            Record.SpawnTransform = SpawnTransform;
            Record.Mount = Station->MountType;
            Record.Condition = Station->Condition;
            Record.Rarity = Station->Rarity;
            Record.ConditionPercent = Station->ConditionPercent;
            Record.BloomPressure = Station->Activity.MinimumBloomInterference;
            Record.PopulationSeed = Station->PopulationSeed;
            Record.SlotIndex = StationIndex;
            ++TotalSpawned;
        }
    }

    UE_LOG(LogTemp, Display, TEXT("Procedurally populated %d activity stations across %d ship rooms (seed %d)."),
        TotalSpawned, SpawnedRooms.Num(), ActivityPopulationSeed);
}

AActivityStation* AProceduralShipBuilder::FindActivityStationById(FName StationId) const
{
    if (StationId.IsNone()) return nullptr;
    for (AActivityStation* Station : SpawnedActivityStations)
    {
        if (IsValid(Station) && Station->StationId == StationId) return Station;
    }
    return nullptr;
}

TArray<AActivityStation*> AProceduralShipBuilder::GetActivityStationsForRoom(FName RoomCode) const
{
    TArray<AActivityStation*> Result;
    for (AActivityStation* Station : SpawnedActivityStations)
    {
        if (IsValid(Station) && Station->OwningRoomCode == RoomCode) Result.Add(Station);
    }
    return Result;
}

bool AProceduralShipBuilder::ValidateActivityPopulation(TArray<FString>& OutErrors) const
{
    OutErrors.Reset();
    TSet<FName> SeenIds;
    for (const FProceduralActivitySpawnRecord& Record : ActivityPopulationManifest)
    {
        if (!Record.IsValid())
        {
            OutErrors.Add(TEXT("Activity population contains an incomplete spawn record."));
            continue;
        }
        if (SeenIds.Contains(Record.StationId))
            OutErrors.Add(FString::Printf(TEXT("Duplicate activity station id: %s"), *Record.StationId.ToString()));
        SeenIds.Add(Record.StationId);

        const AModularShipRoom* Room = FindBuiltRoom(Record.RoomCode);
        if (!Room)
            OutErrors.Add(FString::Printf(TEXT("Activity %s references missing room %s."),
                *Record.StationId.ToString(), *Record.RoomCode.ToString()));
        else if (!Room->ContainsPoint(Record.SpawnTransform.GetLocation()))
            OutErrors.Add(FString::Printf(TEXT("Activity %s lies outside room %s."),
                *Record.StationId.ToString(), *Record.RoomCode.ToString()));
        if (!FindActivityStationById(Record.StationId))
            OutErrors.Add(FString::Printf(TEXT("Activity record %s has no live actor."), *Record.StationId.ToString()));
    }

    for (int32 A = 0; A < ActivityPopulationManifest.Num(); ++A)
    {
        for (int32 B = A + 1; B < ActivityPopulationManifest.Num(); ++B)
        {
            const FProceduralActivitySpawnRecord& Left = ActivityPopulationManifest[A];
            const FProceduralActivitySpawnRecord& Right = ActivityPopulationManifest[B];
            if (Left.RoomCode == Right.RoomCode
                && FVector::DistSquared2D(Left.SpawnTransform.GetLocation(), Right.SpawnTransform.GetLocation())
                    < FMath::Square(MinimumActivitySpacing - 1.0f))
            {
                OutErrors.Add(FString::Printf(TEXT("Activities %s and %s violate minimum spacing."),
                    *Left.StationId.ToString(), *Right.StationId.ToString()));
            }
        }
    }
    return OutErrors.IsEmpty();
}

FString AProceduralShipBuilder::GetActivityPopulationSummary() const
{
    int32 Bioscans = 0, Rewiring = 0, BloomAffected = 0, Depleted = 0;
    TSet<FName> PopulatedRooms;
    for (const AActivityStation* Station : SpawnedActivityStations)
    {
        if (!IsValid(Station)) continue;
        PopulatedRooms.Add(Station->OwningRoomCode);
        if (Station->Activity.Mechanic == EActivityMechanic::GenomeSequence) ++Bioscans;
        if (Station->Activity.Mechanic == EActivityMechanic::CableMatching) ++Rewiring;
        if (Station->Condition == EActivityStationCondition::BloomTouched
            || Station->Condition == EActivityStationCondition::BloomOverrun) ++BloomAffected;
        if (!Station->bEnabled || Station->RemainingUses == 0) ++Depleted;
    }
    return FString::Printf(TEXT("%d stations / %d rooms / %d bioscan / %d rewiring / %d Bloom-affected / %d depleted / seed %d"),
        SpawnedActivityStations.Num(), PopulatedRooms.Num(), Bioscans, Rewiring, BloomAffected, Depleted,
        ActivityPopulationSeed);
}

void AProceduralShipBuilder::AddBloomCluster(AShipSection* Section, const FVector& RelativeLocation,
    const FRotator& Rotation, float Scale)
{
    if (!Section || !BloomMaterial) return;
    AddPrimitive(Section, SphereMesh, RelativeLocation, FVector(260, 210, 45) * Scale, Rotation, BloomMaterial, false);
    for (int32 i = 0; i < 5; ++i)
    {
        const float Angle = i * 72.0f + 13.0f;
        const FVector TendrilOffset(FMath::Cos(FMath::DegreesToRadians(Angle)) * 120.0f * Scale,
            FMath::Sin(FMath::DegreesToRadians(Angle)) * 100.0f * Scale, 18.0f * i);
        AddPrimitive(Section, CylinderMesh, RelativeLocation + TendrilOffset, FVector(190, 12, 12) * Scale,
            FRotator(0, Angle, 88), BloomMaterial, false);
    }
    UPointLightComponent* Glow = NewObject<UPointLightComponent>(Section);
    Glow->SetupAttachment(Section->GetRootComponent());
    Glow->SetRelativeLocation(RelativeLocation + FVector(0, 0, 35));
    Glow->SetLightColor(FColor(95, 20, 180));
    Glow->SetIntensity(700.0f * Scale);
    Glow->SetAttenuationRadius(330.0f * Scale);
    Glow->SetCastShadows(false);
    Glow->RegisterComponent();
}

void AProceduralShipBuilder::SpawnCrewCorpse(AShipSection* Section, const FVector& RelativeLocation,
    const FRotator& Rotation, bool bBloomCovered)
{
    UWorld* World = GetWorld();
    if (!World || !Section || !CrewMesh) return;
    FActorSpawnParameters SpawnParameters;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACrewCorpse* Corpse = World->SpawnActor<ACrewCorpse>(ACrewCorpse::StaticClass(),
        Section->GetActorTransform().TransformPosition(RelativeLocation), Rotation, SpawnParameters);
    if (!Corpse) return;
    Corpse->Tags.Add(TEXT("DamagedSpaceSuit"));
    Corpse->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (USkeletalMeshComponent* Mesh = Corpse->GetMesh())
    {
        // ACrewCorpse enables ragdoll physics by default. Pause it while changing the authored
        // mesh transform, then re-enable it after setup to avoid moving a simulated body.
        Mesh->SetSimulatePhysics(false);
        Mesh->SetSkeletalMeshAsset(CrewMesh);
        Mesh->SetRelativeLocation(FVector(0, 0, -88));
        Mesh->SetRelativeRotation(FRotator(0, -90, 0));
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
            Mesh->SetMaterial(Slot, bBloomCovered ? BloomMaterial : SpaceSuitMaterial);
        Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Mesh->SetSimulatePhysics(true);
    }
    if (bBloomCovered)
        AddBloomCluster(Section, RelativeLocation + FVector(0, 0, -245), FRotator::ZeroRotator, 0.7f);
}

void AProceduralShipBuilder::AddRoomDetails(AShipSection* Section, const FString& RoomName, const FLinearColor& AccentColor)
{
    if (!Section) return;
    const FVector E = Section->SectionBounds->GetUnscaledBoxExtent();

    // Armored ribs, waist-height storage/cover, and a glowing tactical console give each room
    // readable military scale and break up the grid materials.
    for (float X : { -E.X * .65f, E.X * .65f })
    {
        AddBox(Section, FVector(X, -E.Y + 45, 0), FVector(28, 70, E.Z * 1.8f), AccentMaterial);
        AddBox(Section, FVector(X, E.Y - 45, 0), FVector(28, 70, E.Z * 1.8f), AccentMaterial);
    }
    AddBox(Section, FVector(E.X * .35f, E.Y * .35f, -E.Z + 55), FVector(180, 110, 110), DeckMaterial);
    AddBox(Section, FVector(-E.X * .35f, -E.Y * .35f, -E.Z + 55), FVector(140, 100, 110), DeckMaterial);
    UStaticMeshComponent* Console = AddBox(Section, FVector(0, E.Y * .45f, -E.Z + 90), FVector(190, 70, 180), AccentMaterial);
    if (Console && AccentMaterial)
    {
        UMaterialInstanceDynamic* MID = Console->CreateAndSetMaterialInstanceDynamic(0);
        if (MID)
        {
            MID->SetVectorParameterValue(TEXT("Color"), AccentColor);
            MID->SetVectorParameterValue(TEXT("BaseColor"), AccentColor);
        }
    }

    UPointLightComponent* Light = NewObject<UPointLightComponent>(Section);
    Light->SetupAttachment(Section->GetRootComponent());
    Light->SetRelativeLocation(FVector(0, 0, E.Z - 70));
    Light->SetLightColor(AccentColor.ToFColorSRGB());
    Light->SetIntensity(2800.0f);
    Light->SetAttenuationRadius(FMath::Max(E.X, E.Y) * 1.4f);
    Light->SetCastShadows(false);
    Light->RegisterComponent();
    Section->Tags.AddUnique(FName(*RoomName));
}

AShipSection* AProceduralShipBuilder::AddCorridor(const FVector& Start, const FVector& End,
    int32 SectionID, FName CorridorCode)
{
    const FVector Delta = End - Start;
    const float Length = Delta.Size2D();
    UWorld* World = GetWorld();
    if (!World || Length < 10.0f)
    {
        return nullptr;
    }

    const FVector Mid = (Start + End) * .5f;
    const FRotator Rotation = Delta.Rotation();
    AShipSection* Corridor = World->SpawnActor<AShipSection>(AShipSection::StaticClass(), Mid, Rotation);
    if (!Corridor)
    {
        return nullptr;
    }

    Corridor->SectionID = SectionID;
    Corridor->SectionType = EShipSectionType::Corridor;
    Corridor->Tags.AddUnique(TEXT("GeneratedShipCorridor"));
    Corridor->Tags.AddUnique(CorridorCode);
    Corridor->SectionBounds->SetBoxExtent(FVector(Length * 0.5f, CorridorWidth * 0.5f, CorridorHeight * 0.5f));

    const float HalfHeight = CorridorHeight * 0.5f;
    AddBox(Corridor, FVector(0, 0, -HalfHeight), FVector(Length, CorridorWidth, 24), DeckMaterial);
    AddBox(Corridor, FVector(0, 0, HalfHeight), FVector(Length, CorridorWidth, 24), HullMaterial);
    for (float Side : { -1.0f, 1.0f })
    {
        AddBox(Corridor, FVector(0, Side * CorridorWidth * 0.5f, 0),
            FVector(Length, 24, CorridorHeight), HullMaterial);
    }

    PopulateCorridorGameplayHardpoints(Corridor, CorridorCode, Length);
    SpawnedCorridors.Add(Corridor);
    return Corridor;
}

void AProceduralShipBuilder::PopulateCorridorGameplayHardpoints(AShipSection* Corridor,
    FName CorridorCode, float Length)
{
    if (!Corridor)
    {
        return;
    }

    int32 Sequence = 0;
    auto Add = [Corridor, CorridorCode, &Sequence](EShipGameplayHardpointType Type, const FVector& Location,
        const FRotator& Rotation, float Clearance, FName Context)
    {
        FShipGameplayHardpoint Hardpoint;
        Hardpoint.HardpointId = FName(*FString::Printf(TEXT("%s-HP-%02d"), *CorridorCode.ToString(), Sequence++));
        Hardpoint.HardpointType = Type;
        Hardpoint.RelativeLocation = Location;
        Hardpoint.RelativeRotation = Rotation;
        Hardpoint.ClearanceRadius = Clearance;
        Hardpoint.ContextTag = Context;
        Corridor->AddGameplayHardpoint(Hardpoint);
    };

    const float FloorZ = -CorridorHeight * 0.5f + 24.0f;
    Add(EShipGameplayHardpointType::Doorway, FVector(-Length * 0.5f, 0, 0),
        FRotator::ZeroRotator, 145.0f, TEXT("RoomThreshold"));
    Add(EShipGameplayHardpointType::Doorway, FVector(Length * 0.5f, 0, 0),
        FRotator(0, 180, 0), 145.0f, TEXT("RoomThreshold"));
    Add(EShipGameplayHardpointType::Body, FVector(-Length * 0.18f, -CorridorWidth * 0.16f, FloorZ),
        FRotator(0, 15, 0), 95.0f, TEXT("CorridorBody"));
    Add(EShipGameplayHardpointType::Obstacle, FVector(Length * 0.12f, CorridorWidth * 0.10f, FloorZ),
        FRotator(0, 90, 0), 115.0f, TEXT("PartialBlocker"));
    Add(EShipGameplayHardpointType::BloomGrowth, FVector(0, -CorridorWidth * 0.38f, FloorZ),
        FRotator::ZeroRotator, 90.0f, TEXT("WallFloorGrowth"));
    Add(EShipGameplayHardpointType::Activity, FVector(Length * 0.24f, CorridorWidth * 0.38f, FloorZ + 150.0f),
        FRotator(0, -90, 0), 80.0f, TEXT("WallMount"));
    Add(EShipGameplayHardpointType::DamageRepair, FVector(-Length * 0.24f, -CorridorWidth * 0.38f, FloorZ + 150.0f),
        FRotator(0, 90, 0), 80.0f, TEXT("UtilityRepair"));
}

ABulkheadDoor* AProceduralShipBuilder::ConnectSections(AShipSection* A, AShipSection* B, const FVector& DoorLocation,
    const FRotator& DoorRotation, float TransferCoefficient)
{
    UWorld* World = GetWorld();
    if (!World || !A || !B)
    {
        return nullptr;
    }

    ABulkheadDoor* Door = World->SpawnActor<ABulkheadDoor>(ABulkheadDoor::StaticClass(), DoorLocation, DoorRotation);

    FSectionConnection AToB;
    AToB.Target = B;
    AToB.Door = Door;
    AToB.TransferCoefficient = TransferCoefficient;
    A->Connections.Add(AToB);

    FSectionConnection BToA;
    BToA.Target = A;
    BToA.Door = Door;
    BToA.TransferCoefficient = TransferCoefficient;
    B->Connections.Add(BToA);
    return Door;
}

bool AProceduralShipBuilder::ConnectRoomModules(AModularShipRoom* A, EShipRoomSocket ASocket,
    AModularShipRoom* B, EShipRoomSocket BSocket, float TransferCoefficient)
{
    if (!A || !B)
    {
        return false;
    }

    if (!A->ConnectRoom(ASocket, B, BSocket))
    {
        UE_LOG(LogTemp, Warning, TEXT("Could not connect room modules %s and %s: selected socket is disabled or occupied."),
            *A->RoomCode.ToString(), *B->RoomCode.ToString());
        return false;
    }

    const FVector APortal = A->GetBulkheadSocketTransform(ASocket).GetLocation();
    const FVector BPortal = B->GetBulkheadSocketTransform(BSocket).GetLocation();
    const FName CorridorCode(*FString::Printf(TEXT("COR-%s-%s"), *A->RoomCode.ToString(), *B->RoomCode.ToString()));
    AShipSection* Corridor = AddCorridor(APortal, BPortal,
        RoomModules.Num() + SpawnedCorridors.Num(), CorridorCode);
    if (!Corridor)
    {
        A->DisconnectRoom(ASocket);
        return false;
    }

    auto AddDoorwayHardpoint = [](AModularShipRoom* Room, EShipRoomSocket Socket, const FVector& Portal)
    {
        FShipGameplayHardpoint Hardpoint;
        Hardpoint.HardpointId = FName(*FString::Printf(TEXT("%s-DOOR-%d"),
            *Room->RoomCode.ToString(), static_cast<int32>(Socket)));
        Hardpoint.HardpointType = EShipGameplayHardpointType::Doorway;
        Hardpoint.RelativeLocation = Room->GetActorTransform().InverseTransformPosition(Portal);
        Hardpoint.RelativeRotation = Room->GetBulkheadSocket(Socket)->GetRelativeRotation();
        Hardpoint.ClearanceRadius = 145.0f;
        Hardpoint.ContextTag = TEXT("RoomThreshold");
        Room->AddGameplayHardpoint(Hardpoint);
    };
    AddDoorwayHardpoint(A, ASocket, APortal);
    AddDoorwayHardpoint(B, BSocket, BPortal);

    const FVector Direction = (BPortal - APortal).GetSafeNormal2D();
    ABulkheadDoor* DoorA = ConnectSections(A, Corridor, APortal, Direction.Rotation(), TransferCoefficient);
    ABulkheadDoor* DoorB = ConnectSections(Corridor, B, BPortal, (-Direction).Rotation(), TransferCoefficient);
    if (DoorA) DoorA->ConfigureThresholdSides(A, Corridor);
    if (DoorB) DoorB->ConfigureThresholdSides(B, Corridor);
    return true;
}

AModularShipRoom* AProceduralShipBuilder::FindBuiltRoom(FName RoomCode) const
{
    for (AModularShipRoom* Room : SpawnedRooms)
    {
        if (IsValid(Room) && Room->RoomCode == RoomCode)
        {
            return Room;
        }
    }
    return nullptr;
}

bool AProceduralShipBuilder::ValidateLayout(TArray<FString>& OutErrors) const
{
    OutErrors.Reset();
    TSet<FName> Codes;
    TSet<int32> NumericRoomIds;
    for (const FShipRoomModuleDefinition& Room : RoomModules)
    {
        FString Error;
        if (!Room.IsValid(&Error))
        {
            OutErrors.Add(Error);
        }
        if (Codes.Contains(Room.RoomCode))
        {
            OutErrors.Add(FString::Printf(TEXT("Duplicate room code %s."), *Room.RoomCode.ToString()));
        }
        Codes.Add(Room.RoomCode);
        if (Room.RoomId > 0)
        {
            if (NumericRoomIds.Contains(Room.RoomId))
            {
                OutErrors.Add(FString::Printf(TEXT("Duplicate numeric room id %d."), Room.RoomId));
            }
            NumericRoomIds.Add(Room.RoomId);
        }
    }

    const FName RequiredCorvetteRooms[] = { TEXT("BRG-01"), TEXT("CIC-01"), TEXT("SNS-01"),
        TEXT("ARM-01"), TEXT("CMP-01"), TEXT("MED-01"), TEXT("CRW-01"), TEXT("DCR-01"),
        TEXT("CGO-01"), TEXT("ENG-01"), TEXT("RCT-01"), TEXT("ESC-P1"), TEXT("ESC-S1") };
    for (const FName RequiredCode : RequiredCorvetteRooms)
    {
        if (!Codes.Contains(RequiredCode))
        {
            OutErrors.Add(FString::Printf(TEXT("Corvette gameplay requires room %s."), *RequiredCode.ToString()));
        }
    }

    TSet<FString> UsedSockets;
    TMap<FName, TArray<FName>> Adjacency;
    for (const FShipRoomConnectionDefinition& Connection : RoomConnections)
    {
        FString Error;
        if (!Connection.IsValid(&Error))
        {
            OutErrors.Add(Error);
            continue;
        }
        if (!Codes.Contains(Connection.RoomA) || !Codes.Contains(Connection.RoomB))
        {
            OutErrors.Add(FString::Printf(TEXT("Connection %s -> %s references an unknown room."),
                *Connection.RoomA.ToString(), *Connection.RoomB.ToString()));
        }
        const FString EndpointA = FString::Printf(TEXT("%s:%d"), *Connection.RoomA.ToString(), static_cast<int32>(Connection.SocketA));
        const FString EndpointB = FString::Printf(TEXT("%s:%d"), *Connection.RoomB.ToString(), static_cast<int32>(Connection.SocketB));
        for (const FString& Endpoint : { EndpointA, EndpointB })
        {
            if (UsedSockets.Contains(Endpoint))
            {
                OutErrors.Add(FString::Printf(TEXT("Socket %s is assigned more than once."), *Endpoint));
            }
            UsedSockets.Add(Endpoint);
        }
        Adjacency.FindOrAdd(Connection.RoomA).Add(Connection.RoomB);
        Adjacency.FindOrAdd(Connection.RoomB).Add(Connection.RoomA);
    }

    if (!RoomModules.IsEmpty())
    {
        TSet<FName> Visited;
        TArray<FName> Pending = { RoomModules[0].RoomCode };
        while (!Pending.IsEmpty())
        {
            const FName Current = Pending.Pop(EAllowShrinking::No);
            if (Visited.Contains(Current))
            {
                continue;
            }
            Visited.Add(Current);
            for (const FName Neighbor : Adjacency.FindRef(Current))
            {
                Pending.Add(Neighbor);
            }
        }
        for (const FShipRoomModuleDefinition& Room : RoomModules)
        {
            if (!Visited.Contains(Room.RoomCode))
            {
                OutErrors.Add(FString::Printf(TEXT("Room %s is disconnected from the layout graph."), *Room.RoomCode.ToString()));
            }
        }
    }

    for (int32 LeftIndex = 0; LeftIndex < RoomModules.Num(); ++LeftIndex)
    {
        const FShipRoomModuleDefinition& Left = RoomModules[LeftIndex];
        if (Left.RoomTypeId <= 0)
        {
            continue;
        }
        for (int32 RightIndex = LeftIndex + 1; RightIndex < RoomModules.Num(); ++RightIndex)
        {
            const FShipRoomModuleDefinition& Right = RoomModules[RightIndex];
            if (Left.RoomTypeId != Right.RoomTypeId)
            {
                continue;
            }
            const bool bClusterAllowed = Left.bAllowSameTypeClusterInSection
                && Right.bAllowSameTypeClusterInSection
                && !Left.PlacementSection.IsNone()
                && Left.PlacementSection == Right.PlacementSection;
            if (bClusterAllowed)
            {
                continue;
            }

            const int32 MinimumDistance = FMath::Max(
                Left.SameTypeExclusionDistance, Right.SameTypeExclusionDistance);
            TSet<FName> VisitedForDistance;
            TArray<TPair<FName, int32>> PendingForDistance;
            PendingForDistance.Emplace(Left.RoomCode, 0);
            int32 GraphDistance = INDEX_NONE;
            while (!PendingForDistance.IsEmpty())
            {
                const TPair<FName, int32> Current = PendingForDistance[0];
                PendingForDistance.RemoveAt(0, 1, EAllowShrinking::No);
                if (VisitedForDistance.Contains(Current.Key))
                {
                    continue;
                }
                if (Current.Key == Right.RoomCode)
                {
                    GraphDistance = Current.Value;
                    break;
                }
                VisitedForDistance.Add(Current.Key);
                for (const FName Neighbor : Adjacency.FindRef(Current.Key))
                {
                    PendingForDistance.Emplace(Neighbor, Current.Value + 1);
                }
            }
            if (GraphDistance != INDEX_NONE && GraphDistance < MinimumDistance)
            {
                OutErrors.Add(FString::Printf(
                    TEXT("Rooms %s and %s share type %d at graph distance %d; minimum is %d."),
                    *Left.RoomCode.ToString(), *Right.RoomCode.ToString(), Left.RoomTypeId,
                    GraphDistance, MinimumDistance));
            }
        }
    }
    return OutErrors.IsEmpty();
}

void AProceduralShipBuilder::BuildShip()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    if (bHasBuiltShip)
    {
        UE_LOG(LogTemp, Warning, TEXT("BuildShip ignored because this builder has already created a ship."));
        return;
    }

    TArray<FString> LayoutErrors;
    if (!ValidateLayout(LayoutErrors))
    {
        for (const FString& Error : LayoutErrors)
        {
            UE_LOG(LogTemp, Error, TEXT("Invalid modular ship layout: %s"), *Error);
        }
        return;
    }

    // Raise the deck above the template map's ground plane. Room floors sit 300uu below their
    // section origin, so this offset exposes the authored non-slip deck instead of the map's
    // prototype checker surface.
    const FVector Origin = GetActorLocation() + FVector(0, 0, 320);
    SpawnedRooms.Reset();
    SpawnedCorridors.Reset();
    for (int32 i = 0; i < RoomModules.Num(); ++i)
    {
        const FShipRoomModuleDefinition& Definition = RoomModules[i];
        FString ValidationError;
        if (!Definition.IsValid(&ValidationError))
        {
            UE_LOG(LogTemp, Error, TEXT("Skipping invalid room module: %s"), *ValidationError);
            continue;
        }
        AModularShipRoom* Section = SpawnRoomModule(i, Definition.RoomCode, Definition.DisplayName,
            Definition.Archetype, Definition.SectionType, Origin + Definition.RelativeLocation, Definition.ModuleSize * 0.5);
        if (Section)
        {
            Section->ConfigurePlacementIdentity(Definition.RoomId, Definition.RoomTypeId,
                Definition.PlacementSection, Definition.SameTypeExclusionDistance,
                Definition.bAllowSameTypeClusterInSection);
        }
        SpawnedRooms.Add(Section);
        if (Definition.RoomCode != TEXT("MED-01"))
        {
            AddRoomDetails(Section, Definition.DisplayName.ToString(), Definition.AccentColor);
            AddShipProps(Section, Definition.DisplayName.ToString());
        }
    }

    for (const FShipRoomConnectionDefinition& Connection : RoomConnections)
    {
        ConnectRoomModules(FindBuiltRoom(Connection.RoomA), Connection.SocketA,
            FindBuiltRoom(Connection.RoomB), Connection.SocketB, Connection.TransferCoefficient);
    }

    AModularShipRoom* const Bridge = FindBuiltRoom(TEXT("BRG-01"));
    AModularShipRoom* const Armory = FindBuiltRoom(TEXT("ARM-01"));
    AModularShipRoom* const Medical = FindBuiltRoom(TEXT("MED-01"));
    AModularShipRoom* const DamageControl = FindBuiltRoom(TEXT("DCR-01"));
    AModularShipRoom* const Cargo = FindBuiltRoom(TEXT("CGO-01"));
    AModularShipRoom* const Engineering = FindBuiltRoom(TEXT("ENG-01"));
    AModularShipRoom* const Reactor = FindBuiltRoom(TEXT("RCT-01"));
    AModularShipRoom* const StarboardEscape = FindBuiltRoom(TEXT("ESC-S1"));

    // Environmental storytelling: a failed damage-control response becomes progressively worse
    // toward the aft reactor. The corpse actors retain their BloomHost gameplay behavior.
    SpawnCrewCorpse(Armory, FVector(130, -80, -180), FRotator(0, 25, 90), false);
    SpawnCrewCorpse(Medical, FVector(-170, -40, -180), FRotator(0, -35, 90), false);
    SpawnCrewCorpse(DamageControl, FVector(180, 20, -180), FRotator(0, 70, 90), true);
    SpawnCrewCorpse(Cargo, FVector(-60, 80, -180), FRotator(0, -15, 90), false);
    SpawnCrewCorpse(Engineering, FVector(120, 40, -180), FRotator(0, 110, 90), true);
    SpawnCrewCorpse(Reactor, FVector(-120, -60, -180), FRotator(0, 160, 90), true);
    SpawnCrewCorpse(StarboardEscape, FVector(170, -20, -180), FRotator(0, 45, 90), true);

    AddBloomCluster(DamageControl, FVector(-430, 330, -250), FRotator::ZeroRotator, 0.7f);
    AddBloomCluster(Cargo, FVector(360, -300, -245), FRotator::ZeroRotator, 0.85f);
    AddBloomCluster(Engineering, FVector(-380, 360, -235), FRotator::ZeroRotator, 1.15f);
    AddBloomCluster(Engineering, FVector(520, 0, 20), FRotator(0, 90, 0), 0.9f);
    AddBloomCluster(Reactor, FVector(0, -420, 60), FRotator(90, 0, 0), 1.35f);
    AddBloomCluster(Reactor, FVector(330, 250, -230), FRotator::ZeroRotator, 1.1f);
    AddBloomCluster(StarboardEscape, FVector(-330, 320, -245), FRotator::ZeroRotator, 0.75f);

    // Broad corrupted machinery faces make the infestation read from corridor sightlines.
    AddBox(Engineering, FVector(-260, 250, -80), FVector(190, 190, 335), BloomMaterial, false);
    AddBox(Reactor, FVector(270, 0, -130), FVector(120, 120, 245), BloomMaterial, false);

    AShipSection* const JumpBay = Bridge;
    AShipSection* const SensorBay = FindBuiltRoom(TEXT("SNS-01"));
    AShipSection* const CryoBay = Medical;
    AShipSection* const LifeSupportBay = Engineering;
    AShipSection* const CargoBay = Cargo;
    AShipSection* const EscapeBay = FindBuiltRoom(TEXT("ESC-P1"));

    if (CryoBay)
    {
        AddAuthoredCryoRoom(Cast<AModularShipRoom>(CryoBay));
    }

    if (LifeSupportBay)
    {
        World->SpawnActor<ALifeSupportSystem>(ALifeSupportSystem::StaticClass(), LifeSupportBay->GetActorLocation(), FRotator::ZeroRotator);
    }

    if (SensorBay)
    {
        World->SpawnActor<ASensorArraySystem>(ASensorArraySystem::StaticClass(), SensorBay->GetActorLocation(), FRotator::ZeroRotator);
    }

    if (JumpBay)
    {
        World->SpawnActor<AJumpConsoleSystem>(AJumpConsoleSystem::StaticClass(), JumpBay->GetActorLocation(), FRotator::ZeroRotator);
    }

    if (CargoBay)
    {
        const FVector CargoLocation = CargoBay->GetActorLocation();

        ADormantCollectorSystem* Collector = World->SpawnActor<ADormantCollectorSystem>(
            ADormantCollectorSystem::StaticClass(), CargoLocation + FVector(100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);

        AResourceNodeActor* ReactivationNode = World->SpawnActor<AResourceNodeActor>(
            AResourceNodeActor::StaticClass(), CargoLocation - FVector(100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
        if (ReactivationNode)
        {
            ReactivationNode->RequiredMethod = EResourceAcquisitionMethod::ShipSystemReactivation;
            ReactivationNode->RequiredSystem = Collector;
        }

        World->SpawnActor<ARetrievalDroneActor>(ARetrievalDroneActor::StaticClass(), CargoLocation + FVector(0.0f, 100.0f, 0.0f), FRotator::ZeroRotator);
    }

    if (EscapeBay)
    {
        const FVector EscapeBayLocation = EscapeBay->GetActorLocation();

        World->SpawnActor<AEscapePodSystem>(AEscapePodSystem::StaticClass(), EscapeBayLocation + FVector(100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
        World->SpawnActor<ASelfDestructConsoleSystem>(ASelfDestructConsoleSystem::StaticClass(), EscapeBayLocation - FVector(100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
    }

    World->SpawnActor<AArmorPlatingSystem>(AArmorPlatingSystem::StaticClass(), DamageControl->GetActorLocation(), FRotator::ZeroRotator);

    // Populate after authored machinery and environmental damage exist so obstruction tests can
    // choose clear wall slots and local Bloom pressure can tune each station's challenge.
    PopulateActivityStations();

    // Placed far outside every section's bounds so UShipNavigationSubsystem::GetSectionContainingLocation
    // returns null there, satisfying AResourceNodeActor's own EVA-retrieval gating.
    const FVector EVANodeLocation = Origin + FVector(HubRadius * 4.0f, HubRadius * 4.0f, 0.0f);
    AResourceNodeActor* EVANode = World->SpawnActor<AResourceNodeActor>(AResourceNodeActor::StaticClass(), EVANodeLocation, FRotator::ZeroRotator);
    if (EVANode)
    {
        EVANode->RequiredMethod = EResourceAcquisitionMethod::EVARetrieval;
    }

    TArray<AShipSection*> AllSections;
    AllSections.Reserve(SpawnedRooms.Num() + SpawnedCorridors.Num());
    for (AModularShipRoom* Room : SpawnedRooms)
    {
        AllSections.Add(Room);
    }
    for (AShipSection* Corridor : SpawnedCorridors)
    {
        AllSections.Add(Corridor);
    }

    // A fireteam-sized hostile patrol roams the full corvette deck, relying on
    // APatrollingEnemyController's native (BT-less) Tick movement.
    for (int32 i = 0; i < 4; ++i)
    {
        const FVector EnemySpawnLocation = Origin + FVector(-800.0f + i * 500.0f, (i % 2 ? 1 : -1) * 180.0f, 0.0f);
        AHorrorEnemy* Enemy = World->SpawnActor<AHorrorEnemy>(AHorrorEnemy::StaticClass(), EnemySpawnLocation, FRotator::ZeroRotator);
        if (Enemy)
        {
            if (APatrollingEnemyController* Controller = Cast<APatrollingEnemyController>(Enemy->GetController()))
            {
                Controller->PatrolSections = AllSections;
            }
        }
    }

    const FVector DeploymentPoint = Origin + FVector(3500, 0, 20);
    const FRotator DeploymentRotation(0, 180, 0);
    World->SpawnActor<APlayerStart>(APlayerStart::StaticClass(), DeploymentPoint, DeploymentRotation);

    // GameMode builds the procedural deck during BeginPlay, after the map's original PlayerStart
    // may already have spawned the pawn. Move the live player onto the completed bridge route so
    // play sessions and automated walkthrough captures never begin outside the ship.
    if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(World, 0))
    {
        PlayerPawn->TeleportTo(DeploymentPoint, DeploymentRotation, false, true);
        if (AController* Controller = PlayerPawn->GetController())
        {
            Controller->SetControlRotation(DeploymentRotation);
        }
    }

    bHasBuiltShip = true;
}
