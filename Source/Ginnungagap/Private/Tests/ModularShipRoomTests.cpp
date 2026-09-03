#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Ship/ModularShipRoom.h"
#include "Ship/BulkheadDoor.h"
#include "LevelSetup/ProceduralShipBuilder.h"
#include "Activities/ActivityPopulationTypes.h"
#include "Activities/MaintenanceActivityStations.h"
#include "Bloom/CrewCorpse.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "Ship/ShipHardpointPopulationDirector.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipRoomDefinitionValidationTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.DefinitionValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipRoomDefinitionValidationTest::RunTest(const FString& Parameters)
{
    FShipRoomModuleDefinition Definition;
    FString Error;
    TestFalse(TEXT("Default definition needs a display name"), Definition.IsValid(&Error));
    TestFalse(TEXT("Invalid definition reports a reason"), Error.IsEmpty());

    Definition.RoomCode = TEXT("MED-02");
    Definition.DisplayName = FText::FromString(TEXT("Auxiliary Medical Bay"));
    TestTrue(TEXT("Named standard-size room is valid"), Definition.IsValid(&Error));

    Definition.ModuleSize.Z = 99.0;
    TestFalse(TEXT("Undersized room is rejected"), Definition.IsValid(&Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipRoomSocketPairTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.SocketPairs",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipRoomSocketPairTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Forward pairs with aft"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Forward), EShipRoomSocket::Aft);
    TestEqual(TEXT("Aft pairs with forward"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Aft), EShipRoomSocket::Forward);
    TestEqual(TEXT("Port pairs with starboard"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Port), EShipRoomSocket::Starboard);
    TestEqual(TEXT("Starboard pairs with port"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Starboard), EShipRoomSocket::Port);
    TestEqual(TEXT("Forward-port pairs with aft-port"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::ForwardPort), EShipRoomSocket::AftPort);
    TestEqual(TEXT("Forward-starboard pairs with aft-starboard"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::ForwardStarboard), EShipRoomSocket::AftStarboard);
    TestEqual(TEXT("Up pairs with down"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Up), EShipRoomSocket::Down);
    TestEqual(TEXT("Down pairs with up"), AModularShipRoom::GetOppositeSocket(EShipRoomSocket::Down), EShipRoomSocket::Up);

    const AModularShipRoom* RoomDefaults = GetDefault<AModularShipRoom>();
    TestNotNull(TEXT("Room exposes a ceiling traversal socket"), RoomDefaults->GetBulkheadSocket(EShipRoomSocket::Up));
    TestNotNull(TEXT("Room exposes a deck traversal socket"), RoomDefaults->GetBulkheadSocket(EShipRoomSocket::Down));
    TestTrue(TEXT("Vertical sockets are enabled on the reusable room module"),
        RoomDefaults->IsSocketEnabled(EShipRoomSocket::Up) && RoomDefaults->IsSocketEnabled(EShipRoomSocket::Down));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipRoomGameplayProfileValidationTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.GameplayProfileValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipRoomGameplayProfileValidationTest::RunTest(const FString& Parameters)
{
    FShipRoomGameplayProfile Profile;
    FString Error;
    TestTrue(TEXT("Default gameplay profile is valid"), Profile.IsValid(&Error));
    Profile.PowerPriority = 11;
    TestFalse(TEXT("Power priorities above ten are rejected"), Profile.IsValid(&Error));
    Profile.PowerPriority = 10;
    Profile.HazardTier = 6;
    TestFalse(TEXT("Hazard tiers above five are rejected"), Profile.IsValid(&Error));
    Profile.HazardTier = 5;
    Profile.NominalPowerDraw = -1.0f;
    TestFalse(TEXT("Negative power draw is rejected"), Profile.IsValid(&Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipRoomConnectionValidationTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.ConnectionValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipRoomConnectionValidationTest::RunTest(const FString& Parameters)
{
    FShipRoomConnectionDefinition Connection;
    FString Error;
    TestFalse(TEXT("Empty endpoints are rejected"), Connection.IsValid(&Error));
    Connection.RoomA = TEXT("BRG-01");
    Connection.RoomB = TEXT("BRG-01");
    TestFalse(TEXT("Self connections are rejected"), Connection.IsValid(&Error));
    Connection.RoomB = TEXT("CIC-01");
    TestTrue(TEXT("Distinct endpoints are accepted"), Connection.IsValid(&Error));
    Connection.TransferCoefficient = 1.1f;
    TestFalse(TEXT("Transfer above one is rejected"), Connection.IsValid(&Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipGameplayHardpointValidationTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.GameplayHardpointValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipGameplayHardpointValidationTest::RunTest(const FString& Parameters)
{
    FShipGameplayHardpoint Hardpoint;
    FString Error;
    TestFalse(TEXT("Anonymous hardpoint is rejected"), Hardpoint.IsValid(&Error));
    Hardpoint.HardpointId = TEXT("ENG-01-REPAIR-00");
    Hardpoint.HardpointType = EShipGameplayHardpointType::DamageRepair;
    Hardpoint.ClearanceRadius = 90.0f;
    TestTrue(TEXT("Stable damage-repair hardpoint is valid"), Hardpoint.IsValid(&Error));
    Hardpoint.ClearanceRadius = -1.0f;
    TestFalse(TEXT("Negative hardpoint clearance is rejected"), Hardpoint.IsValid(&Error));

    const ABulkheadDoor* DoorDefaults = GetDefault<ABulkheadDoor>();
    TestNotNull(TEXT("Bulkhead exposes a room-side hardpoint"), DoorDefaults->RoomSideHardpoint.Get());
    TestNotNull(TEXT("Bulkhead exposes a corridor-side hardpoint"), DoorDefaults->CorridorSideHardpoint.Get());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDefaultCorvetteLayoutTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.DefaultCorvetteLayout",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FDefaultCorvetteLayoutTest::RunTest(const FString& Parameters)
{
    const AProceduralShipBuilder* Builder = GetDefault<AProceduralShipBuilder>();
    TestNotNull(TEXT("Builder class default exists"), Builder);
    if (!Builder)
    {
        return false;
    }

    TestEqual(TEXT("Corvette has thirteen room recipes"), Builder->RoomModules.Num(), 13);
    TestEqual(TEXT("Corvette has twelve graph edges"), Builder->RoomConnections.Num(), 12);
    TestTrue(TEXT("Generated corridors preserve player traversal width"), Builder->CorridorWidth >= 360.0f);
    TestTrue(TEXT("Generated corridors preserve standing height"), Builder->CorridorHeight >= 500.0f);
    TArray<FString> Errors;
    TestTrue(TEXT("Default corvette graph validates"), Builder->ValidateLayout(Errors));
    TestEqual(TEXT("Valid graph has no diagnostics"), Errors.Num(), 0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActivityPopulationConfigurationTest,
    "Ginnungagap.Gameplay.Activities.Population.DefaultConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FActivityPopulationConfigurationTest::RunTest(const FString& Parameters)
{
    const AProceduralShipBuilder* Builder = GetDefault<AProceduralShipBuilder>();
    TestNotNull(TEXT("Builder default exists"), Builder);
    if (!Builder) return false;
    TestTrue(TEXT("Activity population is enabled"), Builder->bPopulateActivityStations);
    TestTrue(TEXT("Population seed is stable and non-zero"), Builder->ActivityPopulationSeed != 0);
    TestTrue(TEXT("Minimum count does not exceed maximum"),
        Builder->MinActivitiesPerRoom <= Builder->MaxActivitiesPerRoom);
    TestTrue(TEXT("Spawn chance is normalized"),
        Builder->ActivitySpawnChance >= 0.0f && Builder->ActivitySpawnChance <= 1.0f);
    TestTrue(TEXT("Station spacing protects navigation"), Builder->MinimumActivitySpacing >= 100.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FShipHardpointPopulationConfigurationTest,
    "Ginnungagap.Gameplay.Ship.ModularRooms.HardpointPopulationConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipHardpointPopulationConfigurationTest::RunTest(const FString& Parameters)
{
    const AShipHardpointPopulationDirector* Director = GetDefault<AShipHardpointPopulationDirector>();
    TestNotNull(TEXT("Hardpoint population director class default exists"), Director);
    if (!Director)
    {
        return false;
    }
    TestTrue(TEXT("Hardpoint population is enabled by default"), Director->bPopulateOnBeginPlay);
    TestTrue(TEXT("Population seed is stable and non-zero"), Director->PopulationSeed != 0);
    TestTrue(TEXT("Bodies, obstacles, and Bloom all receive a positive default budget"),
        Director->BodyCount > 0 && Director->ObstacleCount > 0 && Director->BloomGrowthCount > 0);
    TestNotNull(TEXT("Body population uses the Bloom-possessable crew corpse"),
        Director->BodyActorClass.Get());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FActivitySpawnRecordValidationTest,
    "Ginnungagap.Gameplay.Activities.Population.SpawnRecordValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FActivitySpawnRecordValidationTest::RunTest(const FString& Parameters)
{
    FProceduralActivitySpawnRecord Record;
    TestFalse(TEXT("Empty spawn record is invalid"), Record.IsValid());
    Record.StationId = TEXT("ENG-01-ACT-00000001-00");
    Record.RoomCode = TEXT("ENG-01");
    Record.StationClass = ABreakerReroutingStation::StaticClass();
    Record.SlotIndex = 0;
    TestTrue(TEXT("Identified class-backed spawn record is valid"), Record.IsValid());

    FShipCheckpointRecord Checkpoint;
    TestEqual(TEXT("New checkpoints use activity-aware version"), Checkpoint.SaveVersion, 2);
    return true;
}

#endif
