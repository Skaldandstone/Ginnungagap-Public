#include "WorldItems/WorldItemSeedPoint.h"

#include "Components/ArrowComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Inventory/InventoryItemPickup.h"
#include "Meta/RunSeedSubsystem.h"

AWorldItemSeedPoint::AWorldItemSeedPoint()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    SpawnDirection = CreateDefaultSubobject<UArrowComponent>(TEXT("SpawnDirection"));
    SpawnDirection->SetupAttachment(SceneRoot);
    SpawnDirection->ArrowColor = FColor(40, 180, 255);
    SpawnDirection->ArrowSize = 1.25f;
}

void AWorldItemSeedPoint::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority() && bSeedOnBeginPlay)
    {
        SeedNow();
    }
}

void AWorldItemSeedPoint::SeedNow()
{
    SpawnedItems.RemoveAll([](const TObjectPtr<AActor>& Spawned)
    {
        return !IsValid(Spawned);
    });
    if (!HasAuthority() || SpawnedItems.Num() > 0)
    {
        return;
    }

    TArray<FWorldItemSeedEntry> Eligible = GetEligibleEntries();
    if (Eligible.IsEmpty())
    {
        return;
    }

    // Folded in with the run seed, so what a ship is carrying differs run to run and still
    // reproduces exactly from the one number in the log. Before this the stream was built from a
    // hardcoded constant and the actor's path, which made every run place identical loot in
    // identical spots -- a seed nobody could vary is not randomness, it is a fixed layout with
    // extra steps.
    //
    // Deliberately its own stream off the run seed rather than draws from a shared channel. Seed
    // points fire from BeginPlay in whatever order the level hands them over, and a shared channel
    // would make each point's result depend on that order -- so adding one point anywhere would
    // change the loot everywhere, which is precisely what the per-channel design exists to stop.
    // Hashing the actor's own path keeps every point independent of every other.
    int32 RunSeed = 0;
    if (const UWorld* World = GetWorld())
    {
        if (const UGameInstance* GameInstance = World->GetGameInstance())
        {
            if (const URunSeedSubsystem* Seeds = GameInstance->GetSubsystem<URunSeedSubsystem>())
            {
                RunSeed = Seeds->GetRunSeed();
            }
        }
    }

    // Seed stays an author-set offset so two points in the same room can be told apart, and so a
    // hand-placed point can be varied against its neighbours without moving it.
    FRandomStream Stream(HashCombineFast(HashCombineFast(RunSeed, Seed), GetTypeHash(GetPathName())));
    for (int32 Roll = 0; Roll < FMath::Max(1, SpawnRolls) && !Eligible.IsEmpty(); ++Roll)
    {
        if (Stream.FRand() > SpawnChance)
        {
            continue;
        }

        const FWorldItemSeedEntry* Chosen = ChooseWeightedEntry(Eligible, Stream);
        if (!Chosen || !Chosen->ActorClass)
        {
            continue;
        }

        const float ScatterAngle = Stream.FRandRange(0.0f, UE_TWO_PI);
        const float ScatterDistance = FMath::Sqrt(Stream.FRand()) * ScatterRadiusCm;
        const FVector2D Scatter(FMath::Cos(ScatterAngle) * ScatterDistance, FMath::Sin(ScatterAngle) * ScatterDistance);
        const FVector SpawnLocation = GetActorLocation() + GetActorRightVector() * Scatter.X + GetActorForwardVector() * Scatter.Y;
        FActorSpawnParameters Params;
        Params.Owner = this;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
        AActor* Spawned = GetWorld()->SpawnActor<AActor>(Chosen->ActorClass, SpawnLocation, GetActorRotation(), Params);
        if (Spawned)
        {
            Spawned->Tags.AddUnique(Chosen->ContentId);
            Spawned->Tags.Append(Chosen->ContentTags);
            if (AInventoryItemPickup* Pickup = Cast<AInventoryItemPickup>(Spawned))
            {
                const int32 Minimum = FMath::Max(1, Chosen->MinQuantity);
                const int32 Maximum = FMath::Max(Minimum, Chosen->MaxQuantity);
                Pickup->ConfigurePickup(Pickup->ItemDefinition, Stream.RandRange(Minimum, Maximum));
            }
            SpawnedItems.Add(Spawned);
        }

        if (!bAllowDuplicateEntries)
        {
            const FName ChosenId = Chosen->ContentId;
            const TSubclassOf<AActor> ChosenClass = Chosen->ActorClass;
            Eligible.RemoveAll([ChosenId, ChosenClass](const FWorldItemSeedEntry& Candidate)
            {
                return Candidate.ContentId == ChosenId && Candidate.ActorClass == ChosenClass;
            });
        }
    }
}

void AWorldItemSeedPoint::ClearSpawnedItems()
{
    if (!HasAuthority())
    {
        return;
    }

    for (AActor* Spawned : SpawnedItems)
    {
        if (IsValid(Spawned))
        {
            Spawned->Destroy();
        }
    }
    SpawnedItems.Reset();
}

TArray<FWorldItemSeedEntry> AWorldItemSeedPoint::GetEligibleEntries() const
{
    TArray<FWorldItemSeedEntry> Result = Catalog ? Catalog->Entries : TArray<FWorldItemSeedEntry>();
    Result.Append(LocalEntries);
    Result.RemoveAll([this](const FWorldItemSeedEntry& Entry)
    {
        return !Entry.ActorClass || Entry.Weight <= 0.0f ||
            (!RoomProfile.IsNone() && !Entry.RoomProfiles.IsEmpty() && !Entry.RoomProfiles.Contains(RoomProfile));
    });
    return Result;
}

const FWorldItemSeedEntry* AWorldItemSeedPoint::ChooseWeightedEntry(
    const TArray<FWorldItemSeedEntry>& Entries, FRandomStream& Stream) const
{
    float TotalWeight = 0.0f;
    for (const FWorldItemSeedEntry& Entry : Entries)
    {
        TotalWeight += FMath::Max(0.0f, Entry.Weight);
    }
    if (TotalWeight <= 0.0f)
    {
        return nullptr;
    }

    float Selection = Stream.FRandRange(0.0f, TotalWeight);
    for (const FWorldItemSeedEntry& Entry : Entries)
    {
        Selection -= FMath::Max(0.0f, Entry.Weight);
        if (Selection <= 0.0f)
        {
            return &Entry;
        }
    }
    return &Entries.Last();
}
