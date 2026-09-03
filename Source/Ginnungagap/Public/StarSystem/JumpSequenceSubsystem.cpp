#include "JumpSequenceSubsystem.h"
#include "Meta/RunSeedSubsystem.h"
#include "../CoopSurvivalCharacter.h"
#include "../Ship/ShipHelmSystem.h"
#include "../Ship/SensorArraySystem.h"
#include "../Ship/CryoPodSystem.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "../Ship/LifeSupportSystem.h"
#include "../Ship/ShipNavigationSubsystem.h"
#include "../Ship/ShipSection.h"
#include "../Bloom/BloomDirector.h"
#include "../Meta/RunOutcomeSubsystem.h"
#include "../Mission/MissionObjectiveSubsystem.h"
#include "../HazardZoneActor.h"
#include "ProceduralStarSystemMap.h"
#include "PelagosOrbitalArrivalDirector.h"
#include "ResourceNodeActor.h"
#include "DormantCollectorSystem.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

namespace
{
    EBloomHazardType MapHazardCategoryToBloomHazard(EHazardCategory Category)
    {
        switch (Category)
        {
        case EHazardCategory::BlackHole:
        case EHazardCategory::ExcessiveGravityWell:
        case EHazardCategory::MicrogravityShear:
            return EBloomHazardType::Microgravity;
        case EHazardCategory::SolarRadiationStorm:
        case EHazardCategory::CosmicRadiationBelt:
            return EBloomHazardType::Radiation;
        case EHazardCategory::MicroDebrisField:
            return EBloomHazardType::Dust;
        case EHazardCategory::ThermalExtreme:
            return EBloomHazardType::Thermal;
        default:
            return EBloomHazardType::Radiation;
        }
    }

    // GenerateRandomSystemData() only ever sets Category/Severity/MappedBloomHazardType, leaving
    // FHazardEntry::EnvironmentPreset default-constructed - derive an actual environment state here
    // so spawned AHazardZoneActors are mechanically distinct per category/severity instead of all
    // sharing identical (default) physics values.
    FPhysicsEnvironmentState BuildEnvironmentStateForHazard(const FHazardEntry& Hazard)
    {
        FPhysicsEnvironmentState State;
        const float Severity = FMath::Clamp(Hazard.Severity, 0.0f, 1.0f);

        switch (Hazard.Category)
        {
        case EHazardCategory::BlackHole:
        case EHazardCategory::ExcessiveGravityWell:
            State.GravityMultiplier = 1.0f + Severity * 5.0f;
            break;
        case EHazardCategory::MicrogravityShear:
            State.bMicrogravityZone = true;
            State.GravityMultiplier = FMath::Max(0.05f, 1.0f - Severity);
            break;
        case EHazardCategory::SolarRadiationStorm:
            State.bSolarStormActive = true;
            State.SolarRadiationFlux = Severity * 100.0f;
            break;
        case EHazardCategory::CosmicRadiationBelt:
            State.SolarRadiationFlux = Severity * 50.0f;
            break;
        case EHazardCategory::MicroDebrisField:
            State.DustDensity = Severity;
            break;
        case EHazardCategory::ThermalExtreme:
            State.TemperatureC = Severity >= 0.5f ? FMath::Lerp(20.0f, 300.0f, Severity) : FMath::Lerp(20.0f, -200.0f, 1.0f - Severity);
            break;
        default:
            break;
        }

        return State;
    }
}

URunSeedSubsystem& UJumpSequenceSubsystem::GetSeeds() const
{
    // Both are game-instance subsystems, so this one exists for exactly as long as that one does.
    // A null here is a programming error rather than a runtime condition, and failing loudly beats
    // silently falling back to unseeded randomness -- which would look fine until someone tried to
    // reproduce a run and could not.
    URunSeedSubsystem* Seeds = GetGameInstance() ? GetGameInstance()->GetSubsystem<URunSeedSubsystem>() : nullptr;
    checkf(Seeds, TEXT("URunSeedSubsystem missing; jump randomness would be irreproducible"));
    return *Seeds;
}

void UJumpSequenceSubsystem::Deinitialize()
{
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            World->GetTimerManager().ClearTimer(WarningTimerHandle);
        }
    }

    Super::Deinitialize();
}

FStarSystemData UJumpSequenceSubsystem::GenerateRandomSystemData() const
{
    URunSeedSubsystem& Seeds = GetSeeds();
    FStarSystemData Data;
    Data.SystemID = FGuid::NewGuid();
    Data.DisplayName = FString::Printf(TEXT("System-%04d"), Seeds.RandRange(RunSeedChannels::JumpGeneration, 1000, 9999));
    Data.DangerTier = Seeds.RandRange(RunSeedChannels::JumpGeneration, 1, 5);

    const int32 HazardCount = Seeds.RandRange(RunSeedChannels::JumpGeneration, MinHazardsPerSystem, MaxHazardsPerSystem);
    for (int32 i = 0; i < HazardCount; ++i)
    {
        FHazardEntry Hazard;
        Hazard.Category = static_cast<EHazardCategory>(Seeds.RandRange(RunSeedChannels::JumpGeneration, 0, static_cast<int32>(EHazardCategory::MicrogravityShear)));
        Hazard.Severity = Seeds.FRandRange(RunSeedChannels::JumpGeneration, 0.2f, 1.0f);
        Hazard.MappedBloomHazardType = MapHazardCategoryToBloomHazard(Hazard.Category);
        Data.Hazards.Add(Hazard);
    }

    const TArray<EResourceAcquisitionMethod> AllMethods = { EResourceAcquisitionMethod::ShipSystemReactivation, EResourceAcquisitionMethod::EVARetrieval, EResourceAcquisitionMethod::DroneDispatch };
    const int32 ResourceCount = Seeds.RandRange(RunSeedChannels::JumpGeneration, MinResourcesPerSystem, MaxResourcesPerSystem);
    for (int32 i = 0; i < ResourceCount; ++i)
    {
        FResourceEntry Resource;
        Resource.ResourceType = static_cast<EStarSystemResourceType>(Seeds.RandRange(RunSeedChannels::JumpGeneration, 0, static_cast<int32>(EStarSystemResourceType::PowerCells)));
        Resource.Quantity = Seeds.RandRange(RunSeedChannels::JumpGeneration, 5, 25);
        Resource.bCriticallyNeeded = Seeds.RollChance(RunSeedChannels::JumpGeneration, 0.2f);

        const int32 MethodCount = Seeds.RandRange(RunSeedChannels::JumpGeneration, 1, AllMethods.Num());
        while (Resource.AvailableMethods.Num() < MethodCount)
        {
            Resource.AvailableMethods.AddUnique(AllMethods[Seeds.RandRange(RunSeedChannels::JumpGeneration, 0, AllMethods.Num() - 1)]);
        }

        Data.Resources.Add(Resource);
    }

    return Data;
}

void UJumpSequenceSubsystem::GenerateJumpCandidates()
{
    URunSeedSubsystem& Seeds = GetSeeds();
    CurrentCandidates.Reset();
    SelectedCandidateIndex = INDEX_NONE;

    ASensorArraySystem* Sensors = nullptr;
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            for (TActorIterator<ASensorArraySystem> It(World); It; ++It)
            {
                Sensors = *It;
                break;
            }
        }
    }

    const float FalsificationChance = ComputeFalsificationChance(Sensors);

    for (int32 Index = 0; Index < MaxCandidates; ++Index)
    {
        FJumpCandidate Candidate;
        Candidate.ActualData = GenerateRandomSystemData();

        if (Seeds.RollChance(RunSeedChannels::Falsification, FalsificationChance))
        {
            FStarSystemData Decoy = GenerateRandomSystemData();
            Decoy.SystemID = Candidate.ActualData.SystemID;
            Decoy.DisplayName = Candidate.ActualData.DisplayName;
            Candidate.DisplayedData = Decoy;
            Candidate.bIsFalsified = true;
        }
        else
        {
            Candidate.DisplayedData = Candidate.ActualData;
            Candidate.bIsFalsified = false;
        }

        CurrentCandidates.Add(Candidate);
    }
}

bool UJumpSequenceSubsystem::SelectJumpCandidate(int32 CandidateIndex)
{
    if (CurrentPhase != EJumpPhase::Cruising || !CurrentCandidates.IsValidIndex(CandidateIndex))
    {
        return false;
    }

    SelectedCandidateIndex = CandidateIndex;
    return true;
}

bool UJumpSequenceSubsystem::BeginJumpWarningCountdown()
{
    if (CurrentPhase != EJumpPhase::Cruising || !CurrentCandidates.IsValidIndex(SelectedCandidateIndex))
    {
        return false;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GI->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            if (!Missions->CanBeginJump())
            {
                return false;
            }
        }
    }

    CurrentPhase = EJumpPhase::WarningCountdown;
    WarningSecondsRemaining = WarningCountdownSeconds;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            World->GetTimerManager().SetTimer(WarningTimerHandle, this, &UJumpSequenceSubsystem::TickWarningCountdown, 1.0f, true);
        }
    }

    return true;
}

void UJumpSequenceSubsystem::TickWarningCountdown()
{
    WarningSecondsRemaining = FMath::Max(0.0f, WarningSecondsRemaining - 1.0f);
    OnJumpWarningTick(WarningSecondsRemaining);

    if (WarningSecondsRemaining <= 0.0f)
    {
        if (UGameInstance* GI = GetGameInstance())
        {
            if (UWorld* World = GI->GetWorld())
            {
                World->GetTimerManager().ClearTimer(WarningTimerHandle);
            }
        }

        ExecuteJump();
    }
}

bool UJumpSequenceSubsystem::IsCharacterOutsideShip(const ACoopSurvivalCharacter* Character) const
{
    if (!Character)
    {
        return false;
    }

    UWorld* World = Character->GetWorld();
    UShipNavigationSubsystem* NavSubsystem = World ? World->GetSubsystem<UShipNavigationSubsystem>() : nullptr;
    return NavSubsystem && NavSubsystem->GetSectionContainingLocation(Character->GetActorLocation()) == nullptr;
}

void UJumpSequenceSubsystem::ResolveCharacterJumpFate(ACoopSurvivalCharacter* Character)
{
    URunSeedSubsystem& Seeds = GetSeeds();
    if (!Character || Character->bIsDead)
    {
        return;
    }

    if (IsCharacterOutsideShip(Character))
    {
        if (Seeds.RollChance(RunSeedChannels::JumpFate, EVAInstantFatalChance))
        {
            Character->HealthPercent = 0.0f;
            Character->bIsDead = true;
        }
        else
        {
            Character->HealthPercent = FMath::Max(1.0f, Character->HealthPercent * 0.25f);
            Character->OxygenLevelPercent = FMath::Max(1.0f, Character->OxygenLevelPercent * 0.25f);
        }
        return;
    }

    bool bProtectedByCryo = false;
    if (UWorld* World = Character->GetWorld())
    {
        for (TActorIterator<ACryoPodSystem> It(World); It; ++It)
        {
            if (It->bIsOccupied && It->OccupyingCharacter.Get() == Character && It->IsFunctioning())
            {
                bProtectedByCryo = true;
                break;
            }
        }
    }

    if (!bProtectedByCryo)
    {
        Character->HealthPercent = FMath::Max(NoPodMinHealthPercent, Character->HealthPercent - NoPodDetrimentalHealthLoss);
        if (UPlayerStatusEffectComponent* StatusEffects = Character->GetStatusEffectComponent())
        {
            const float Severity = FMath::Clamp(0.35f + JumpsCompleted * 0.08f, 0.0f, 1.0f);
            StatusEffects->ApplyStatusEffect(EPlayerStatusEffect::JumpPsychosis, Severity, 300.0f,
                EPlayerStatusSource::JumpExposure);
        }
    }
}

float UJumpSequenceSubsystem::ComputeFalsificationChance(ASensorArraySystem* Sensors) const
{
    float Chance = BaseFalsificationChance;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            if (Director->CurrentStage >= EBloomStage::Puppeteer)
            {
                const int32 StagesBeyond = static_cast<int32>(Director->CurrentStage) - static_cast<int32>(EBloomStage::Puppeteer);
                Chance += FalsificationChancePerStageBeyondPuppeteer * StagesBeyond;
            }
        }
    }

    if (Sensors)
    {
        Chance *= Sensors->GetFalsificationResistance();
    }

    return FMath::Clamp(Chance, 0.0f, MaxFalsificationChance);
}

void UJumpSequenceSubsystem::ExecuteJump()
{
    if (!CurrentCandidates.IsValidIndex(SelectedCandidateIndex))
    {
        CurrentPhase = EJumpPhase::Cruising;
        return;
    }

    CurrentPhase = EJumpPhase::Jumping;
    ++JumpsCompleted;

    UGameInstance* GI = GetGameInstance();
    UWorld* World = GI ? GI->GetWorld() : nullptr;
    UBloomDirector* Director = GI ? GI->GetSubsystem<UBloomDirector>() : nullptr;

    float TotalHeadingOffsetMagnitude = 0.0f;

    if (World)
    {
        for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
        {
            ResolveCharacterJumpFate(*It);
        }

        for (TActorIterator<AShipHelmSystem> It(World); It; ++It)
        {
            TotalHeadingOffsetMagnitude += It->CurrentHeadingOffset.Size();
            It->ConsumeHeadingOffset(1.0f);
        }
    }

    PendingLandingErrorSeverityBonus = FMath::Clamp(TotalHeadingOffsetMagnitude / LandingErrorOffsetScale, 0.0f, 1.0f) * MaxLandingErrorSeverityBonus;

    if (Director)
    {
        Director->OnSystemJump();

        if (World)
        {
            for (TActorIterator<ACryoPodSystem> It(World); It; ++It)
            {
                Director->RollForJumpSabotage(*It);
            }

            for (TActorIterator<ALifeSupportSystem> It(World); It; ++It)
            {
                Director->RollForJumpSabotage(*It);
            }
        }
    }

    CompleteArrival();
}

void UJumpSequenceSubsystem::CompleteArrival()
{
    if (CurrentCandidates.IsValidIndex(SelectedCandidateIndex))
    {
        CurrentSystemData = CurrentCandidates[SelectedCandidateIndex].ActualData;

        if (PendingLandingErrorSeverityBonus > 0.0f)
        {
            for (FHazardEntry& Hazard : CurrentSystemData.Hazards)
            {
                Hazard.Severity = FMath::Clamp(Hazard.Severity + PendingLandingErrorSeverityBonus, 0.0f, 1.0f);
            }
        }
    }

    PendingLandingErrorSeverityBonus = 0.0f;
    CurrentCandidates.Reset();
    SelectedCandidateIndex = INDEX_NONE;
    CurrentPhase = EJumpPhase::Arrival;

    // A contact from the departed system must never survive as a stale helm/HUD waypoint.
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ASensorArraySystem> It(World); It; ++It)
        {
            It->ClearTrackedContact();
        }
    }

    DespawnSystemContentActors();
    SpawnSystemContentActors();

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GI->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->ResetForNextSystem();
        }
    }

    OnArrivalComplete(CurrentSystemData);

    // Authored arrival maps can now take over from the generic jump sequence without
    // coupling the ship UI to a specific level Blueprint.
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<APelagosOrbitalArrivalDirector> It(World); It; ++It)
        {
            It->NotifyJumpArrival(CurrentSystemData);
        }
    }

    if (IsFinalJump())
    {
        if (UGameInstance* GI = GetGameInstance())
        {
            if (URunOutcomeSubsystem* RunOutcome = GI->GetSubsystem<URunOutcomeSubsystem>())
            {
                RunOutcome->EvaluateDestinationArrival();
            }
        }
    }
}

void UJumpSequenceSubsystem::DespawnSystemContentActors()
{
    for (const TObjectPtr<AActor>& Actor : SpawnedSystemContentActors)
    {
        if (Actor)
        {
            Actor->Destroy();
        }
    }

    SpawnedSystemContentActors.Reset();
}

void UJumpSequenceSubsystem::SpawnSystemContentActors()
{
    URunSeedSubsystem& Seeds = GetSeeds();
    UGameInstance* GI = GetGameInstance();
    UWorld* World = GI ? GI->GetWorld() : nullptr;
    if (!World)
    {
        return;
    }

    TArray<AShipSection*> Sections;
    for (TActorIterator<AShipSection> It(World); It; ++It)
    {
        Sections.Add(*It);
    }

    const FVector ShipOrigin = Sections.Num() > 0 ? Sections[0]->GetActorLocation() : FVector::ZeroVector;

    AProceduralStarSystemMap* SystemMap = World->SpawnActor<AProceduralStarSystemMap>(
        AProceduralStarSystemMap::StaticClass(), ShipOrigin, FRotator::ZeroRotator);
    if (SystemMap)
    {
        SystemMap->BuildSystem(CurrentSystemData, ShipOrigin);
        SpawnedSystemContentActors.Add(SystemMap);
    }

    // Placed well outside every section's bounds so UShipNavigationSubsystem::GetSectionContainingLocation
    // returns null there, satisfying AResourceNodeActor's own EVA/DroneDispatch gating (see
    // AProceduralShipBuilder::BuildShip for the same convention).
    int32 PlacementSalt = 1;
    auto RandomExteriorLocation = [&ShipOrigin, &SystemMap, &PlacementSalt, &Seeds]() -> FVector
    {
        if (SystemMap)
        {
            return SystemMap->SampleGameplayLocation(PlacementSalt++);
        }
        const float Angle = Seeds.FRandRange(RunSeedChannels::ArrivalPlacement, 0.0f, 2.0f * PI);
        const float Distance = Seeds.FRandRange(RunSeedChannels::ArrivalPlacement, 8000.0f, 10000.0f);
        return ShipOrigin + FVector(FMath::Cos(Angle) * Distance, FMath::Sin(Angle) * Distance, 0.0f);
    };

    for (int32 HazardIndex = 0; HazardIndex < CurrentSystemData.Hazards.Num(); ++HazardIndex)
    {
        const FHazardEntry& Hazard = CurrentSystemData.Hazards[HazardIndex];
        const FVector HazardLocation = SystemMap ? SystemMap->GetHazardLocation(HazardIndex) : RandomExteriorLocation();
        AHazardZoneActor* Zone = World->SpawnActor<AHazardZoneActor>(AHazardZoneActor::StaticClass(), HazardLocation, FRotator::ZeroRotator);
        if (Zone)
        {
            Zone->Tags.AddUnique(TEXT("GeneratedSystemContent"));
            Zone->EnvironmentState = BuildEnvironmentStateForHazard(Hazard);
            const float RegionRadius = FMath::Lerp(25000.0f, 140000.0f, FMath::Clamp(Hazard.Severity, 0.0f, 1.0f));
            Zone->MaxFalloffDistance = RegionRadius;
            Zone->ZoneBounds->SetBoxExtent(FVector(RegionRadius));
            SpawnedSystemContentActors.Add(Zone);
        }
    }

    for (int32 ResourceIndex = 0; ResourceIndex < CurrentSystemData.Resources.Num(); ++ResourceIndex)
    {
        const FResourceEntry& Resource = CurrentSystemData.Resources[ResourceIndex];
        if (Resource.AvailableMethods.Num() == 0)
        {
            continue;
        }

        const EResourceAcquisitionMethod Method = Resource.AvailableMethods[Seeds.RandRange(RunSeedChannels::ArrivalPlacement, 0, Resource.AvailableMethods.Num() - 1)];
        const bool bNeedsExteriorPlacement = Method == EResourceAcquisitionMethod::EVARetrieval || Method == EResourceAcquisitionMethod::DroneDispatch;
        const FVector SpawnLocation = bNeedsExteriorPlacement || Sections.Num() == 0
            ? (SystemMap ? SystemMap->GetResourceLocation(ResourceIndex) : RandomExteriorLocation())
            : Sections[Seeds.RandRange(RunSeedChannels::ArrivalPlacement, 0, Sections.Num() - 1)]->GetActorLocation();

        if (!bNeedsExteriorPlacement && SystemMap)
        {
            SystemMap->OverrideResourceLocation(ResourceIndex, SpawnLocation);
        }

        AResourceNodeActor* Node = World->SpawnActor<AResourceNodeActor>(AResourceNodeActor::StaticClass(), SpawnLocation, FRotator::ZeroRotator);
        if (!Node)
        {
            continue;
        }

        Node->RequiredMethod = Method;
        if (bNeedsExteriorPlacement)
        {
            Node->Tags.AddUnique(TEXT("GeneratedSystemContent"));
        }
        Node->ResourceType = Resource.ResourceType;
        Node->Quantity = Resource.Quantity;
        Node->GeneratedResourceIndex = ResourceIndex;
        SpawnedSystemContentActors.Add(Node);

        if (Method == EResourceAcquisitionMethod::ShipSystemReactivation)
        {
            ADormantCollectorSystem* Collector = World->SpawnActor<ADormantCollectorSystem>(
                ADormantCollectorSystem::StaticClass(), SpawnLocation + FVector(100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
            if (Collector)
            {
                Node->RequiredSystem = Collector;
                SpawnedSystemContentActors.Add(Collector);
            }
        }
    }
}
