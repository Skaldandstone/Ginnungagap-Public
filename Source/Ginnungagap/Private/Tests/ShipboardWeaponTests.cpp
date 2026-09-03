#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Weapons/CaptiveBoltDriver.h"
#include "Weapons/ShipboardControlStatusComponent.h"
#include "Weapons/ShipboardWeaponDefinition.h"
#include "Weapons/TraversalClearanceVolume.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FShipboardWeaponSafeDefaultsTest,
    "Ginnungagap.Weapons.SafeDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipboardWeaponSafeDefaultsTest::RunTest(const FString& Parameters)
{
    const UShipboardWeaponDefinition* Definition = NewObject<UShipboardWeaponDefinition>();
    TestNotNull(TEXT("A weapon definition can be created"), Definition);
    if (!Definition)
    {
        return false;
    }

    TestTrue(TEXT("Civilian weapon definitions support players"), Definition->bPlayerCompatible);
    TestTrue(TEXT("Civilian weapon definitions support aerial drones"), Definition->bAerialDroneCompatible);
    TestFalse(TEXT("The default safe profile cannot damage the hull"), Definition->SafeProfile.bCanDamageHull);
    TestTrue(TEXT("The default profile has a physical range"), Definition->SafeProfile.MaxRangeCm > 0.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FShipboardWeaponUpgradeDefinitionTest,
    "Ginnungagap.Weapons.UpgradeDefinitions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipboardWeaponUpgradeDefinitionTest::RunTest(const FString& Parameters)
{
    UShipboardWeaponDefinition* Definition = NewObject<UShipboardWeaponDefinition>();
    Definition->SafeProfile.BiologicalDamage = 8.0f;
    Definition->SafeProfile.DeliveryMode = EWeaponDeliveryMode::Projectile;

    FWeaponUpgradeStage RegulatedFeed;
    RegulatedFeed.UpgradeId = TEXT("RegulatedFeed");
    RegulatedFeed.FiringProfile = Definition->SafeProfile;
    RegulatedFeed.FiringProfile.BiologicalDamage = 12.0f;
    RegulatedFeed.ResourceCost = 4;
    Definition->UpgradeStages.Add(RegulatedFeed);

    FWeaponUpgradeStage FerricSleeve = RegulatedFeed;
    FerricSleeve.UpgradeId = TEXT("FerricSleeve");
    FerricSleeve.FiringProfile.BiologicalDamage = 18.0f;
    Definition->UpgradeStages.Add(FerricSleeve);

    TestEqual(TEXT("Two authored stages produce two upgrade levels"), Definition->GetMaxUpgradeLevel(), 2);
    TestEqual(TEXT("Level zero returns the safe profile"),
        Definition->GetFiringProfileForUpgradeLevel(0).BiologicalDamage, 8.0f);
    TestEqual(TEXT("Level one returns the first upgrade"),
        Definition->GetFiringProfileForUpgradeLevel(1).BiologicalDamage, 12.0f);
    TestEqual(TEXT("Levels above maximum clamp to the final upgrade"),
        Definition->GetFiringProfileForUpgradeLevel(99).BiologicalDamage, 18.0f);
    TestTrue(TEXT("Projectile delivery survives upgrade selection"),
        Definition->GetFiringProfileForUpgradeLevel(2).DeliveryMode == EWeaponDeliveryMode::Projectile);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FShipboardWeaponControlProfileTest,
    "Ginnungagap.Weapons.ControlProfiles",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipboardWeaponControlProfileTest::RunTest(const FString& Parameters)
{
    FWeaponFiringProfile RestraintProfile;
    RestraintProfile.DeliveryMode = EWeaponDeliveryMode::Projectile;
    RestraintProfile.ControlEffect = EWeaponControlEffect::Restrain;
    RestraintProfile.ControlDurationSeconds = 4.5f;
    RestraintProfile.ControlMovementMultiplier = 0.0f;

    TestTrue(TEXT("Restraint payload uses physical projectile delivery"),
        RestraintProfile.DeliveryMode == EWeaponDeliveryMode::Projectile);
    TestTrue(TEXT("Restraint payload selects the restraint effect"),
        RestraintProfile.ControlEffect == EWeaponControlEffect::Restrain);
    TestEqual(TEXT("Restraint payload stores its authored duration"),
        RestraintProfile.ControlDurationSeconds, 4.5f);
    TestEqual(TEXT("Restraint payload can stop target movement"),
        RestraintProfile.ControlMovementMultiplier, 0.0f);

    const UShipboardControlStatusComponent* Status =
        GetDefault<UShipboardControlStatusComponent>();
    TestNotNull(TEXT("Control status component has a default object"), Status);
    if (Status)
    {
        TestFalse(TEXT("Control status starts inactive"), Status->IsControlEffectActive());
        TestFalse(TEXT("Control status starts unmarked"), Status->IsMarked());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FShipboardWeaponEmergencySupportProfilesTest,
    "Ginnungagap.Weapons.EmergencySupportProfiles",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FShipboardWeaponEmergencySupportProfilesTest::RunTest(const FString& Parameters)
{
    FWeaponFiringProfile AcousticProfile;
    AcousticProfile.ControlEffect = EWeaponControlEffect::AcousticDisorient;
    AcousticProfile.ControlDurationSeconds = 2.5f;
    AcousticProfile.ControlMovementMultiplier = 0.55f;

    TestTrue(TEXT("Acoustic emitters expose a distinct replicated disorient state"),
        AcousticProfile.ControlEffect == EWeaponControlEffect::AcousticDisorient);
    TestTrue(TEXT("Acoustic disorientation slows without immobilizing"),
        AcousticProfile.ControlMovementMultiplier > 0.0f
        && AcousticProfile.ControlMovementMultiplier < 1.0f);

    FWeaponFiringProfile ShieldProfile;
    ShieldProfile.DeliveryMode = EWeaponDeliveryMode::RescueShield;
    ShieldProfile.ShieldDurationSeconds = 4.0f;
    ShieldProfile.ShieldHalfExtentsCm = FVector(7.0f, 44.0f, 70.0f);

    TestTrue(TEXT("Rescue shield profiles select timed shield delivery"),
        ShieldProfile.DeliveryMode == EWeaponDeliveryMode::RescueShield);
    TestTrue(TEXT("Rescue shield profiles carry a useful duration"),
        ShieldProfile.ShieldDurationSeconds > 0.0f);
    TestTrue(TEXT("Rescue shield profiles cover a standing operator"),
        ShieldProfile.ShieldHalfExtentsCm.Y >= 40.0f
        && ShieldProfile.ShieldHalfExtentsCm.Z >= 60.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FCaptiveBoltDriverProfileTest,
    "Ginnungagap.Weapons.CaptiveBoltDriverProfiles",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FCaptiveBoltDriverProfileTest::RunTest(const FString& Parameters)
{
    const ACaptiveBoltDriver* Driver = GetDefault<ACaptiveBoltDriver>();
    TestNotNull(TEXT("The captive-bolt driver class has a default object"), Driver);
    if (!Driver)
    {
        return false;
    }

    TestFalse(TEXT("The captive safe profile protects the hull"), Driver->SafeProfile.bCanDamageHull);
    TestTrue(TEXT("The extended bolt can damage the hull"), Driver->UnsafeModifiedProfile.bCanDamageHull);
    TestTrue(TEXT("The unsafe profile increases biological damage"),
        Driver->UnsafeModifiedProfile.BiologicalDamage > Driver->SafeProfile.BiologicalDamage);
    TestTrue(TEXT("The unsafe profile increases recoil"),
        Driver->UnsafeModifiedProfile.RecoilImpulse > Driver->SafeProfile.RecoilImpulse);
    TestTrue(TEXT("The driver is compatible with aerial drones"),
        Driver->IsCompatibleWith(EWeaponOperatorType::AerialDrone));
    TestTrue(TEXT("The compact driver fits a generous maintenance opening"),
        Driver->FitsOpening(FVector(90.0f, 40.0f, 40.0f)));
    TestFalse(TEXT("The driver does not fit an opening narrower than its envelope"),
        Driver->FitsOpening(FVector(60.0f, 20.0f, 20.0f)));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FWeaponCollisionEnvelopeApertureTest,
    "Ginnungagap.Weapons.CollisionEnvelopeAperture",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FWeaponCollisionEnvelopeApertureTest::RunTest(const FString& Parameters)
{
    FWeaponCollisionEnvelope Envelope;
    Envelope.HalfExtentsCm = FVector(100.0f, 15.0f, 20.0f);
    Envelope.bCanFoldForTraversal = true;
    Envelope.FoldedHalfExtentsCm = FVector(20.0f, 10.0f, 10.0f);

    TestTrue(TEXT("A long weapon fits while aligned with the passage travel axis"),
        Envelope.FitsPassageAperture(FQuat::Identity, FQuat::Identity, 40.0f, 50.0f, false));
    TestFalse(TEXT("Turning the long weapon broadside exceeds the same aperture"),
        Envelope.FitsPassageAperture(FRotator(0.0f, 90.0f, 0.0f).Quaternion(),
            FQuat::Identity, 40.0f, 50.0f, false));
    TestTrue(TEXT("The folded envelope fits broadside"),
        Envelope.FitsPassageAperture(FRotator(0.0f, 90.0f, 0.0f).Quaternion(),
            FQuat::Identity, 40.0f, 50.0f, true));

    const ATraversalClearanceVolume* Passage = GetDefault<ATraversalClearanceVolume>();
    TestNotNull(TEXT("A clearance volume has an authorable default object"), Passage);
    if (Passage)
    {
        TestTrue(TEXT("The approach region is deeper than the default compact envelope"),
            Passage->ApproachDepthCm > 70.0f);
        TestTrue(TEXT("Automatic folding is enabled by default"), Passage->bAllowAutomaticWeaponFolding);
    }
    return true;
}

#endif
