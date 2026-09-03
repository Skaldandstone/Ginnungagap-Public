#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Bloom/BloomCorruptible.h"
#include "Components/StaticMeshComponent.h"
#include "Interfaces/Interactable.h"
#include "Robotics/ShipboardRobotArchetypes.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FShipboardRobotCleanArchetypeTest,
    "Ginnungagap.Gameplay.Robotics.CleanArchetypeDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipboardRobotCleanArchetypeTest::RunTest(const FString& Parameters)
{
    const ACompactMaintenanceRobot* Maintenance = GetDefault<ACompactMaintenanceRobot>();
    const ATallUtilityRobot* Utility = GetDefault<ATallUtilityRobot>();
    const AHeavyCargoRobot* Cargo = GetDefault<AHeavyCargoRobot>();
    const ASecuritySentryRobot* Security = GetDefault<ASecuritySentryRobot>();

    TestNotNull(TEXT("Maintenance archetype resolves"), Maintenance);
    TestNotNull(TEXT("Utility archetype resolves"), Utility);
    TestNotNull(TEXT("Cargo archetype resolves"), Cargo);
    TestNotNull(TEXT("Security archetype resolves"), Security);
    if (!Maintenance || !Utility || !Cargo || !Security)
    {
        return false;
    }

    const AShipboardRobotBase* Robots[] = {Maintenance, Utility, Cargo, Security};
    for (const AShipboardRobotBase* Robot : Robots)
    {
        TestTrue(TEXT("Clean robot starts operational"), Robot->bOperational);
        TestFalse(TEXT("Clean robot starts uncorrupted"), Robot->bBloomCorrupted);
        TestFalse(TEXT("Clean robot starts in standby, not working"), Robot->bWorking);
        TestEqual(TEXT("Clean robot state is standby"), Robot->RobotState, EShipboardRobotState::Standby);
        TestEqual(TEXT("Clean robot starts fully intact"), Robot->CurrentIntegrity, Robot->MaxIntegrity);
        TestEqual(TEXT("Clean robot starts fully charged"), Robot->BatteryCharge, 1.0f);
        TestNotNull(TEXT("Robot has collision bounds"), Robot->CollisionBounds.Get());
        TestNotNull(TEXT("Robot has a status light"), Robot->StatusLight.Get());
        TestTrue(TEXT("Robot supports player interaction"), Robot->GetClass()->ImplementsInterface(UInteractable::StaticClass()));
        TestTrue(TEXT("Robot supports Bloom corruption"), Robot->GetClass()->ImplementsInterface(UBloomCorruptible::StaticClass()));
        TestTrue(TEXT("Healthy clean robot can be corrupted"),
            IBloomCorruptible::Execute_CanBeBloomCorrupted(const_cast<AShipboardRobotBase*>(Robot)));
        TestFalse(TEXT("Standby robot cannot advance work"), Robot->CanPerformWork());

        TArray<UStaticMeshComponent*> VisualParts;
        Robot->GetComponents<UStaticMeshComponent>(VisualParts);
        for (const UStaticMeshComponent* Part : VisualParts)
        {
            if (!Part || !Part->GetStaticMesh())
            {
                continue;
            }
            const FString MeshName = Part->GetStaticMesh()->GetName().ToUpper();
            TestFalse(TEXT("Shipboard robot visual contains no wheel mesh"), MeshName.Contains(TEXT("WHEEL")));
            TestFalse(TEXT("Shipboard robot visual contains no tire mesh"), MeshName.Contains(TEXT("TIRE")));
            TestFalse(TEXT("Shipboard robot visual contains no track mesh"), MeshName.Contains(TEXT("TRACK")));
        }
    }

    TestEqual(TEXT("Maintenance role is correct"), Maintenance->RobotRole, EShipboardRobotRole::Maintenance);
    TestEqual(TEXT("Utility role is correct"), Utility->RobotRole, EShipboardRobotRole::Utility);
    TestEqual(TEXT("Cargo role is correct"), Cargo->RobotRole, EShipboardRobotRole::Cargo);
    TestEqual(TEXT("Security role is correct"), Security->RobotRole, EShipboardRobotRole::Security);

    TestTrue(TEXT("Maintenance robot has the highest repair output"),
        Maintenance->Capabilities.RepairOutput > Utility->Capabilities.RepairOutput
        && Utility->Capabilities.RepairOutput > Cargo->Capabilities.RepairOutput);
    TestTrue(TEXT("Security robot has the longest sensor range"),
        Security->Capabilities.SensorRangeCm > Utility->Capabilities.SensorRangeCm
        && Utility->Capabilities.SensorRangeCm > Maintenance->Capabilities.SensorRangeCm
        && Maintenance->Capabilities.SensorRangeCm > Cargo->Capabilities.SensorRangeCm);
    TestTrue(TEXT("Cargo robot has the highest carrying capacity"),
        Cargo->Capabilities.CarryCapacityKg > Utility->Capabilities.CarryCapacityKg
        && Utility->Capabilities.CarryCapacityKg > Maintenance->Capabilities.CarryCapacityKg);
    TestTrue(TEXT("Cargo robot has the highest integrity"),
        Cargo->MaxIntegrity > Utility->MaxIntegrity && Utility->MaxIntegrity > Maintenance->MaxIntegrity);

    TestNotNull(TEXT("Maintenance robot has a scanner"), Maintenance->SensorHead.Get());
    TestNotNull(TEXT("Maintenance robot has a manipulator"), Maintenance->ToolArm.Get());
    TestNotNull(TEXT("Utility robot has a chest display"), Utility->ChestDisplay.Get());
    TestNotNull(TEXT("Cargo robot has a left equipment pod"), Cargo->LeftCargoPod.Get());
    TestNotNull(TEXT("Cargo robot has a right equipment pod"), Cargo->RightCargoPod.Get());
    TestNotNull(TEXT("Cargo robot has a mechanical crane"), Cargo->IndustrialTool.Get());
    TestNotNull(TEXT("Security robot has a front-left magnetic clamp"), Security->FrontLeftClamp.Get());
    TestNotNull(TEXT("Security robot has a front-right magnetic clamp"), Security->FrontRightClamp.Get());
    TestNotNull(TEXT("Security robot has a rear-left magnetic clamp"), Security->RearLeftClamp.Get());
    TestNotNull(TEXT("Security robot has a rear-right magnetic clamp"), Security->RearRightClamp.Get());
    TestNotNull(TEXT("Security robot has a front-left magnetic pad"), Security->FrontLeftMagPad.Get());
    TestNotNull(TEXT("Security robot has a front-right magnetic pad"), Security->FrontRightMagPad.Get());
    TestNotNull(TEXT("Security robot has a rear-left magnetic pad"), Security->RearLeftMagPad.Get());
    TestNotNull(TEXT("Security robot has a rear-right magnetic pad"), Security->RearRightMagPad.Get());
    TestTrue(TEXT("Security robot starts magnetically anchored"), Security->bMagneticAnchorsEngaged);
    TestTrue(TEXT("Security magnetic clamps have positive holding strength"),
        Security->MagneticClampStrengthNewtons > 0.0f);
    TestNotNull(TEXT("Security robot has a scanner"), Security->SensorHead.Get());
    TestNotNull(TEXT("Security robot has a response arm"), Security->ResponseArm.Get());
    return true;
}

#endif
