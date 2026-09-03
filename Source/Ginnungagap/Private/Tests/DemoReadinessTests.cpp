#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "GinnungagapGameMode.h"
#include "LevelSetup/ShipDistrictGameplayDirector.h"
#include "Ship/JumpConsoleSystem.h"
#include "Ship/SelfDestructConsoleSystem.h"
#include "UI/JumpDestinationWidget.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProductionDemoDefaultsTest,
    "Ginnungagap.Demo.ProductionDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FProductionDemoDefaultsTest::RunTest(const FString& Parameters)
{
    const AGinnungagapGameMode* Mode = GetDefault<AGinnungagapGameMode>();
    TestTrue(TEXT("Production districts suppress procedural geometry"), Mode->bSkipAutoBuildForProductionDistricts);

    const AShipDistrictGameplayDirector* Director = GetDefault<AShipDistrictGameplayDirector>();
    TestTrue(TEXT("Demo countdown remains survivable"), Director->DemoJumpCountdownSeconds >= 10.0f);
    TestTrue(TEXT("Demo destination can be reached quickly"), Director->DemoJumpsToDestination <= 3);

    const AJumpConsoleSystem* JumpConsole = GetDefault<AJumpConsoleSystem>();
    TestNotNull(TEXT("Jump console has a native destination picker"), JumpConsole->DestinationWidgetClass.Get());
    TestFalse(TEXT("Automatic destination selection stays opt-in"), JumpConsole->bAutoSelectFirstCandidate);

    const ASelfDestructConsoleSystem* SelfDestruct = GetDefault<ASelfDestructConsoleSystem>();
    TestFalse(TEXT("Native self destruct fallback stays opt-in"), SelfDestruct->bArmOnInteractForNativeDemo);
    return true;
}

#endif
