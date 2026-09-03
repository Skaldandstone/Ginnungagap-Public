#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "CoopSurvivalCharacter.h"
#include "Components/PointLightComponent.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMagneticSuitContractTest,
    "Ginnungagap.PlayerSuit.MagneticSuit.Contract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMagneticSuitContractTest::RunTest(const FString& Parameters)
{
    FProperty* Boots = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("bMagneticBootsEnabled"));
    FProperty* Gloves = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("bMagneticGlovesActive"));
    FProperty* LeftGlove = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("bLeftMagneticGloveActive"));
    FProperty* RightGlove = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("bRightMagneticGloveActive"));
    FProperty* RotationThruster = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("bRotationThrusterActive"));
    FProperty* ThrusterFuel = FindFProperty<FProperty>(ACoopSurvivalCharacter::StaticClass(), TEXT("ThrusterFuelPercent"));
    TestNotNull(TEXT("Magnetic boot state is exposed to reflection"), Boots);
    TestNotNull(TEXT("Magnetic glove state is exposed to reflection"), Gloves);
    if (Boots) TestTrue(TEXT("Magnetic boot state replicates"), Boots->HasAnyPropertyFlags(CPF_Net));
    if (Gloves) TestTrue(TEXT("Magnetic glove state replicates"), Gloves->HasAnyPropertyFlags(CPF_Net));
    if (LeftGlove) TestTrue(TEXT("Left glove state replicates"), LeftGlove->HasAnyPropertyFlags(CPF_Net));
    if (RightGlove) TestTrue(TEXT("Right glove state replicates"), RightGlove->HasAnyPropertyFlags(CPF_Net));
    if (RotationThruster) TestTrue(TEXT("Rotation thruster state replicates"), RotationThruster->HasAnyPropertyFlags(CPF_Net));
    if (ThrusterFuel) TestTrue(TEXT("Thruster fuel replicates"), ThrusterFuel->HasAnyPropertyFlags(CPF_Net));

    TestNotNull(TEXT("Boot toggle is callable"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ToggleMagneticBoots")));
    TestNotNull(TEXT("Glove grip start is callable"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("BeginMagneticGloveGrip")));
    TestNotNull(TEXT("Rotation thruster is callable"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("BeginRotationThruster")));
    TestNotNull(TEXT("Right glove grip is callable"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("BeginRightMagneticGloveGrip")));
    TestNotNull(TEXT("Physics-object throw is callable"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ThrowMagneticObject")));
    TestNotNull(TEXT("Server validates glove targets"), ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ServerRequestGloveGrip")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMagneticSuitLifecycleTest,
    "Ginnungagap.PlayerSuit.MagneticSuit.LifecycleAndSafety",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMagneticSuitLifecycleTest::RunTest(const FString& Parameters)
{
    const ACoopSurvivalCharacter* Defaults = GetDefault<ACoopSurvivalCharacter>();
    TestNotNull(TEXT("Magnetic suit class defaults are available"), Defaults);
    if (Defaults)
    {
        TestFalse(TEXT("Boots start disengaged"), Defaults->AreMagneticBootsEnabled());
        TestFalse(TEXT("Left glove starts released"), Defaults->IsLeftMagneticGloveActive());
        TestFalse(TEXT("Right glove starts released"), Defaults->IsRightMagneticGloveActive());
        TestFalse(TEXT("Rotation thruster starts idle"), Defaults->IsRotationThrusterActive());
        TestEqual(TEXT("Thruster starts fully fueled"), Defaults->GetThrusterFuelPercent(), 100.0f);
        TestTrue(TEXT("Thruster drain is positive"), Defaults->ThrusterFuelDrainPerSecond > 0.0f);
        TestTrue(TEXT("Thruster recharge is positive"), Defaults->ThrusterFuelRechargePerSecond > 0.0f);
        TestTrue(TEXT("Throw impulse is positive"), Defaults->MagneticObjectThrowImpulse > 0.0f);
    }

    UFunction* RepNotify = ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("OnRep_MagneticSuitState"));
    UFunction* ServerGrip = ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ServerRequestGloveGrip"));
    UFunction* ServerThrow = ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ServerThrowMagneticObject"));
    UFunction* ServerThruster = ACoopSurvivalCharacter::StaticClass()->FindFunctionByName(TEXT("ServerSetRotationThruster"));
    TestNotNull(TEXT("RepNotify refreshes remote feedback"), RepNotify);
    TestTrue(TEXT("Grip request is a server RPC"), ServerGrip && ServerGrip->HasAnyFunctionFlags(FUNC_NetServer));
    TestTrue(TEXT("Throw request is a server RPC"), ServerThrow && ServerThrow->HasAnyFunctionFlags(FUNC_NetServer));
    TestTrue(TEXT("Thruster request is a server RPC"), ServerThruster && ServerThruster->HasAnyFunctionFlags(FUNC_NetServer));
    return true;
}

#endif
