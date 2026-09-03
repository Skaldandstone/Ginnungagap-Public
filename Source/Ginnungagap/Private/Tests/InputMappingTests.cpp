#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "GameFramework/InputSettings.h"
#include "InputCoreTypes.h"

namespace GinnungagapInputTests
{
bool HasActionKey(const UInputSettings* Settings, const FName ActionName, const FKey Key)
{
    TArray<FInputActionKeyMapping> Mappings;
    Settings->GetActionMappingByName(ActionName, Mappings);
    return Mappings.ContainsByPredicate([Key](const FInputActionKeyMapping& Mapping)
    {
        return Mapping.Key == Key;
    });
}

bool HasAxisKey(const UInputSettings* Settings, const FName AxisName, const FKey Key, const float Scale)
{
    TArray<FInputAxisKeyMapping> Mappings;
    Settings->GetAxisMappingByName(AxisName, Mappings);
    return Mappings.ContainsByPredicate([Key, Scale](const FInputAxisKeyMapping& Mapping)
    {
        return Mapping.Key == Key && FMath::IsNearlyEqual(Mapping.Scale, Scale);
    });
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FDesktopAndPlayStationInputMappingTest,
    "Ginnungagap.Input.DesktopAndPlayStationMappings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FDesktopAndPlayStationInputMappingTest::RunTest(const FString& Parameters)
{
    using namespace GinnungagapInputTests;

    const UInputSettings* Settings = GetDefault<UInputSettings>();
    TestNotNull(TEXT("Input settings are available"), Settings);
    if (!Settings)
    {
        return false;
    }

    struct FActionPair
    {
        FName Name;
        FKey DesktopKey;
        FKey GamepadKey;
    };

    // Gamepad_* keys are Unreal's platform-neutral controller keys. On PS5 they
    // are supplied by the DualSense device layer (Bottom = Cross, Right = Circle,
    // Left = Square, Top = Triangle, Special Right = Options, Special Left = Create).
    const FActionPair Actions[] = {
        {TEXT("Jump"), EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom},
        {TEXT("Interact"), EKeys::E, EKeys::Gamepad_FaceButton_Right},
        {TEXT("ActivitySecondary"), EKeys::F, EKeys::Gamepad_FaceButton_Left},
        // Deliberately the same keys as ActivitySecondary. The two can never both apply:
        // ActivitySecondary only means anything while an activity is running, and CycleApproach
        // only does anything while looking at an obstruction that has not been started. Sharing
        // beats a fourteenth binding on a scheme that is meant to stay close to WASD -- and this
        // line records that the collision is intended, so nobody "fixes" it later.
        {TEXT("CycleApproach"), EKeys::F, EKeys::Gamepad_FaceButton_Left},
        {TEXT("ActivityTertiary"), EKeys::Three, EKeys::Gamepad_DPad_Left},
        {TEXT("ActivityQuaternary"), EKeys::Four, EKeys::Gamepad_DPad_Right},
        {TEXT("ActivityCancel"), EKeys::X, EKeys::Gamepad_FaceButton_Top},
        {TEXT("Progression"), EKeys::Escape, EKeys::Gamepad_Special_Right},
        {TEXT("ToggleMagneticBoots"), EKeys::M, EKeys::Gamepad_DPad_Down},
        {TEXT("MagneticGloveGrip"), EKeys::LeftShift, EKeys::Gamepad_LeftShoulder},
        {TEXT("RightMagneticGloveGrip"), EKeys::RightShift, EKeys::Gamepad_LeftTrigger},
        {TEXT("ThrowMagneticObject"), EKeys::Q, EKeys::Gamepad_FaceButton_Left},
        {TEXT("RotationThruster"), EKeys::R, EKeys::Gamepad_RightShoulder},
        {TEXT("RestartDemo"), EKeys::Enter, EKeys::Gamepad_Special_Left},
        {TEXT("PrimaryFire"), EKeys::LeftMouseButton, EKeys::Gamepad_RightTrigger},
        {TEXT("ToggleWeaponModification"), EKeys::V, EKeys::Gamepad_DPad_Up},
    };

    for (const FActionPair& Action : Actions)
    {
        TestTrue(*FString::Printf(TEXT("%s has a PC binding"), *Action.Name.ToString()),
            HasActionKey(Settings, Action.Name, Action.DesktopKey));
        TestTrue(*FString::Printf(TEXT("%s has a PS5-compatible gamepad binding"), *Action.Name.ToString()),
            HasActionKey(Settings, Action.Name, Action.GamepadKey));
    }

    TestTrue(TEXT("PC forward movement uses W"), HasAxisKey(Settings, TEXT("MoveForward"), EKeys::W, 1.0f));
    TestTrue(TEXT("PC backward movement uses S"), HasAxisKey(Settings, TEXT("MoveForward"), EKeys::S, -1.0f));
    TestTrue(TEXT("PS5 movement uses the left stick Y axis"), HasAxisKey(Settings, TEXT("MoveForward"), EKeys::Gamepad_LeftY, 1.0f));
    TestTrue(TEXT("PC left movement uses A"), HasAxisKey(Settings, TEXT("MoveRight"), EKeys::A, -1.0f));
    TestTrue(TEXT("PC right movement uses D"), HasAxisKey(Settings, TEXT("MoveRight"), EKeys::D, 1.0f));
    TestTrue(TEXT("PS5 movement uses the left stick X axis"), HasAxisKey(Settings, TEXT("MoveRight"), EKeys::Gamepad_LeftX, 1.0f));
    TestTrue(TEXT("PC horizontal look uses the mouse"), HasAxisKey(Settings, TEXT("Turn"), EKeys::MouseX, 1.0f));
    TestTrue(TEXT("PS5 horizontal look uses the right stick"), HasAxisKey(Settings, TEXT("Turn"), EKeys::Gamepad_RightX, 45.0f));
    TestTrue(TEXT("PC vertical look uses the mouse"), HasAxisKey(Settings, TEXT("LookUp"), EKeys::MouseY, -1.0f));
    TestTrue(TEXT("PS5 vertical look uses the right stick"), HasAxisKey(Settings, TEXT("LookUp"), EKeys::Gamepad_RightY, -45.0f));

    return true;
}

#endif
