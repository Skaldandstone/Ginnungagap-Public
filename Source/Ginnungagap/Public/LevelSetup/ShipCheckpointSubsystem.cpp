#include "LevelSetup/ShipCheckpointSubsystem.h"

#include "Activities/ActivityStation.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/ProceduralShipBuilder.h"
#include "Mission/MissionObjectiveSubsystem.h"

const FString UShipCheckpointSubsystem::SaveSlotName = TEXT("GinnungagapShipCheckpoint");

void UShipCheckpointSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    if (UShipCheckpointSaveGame* Save = Cast<UShipCheckpointSaveGame>(
        UGameplayStatics::LoadGameFromSlot(SaveSlotName, UserIndex)))
    {
        CachedRecord = Save->Record;
    }
}

FName UShipCheckpointSubsystem::GetStableMapName(const UWorld* World)
{
    return World ? FName(*UGameplayStatics::GetCurrentLevelName(World, true)) : NAME_None;
}

bool UShipCheckpointSubsystem::RecordCheckpoint(
    UWorld* World, FName CheckpointId, const FTransform& RespawnTransform)
{
    if (!World || CheckpointId.IsNone())
    {
        return false;
    }

    FShipCheckpointRecord NewRecord;
    NewRecord.DistrictMapName = GetStableMapName(World);
    NewRecord.CheckpointId = CheckpointId;
    NewRecord.RespawnTransform = RespawnTransform;

    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            for (const FMissionObjectiveRuntime& Objective : Missions->GetAllObjectives(true))
            {
                if (Objective.State == EMissionObjectiveState::Completed)
                {
                    NewRecord.CompletedObjectiveIds.Add(Objective.Definition.ObjectiveId);
                }
            }
        }
        if (UBloomDirector* Bloom = GameInstance->GetSubsystem<UBloomDirector>())
        {
            NewRecord.BloomStage = Bloom->GetCurrentStage();
        }
    }

    for (TActorIterator<AProceduralShipBuilder> It(World); It; ++It)
    {
        NewRecord.ActivityPopulationSeed = It->ActivityPopulationSeed;
        break;
    }
    for (TActorIterator<AActivityStation> It(World); It; ++It)
    {
        if (It->StationId.IsNone()) continue;
        FActivityStationCheckpointRecord& StationRecord = NewRecord.ActivityStations.AddDefaulted_GetRef();
        StationRecord.StationId = It->StationId;
        StationRecord.CompletionCount = It->CompletionCount;
        StationRecord.Condition = It->Condition;
        StationRecord.ConditionPercent = It->ConditionPercent;
        StationRecord.RemainingUses = It->RemainingUses;
        StationRecord.bEnabled = It->bEnabled;
    }

    UShipCheckpointSaveGame* Save = Cast<UShipCheckpointSaveGame>(
        UGameplayStatics::CreateSaveGameObject(UShipCheckpointSaveGame::StaticClass()));
    if (!Save)
    {
        return false;
    }
    Save->Record = NewRecord;
    if (!UGameplayStatics::SaveGameToSlot(Save, SaveSlotName, UserIndex))
    {
        return false;
    }
    CachedRecord = MoveTemp(NewRecord);
    return true;
}

bool UShipCheckpointSubsystem::RestoreCheckpoint(UWorld* World, APawn* PlayerPawn)
{
    if (!PlayerPawn || !HasCheckpointForWorld(World))
    {
        return false;
    }

    PlayerPawn->SetActorTransform(CachedRecord.RespawnTransform, false, nullptr, ETeleportType::TeleportPhysics);
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->RestoreCompletedObjectives(CachedRecord.CompletedObjectiveIds);
        }
        if (UBloomDirector* Bloom = GameInstance->GetSubsystem<UBloomDirector>())
        {
            Bloom->RestoreStage(CachedRecord.BloomStage);
        }
    }

    if (!CachedRecord.ActivityStations.IsEmpty())
    {
        TMap<FName, const FActivityStationCheckpointRecord*> SavedStations;
        for (const FActivityStationCheckpointRecord& Record : CachedRecord.ActivityStations)
            SavedStations.Add(Record.StationId, &Record);
        for (TActorIterator<AActivityStation> It(World); It; ++It)
        {
            if (const FActivityStationCheckpointRecord* const* Record = SavedStations.Find(It->StationId))
            {
                It->RestoreRuntimeState((*Record)->CompletionCount, (*Record)->Condition,
                    (*Record)->ConditionPercent, (*Record)->RemainingUses, (*Record)->bEnabled);
            }
        }
    }
    return true;
}

bool UShipCheckpointSubsystem::HasCheckpointForWorld(const UWorld* World) const
{
    return CachedRecord.IsForMap(GetStableMapName(World));
}

void UShipCheckpointSubsystem::ClearCheckpoint()
{
    CachedRecord = FShipCheckpointRecord();
    UGameplayStatics::DeleteGameInSlot(SaveSlotName, UserIndex);
}
