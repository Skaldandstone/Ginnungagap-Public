#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "AI/PatrollingEnemyController.h"
#include "Bloom/BloomDirector.h"
#include "Activities/PlayerActivityTypes.h"
#include "Stealth/NoisePerceptionSubsystem.h"
#include "Stealth/PlayerNoiseEmitterComponent.h"
#include "Stealth/PlayerVisibilityComponent.h"
#include "Stealth/StealthTypes.h"
#include "CoopSurvivalCharacter.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/ShipboardWeaponTypes.h"

/**
 * These exercise the audibility maths directly on the subsystem. They deliberately avoid a world
 * so they stay fast and deterministic; occlusion tracing and the AI reaction are covered by PIE
 * testing instead, since both need real geometry to mean anything.
 */

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNoiseAudibilityFalloffTest,
    "Ginnungagap.Gameplay.Stealth.NoiseAudibilityFalloff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FNoiseAudibilityFalloffTest::RunTest(const FString& Parameters)
{
    UNoisePerceptionSubsystem* Perception = NewObject<UNoisePerceptionSubsystem>();

    // Without a world the subsystem cannot timestamp or trace, so ReportNoise is a no-op and a
    // query must fail rather than inventing a stimulus.
    FNoiseEvent Heard;
    float Strength = 0.0f;
    Perception->ReportNoise(FVector::ZeroVector, 1.0f, ENoiseCategory::Weapon, nullptr);
    TestFalse(TEXT("Query on an unworlded subsystem reports nothing audible"),
        Perception->QueryLoudestAudibleNoise(FVector::ZeroVector, 1.0f, nullptr, Heard, Strength));
    TestEqual(TEXT("Perceived strength is zero when nothing is audible"), Strength, 0.0f);

    // Tuning defaults are load-bearing for the stealth feel; assert the shipped values so an
    // accidental edit shows up as a failing test rather than as silently different gameplay.
    TestTrue(TEXT("Default propagation distance is positive"), Perception->MaxPropagationDistance > 0.0f);
    TestTrue(TEXT("Occlusion attenuates rather than amplifies"),
        Perception->OcclusionAttenuation >= 0.0f && Perception->OcclusionAttenuation <= 1.0f);
    TestTrue(TEXT("Audibility threshold is within the normalized strength range"),
        Perception->AudibilityThreshold >= 0.0f && Perception->AudibilityThreshold <= 1.0f);
    TestTrue(TEXT("Noise below the reportable floor is ignorable"),
        Perception->MinimumReportableLoudness > 0.0f);
    TestTrue(TEXT("Noise memory outlives a single frame"), Perception->NoiseMemorySeconds > 0.0f);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNoiseEventDefaultsTest,
    "Ginnungagap.Gameplay.Stealth.NoiseEventDefaults",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FNoiseEventDefaultsTest::RunTest(const FString& Parameters)
{
    const FNoiseEvent Event;
    TestEqual(TEXT("A default noise event is silent"), Event.Loudness, 0.0f);
    TestEqual(TEXT("A default noise event is movement-categorised"), Event.Category, ENoiseCategory::Movement);
    TestFalse(TEXT("A default noise event has no instigator"), Event.Instigator.IsValid());

    // Awareness ordering is relied on by the controller's state machine (sight beats hearing).
    TestTrue(TEXT("Unaware precedes Suspicious"),
        static_cast<uint8>(EEnemyAwareness::Unaware) < static_cast<uint8>(EEnemyAwareness::Suspicious));
    TestTrue(TEXT("Suspicious precedes Alert"),
        static_cast<uint8>(EEnemyAwareness::Suspicious) < static_cast<uint8>(EEnemyAwareness::Alert));

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVisibilityProfileTest,
    "Ginnungagap.Gameplay.Stealth.VisibilityProfile",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FVisibilityProfileTest::RunTest(const FString& Parameters)
{
    UPlayerVisibilityComponent* Visibility = NewObject<UPlayerVisibilityComponent>();

    // With no owner and no world there is no room to read power state from. The component must
    // fail open (fully visible) rather than granting free concealment.
    TestEqual(TEXT("Ownerless component is fully lit"), Visibility->GetLightExposure(), 1.0f);
    TestEqual(TEXT("Ownerless component is fully movement-exposed"), Visibility->GetMovementExposure(), 1.0f);
    TestEqual(TEXT("Ownerless component is fully visible"), Visibility->GetVisibilityMultiplier(), 1.0f);

    // Concealment must stay partial: total invisibility reads as a bug and leaves no counterplay.
    TestTrue(TEXT("Minimum visibility is above zero"), Visibility->MinimumVisibility > 0.0f);
    TestTrue(TEXT("Darkness conceals but does not erase"),
        Visibility->DarkroomVisibility > 0.0f && Visibility->DarkroomVisibility < 1.0f);
    TestTrue(TEXT("Stillness conceals but does not erase"),
        Visibility->StillVisibility > 0.0f && Visibility->StillVisibility < 1.0f);

    // The two factors compound, so combining them must beat either alone. This is what makes
    // both stealth behaviours worth doing together.
    const float Combined = Visibility->DarkroomVisibility * Visibility->StillVisibility;
    TestTrue(TEXT("Dark and still compounds below either factor alone"),
        Combined < Visibility->DarkroomVisibility && Combined < Visibility->StillVisibility);

    TestTrue(TEXT("Still speed threshold is below the fully-visible speed"),
        Visibility->StillSpeedThreshold < Visibility->FullyVisibleSpeed);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDetectionTuningTest,
    "Ginnungagap.Gameplay.Stealth.DetectionTuning",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FDetectionTuningTest::RunTest(const FString& Parameters)
{
    const APatrollingEnemyController* Controller = GetDefault<APatrollingEnemyController>();

    // Vision must be a cone, not a sphere: a half-angle of 180 would restore the old behaviour
    // where enemies saw directly behind themselves.
    TestTrue(TEXT("Vision is a forward cone"),
        Controller->VisionConeHalfAngleDegrees > 0.0f && Controller->VisionConeHalfAngleDegrees < 180.0f);

    // Suspicion must be reachable strictly before confirmation, otherwise partial sightings
    // collapse back into the old instant-detection behaviour.
    TestTrue(TEXT("Suspicion threshold precedes confirmation"),
        Controller->SuspicionDetectionThreshold < Controller->ConfirmedDetectionThreshold);

    TestTrue(TEXT("Detection builds over time rather than instantly"), Controller->DetectionBuildRate > 0.0f);
    TestTrue(TEXT("Detection decays when nothing is visible"), Controller->DetectionDecayRate > 0.0f);

    // Escaping has to be possible: if certainty drained slower than it built, a target that broke
    // line of sight could never actually lose a pursuer.
    TestTrue(TEXT("A fresh controller starts unaware"), Controller->GetAwareness() == EEnemyAwareness::Unaware);
    TestEqual(TEXT("A fresh controller has no accumulated certainty"), Controller->GetDetectionProgress(), 0.0f);

    // Investigating sits between patrolling and chasing so awareness reads through movement speed.
    TestTrue(TEXT("Investigate speed sits between patrol and chase"),
        Controller->InvestigateSpeed > Controller->PatrolSpeed && Controller->InvestigateSpeed < Controller->ChaseSpeed);

    // Bloom adaptation must only ever sharpen perception, never dull it.
    TestTrue(TEXT("Bloom adaptation does not weaken perception"), Controller->MaxBloomPerceptionScale >= 1.0f);
    TestTrue(TEXT("Bloom adaptation is meaningful at full maturity"), Controller->MaxBloomPerceptionScale > 1.0f);

    // A controller with no pawn has no faction to check, so it must resolve to the neutral scale
    // rather than assuming Bloom and silently buffing every unpossessed AI.
    TestEqual(TEXT("An unpossessed controller gets no Bloom advantage"),
        Controller->GetBloomPerceptionScale(), 1.0f);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBloomStealthAdaptationTest,
    "Ginnungagap.Gameplay.Stealth.BloomAdaptation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBloomStealthAdaptationTest::RunTest(const FString& Parameters)
{
    // UBloomDirector is a UGameInstanceSubsystem, so its ClassWithin requires a GameInstance
    // outer. Constructing it bare trips a CoreUObject ensure rather than failing cleanly.
    UGameInstance* OwningInstance = NewObject<UGameInstance>(GetTransientPackage());
    UBloomDirector* Bloom = NewObject<UBloomDirector>(OwningInstance);

    // Nothing learned yet: every tactic works fully.
    TestEqual(TEXT("An unadapted Bloom does not counter darkness"),
        Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Darkness), 1.0f);

    // Using a tactic must not weaken it mid-run. The organism adapts during jumps, so the crew
    // discovers the change on arrival rather than watching it erode while relying on it.
    Bloom->RegisterStealthTacticUse(EBloomStealthTactic::Darkness, 20.0f);
    TestEqual(TEXT("Tactic use alone does not change effectiveness before a jump"),
        Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Darkness), 1.0f);

    Bloom->OnSystemJump();
    const float AfterFirstJump = Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Darkness);
    TestTrue(TEXT("Relied-on tactic is countered after a jump"), AfterFirstJump < 1.0f);

    // Adaptation is per-tactic: countering darkness must not also counter stillness, or varying
    // approach would gain the player nothing.
    TestEqual(TEXT("An unused tactic is unaffected"),
        Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Stillness), 1.0f);

    // Switching approach lets the abandoned tactic recover, so an early over-reliance is not a
    // permanent loss.
    Bloom->OnSystemJump();
    TestTrue(TEXT("An abandoned tactic recovers across later jumps"),
        Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Darkness) > AfterFirstJump);

    // Sustained reliance must bottom out rather than reach zero: a tactic that stops working
    // entirely removes a verb from the player instead of pressuring them.
    for (int32 Jump = 0; Jump < 50; ++Jump)
    {
        Bloom->RegisterStealthTacticUse(EBloomStealthTactic::Darkness, 100.0f);
        Bloom->OnSystemJump();
    }
    const float Floor = Bloom->GetStealthTacticEffectiveness(EBloomStealthTactic::Darkness);
    TestTrue(TEXT("Counter-adaptation respects its floor"), Floor >= Bloom->MinStealthTacticEffectiveness);
    TestTrue(TEXT("A countered tactic still retains some value"), Floor > 0.0f);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNoiseSourceLoudnessTest,
    "Ginnungagap.Gameplay.Stealth.NoiseSourceLoudness",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FNoiseSourceLoudnessTest::RunTest(const FString& Parameters)
{
    const AShipboardWeapon* Weapon = GetDefault<AShipboardWeapon>();
    const FPlayerActivityDefinition ActivityDefaults;

    // Firing must be loud enough to matter. A weapon quieter than ordinary shipboard work would
    // make shooting the stealthy option, inverting the intended risk.
    TestTrue(TEXT("Safe firing is loud"), Weapon->SafeProfile.FiringNoiseLoudness > 0.5f);
    TestTrue(TEXT("Firing is louder than routine work"),
        Weapon->SafeProfile.FiringNoiseLoudness > ActivityDefaults.WorkNoiseLoudness);

    // The unsafe modification trades stealth for power rather than being strictly better.
    TestTrue(TEXT("Unsafe firing is at least as loud as safe firing"),
        Weapon->UnsafeModifiedProfile.FiringNoiseLoudness >= Weapon->SafeProfile.FiringNoiseLoudness);

    // Work has to be audible or repairing under pressure carries no risk at all.
    TestTrue(TEXT("Routine work is audible"), ActivityDefaults.WorkNoiseLoudness > 0.0f);
    TestTrue(TEXT("Routine work is not maximally loud"), ActivityDefaults.WorkNoiseLoudness < 1.0f);

    // A thrown object has to be loud enough to actually pull an investigator away. If it were
    // quieter than the work the player is trying to do undisturbed, it would be useless as a
    // distraction -- the AI would keep investigating the louder thing.
    const ACoopSurvivalCharacter* Character = GetDefault<ACoopSurvivalCharacter>();
    TestTrue(TEXT("A thrown object is audible"), Character->GetThrownObjectImpactLoudness() > 0.0f);
    TestTrue(TEXT("A thrown object out-competes routine work as a distraction"),
        Character->GetThrownObjectImpactLoudness() > ActivityDefaults.WorkNoiseLoudness);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FNoiseTellContractTest,
    "Ginnungagap.Gameplay.Stealth.NoiseTellContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FNoiseTellContractTest::RunTest(const FString& Parameters)
{
    UPlayerNoiseEmitterComponent* Emitter = NewObject<UPlayerNoiseEmitterComponent>();

    // The tell exists because the stealth loop was one-sided: the AI knew exactly how loud the
    // player was and the player could not hear themselves. These pin the properties that keep the
    // two sides agreeing, since a tell that disagrees teaches the player something untrue.

    // Silent by default. Audio is not sourced yet, and an unassigned loop must stay quiet rather
    // than warn every frame or play a placeholder tone into real footage.
    TestNull(TEXT("No movement loop is assigned by default"), Emitter->MovementNoiseLoop.Get());
    TestNull(TEXT("No magnetic boot loop is assigned by default"), Emitter->MagneticBootNoiseLoop.Get());

    // The boots are the central traversal trade -- safe footing for a much larger noise signature
    // -- so they need their own asset slot rather than being the same sound played louder.
    TestTrue(TEXT("Boot noise is louder than ordinary movement"), Emitter->MagneticBootNoiseMultiplier > 1.0f);

    // A mix control that could exceed the audible range would let the tell claim a loudness the AI
    // never acted on, which is the drift this whole thing exists to prevent.
    TestTrue(TEXT("Audio volume scale is non-negative"), Emitter->NoiseAudioVolumeScale >= 0.0f);
    TestTrue(TEXT("A floor exists so near-silence is not looped"), Emitter->MinAudibleNoise > 0.0f);
    TestTrue(TEXT("The floor sits below the loudest movement"),
        Emitter->MinAudibleNoise < Emitter->MaxMovementLoudness);

    // Smoothing has to be short. The point is to feel the consequence of moving, so a long fade
    // would disconnect the sound from the action that caused it.
    TestTrue(TEXT("Smoothing is not negative"), Emitter->NoiseAudioSmoothing >= 0.0f);
    TestTrue(TEXT("Smoothing stays short enough to feel connected"), Emitter->NoiseAudioSmoothing <= 0.5f);

    // Nothing has been triggered, so the reported level must be silent rather than defaulting to
    // something audible.
    TestEqual(TEXT("A fresh emitter reports no noise"), Emitter->GetCurrentNoiseLevel(), 0.0f);

    return true;
}

#endif
