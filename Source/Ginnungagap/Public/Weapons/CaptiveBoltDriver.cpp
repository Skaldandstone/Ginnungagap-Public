#include "Weapons/CaptiveBoltDriver.h"

#include "Components/StaticMeshComponent.h"

ACaptiveBoltDriver::ACaptiveBoltDriver()
{
    VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/Assets/Models/GameplayItems/SM_Weapon_RivetRifle.SM_Weapon_RivetRifle")));
    VisualMesh->SetRelativeScale3D(FVector(0.72f));

    SafeProfile.MaxRangeCm = 72.0f;
    SafeProfile.TraceRadiusCm = 5.0f;
    SafeProfile.BiologicalDamage = 45.0f;
    SafeProfile.ImpactImpulse = 18000.0f;
    SafeProfile.RecoilImpulse = 1800.0f;
    SafeProfile.CooldownSeconds = 0.65f;
    SafeProfile.bCanDamageHull = false;

    UnsafeModifiedProfile = SafeProfile;
    UnsafeModifiedProfile.MaxRangeCm = 115.0f;
    UnsafeModifiedProfile.BiologicalDamage = 85.0f;
    UnsafeModifiedProfile.ImpactImpulse = 36000.0f;
    UnsafeModifiedProfile.RecoilImpulse = 7200.0f;
    UnsafeModifiedProfile.CooldownSeconds = 0.9f;
    UnsafeModifiedProfile.bCanDamageHull = true;
    UnsafeModifiedProfile.HullImpactSeverity = 0.04f;
    UnsafeModifiedProfile.BreachSeverity = 0.08f;

    CollisionEnvelope.EnvelopeClass = EWeaponEnvelopeClass::Compact;
    CollisionEnvelope.HalfExtentsCm = FVector(35.0f, 12.0f, 12.0f);
}
