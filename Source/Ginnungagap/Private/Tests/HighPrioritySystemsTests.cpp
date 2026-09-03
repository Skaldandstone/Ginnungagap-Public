#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Bloom/BloomDirector.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Inventory/InventoryComponent.h"
#include "Inventory/ItemDefinition.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMissionObjectiveFlowTest,
    "Ginnungagap.Gameplay.Missions.ObjectiveFlow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMissionObjectiveFlowTest::RunTest(const FString& Parameters)
{
    UGameInstance* GameInstance = NewObject<UGameInstance>();
    UMissionObjectiveSubsystem* Missions = NewObject<UMissionObjectiveSubsystem>(GameInstance);
    FMissionObjectiveDefinition Repair;
    Repair.ObjectiveId = TEXT("RepairLifeSupport");
    Repair.TargetProgress = 2.0f;
    TestTrue(TEXT("Adds required objective"), Missions->AddObjective(Repair));
    TestFalse(TEXT("Unresolved objective blocks jump"), Missions->CanBeginJump());
    TestTrue(TEXT("Progress is accepted"), Missions->AddObjectiveProgress(Repair.ObjectiveId, 1.0f));
    TestTrue(TEXT("Target progress completes objective"), Missions->AddObjectiveProgress(Repair.ObjectiveId, 1.0f));
    TestTrue(TEXT("Completed objective permits jump"), Missions->CanBeginJump());

    FMissionObjectiveDefinition FollowUp;
    FollowUp.ObjectiveId = TEXT("VerifyAtmosphere");
    FollowUp.PrerequisiteObjectiveIds.Add(Repair.ObjectiveId);
    TestTrue(TEXT("Adds prerequisite objective"), Missions->AddObjective(FollowUp));
    FMissionObjectiveRuntime Runtime;
    TestTrue(TEXT("Can query objective"), Missions->GetObjective(FollowUp.ObjectiveId, Runtime));
    TestEqual(TEXT("Satisfied prerequisite auto-activates"), Runtime.State, EMissionObjectiveState::Active);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FInventoryCapacityAndTransferTest,
    "Ginnungagap.Gameplay.Inventory.CapacityAndTransfer",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FInventoryCapacityAndTransferTest::RunTest(const FString& Parameters)
{
    UInventoryComponent* Source = NewObject<UInventoryComponent>();
    UInventoryComponent* Target = NewObject<UInventoryComponent>();
    UItemDefinition* Item = NewObject<UItemDefinition>();
    Item->ItemId = TEXT("RepairPart");
    Item->MaxStackSize = 4;
    Item->UnitMassKg = 2.0f;
    Source->MaxSlots = 2;
    Source->MaxMassKg = 10.0f;

    TestTrue(TEXT("Adds within mass and slot capacity"), Source->AddItem(Item, 5));
    TestEqual(TEXT("Quantity spans stacks"), Source->GetItemQuantity(Item), 5);
    TestFalse(TEXT("Rejects excess mass"), Source->AddItem(Item, 1));
    TestTrue(TEXT("Transfers atomically"), Source->TransferItemTo(Target, Item, 2));
    TestEqual(TEXT("Source quantity updated"), Source->GetItemQuantity(Item), 3);
    TestEqual(TEXT("Target quantity updated"), Target->GetItemQuantity(Item), 2);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipDamageAndPowerNodeTest,
    "Ginnungagap.Gameplay.Ship.DamageAndPowerNode",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipDamageAndPowerNodeTest::RunTest(const FString& Parameters)
{
    UShipDamageComponent* Damage = NewObject<UShipDamageComponent>();
    Damage->ApplyShipDamage(EShipDamageType::Breach, 0.8f);
    TestTrue(TEXT("Severe breach is critical"), Damage->HasCriticalDamage());
    TestTrue(TEXT("Breach can be sealed"), Damage->SealBreach(0.8f));

    UShipPowerNodeComponent* Generator = NewObject<UShipPowerNodeComponent>();
    Generator->Role = EShipPowerNodeRole::Generator;
    Generator->GenerationUnits = 100.0f;
    Generator->SetDamageFraction(0.25f);
    TestEqual(TEXT("Generator damage reduces output"), Generator->GetEffectiveGeneration(), 75.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBloomStageLifecycleTest,
    "Ginnungagap.Gameplay.Bloom.StageLifecycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBloomStageLifecycleTest::RunTest(const FString& Parameters)
{
    UGameInstance* GameInstance = NewObject<UGameInstance>();
    UBloomDirector* Bloom = NewObject<UBloomDirector>(GameInstance);
    TestEqual(TEXT("Bloom begins latent"), Bloom->GetCurrentStage(), EBloomStage::Latent);

    Bloom->AdvanceStage();
    TestEqual(TEXT("First progression creates a colony"), Bloom->GetCurrentStage(), EBloomStage::Colony);

    for (int32 Index = 0; Index < 10; ++Index)
    {
        Bloom->AdvanceStage();
    }
    TestEqual(TEXT("Progression clamps at manifestation"), Bloom->GetCurrentStage(), EBloomStage::Manifestation);

    Bloom->ForceResetBloom();
    TestEqual(TEXT("Purge/reset returns the visual signal to latent"), Bloom->GetCurrentStage(), EBloomStage::Latent);
    Bloom->RestoreStage(EBloomStage::Puppeteer);
    TestEqual(TEXT("Persisted Bloom stage restores exactly"), Bloom->GetCurrentStage(), EBloomStage::Puppeteer);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipCheckpointRecordTest,
    "Ginnungagap.Gameplay.Ship.CheckpointRecord",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipCheckpointRecordTest::RunTest(const FString& Parameters)
{
    FShipCheckpointRecord Record;
    TestFalse(TEXT("Empty checkpoint is invalid"), Record.IsValid());

    Record.DistrictMapName = TEXT("L_Small_Companionway_Showcase");
    Record.CheckpointId = TEXT("RestoreSystems_Checkpoint");
    Record.RespawnTransform = FTransform(FRotator(0.0f, 90.0f, 0.0f), FVector(1200.0f, 25.0f, 100.0f));
    Record.CompletedObjectiveIds.Add(TEXT("RestoreSystems"));
    Record.BloomStage = EBloomStage::Swarm;

    TestTrue(TEXT("Populated checkpoint is valid"), Record.IsValid());
    TestTrue(TEXT("Checkpoint matches its district"), Record.IsForMap(TEXT("L_Small_Companionway_Showcase")));
    TestFalse(TEXT("Checkpoint rejects another district"), Record.IsForMap(TEXT("L_Large_CarrierConcourse_Showcase")));
    TestEqual(TEXT("Checkpoint retains objective completion"), Record.CompletedObjectiveIds.Num(), 1);
    TestEqual(TEXT("Checkpoint retains Bloom stage"), Record.BloomStage, EBloomStage::Swarm);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProceduralRoomPropAssetResolutionTest,
    "Ginnungagap.Gameplay.Ship.ProceduralRoomPropAssetResolution",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FProceduralRoomPropAssetResolutionTest::RunTest(const FString& Parameters)
{
    static const TCHAR* RoomPropPaths[] =
    {
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Command_HelmChair.SM_Command_HelmChair"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Command_HolographicTable.SM_Command_HolographicTable"),
        TEXT("/Game/Assets/Models/Environment/SM_Prop_ToolCabinet.SM_Prop_ToolCabinet"),
        TEXT("/Game/Assets/Models/DamageControl/SM_Emergency_RadiationBarrier.SM_Emergency_RadiationBarrier"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Medical_DiagnosticArch.SM_Medical_DiagnosticArch"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Medical_SupplyCabinet.SM_Medical_SupplyCabinet"),
        TEXT("/Game/Assets/Models/Environment/SM_Prop_Bunk.SM_Prop_Bunk"),
        TEXT("/Game/Assets/Models/Environment/SM_Prop_GalleyUnit.SM_Prop_GalleyUnit"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Cargo_Pallet.SM_Cargo_Pallet"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Cargo_HandLoader.SM_Cargo_HandLoader"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Engineering_ReactorCoil.SM_Engineering_ReactorCoil"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Engineering_CoolantPump.SM_Engineering_CoolantPump"),
        TEXT("/Game/Assets/Models/RoomMachinery/SM_Drone_LaunchCradle.SM_Drone_LaunchCradle"),
        TEXT("/Game/Assets/Models/DamageControl/SM_Emergency_PortableAirScrubber.SM_Emergency_PortableAirScrubber")
    };

    for (const TCHAR* AssetPath : RoomPropPaths)
    {
        TestNotNull(FString::Printf(TEXT("Procedural room prop resolves: %s"), AssetPath),
            LoadObject<UStaticMesh>(nullptr, AssetPath));
    }
    return true;
}

#endif
