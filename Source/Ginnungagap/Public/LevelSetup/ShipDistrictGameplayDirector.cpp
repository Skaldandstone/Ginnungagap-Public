#include "LevelSetup/ShipDistrictGameplayDirector.h"

#include "AI/HorrorEnemy.h"
#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Pickup/SurvivalPickup.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "TimerManager.h"
#include "Ship/CryoPodSystem.h"
#include "Ship/JumpConsoleSystem.h"
#include "Ship/LifeSupportSystem.h"
#include "Ship/SensorArraySystem.h"
#include "Ship/ShipHelmSystem.h"
#include "Ship/EscapePodSystem.h"
#include "Ship/SelfDestructConsoleSystem.h"
#include "StarSystem/DormantCollectorSystem.h"
#include "StarSystem/ResourceNodeActor.h"
#include "StarSystem/RetrievalDroneActor.h"
#include "StarSystem/JumpSequenceSubsystem.h"
#include "Threats/ShipThreatDirector.h"
#include "WorldItems/WorldItemSeedCatalog.h"
#include "WorldItems/WorldItemSeedPoint.h"

AShipDistrictGameplayDirector::AShipDistrictGameplayDirector()
{
    PrimaryActorTick.bCanEverTick = false;
    DistrictBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("DistrictBounds"));
    SetRootComponent(DistrictBounds);
    DistrictBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DistrictBounds->SetBoxExtent(DistrictExtent);
}

void AShipDistrictGameplayDirector::BeginPlay()
{
    Super::BeginPlay();
    DistrictBounds->SetBoxExtent(DistrictExtent);
    RegisterPrimaryObjective();
    if (bRestoreCheckpointOnBeginPlay)
    {
        GetWorldTimerManager().SetTimerForNextTick(this, &AShipDistrictGameplayDirector::RestoreCheckpointState);
    }
    if (bSpawnGameplayOnBeginPlay)
    {
        SeedDistrictGameplay();
    }
    if (bSpawnDemoSystems)
    {
        if (UGameInstance* GI = GetGameInstance())
        {
            if (UJumpSequenceSubsystem* Jump = GI->GetSubsystem<UJumpSequenceSubsystem>())
            {
                Jump->WarningCountdownSeconds = DemoJumpCountdownSeconds;
                Jump->TotalJumpsToDestination = DemoJumpsToDestination;
            }
        }
        SpawnDemoSystems();
    }
}

void AShipDistrictGameplayDirector::SpawnDemoSystems()
{
    UWorld* World = GetWorld();
    if (!World || !HasAuthority())
    {
        return;
    }

    // Keep every station within the authored companionway bounds. Alternating sides leaves a
    // clear route down the center and makes the vertical slice readable in either direction.
    const FVector Origin = GetActorLocation();
    const float SideY = FMath::Max(250.0f, DistrictExtent.Y - 125.0f);
    auto SpawnStation = [World, Origin](UClass* Class, float X, float Y, float Yaw)
    {
        return World->SpawnActor<AActor>(Class, Origin + FVector(X, Y, 25.0f), FRotator(0.0f, Yaw, 0.0f));
    };

    auto NameSystem = [](AActor* Actor, const TCHAR* Name)
    {
        if (AShipSystemActor* System = Cast<AShipSystemActor>(Actor))
        {
            System->SystemName = Name;
        }
    };
    NameSystem(SpawnStation(ALifeSupportSystem::StaticClass(), -2100.0f, -SideY, 90.0f), TEXT("Restore Life Support"));
    NameSystem(SpawnStation(ASensorArraySystem::StaticClass(), -750.0f, -SideY, 90.0f), TEXT("Open Sensor Survey"));
    NameSystem(SpawnStation(AShipHelmSystem::StaticClass(), 0.0f, SideY, -90.0f), TEXT("Helm Navigation"));
    if (AJumpConsoleSystem* JumpConsole = Cast<AJumpConsoleSystem>(
        SpawnStation(AJumpConsoleSystem::StaticClass(), 750.0f, -SideY, 90.0f)))
    {
        JumpConsole->bAutoSelectFirstCandidate = true;
        JumpConsole->SystemName = TEXT("Select Jump Destination");
    }
    NameSystem(SpawnStation(ACryoPodSystem::StaticClass(), 1450.0f, SideY, -90.0f), TEXT("Enter Cryo Pod"));
    NameSystem(SpawnStation(AEscapePodSystem::StaticClass(), 2050.0f, SideY, -90.0f), TEXT("Enter Escape Pod"));
    if (ASelfDestructConsoleSystem* SelfDestruct = Cast<ASelfDestructConsoleSystem>(
        SpawnStation(ASelfDestructConsoleSystem::StaticClass(), 2050.0f, -SideY, 90.0f)))
    {
        SelfDestruct->bArmOnInteractForNativeDemo = true;
        SelfDestruct->SystemName = TEXT("Arm Self Destruct");
    }

    // A reachable node demonstrates ship-system reactivation; the drone provides the second
    // acquisition method without asking the player to leave this room-scale demo district.
    ADormantCollectorSystem* Collector = Cast<ADormantCollectorSystem>(
        SpawnStation(ADormantCollectorSystem::StaticClass(), -1450.0f, SideY - 140.0f, -90.0f));
    AResourceNodeActor* Resource = Cast<AResourceNodeActor>(
        SpawnStation(AResourceNodeActor::StaticClass(), -1150.0f, SideY - 140.0f, -90.0f));
    if (Resource && Collector)
    {
        Collector->SystemName = TEXT("Reactivate Resource Collector");
        Resource->RequiredMethod = EResourceAcquisitionMethod::ShipSystemReactivation;
        Resource->RequiredSystem = Collector;
    }
    SpawnStation(ARetrievalDroneActor::StaticClass(), -850.0f, SideY - 140.0f, -90.0f);

    UE_LOG(LogTemp, Display, TEXT("Spawned authored-district demo systems in %s."), *GetWorld()->GetMapName());
}

void AShipDistrictGameplayDirector::RestoreCheckpointState()
{
    UGameInstance* GameInstance = GetGameInstance();
    APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    if (GameInstance && PlayerPawn && HasAuthority())
    {
        if (UShipCheckpointSubsystem* Checkpoints = GameInstance->GetSubsystem<UShipCheckpointSubsystem>())
        {
            Checkpoints->RestoreCheckpoint(GetWorld(), PlayerPawn);
        }
    }
}

void AShipDistrictGameplayDirector::RegisterPrimaryObjective()
{
    UGameInstance* GameInstance = GetGameInstance();
    UMissionObjectiveSubsystem* Missions = GameInstance
        ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    if (!Missions || PrimaryObjectiveId.IsNone())
    {
        return;
    }

    FMissionObjectiveDefinition Definition;
    Definition.ObjectiveId = PrimaryObjectiveId;
    Definition.Title = PrimaryObjectiveTitle;
    Definition.Description = NSLOCTEXT("ShipDistrict", "DistrictObjectiveDescription",
        "Reach the marked control station and restore this district before the Bloom advances.");
    Definition.Type = ObjectiveType;
    Definition.TargetProgress = 1.0f;
    Definition.bAutoActivate = true;
    Definition.bBlocksJumpWhileUnresolved = true;
    Definition.CurrencyReward = ObjectiveReward;
    Missions->AddObjective(Definition);
}

FVector AShipDistrictGameplayDirector::RandomPointOnDeck(FRandomStream& Random, float EdgeMargin) const
{
    const FVector SafeExtent(
        FMath::Max(100.0f, DistrictExtent.X - EdgeMargin),
        FMath::Max(100.0f, DistrictExtent.Y - EdgeMargin),
        0.0f);
    return GetActorLocation() + FVector(
        Random.FRandRange(-SafeExtent.X, SafeExtent.X),
        Random.FRandRange(-SafeExtent.Y, SafeExtent.Y),
        95.0f);
}

void AShipDistrictGameplayDirector::SeedDistrictGameplay()
{
    UWorld* World = GetWorld();
    if (!World || !HasAuthority())
    {
        return;
    }

    FRandomStream Random(LayoutSeed);
    const int32 BudgetedEnemies = PerformanceBudget
        ? FMath::Min(EncounterCount, PerformanceBudget->MaxActiveEnemies) : EncounterCount;
    if (ThreatPreset != EThreatEncounterPreset::Custom)
    {
        FTransform DirectorTransform(GetActorRotation(), GetActorLocation());
        AShipThreatDirector* ThreatDirector = World->SpawnActorDeferred<AShipThreatDirector>(
            AShipThreatDirector::StaticClass(), DirectorTransform, this, nullptr,
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
        if (ThreatDirector)
        {
            ThreatDirector->Preset = EThreatEncounterPreset::Custom;
            ThreatDirector->EncounterDefinition = AShipThreatDirector::BuildPresetDefinition(ThreatPreset);
            ThreatDirector->EncounterDefinition.RandomSeed = LayoutSeed;
            ThreatDirector->EncounterDefinition.FallbackSpawnRadius = FMath::Max(DistrictExtent.X, DistrictExtent.Y) * 0.75f;

            int32 RemainingBudget = PerformanceBudget ? PerformanceBudget->MaxActiveEnemies
                : ThreatDirector->EncounterDefinition.GetTotalThreatCount();
            for (FThreatSpawnGroup& Group : ThreatDirector->EncounterDefinition.SpawnGroups)
            {
                Group.Count = FMath::Min(Group.Count, RemainingBudget);
                RemainingBudget -= Group.Count;
            }
            ThreatDirector->FinishSpawning(DirectorTransform);
        }
    }
    else for (int32 Index = 0; Index < BudgetedEnemies; ++Index)
    {
        AHorrorEnemy* Enemy = World->SpawnActor<AHorrorEnemy>(AHorrorEnemy::StaticClass(),
            RandomPointOnDeck(Random, 650.0f), FRotator(0.0f, Random.FRandRange(-180.0f, 180.0f), 0.0f));
        if (Enemy)
        {
            Enemy->PatrolPoints = {
                RandomPointOnDeck(Random, 500.0f),
                RandomPointOnDeck(Random, 500.0f),
                RandomPointOnDeck(Random, 500.0f)
            };
        }
    }

    auto SpawnPickups = [&](EPickupType Type, int32 Count)
    {
        for (int32 Index = 0; Index < Count; ++Index)
        {
            ASurvivalPickup* Pickup = World->SpawnActor<ASurvivalPickup>(ASurvivalPickup::StaticClass(),
                RandomPointOnDeck(Random, 350.0f), FRotator::ZeroRotator);
            if (Pickup)
            {
                Pickup->PickupType = Type;
                Pickup->Amount = Type == EPickupType::Oxygen ? 30.0f : 25.0f;
            }
        }
    };
    SpawnPickups(EPickupType::Oxygen, OxygenPickupCount);
    SpawnPickups(EPickupType::Health, HealthPickupCount);

    if (WorldItemCatalog)
    {
        for (int32 Index = 0; Index < WorldItemSeedCount; ++Index)
        {
            const FTransform SeedTransform(
                FRotator(0.0f, Random.FRandRange(-180.0f, 180.0f), 0.0f),
                RandomPointOnDeck(Random, 300.0f));
            AWorldItemSeedPoint* SeedPoint = World->SpawnActorDeferred<AWorldItemSeedPoint>(
                AWorldItemSeedPoint::StaticClass(), SeedTransform, this, nullptr,
                ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
            if (!SeedPoint)
            {
                continue;
            }

            SeedPoint->Catalog = WorldItemCatalog;
            SeedPoint->Seed = HashCombineFast(LayoutSeed, Index + 1);
            SeedPoint->RoomProfile = WorldItemRoomProfiles.IsEmpty()
                ? NAME_None
                : WorldItemRoomProfiles[Random.RandRange(0, WorldItemRoomProfiles.Num() - 1)];
            SeedPoint->bSeedOnBeginPlay = false;
            SeedPoint->FinishSpawning(SeedTransform);
            SeedPoint->SeedNow();
        }
    }
}
