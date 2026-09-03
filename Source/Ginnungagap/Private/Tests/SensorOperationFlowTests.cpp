#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "UI/SensorSurveyWidget.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSensorDirectOperationPolicyTest,
    "Ginnungagap.UI.Sensors.DirectResourceOperationPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSensorDirectOperationPolicyTest::RunTest(const FString& Parameters)
{
    TestFalse(TEXT("EVA recovery is blocked before arrival"),
        USensorSurveyWidget::CanExecuteDirectResourceOperation(
            EResourceAcquisitionMethod::EVARetrieval, false, true));
    TestFalse(TEXT("EVA recovery remains blocked until the pawn satisfies EVA requirements"),
        USensorSurveyWidget::CanExecuteDirectResourceOperation(
            EResourceAcquisitionMethod::EVARetrieval, true, false));
    TestTrue(TEXT("On-station EVA recovery is enabled after its requirement is met"),
        USensorSurveyWidget::CanExecuteDirectResourceOperation(
            EResourceAcquisitionMethod::EVARetrieval, true, true));
    TestTrue(TEXT("A ready on-station ship collector can transfer its yield"),
        USensorSurveyWidget::CanExecuteDirectResourceOperation(
            EResourceAcquisitionMethod::ShipSystemReactivation, true, true));
    TestFalse(TEXT("Drone nodes cannot bypass the existing dispatch flow"),
        USensorSurveyWidget::CanExecuteDirectResourceOperation(
            EResourceAcquisitionMethod::DroneDispatch, true, true));
    return true;
}

#endif
