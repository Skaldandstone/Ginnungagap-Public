#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "StarSystem/PelagosOrbitalArrivalDirector.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPelagosArrivalTransitionTest,
    "Ginnungagap.StarSystem.Pelagos.ArrivalTransitions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FPelagosArrivalTransitionTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Jump exit advances to sensor acquisition"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::JumpExit, EPelagosArrivalState::SensorAcquisition));
    TestTrue(TEXT("Dock request advances to assignment"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::DockRequest, EPelagosArrivalState::DockAssignment));
    TestFalse(TEXT("Arrival cannot skip directly to hard dock"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::JumpExit, EPelagosArrivalState::HardDock));
    TestTrue(TEXT("Departure can begin another arrival"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::Departure, EPelagosArrivalState::JumpExit));
    TestTrue(TEXT("Final approach advances to soft capture"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::FinalApproach, EPelagosArrivalState::SoftCapture));
    TestTrue(TEXT("Soft capture advances to hard dock"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::SoftCapture, EPelagosArrivalState::HardDock));
    TestFalse(TEXT("Dock assignment cannot bypass final approach"),
        APelagosOrbitalArrivalDirector::IsValidStateTransition(
            EPelagosArrivalState::DockAssignment, EPelagosArrivalState::SoftCapture));
    return true;
}

#endif
