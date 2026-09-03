#include "Ship/ShipHardpointPopulationDirector.h"

#include "Bloom/CrewCorpse.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Net/UnrealNetwork.h"

namespace
{
    struct FPopulationCandidate
    {
        AShipSection* Section = nullptr;
        FShipGameplayHardpoint Hardpoint;
        FTransform WorldTransform;
    };
}

AShipHardpointStaticOccupant::AShipHardpointStaticOccupant()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    SetRootComponent(VisualMesh);
    VisualMesh->SetMobility(EComponentMobility::Movable);
}

void AShipHardpointStaticOccupant::ConfigureOccupant(EShipGameplayHardpointType Type,
    UStaticMesh* Mesh)
{
    OccupantType = Type;
    MeshAsset = Mesh;
    RefreshVisual();
}

void AShipHardpointStaticOccupant::GetLifetimeReplicatedProps(
    TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AShipHardpointStaticOccupant, MeshAsset);
    DOREPLIFETIME(AShipHardpointStaticOccupant, OccupantType);
}

void AShipHardpointStaticOccupant::OnRep_OccupantVisual()
{
    RefreshVisual();
}

void AShipHardpointStaticOccupant::RefreshVisual()
{
    VisualMesh->SetStaticMesh(MeshAsset);
    VisualMesh->SetCollisionProfileName(OccupantType == EShipGameplayHardpointType::Obstacle
        ? FName(TEXT("BlockAllDynamic")) : FName(TEXT("NoCollision")));
}

AShipHardpointPopulationDirector::AShipHardpointPopulationDirector()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    BodyActorClass = ACrewCorpse::StaticClass();
}

void AShipHardpointPopulationDirector::BeginPlay()
{
    Super::BeginPlay();
    if (bPopulateOnBeginPlay && HasAuthority())
    {
        PopulateHardpoints();
    }
}

int32 AShipHardpointPopulationDirector::PopulateHardpoints()
{
    if (!HasAuthority())
    {
        return 0;
    }
    if (!SpawnedBindings.IsEmpty())
    {
        return SpawnedBindings.Num();
    }

    FRandomStream Random(PopulationSeed);
    PopulateType(EShipGameplayHardpointType::Body, BodyCount, Random);
    PopulateType(EShipGameplayHardpointType::Obstacle, ObstacleCount, Random);
    PopulateType(EShipGameplayHardpointType::BloomGrowth, BloomGrowthCount, Random);
    return SpawnedBindings.Num();
}

void AShipHardpointPopulationDirector::ClearPopulation()
{
    if (!HasAuthority())
    {
        return;
    }

    for (const FShipHardpointPopulationBinding& Binding : SpawnedBindings)
    {
        if (Binding.Section)
        {
            Binding.Section->SetGameplayHardpointReserved(Binding.HardpointId, false);
        }
        if (IsValid(Binding.SpawnedActor))
        {
            Binding.SpawnedActor->Destroy();
        }
    }
    SpawnedBindings.Reset();
}

int32 AShipHardpointPopulationDirector::PopulateType(EShipGameplayHardpointType Type,
    int32 RequestedCount, FRandomStream& Random)
{
    UWorld* World = GetWorld();
    if (!World || RequestedCount <= 0)
    {
        return 0;
    }

    TArray<FPopulationCandidate> Candidates;
    for (TActorIterator<AShipSection> It(World); It; ++It)
    {
        AShipSection* Section = *It;
        if (!IsValid(Section) || (PopulationRadius > 0.0f
            && FVector::DistSquared(GetActorLocation(), Section->GetActorLocation())
                > FMath::Square(PopulationRadius)))
        {
            continue;
        }

        for (const FShipGameplayHardpoint& Hardpoint : Section->GetGameplayHardpoints(Type, true))
        {
            FTransform WorldTransform;
            if (Section->GetGameplayHardpointWorldTransform(Hardpoint.HardpointId, WorldTransform))
            {
                FPopulationCandidate& Candidate = Candidates.AddDefaulted_GetRef();
                Candidate.Section = Section;
                Candidate.Hardpoint = Hardpoint;
                Candidate.WorldTransform = WorldTransform;
            }
        }
    }

    Candidates.Sort([](const FPopulationCandidate& A, const FPopulationCandidate& B)
    {
        if (A.Section->SectionID != B.Section->SectionID)
        {
            return A.Section->SectionID < B.Section->SectionID;
        }
        const int32 SectionNameOrder = A.Section->GetFName().Compare(B.Section->GetFName());
        return SectionNameOrder != 0 ? SectionNameOrder < 0
            : A.Hardpoint.HardpointId.Compare(B.Hardpoint.HardpointId) < 0;
    });
    for (int32 Index = Candidates.Num() - 1; Index > 0; --Index)
    {
        Candidates.Swap(Index, Random.RandRange(0, Index));
    }

    int32 SpawnedCount = 0;
    for (const FPopulationCandidate& Candidate : Candidates)
    {
        if (SpawnedCount >= RequestedCount)
        {
            break;
        }

        AActor* Occupant = SpawnAtHardpoint(Type, Candidate.WorldTransform);
        if (!Occupant || !Candidate.Section->SetGameplayHardpointReserved(
            Candidate.Hardpoint.HardpointId, true))
        {
            if (Occupant)
            {
                Occupant->Destroy();
            }
            continue;
        }

        Occupant->SetOwner(this);
        Occupant->Tags.AddUnique(TEXT("ShipHardpointOccupant"));
        Occupant->Tags.AddUnique(Candidate.Hardpoint.HardpointId);
        Occupant->Tags.AddUnique(FName(*UEnum::GetValueAsString(Type)));

        FShipHardpointPopulationBinding& Binding = SpawnedBindings.AddDefaulted_GetRef();
        Binding.Section = Candidate.Section;
        Binding.HardpointId = Candidate.Hardpoint.HardpointId;
        Binding.HardpointType = Type;
        Binding.SpawnedActor = Occupant;
        ++SpawnedCount;
    }
    return SpawnedCount;
}

AActor* AShipHardpointPopulationDirector::SpawnAtHardpoint(EShipGameplayHardpointType Type,
    const FTransform& Transform)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    if (Type == EShipGameplayHardpointType::Body && BodyActorClass)
    {
        ACrewCorpse* Body = World->SpawnActorDeferred<ACrewCorpse>(BodyActorClass, Transform, this,
            nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
        if (!Body)
        {
            return nullptr;
        }
        Body->SetReplicates(true);
        Body->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        if (USkeletalMeshComponent* Mesh = Body->GetMesh())
        {
            Mesh->SetSkeletalMeshAsset(BodyMesh);
            Mesh->SetRelativeLocation(FVector(0.0f, 0.0f, -88.0f));
            Mesh->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
        }
        Body->FinishSpawning(Transform);
        return Body;
    }

    UStaticMesh* Mesh = Type == EShipGameplayHardpointType::Obstacle
        ? ObstacleMesh : (Type == EShipGameplayHardpointType::BloomGrowth ? BloomGrowthMesh : nullptr);
    if (!Mesh)
    {
        return nullptr;
    }

    AShipHardpointStaticOccupant* MeshActor =
        World->SpawnActorDeferred<AShipHardpointStaticOccupant>(
            AShipHardpointStaticOccupant::StaticClass(), Transform, this, nullptr,
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!MeshActor)
    {
        return nullptr;
    }
    const bool bObstacle = Type == EShipGameplayHardpointType::Obstacle;
    MeshActor->ConfigureOccupant(Type, Mesh);
    MeshActor->SetActorScale3D(FVector(bObstacle ? ObstacleScale : BloomGrowthScale));
    MeshActor->FinishSpawning(Transform);
    return MeshActor;
}
