#include "Threats/ShipThreatDirector.h"

#include "AI/PatrollingEnemyController.h"
#include "Bloom/BloomDirector.h"
#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Ship/ShipSection.h"
#include "Threats/ShipboardThreat.h"

namespace
{
    FThreatSpawnGroup ThreatGroup(EThreatArchetype Archetype, int32 Count)
    {
        FThreatSpawnGroup Group;
        Group.Archetype = Archetype;
        Group.Count = Count;
        return Group;
    }
}

AShipThreatDirector::AShipThreatDirector()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    EncounterDefinition = BuildPresetDefinition(EThreatEncounterPreset::PirateBoarding);
}

void AShipThreatDirector::BeginPlay()
{
    Super::BeginPlay();
    if (Preset != EThreatEncounterPreset::Custom)
    {
        EncounterDefinition = BuildPresetDefinition(Preset);
    }

    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UBloomDirector* Bloom = GameInstance->GetSubsystem<UBloomDirector>())
        {
            Bloom->OnBloomStageChanged.AddDynamic(this, &AShipThreatDirector::HandleBloomStageChanged);
        }
    }

    if (bAutoStart)
    {
        StartEncounter();
    }
}

bool AShipThreatDirector::StartEncounter()
{
    UWorld* World = GetWorld();
    if (!World || !HasAuthority() || EncounterState != EThreatEncounterState::Dormant
        || !CanStartEncounter() || EncounterDefinition.GetTotalThreatCount() <= 0)
    {
        return false;
    }

    TArray<AShipSection*> Sections;
    if (EncounterDefinition.bPreferShipSections)
    {
        for (TActorIterator<AShipSection> It(World); It; ++It)
        {
            if (IsValid(*It) && (*It)->SectionBounds)
            {
                Sections.Add(*It);
            }
        }
    }

    FRandomStream Random(EncounterDefinition.RandomSeed);
    int32 SpawnIndex = 0;
    for (const FThreatSpawnGroup& Group : EncounterDefinition.SpawnGroups)
    {
        for (int32 Index = 0; Index < FMath::Max(0, Group.Count); ++Index)
        {
            const FTransform SpawnTransform = ChooseSpawnTransform(Random, SpawnIndex++, Sections);
            AShipboardThreat* Threat = World->SpawnActorDeferred<AShipboardThreat>(
                AShipboardThreat::StaticClass(), SpawnTransform, this, nullptr,
                ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);
            if (!Threat)
            {
                continue;
            }

            Threat->ConfigureArchetype(Group.Archetype);
            Threat->FinishSpawning(SpawnTransform);
            Threat->OnEnemyKilled.AddDynamic(this, &AShipThreatDirector::HandleThreatKilled);
            ActiveThreats.Add(Threat);

            if (APatrollingEnemyController* Controller = Cast<APatrollingEnemyController>(Threat->GetController()))
            {
                Controller->PatrolSections = Sections;
            }
        }
    }

    if (ActiveThreats.IsEmpty())
    {
        return false;
    }

    EncounterState = EThreatEncounterState::Active;
    RegisterMissionObjective();
    OnEncounterStateChanged.Broadcast(EncounterDefinition.EncounterId, EncounterState);
    return true;
}

void AShipThreatDirector::CancelEncounter(bool bDestroyRemainingThreats)
{
    if (!HasAuthority() || EncounterState == EThreatEncounterState::Completed
        || EncounterState == EThreatEncounterState::Cancelled)
    {
        return;
    }

    if (bDestroyRemainingThreats)
    {
        for (AShipboardThreat* Threat : ActiveThreats)
        {
            if (IsValid(Threat))
            {
                Threat->Destroy();
            }
        }
    }
    ActiveThreats.Reset();
    EncounterState = EThreatEncounterState::Cancelled;

    if (EncounterDefinition.bPrimaryAntagonist)
    {
        if (UGameInstance* GameInstance = GetGameInstance())
        {
            if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
            {
                Missions->FailObjective(EncounterDefinition.EncounterId,
                    NSLOCTEXT("Threats", "EncounterCancelled", "The hostile force was not neutralized."));
            }
        }
    }
    OnEncounterStateChanged.Broadcast(EncounterDefinition.EncounterId, EncounterState);
}

bool AShipThreatDirector::CanStartEncounter() const
{
    const UGameInstance* GameInstance = GetGameInstance();
    const UBloomDirector* Bloom = GameInstance ? GameInstance->GetSubsystem<UBloomDirector>() : nullptr;
    const bool bBloomPresent = Bloom && Bloom->IsPresentThreat();
    return (!EncounterDefinition.bRequiresBloom || bBloomPresent)
        && (EncounterDefinition.bCanOverlapBloom || !bBloomPresent);
}

int32 AShipThreatDirector::GetRemainingThreatCount() const
{
    int32 Remaining = 0;
    for (const AShipboardThreat* Threat : ActiveThreats)
    {
        Remaining += IsValid(Threat) && !Threat->IsDead() ? 1 : 0;
    }
    return Remaining;
}

FThreatEncounterDefinition AShipThreatDirector::BuildPresetDefinition(EThreatEncounterPreset ForPreset)
{
    FThreatEncounterDefinition Definition;
    switch (ForPreset)
    {
    case EThreatEncounterPreset::PirateBoarding:
        Definition.EncounterId = TEXT("RepelPirateBoarders");
        Definition.DisplayName = NSLOCTEXT("Threats", "PirateBoarding", "Repel pirate boarders");
        Definition.SpawnGroups = {
            ThreatGroup(EThreatArchetype::PirateBreacher, 3),
            ThreatGroup(EThreatArchetype::PirateGunner, 2)
        };
        Definition.CurrencyReward = 350;
        break;
    case EThreatEncounterPreset::RebelTakeover:
        Definition.EncounterId = TEXT("BreakRebelTakeover");
        Definition.DisplayName = NSLOCTEXT("Threats", "RebelTakeover", "Break the rebel takeover");
        Definition.SpawnGroups = {
            ThreatGroup(EThreatArchetype::RebelSaboteur, 3),
            ThreatGroup(EThreatArchetype::RebelHeavy, 1)
        };
        Definition.CurrencyReward = 400;
        break;
    case EThreatEncounterPreset::AlienHuntingPack:
        Definition.EncounterId = TEXT("SurviveAlienHuntingPack");
        Definition.DisplayName = NSLOCTEXT("Threats", "AlienHuntingPack", "Eliminate the alien hunting pack");
        Definition.SpawnGroups = {
            ThreatGroup(EThreatArchetype::AlienBipedHunter, 2),
            ThreatGroup(EThreatArchetype::AlienQuadrupedStalker, 3)
        };
        Definition.CurrencyReward = 425;
        break;
    case EThreatEncounterPreset::AlienBrood:
        Definition.EncounterId = TEXT("PurgeAlienBrood");
        Definition.DisplayName = NSLOCTEXT("Threats", "AlienBrood", "Purge the arachnoped brood");
        Definition.SpawnGroups = {
            ThreatGroup(EThreatArchetype::AlienArachnopedAmbusher, 6),
            ThreatGroup(EThreatArchetype::AlienQuadrupedStalker, 1)
        };
        Definition.CurrencyReward = 450;
        break;
    case EThreatEncounterPreset::MixedAlienIncursion:
        Definition.EncounterId = TEXT("ContainAlienIncursion");
        Definition.DisplayName = NSLOCTEXT("Threats", "MixedAlienIncursion", "Contain the alien incursion");
        Definition.SpawnGroups = {
            ThreatGroup(EThreatArchetype::AlienBipedHunter, 2),
            ThreatGroup(EThreatArchetype::AlienQuadrupedStalker, 2),
            ThreatGroup(EThreatArchetype::AlienArachnopedAmbusher, 3)
        };
        Definition.CurrencyReward = 550;
        break;
    case EThreatEncounterPreset::Custom:
    default:
        Definition.EncounterId = TEXT("CustomMissionThreat");
        Definition.DisplayName = NSLOCTEXT("Threats", "CustomThreat", "Neutralize hostile forces");
        Definition.SpawnGroups.Reset();
        break;
    }
    return Definition;
}

void AShipThreatDirector::HandleThreatKilled()
{
    if (!HasAuthority() || EncounterState != EThreatEncounterState::Active)
    {
        return;
    }

    if (EncounterDefinition.bPrimaryAntagonist)
    {
        if (UGameInstance* GameInstance = GetGameInstance())
        {
            if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
            {
                Missions->AddObjectiveProgress(EncounterDefinition.EncounterId, 1.0f);
            }
        }
    }

    if (GetRemainingThreatCount() == 0)
    {
        CompleteEncounter();
    }
}

void AShipThreatDirector::HandleBloomStageChanged(EBloomStage NewStage)
{
    if (bAutoStart && EncounterState == EThreatEncounterState::Dormant)
    {
        StartEncounter();
    }
}

void AShipThreatDirector::RegisterMissionObjective()
{
    if (!EncounterDefinition.bPrimaryAntagonist || EncounterDefinition.EncounterId.IsNone())
    {
        return;
    }

    UGameInstance* GameInstance = GetGameInstance();
    UMissionObjectiveSubsystem* Missions = GameInstance
        ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    if (!Missions)
    {
        return;
    }

    FMissionObjectiveDefinition Objective;
    Objective.ObjectiveId = EncounterDefinition.EncounterId;
    Objective.Title = EncounterDefinition.DisplayName;
    Objective.Description = NSLOCTEXT("Threats", "EliminateThreatObjective",
        "Neutralize every hostile contact. This threat is tracked separately from Bloom activity.");
    const bool bHumanBoarders = !EncounterDefinition.SpawnGroups.IsEmpty()
        && AShipboardThreat::GetArchetypeTuning(EncounterDefinition.SpawnGroups[0].Archetype).Faction
            != EThreatFaction::Alien;
    Objective.Type = bHumanBoarders
        ? EMissionObjectiveType::RepelBoarders
        : EMissionObjectiveType::EliminateThreats;
    Objective.TargetProgress = FMath::Max(1, ActiveThreats.Num());
    Objective.bAutoActivate = true;
    Objective.bBlocksJumpWhileUnresolved = EncounterDefinition.bBlocksJumpWhileActive;
    Objective.CurrencyReward = EncounterDefinition.CurrencyReward;
    Missions->AddObjective(Objective);
}

void AShipThreatDirector::CompleteEncounter()
{
    EncounterState = EThreatEncounterState::Completed;
    ActiveThreats.Reset();
    OnEncounterStateChanged.Broadcast(EncounterDefinition.EncounterId, EncounterState);
}

FTransform AShipThreatDirector::ChooseSpawnTransform(FRandomStream& Random, int32 SpawnIndex,
    const TArray<AShipSection*>& Sections) const
{
    FVector Location;
    if (!SpawnAnchors.IsEmpty())
    {
        const AActor* Anchor = SpawnAnchors[SpawnIndex % SpawnAnchors.Num()];
        Location = IsValid(Anchor) ? Anchor->GetActorLocation() : GetActorLocation();
    }
    else if (!Sections.IsEmpty())
    {
        const AShipSection* Section = Sections[Random.RandRange(0, Sections.Num() - 1)];
        const FVector Extent = Section->SectionBounds->GetScaledBoxExtent() * 0.7f;
        Location = Section->GetActorLocation() + FVector(
            Random.FRandRange(-Extent.X, Extent.X),
            Random.FRandRange(-Extent.Y, Extent.Y),
            95.0f);
    }
    else
    {
        const float Angle = Random.FRandRange(-PI, PI);
        const float Radius = Random.FRandRange(200.0f, EncounterDefinition.FallbackSpawnRadius);
        Location = GetActorLocation() + FVector(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, 95.0f);
    }
    return FTransform(FRotator(0.0f, Random.FRandRange(-180.0f, 180.0f), 0.0f), Location);
}
