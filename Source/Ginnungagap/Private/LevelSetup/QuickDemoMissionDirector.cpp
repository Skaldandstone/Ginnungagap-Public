#include "Net/UnrealNetwork.h"
#include "Ship/ShipThrustGravity.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/ShipboardWeaponDefinition.h"
#include "Weapons/WeaponMountComponent.h"
#include "Inventory/ItemDefinition.h"
#include "Inventory/InventoryComponent.h"
#include "NavigationSystem.h"

#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Engine/GameInstance.h"
#include "Engine/PointLight.h"
#include "EngineUtils.h"
#include "Equipment/EquipmentComponent.h"
#include "HazardZoneActor.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "Meta/MenuManagerSubsystem.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/ModularShipRoom.h"
#include "TimerManager.h"

namespace QuickDemoObjectives
{
    const FName SuitUp(TEXT("QD_SuitUp"));
    const FName ReachWorkshop(TEXT("QD_ReachWorkshop"));
    const FName RestorePower(TEXT("QD_RestorePower"));
    const FName SealBreach(TEXT("QD_SealBreach"));
    const FName ReachCIC(TEXT("QD_ReachCIC"));

    FEquipmentItem MakeStarterSuit()
    {
        FEquipmentItem Suit;
        Suit.Type = EEquipmentType::PressureSeal;
        Suit.Slot = EEquipmentSlot::Chest;
        Suit.DisplayName = TEXT("Cryo Emergency Pressure Suit");
        Suit.Description = TEXT("A basic pressure-rated suit issued from the cryo bay emergency rack.");
        Suit.Stats.PressureResistance = 101.3f;
        Suit.Stats.SuitIntegrityBonus = 15.0f;
        Suit.DurabilityLossPerSecond = 0.015f;
        return Suit;
    }

    FMissionObjectiveDefinition MakeObjective(FName Id, const FText& Title, const FText& Description,
        EMissionObjectiveType Type, FName Prerequisite = NAME_None)
    {
        FMissionObjectiveDefinition Definition;
        Definition.ObjectiveId = Id;
        Definition.Title = Title;
        Definition.Description = Description;
        Definition.Type = Type;
        Definition.TargetProgress = 1.0f;
        Definition.bAutoActivate = true;
        Definition.bHiddenUntilActive = true;
        Definition.bBlocksJumpWhileUnresolved = true;
        if (!Prerequisite.IsNone())
        {
            Definition.PrerequisiteObjectiveIds.Add(Prerequisite);
        }
        return Definition;
    }
}

AQuickDemoMissionDirector::AQuickDemoMissionDirector()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    // No root component, so distance relevancy has nothing to measure; every client needs the
    // completed list regardless of where they stand.
    bAlwaysRelevant = true;
}

void AQuickDemoMissionDirector::DefineObjectives(UMissionObjectiveSubsystem* Missions)
{
    Missions->AddObjective(QuickDemoObjectives::MakeObjective(
        QuickDemoObjectives::SuitUp,
        // "Suit up" contradicted what the player could see: they wake already wearing the cryo
        // bodysuit. The instruction is about the layer that is missing -- the bodysuit is not
        // pressure-rated, the oversuit on the rack is.
        NSLOCTEXT("QuickDemo", "SuitUpTitle", "Seal a pressure oversuit"),
        NSLOCTEXT("QuickDemo", "SuitUpDescription", "Your cryo bodysuit is not pressure-rated. Draw and seal an oversuit from any lit rack before leaving the bay."),
        EMissionObjectiveType::Custom));
    Missions->AddObjective(QuickDemoObjectives::MakeObjective(
        QuickDemoObjectives::ReachWorkshop,
        NSLOCTEXT("QuickDemo", "WorkshopTitle", "Find the nearby workshop"),
        NSLOCTEXT("QuickDemo", "WorkshopDescription", "Ship struck. Long-jump drive disengaged. Enter the starter workshop and recover its basic field equipment."),
        EMissionObjectiveType::Salvage, QuickDemoObjectives::SuitUp));
    Missions->AddObjective(QuickDemoObjectives::MakeObjective(
        QuickDemoObjectives::RestorePower,
        NSLOCTEXT("QuickDemo", "PowerTitle", "Restore the ship main bus"),
        NSLOCTEXT("QuickDemo", "PowerDescription", "Go forward, descend to deck 2, then route back to Main Power Control."),
        EMissionObjectiveType::Repair, QuickDemoObjectives::ReachWorkshop));
    Missions->AddObjective(QuickDemoObjectives::MakeObjective(
        QuickDemoObjectives::SealBreach,
        NSLOCTEXT("QuickDemo", "BreachTitle", "Seal the Bloom impact breach"),
        NSLOCTEXT("QuickDemo", "BreachDescription", "Return to deck 3 and patch the vacuum rupture near CIC."),
        EMissionObjectiveType::Repair, QuickDemoObjectives::RestorePower));
    Missions->AddObjective(QuickDemoObjectives::MakeObjective(
        QuickDemoObjectives::ReachCIC,
		NSLOCTEXT("QuickDemo", "CICTitle", "Bring the Combat Information Center online"),
		NSLOCTEXT("QuickDemo", "CICDescription", "Crank the CIC door override, enter the command room, and boot the tactical console."),
        EMissionObjectiveType::Investigate, QuickDemoObjectives::SealBreach));

}

void AQuickDemoMissionDirector::BeginPlay()
{
    Super::BeginPlay();

    // Arcing damage sparks from the start: every point light tagged Arcing gets a hard flicker.
    for (TActorIterator<APointLight> It(GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("Arcing"))) continue;
        if (UPointLightComponent* Light = It->GetComponentByClass<UPointLightComponent>())
        {
            ArcLights.Add(Light);
            ArcBaseIntensity.Add(Light->Intensity);
        }
    }
    if (ArcLights.Num() > 0)
    {
        GetWorldTimerManager().SetTimer(ArcFlickerTimer, this, &AQuickDemoMissionDirector::TickArcFlicker, 0.06f, true);
    }

    if (!GetGameInstance())
    {
        return;
    }

    // Every machine defines the chain, because the mission subsystem is a game-instance
    // subsystem and does not replicate: a client that never defined the objectives had a HUD
    // stuck on MISSION INITIALIZING and beacons with nothing to show. State is the server's;
    // it arrives as the replicated completed list below.
    UMissionObjectiveSubsystem* Missions = GetGameInstance()->GetSubsystem<UMissionObjectiveSubsystem>();
    if (!Missions)
    {
        return;
    }
    Missions->ResetAllObjectives();
    Missions->OnObjectiveChanged.AddDynamic(this, &AQuickDemoMissionDirector::HandleObjectiveChanged);
    DefineObjectives(Missions);

    if (!HasAuthority())
    {
        OnRep_CompletedObjectives();
        UE_LOG(LogTemp, Display, TEXT("Quick-demo mission mirrored on client (%d objectives completed so far)."), ReplicatedCompletedObjectives.Num());
        return;
    }


    // This level is generated and dressed by scripts that save from headless sessions, which
    // cannot rebuild navigation, and Dynamic runtime generation trusts whatever navmesh was saved.
    // The demo shipped that way with nothing able to path anywhere; found when the player start
    // stopped projecting after a scripted repair. A full rebuild from live geometry takes seconds
    // with the job count raised, and makes the map self-healing regardless of how it was saved.
    if (UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
    {
        Navigation->SetMaxSimultaneousTileGenerationJobsCount(16);
        Navigation->Build();
    }

    // The ship starts with its main bus down, which until now it did not.
    //
    // AModularShipRoom::bPowered defaults to true and the only calls anywhere in the project were
    // SetPowered(true) -- here, replaying a checkpoint, and in QuickDemoPowerStation. Nothing ever
    // powered a room down, so every room sat at Nominal from the first frame and the third objective
    // restored power that had never been lost.
    //
    // It was invisible in review because the failure only exists at runtime. Nominal drives the
    // room's IdentityLight to 1250 and a cold blue, which floods every room and fights the warm
    // per-room emergency palette the dressing pass was built around -- but hero shots render the
    // editor world, where BeginPlay never runs and those lights sit at the 0 they were saved with.
    // The renders looked right for the wrong reason, and nobody had seen what the game does.
    //
    // Before RestoreCheckpointState rather than after: that runs next tick and turns power back on
    // if RestorePower is already complete, so a resumed run still lands in the right state.
    for (TActorIterator<AModularShipRoom> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("QuickDemoShipRoom")))
        {
            It->SetPowered(false);
        }
    }

    UE_LOG(LogTemp, Display, TEXT("Quick-demo mission initialized: suit, workshop, power, breach, CIC."));
    GetWorldTimerManager().SetTimerForNextTick(this, &AQuickDemoMissionDirector::RestoreCheckpointState);
}

void AQuickDemoMissionDirector::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->OnObjectiveChanged.RemoveDynamic(this, &AQuickDemoMissionDirector::HandleObjectiveChanged);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void AQuickDemoMissionDirector::HandleObjectiveChanged(FName ObjectiveId, EMissionObjectiveState NewState)
{
    if (HasAuthority() && NewState == EMissionObjectiveState::Completed)
    {
        ReplicatedCompletedObjectives.AddUnique(ObjectiveId);
        ForceNetUpdate();
    }
    if (!HasAuthority() || bRestoringCheckpoint || NewState != EMissionObjectiveState::Completed)
    {
        return;
    }

    APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    UGameInstance* GameInstance = GetGameInstance();
    if (!PlayerPawn || !GameInstance)
    {
        return;
    }

    if (UShipCheckpointSubsystem* Checkpoints = GameInstance->GetSubsystem<UShipCheckpointSubsystem>())
    {
        const FName CheckpointId(*FString::Printf(TEXT("%s_Checkpoint"), *ObjectiveId.ToString()));
        if (Checkpoints->RecordCheckpoint(GetWorld(), CheckpointId, PlayerPawn->GetActorTransform()))
        {
            UE_LOG(LogTemp, Display, TEXT("Quick-demo checkpoint recorded after %s."), *ObjectiveId.ToString());
        }
    }

    // ReachCIC is the chain's last objective. Nothing else in the demo watches for that, so the
    // beat sheet's own last beat -- "cut to the title screen" -- never happened; the console just
    // finished booting and the player stood there. ShowStartScreen already exists and already
    // works, it just had no caller here.
    if (ObjectiveId == QuickDemoObjectives::ReachCIC)
    {
        GetWorldTimerManager().SetTimer(TitleCutTimer, this, &AQuickDemoMissionDirector::ShowTitleCut,
            TitleCutDelaySeconds, false);
    }
}

void AQuickDemoMissionDirector::ShowTitleCut()
{
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMenuManagerSubsystem* Menus = GameInstance->GetSubsystem<UMenuManagerSubsystem>())
        {
            Menus->ShowStartScreen();
        }
    }
}

void AQuickDemoMissionDirector::RestoreCheckpointState()
{
    if (!HasAuthority() || !bRestoreCheckpointOnStart)
    {
        return;
    }

    UGameInstance* GameInstance = GetGameInstance();
    APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    UShipCheckpointSubsystem* Checkpoints = GameInstance
        ? GameInstance->GetSubsystem<UShipCheckpointSubsystem>() : nullptr;
    if (!Checkpoints || !PlayerPawn || !Checkpoints->HasCheckpointForWorld(GetWorld()))
    {
        return;
    }

    const TArray<FName> CompletedObjectiveIds = Checkpoints->GetCheckpointRecord().CompletedObjectiveIds;
    // A resumed run does not wake in the pod: the opening stands down before the checkpoint moves
    // the crew, or it would hold them asleep in a tube two decks from where they actually are and
    // the release could never reach it.
    for (TActorIterator<AQuickDemoOpeningSequence> It(GetWorld()); It; ++It)
    {
        It->Skip();
    }
    bRestoringCheckpoint = true;
    const bool bRestored = Checkpoints->RestoreCheckpoint(GetWorld(), PlayerPawn);
    bRestoringCheckpoint = false;
    if (bRestored)
    {
        for (const FName& Id : CompletedObjectiveIds) { ReplicatedCompletedObjectives.AddUnique(Id); }
        ForceNetUpdate();
        ApplyRestoredWorldState(CompletedObjectiveIds);
        UE_LOG(LogTemp, Display, TEXT("Quick-demo checkpoint restored with %d completed objectives."),
            CompletedObjectiveIds.Num());
    }
}

void AQuickDemoMissionDirector::ApplyRestoredWorldState(const TArray<FName>& CompletedObjectiveIds)
{
    if (CompletedObjectiveIds.Contains(QuickDemoObjectives::RestorePower))
    {
        for (TActorIterator<AShipThrustGravity> It(GetWorld()); It; ++It) { It->ApplyThrust(); }
    }
    if (CompletedObjectiveIds.Contains(QuickDemoObjectives::SuitUp))
    {
        if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0))
        {
            if (UEquipmentComponent* Equipment = PlayerPawn->FindComponentByClass<UEquipmentComponent>();
                Equipment && !Equipment->IsSlotEquipped(EEquipmentSlot::Chest))
            {
                Equipment->EquipItem(QuickDemoObjectives::MakeStarterSuit());
            }
            // The slot alone is not the suit: the character must know it is sealed, or the boots,
            // the lamp and every vacuum door refuse a crew who plainly suited up last session.
            if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(PlayerPawn))
            {
                Character->SetPressureOversuitEquipped(true);
                Character->SetWristLampOn(true);
            }
        }
    }

    if (CompletedObjectiveIds.Contains(QuickDemoObjectives::RestorePower))
    {
        // The same emergency bus the power station brings up live, so a resumed run lands in
        // the same ship the player left.
        BringUpEmergencyLighting();
        for (TActorIterator<AModularShipRoom> It(GetWorld()); It; ++It)
        {
            if (It->ActorHasTag(TEXT("QuickDemoShipRoom")))
            {
                It->SetEmergencyPower(true);
                It->SetPowered(true);
            }
        }
    }

    if (CompletedObjectiveIds.Contains(QuickDemoObjectives::SealBreach))
    {
        for (TActorIterator<AHazardZoneActor> It(GetWorld()); It; ++It)
        {
            if (It->ActorHasTag(TEXT("QuickDemoVacuumHazard")))
            {
                It->SetActorTickEnabled(false);
                It->ZoneBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }

    if (CompletedObjectiveIds.Contains(QuickDemoObjectives::ReachCIC))
    {
        for (TActorIterator<ABulkheadDoor> It(GetWorld()); It; ++It)
        {
            if (It->ActorHasTag(TEXT("QuickDemoCICDoor")))
            {
                It->SetLocked(false);
                It->Unseal();
            }
        }
    }
}

void AQuickDemoMissionDirector::OnRep_CompletedObjectives()
{
    UGameInstance* GameInstance = GetGameInstance();
    UMissionObjectiveSubsystem* Missions = GameInstance ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    if (!Missions || ReplicatedCompletedObjectives.IsEmpty())
    {
        return;
    }
    // Completion without rewards, and the subsystem activates whatever is next.
    Missions->RestoreCompletedObjectives(ReplicatedCompletedObjectives);
}

void AQuickDemoMissionDirector::BringUpEmergencyLighting()
{
    EmergencyLights.Reset();
    EmergencyBaseIntensity.Reset();
    EmergencyDropoutUntil.Reset();
    for (TActorIterator<APointLight> It(GetWorld()); It; ++It)
    {
        UPointLightComponent* Light = It->GetComponentByClass<UPointLightComponent>();
        if (!Light) continue;
        if (It->ActorHasTag(TEXT("QuickDemoUtilityLight")))
        {
            // The fixtures: dull red, a third of what a live bus would give.
            Light->SetVisibility(true);
            Light->SetLightColor(FLinearColor(1.0f, 0.16f, 0.06f));
            EmergencyLights.Add(Light);
            EmergencyBaseIntensity.Add(120.0f);
        }
        else if (It->ActorHasTag(TEXT("CorvettePractical")))
        {
            // The practicals: their own amber, at less than half strength.
            Light->SetVisibility(true);
            EmergencyLights.Add(Light);
            EmergencyBaseIntensity.Add(FMath::Max(Light->Intensity, 60.0f) * 0.4f);
        }
    }
    EmergencyDropoutUntil.Init(0.0f, EmergencyLights.Num());
    EmergencyClock = 0.0f;
    TickEmergencyFlicker();
    GetWorldTimerManager().SetTimer(EmergencyFlickerTimer, this, &AQuickDemoMissionDirector::TickEmergencyFlicker, 0.09f, true);
}

void AQuickDemoMissionDirector::TickEmergencyFlicker()
{
    EmergencyClock += 0.09f;
    for (int32 i = 0; i < EmergencyLights.Num(); ++i)
    {
        UPointLightComponent* Light = EmergencyLights[i];
        if (!Light) continue;
        const float Phase = i * 1.73f;
        // A low flicker, a slow beacon pulse every couple of seconds, and the odd dropout.
        float Level = 0.62f + 0.18f * FMath::Sin(EmergencyClock * 5.3f + Phase) + 0.12f * FMath::Sin(EmergencyClock * 13.1f + Phase * 2.3f);
        if (FMath::Fmod(EmergencyClock + Phase * 0.31f, 2.6f) < 0.22f) Level *= 1.9f;
        if (EmergencyDropoutUntil[i] > EmergencyClock) Level = 0.04f;
        else if (FMath::FRand() < 0.012f) EmergencyDropoutUntil[i] = EmergencyClock + FMath::FRandRange(0.2f, 0.7f);
        Light->SetIntensity(EmergencyBaseIntensity[i] * FMath::Clamp(Level, 0.0f, 2.0f));
    }
}

void AQuickDemoMissionDirector::TickArcFlicker()
{
    for (int32 i = 0; i < ArcLights.Num(); ++i)
    {
        UPointLightComponent* Light = ArcLights[i];
        if (!Light) continue;
        // Mostly dark with bursts: a spark is a flash, not a lamp.
        const float Roll = FMath::FRand();
        const float Level = Roll < 0.55f ? 0.03f : (Roll < 0.85f ? FMath::FRandRange(0.4f, 1.0f) : FMath::FRandRange(1.4f, 2.6f));
        Light->SetIntensity(ArcBaseIntensity[i] * Level);
    }
}

void AQuickDemoMissionDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AQuickDemoMissionDirector, ReplicatedCompletedObjectives);
}

bool AQuickDemoMissionDirector::IsObjectiveActive(const UObject* WorldContext, FName ObjectiveId)
{
    const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
    const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    UMissionObjectiveSubsystem* Missions = GameInstance
        ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    FMissionObjectiveRuntime Runtime;
    return Missions && Missions->GetObjective(ObjectiveId, Runtime)
        && Runtime.State == EMissionObjectiveState::Active;
}

bool AQuickDemoMissionDirector::CompleteActiveObjective(const UObject* WorldContext, FName ObjectiveId)
{
    const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
    UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    UMissionObjectiveSubsystem* Missions = GameInstance
        ? GameInstance->GetSubsystem<UMissionObjectiveSubsystem>() : nullptr;
    return Missions && IsObjectiveActive(WorldContext, ObjectiveId) && Missions->CompleteObjective(ObjectiveId);
}

AQuickDemoObjectiveBeacon::AQuickDemoObjectiveBeacon()
{
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    MarkerText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("MarkerText"));
    MarkerText->SetupAttachment(SceneRoot);
    MarkerText->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
    MarkerText->SetVerticalAlignment(EVerticalTextAligment::EVRTA_TextCenter);
    MarkerText->SetWorldSize(24.0f);
    MarkerText->SetTextRenderColor(FColor(255, 176, 35));
    MarkerText->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MarkerText->SetVisibility(false);
}

void AQuickDemoObjectiveBeacon::BeginPlay()
{
    Super::BeginPlay();
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->OnObjectiveChanged.AddDynamic(this, &AQuickDemoObjectiveBeacon::HandleObjectiveChanged);
        }
    }
    MarkerText->SetText(FText::Format(NSLOCTEXT("QuickDemo", "BeaconFormat", ">> {0} <<"), MarkerLabel));
    RefreshVisibility();
}

void AQuickDemoObjectiveBeacon::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->OnObjectiveChanged.RemoveDynamic(this, &AQuickDemoObjectiveBeacon::HandleObjectiveChanged);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void AQuickDemoObjectiveBeacon::HandleObjectiveChanged(FName ChangedObjectiveId,
    EMissionObjectiveState NewState)
{
    if (ChangedObjectiveId == ObjectiveId)
    {
        RefreshVisibility();
    }
}

void AQuickDemoObjectiveBeacon::RefreshVisibility()
{
    bMarkerActive = AQuickDemoMissionDirector::IsObjectiveActive(this, ObjectiveId);
    MarkerText->SetVisibility(bMarkerActive);
    SetActorTickEnabled(bMarkerActive);
}

void AQuickDemoObjectiveBeacon::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bMarkerActive)
    {
        const float Pulse = 0.78f + FMath::Sin(GetWorld()->GetTimeSeconds() * 3.5f) * 0.22f;
        MarkerText->SetWorldSize(24.0f * Pulse);
    }
}

AQuickDemoObjectiveTrigger::AQuickDemoObjectiveTrigger()
{
    PrimaryActorTick.bCanEverTick = false;
    TriggerBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerBounds"));
    SetRootComponent(TriggerBounds);
    TriggerBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TriggerBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    TriggerBounds->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    TriggerBounds->OnComponentBeginOverlap.AddDynamic(this, &AQuickDemoObjectiveTrigger::OnTriggerBeginOverlap);
}

void AQuickDemoObjectiveTrigger::OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent,
    AActor* OtherActor, UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex,
    bool bFromSweep, const FHitResult& SweepResult)
{
    if (Cast<ACoopSurvivalCharacter>(OtherActor)
        && AQuickDemoMissionDirector::CompleteActiveObjective(this, ObjectiveId))
    {
        TriggerBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }
}

AQuickDemoSuitStation::AQuickDemoSuitStation()
{
    Activity.Type = EPlayerActivityType::SuitPatching;
    Activity.Mechanic = EActivityMechanic::Timed;
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "SuitStationActivity", "Seal pressure suit");
    Activity.DurationSeconds = 2.5f;
    Activity.bBloomSensitive = false;
    // No count: a crew that comes back to reseal a suit is surviving, not cheating.
    RemainingUses = -1;
    CooldownSeconds = 0.0f;

    StarterSuit = QuickDemoObjectives::MakeStarterSuit();

    // The rack: a rail across the front of the locker and the suit hanging from it. The station
    // sits with its back to the wall and +X into the room; the suit faces the room too.
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> SuitAsset(
        TEXT("/Game/Characters/PlayerSuits/PrimaryOversuits/SpaceMarshalManny/SK_SpaceMarshal_Manny.SK_SpaceMarshal_Manny"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeAsset(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RailMaterial(
        TEXT("/Game/Modular_Scifi_Mechanic_Base/Material/MI/MI_Metal_03.MI_Metal_03"));
    RackRail = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RackRail"));
    RackRail->SetupAttachment(Mesh);
    if (CubeAsset.Succeeded()) RackRail->SetStaticMesh(CubeAsset.Object);
    if (RailMaterial.Succeeded()) RackRail->SetMaterial(0, RailMaterial.Object);
    RackRail->SetRelativeLocation(FVector(55.0f, 0.0f, 110.0f));
    RackRail->SetRelativeScale3D(FVector(0.05f, 1.1f, 0.05f));
    RackRail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> BackingAsset(TEXT("/Game/Assets/Gameplay/SalvageBatch03/Meshes/SM_SalvageToolRack.SM_SalvageToolRack"));
    RackBacking = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RackBacking"));
    RackBacking->SetupAttachment(Mesh);
    if (BackingAsset.Succeeded()) RackBacking->SetStaticMesh(BackingAsset.Object);
    // The rack stands 70 to 218 above its origin on the floor; the station's origin is a metre up.
    RackBacking->SetRelativeLocation(FVector(22.0f, 0.0f, -100.0f));
    RackBacking->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    RackBacking->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RackSuit = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("RackSuit"));
    RackSuit->SetupAttachment(Mesh);
    if (SuitAsset.Succeeded()) RackSuit->SetSkeletalMesh(SuitAsset.Object);
    // The station's origin is a metre up the wall; the suit's is at its boots. Hung a hand below
    // the rail, boots clear of the deck, facing the room (the mesh faces +Y at rest).
    RackSuit->SetRelativeLocation(FVector(55.0f, 0.0f, -96.0f));
    RackSuit->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    RackSuit->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RackSuit->SetGenerateOverlapEvents(false);
    RackSuit->SetCastShadow(true);
    RackSuit->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
}

void AQuickDemoSuitStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AQuickDemoSuitStation, bSuitTaken);
}

void AQuickDemoSuitStation::OnRep_SuitTaken()
{
    if (RackSuit)
    {
        RackSuit->SetVisibility(!bSuitTaken, true);
    }
}

bool AQuickDemoSuitStation::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, QuickDemoObjectives::SuitUp);
}

void AQuickDemoSuitStation::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority() || !Player)
    {
        return;
    }

    // The suit goes into the chest slot; a slot that already holds one (a resumed run, a second
    // visit to reseal) is not a reason to leave the crew unsealed.
    if (UEquipmentComponent* Equipment = Player->FindComponentByClass<UEquipmentComponent>())
    {
        if (!Equipment->EquipItem(StarterSuit) && !Equipment->IsSlotEquipped(EEquipmentSlot::Chest))
        {
            UE_LOG(LogTemp, Warning, TEXT("Suit station %s: %s could not take the suit (chest slot refused it)."), *GetName(), *Player->GetName());
            return;
        }
    }
    else
    {
        return;
    }

    if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Player))
    {
        Character->SetPressureSuitRole(SuitRole);
        Character->SetPressureOversuitEquipped(true);
        // The wrist lamp comes on with the suit: the bay is the last lit room they will see.
        Character->SetWristLampOn(true);
        UE_LOG(LogTemp, Display, TEXT("Suit station %s: %s sealed in the %s suit (oversuit=%d, lamp=%d)."), *GetName(), *Player->GetName(),
            *UEnum::GetValueAsString(SuitRole), Character->bPressureOversuitEquipped ? 1 : 0, Character->IsWristLampOn() ? 1 : 0);
    }
    if (!bSuitTaken)
    {
        bSuitTaken = true;
        OnRep_SuitTaken();
        ForceNetUpdate();
    }

    Super::OnActivityCompleted_Implementation(Player);
    AQuickDemoMissionDirector::CompleteActiveObjective(this, QuickDemoObjectives::SuitUp);
}

AQuickDemoBreachStation::AQuickDemoBreachStation()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "PatchBreachActivity", "Patch the hull rupture");
    Activity.DurationSeconds = 7.0f;
    Activity.MinimumBloomInterference = 0.35f;
    CompletionEffect = EMaintenanceActivityEffect::SealBreach;
    EffectStrength = 1.0f;
    RemainingUses = 1;
}

bool AQuickDemoBreachStation::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, QuickDemoObjectives::SealBreach);
}

void AQuickDemoBreachStation::OnActivityCompleted_Implementation(APawn* Player)
{
    Super::OnActivityCompleted_Implementation(Player);

    if (!HasAuthority())
    {
        return;
    }

    for (TActorIterator<AHazardZoneActor> It(GetWorld()); It; ++It)
    {
        if (*It == TargetActor || It->ActorHasTag(TEXT("QuickDemoVacuumHazard")))
        {
            It->SetActorTickEnabled(false);
            It->ZoneBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    }
    AQuickDemoMissionDirector::CompleteActiveObjective(this, QuickDemoObjectives::SealBreach);
}

AQuickDemoCICAccessStation::AQuickDemoCICAccessStation()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "CICOverrideActivity", "Crank CIC door override");
    Activity.DurationSeconds = 4.0f;
    Activity.bBloomSensitive = true;
    RemainingUses = 1;
}

bool AQuickDemoCICAccessStation::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, QuickDemoObjectives::ReachCIC);
}

AQuickDemoCICConsole::AQuickDemoCICConsole()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "CICConsoleActivity", "Boot CIC tactical console");
    Activity.Mechanic = EActivityMechanic::DiagnosticSequence;
    Activity.DurationSeconds = 6.0f;
    Activity.PuzzleSteps = 5;
    Activity.MinimumBloomInterference = 0.2f;
    RemainingUses = 1;
}

bool AQuickDemoCICConsole::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, QuickDemoObjectives::ReachCIC);
}

void AQuickDemoCICConsole::OnActivityCompleted_Implementation(APawn* Player)
{
    Super::OnActivityCompleted_Implementation(Player);
    if (HasAuthority())
    {
        AQuickDemoMissionDirector::CompleteActiveObjective(this, QuickDemoObjectives::ReachCIC);
    }
}

namespace
{
    /**
     * Gives a station something to look like.
     *
     * AActivityStation creates its Mesh component and never assigns a mesh, so a station class that
     * does not set one spawns completely invisible -- collision, prompt and all, with nothing to
     * see. Both benches shipped that way: placed, wired, tested and unreachable, because the tests
     * assert what a bench does rather than whether it is there.
     *
     * Set here rather than in the placement script so the class cannot produce an invisible actor
     * no matter who spawns it. A scenario is still free to override it afterwards.
     */
    void SetStationMesh(UStaticMeshComponent* Mesh, const TCHAR* AssetPath)
    {
        if (!Mesh)
        {
            return;
        }
        if (UStaticMesh* Asset = LoadObject<UStaticMesh>(nullptr, AssetPath))
        {
            Mesh->SetStaticMesh(Asset);
        }
    }

    /** As SetStationMesh, and soft for the same reason: a missing asset leaves the field null. */
    template <typename T>
    T* LoadStationAsset(const TCHAR* AssetPath)
    {
        return LoadObject<T>(nullptr, AssetPath);
    }

    // What the workshop actually hands over.
    //
    // AQuickDemoWorkshopBench has always had the machinery to arm the player -- it sets
    // StartingWeaponClass, calls GrantStartingWeapon, walks GrantedItems into the inventory -- and
    // every one of those fields was left at its default, so `if (GrantedWeaponClass)` was false on
    // every run. GrantStartingWeapon's own comment says the demo "hands a weapon over at the
    // workshop rather than in cryo"; the workshop handed over nothing. These are the values that
    // sentence was written against.
    //
    // The fastener tool rather than anything more martial: it is tagged Tool.Fastener, its listed
    // rooms are Fabrication and MachineShop, and a ship's crew waking into an emergency should be
    // holding the thing that was already on the bench. It is a weapon because it has to be, not
    // because anyone designed it as one, which is the whole tone of the game.
    const TCHAR* FastenerToolClass =
        TEXT("/Game/Assets/Gameplay/EarlyProjectileWeapons/Blueprints/BP_Weapon_PressureBottleFastenerTool.BP_Weapon_PressureBottleFastenerTool_C");
    const TCHAR* FastenerToolDefinition =
        TEXT("/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool.DA_Weapon_PressureBottleFastenerTool");

    // Two consumables, not ten. A bench that empties a storeroom into the player removes every
    // reason to search the ship, and the demo is eight minutes long.
    //
    // Sealant because suit integrity is the resource the survival loop actually spends, and the gel
    // pack because burns are now something the ship can inflict -- hazard zones above 50 C accrue
    // BurnTrauma as of this pass, and handing out an injury with no treatment for it would be worse
    // than not having the injury.
    const TCHAR* SuitPatchItem =
        TEXT("/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_SuitPatchSealant.DA_Item_SuitPatchSealant");
    const TCHAR* CoolantGelItem =
        TEXT("/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_CoolantGelPack.DA_Item_CoolantGelPack");

    // Upright operator terminal for drawing equipment; a lower unit for laying gear on to mend.
    const TCHAR* WorkshopBenchMesh =
        TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/COMPUTER/SM_COMPUTER_01.SM_COMPUTER_01");
    const TCHAR* RepairBenchMesh =
        TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/COMPUTER/SM_COMPUTER_02.SM_COMPUTER_02");
}

AQuickDemoWorkshopBench::AQuickDemoWorkshopBench()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "WorkshopBenchActivity", "Take the engineer's tool");
    Activity.DurationSeconds = 5.0f;

    // Component replacement is the closest existing effect, but the real outcome is the handover
    // below. Strength is left low because the bench is not what is being repaired.
    CompletionEffect = EMaintenanceActivityEffect::ReplaceComponent;
    EffectStrength = 0.1f;

    // Once. A bench that could be drawn from repeatedly would turn the workshop into an armoury
    // and remove any reason to be careful with what it hands over.
    RemainingUses = 1;

    SetStationMesh(Mesh, WorkshopBenchMesh);

    // Defaults rather than requirements. Each is still EditAnywhere, so a level or a Blueprint can
    // override any of them; what changes is that an un-overridden bench now does something.
    if (UClass* ToolClass = LoadClass<AShipboardWeapon>(nullptr, FastenerToolClass))
    {
        GrantedWeaponClass = ToolClass;
        GrantedWeaponDefinition = LoadStationAsset<UShipboardWeaponDefinition>(FastenerToolDefinition);
    }

    // Guarded individually: a missing item asset should cost the player that item, not the rest of
    // the kit. AddItem is null-checked at the far end too, but an empty entry in this array would
    // still be a silent lie about what the bench contains.
    if (UItemDefinition* Sealant = LoadStationAsset<UItemDefinition>(SuitPatchItem))
    {
        GrantedItems.Add(Sealant);
    }
    if (UItemDefinition* Coolant = LoadStationAsset<UItemDefinition>(CoolantGelItem))
    {
        GrantedItems.Add(Coolant);
    }
}

bool AQuickDemoWorkshopBench::CanStartActivity_Implementation(APawn* Player) const
{
    return Super::CanStartActivity_Implementation(Player)
        && AQuickDemoMissionDirector::IsObjectiveActive(this, QuickDemoObjectives::ReachWorkshop);
}

void AQuickDemoWorkshopBench::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority() || !Player)
    {
        return;
    }

    if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Player))
    {
        // Configure and grant rather than requiring the pawn to have been set up in advance. The
        // bench is where a scenario decides what the crew is armed with, so the decision lives
        // with the bench instead of being baked into every pawn that might visit it.
        if (GrantedWeaponClass)
        {
            // Every pawn is already armed by the time it reaches this bench: the character
            // constructor sets bSpawnDefaultWeapon and the mount spawns a captive bolt driver in
            // BeginPlay. GrantStartingWeapon refuses while anything is mounted, so without an
            // explicit release the grant below silently never fires -- the fastener tool was never
            // actually handed over in the demo. Releasing first makes the swap deliberate, which is
            // exactly the case that refusal guards against a double-fire, not this.
            if (UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>())
            {
                Mount->ReleaseWeapon();
            }

            Character->StartingWeaponClass = GrantedWeaponClass;
            Character->StartingWeaponDefinition = GrantedWeaponDefinition;
            Character->GrantStartingWeapon();
        }

        if (UInventoryComponent* Inventory = Character->FindComponentByClass<UInventoryComponent>())
        {
            for (UItemDefinition* Item : GrantedItems)
            {
                if (Item)
                {
                    // One of each. AddItem refuses when mass or slots are exhausted, which is a
                    // legitimate outcome rather than an error -- an overloaded crew member simply
                    // cannot carry more.
                    Inventory->AddItem(Item, 1);
                }
            }
        }
    }

    Super::OnActivityCompleted_Implementation(Player);
    AQuickDemoMissionDirector::CompleteActiveObjective(this, QuickDemoObjectives::ReachWorkshop);
}

AQuickDemoSuitRepairBench::AQuickDemoSuitRepairBench()
{
    Activity.DisplayName = NSLOCTEXT("QuickDemo", "SuitRepairActivity", "Patch and re-seal worn gear");
    Activity.DurationSeconds = 6.0f;
    CompletionEffect = EMaintenanceActivityEffect::RepairSuit;

    // A meaningful fraction of a slot's durability, not a full restore. Repair should be worth
    // walking back for without making damage irrelevant.
    EffectStrength = 0.4f;

    // Unlimited, using the -1 sentinel the base class documents. Zero happens to behave the same
    // way -- the decrement is guarded on being above zero -- but reads as "none left" to anyone
    // scanning it, which is the opposite of what is meant.
    //
    // Deliberately unlimited: equipment degrades continuously, so a counter that ran out would
    // only delay the same one-way slide rather than answer it.
    RemainingUses = -1;

    SetStationMesh(Mesh, RepairBenchMesh);
}
