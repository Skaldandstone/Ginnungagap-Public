#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Animation/AnimationAsset.h"
#include "Bloom/BloomEnemyArchetypes.h"
#include "Bloom/PathogenLoadComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FBloomEnemyStageMappingTest,
    "Ginnungagap.Gameplay.Bloom.Enemies.ProgressiveStageMapping",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBloomEnemyStageMappingTest::RunTest(const FString& Parameters)
{
    const ABloomReanimatedCrewEnemy* Crew = GetDefault<ABloomReanimatedCrewEnemy>();
    const ABloomMechanizedEnemy* Robot = GetDefault<ABloomMechanizedEnemy>();
    TestNotNull(TEXT("Reanimated crew archetype resolves"), Crew);
    TestNotNull(TEXT("Mechanized archetype resolves"), Robot);
    if (!Crew || !Robot)
    {
        return false;
    }

    float PreviousCrew = -1.0f;
    float PreviousRobot = -1.0f;
    for (int32 StageIndex = static_cast<int32>(EBloomStage::Latent);
        StageIndex <= static_cast<int32>(EBloomStage::Manifestation);
        ++StageIndex)
    {
        const EBloomStage Stage = static_cast<EBloomStage>(StageIndex);
        const float CrewProgress = Crew->CalculateProgressForGlobalStage(Stage);
        const float RobotProgress = Robot->CalculateProgressForGlobalStage(Stage);
        TestTrue(TEXT("Crew infection is monotonic"), CrewProgress >= PreviousCrew);
        TestTrue(TEXT("Robot infection is monotonic"), RobotProgress >= PreviousRobot);
        TestTrue(TEXT("Crew infection stays normalized"), CrewProgress >= 0.0f && CrewProgress <= 1.0f);
        TestTrue(TEXT("Robot infection stays normalized"), RobotProgress >= 0.0f && RobotProgress <= 1.0f);
        PreviousCrew = CrewProgress;
        PreviousRobot = RobotProgress;
    }

    TestTrue(TEXT("Crew visibly progresses before machinery"),
        Crew->CalculateProgressForGlobalStage(EBloomStage::Swarm) >
        Robot->CalculateProgressForGlobalStage(EBloomStage::Swarm));
    TestEqual(TEXT("Crew reaches terminal overgrowth"),
        Crew->CalculateProgressForGlobalStage(EBloomStage::Manifestation), 1.0f);
    TestEqual(TEXT("Robot reaches terminal overgrowth"),
        Robot->CalculateProgressForGlobalStage(EBloomStage::Manifestation), 1.0f);
    TestNotNull(TEXT("Crew carries a shedding pathogen load"), Crew->PathogenLoadComponent.Get());
    TestNotNull(TEXT("Robot carries a shedding pathogen load"), Robot->PathogenLoadComponent.Get());
    TestNotNull(TEXT("Crew carries a progressive visibility light"), Crew->BloomGlowLight.Get());
    TestNotNull(TEXT("Robot carries a progressive visibility light"), Robot->BloomGlowLight.Get());
    TestNotNull(TEXT("Crew has a native motion pivot"), Crew->AttackPoseRoot.Get());
    TestNotNull(TEXT("Robot has a native motion pivot"), Robot->AttackPoseRoot.Get());
    TestNotNull(TEXT("Crew has a pack-native Fab corpse mesh"), Crew->FabCorpseMesh.Get());
    TestEqual(TEXT("Crew has three audited Fab death-pose variants"), Crew->FabDeathPoseAssets.Num(), 3);
    if (Crew->FabCorpseMesh && Crew->FabCorpseMesh->GetSkeletalMeshAsset())
    {
        const USkeleton* CorpseSkeleton = Crew->FabCorpseMesh->GetSkeletalMeshAsset()->GetSkeleton();
        for (const UAnimationAsset* Pose : Crew->FabDeathPoseAssets)
        {
            TestNotNull(TEXT("Fab death pose resolves"), Pose);
            if (Pose)
            {
                TestTrue(TEXT("Fab pose uses the corpse mesh source skeleton"),
                    Pose->GetSkeleton() == CorpseSkeleton);
            }
        }
    }
    TestTrue(TEXT("Terminal crew attacks faster than terminal machinery"),
        Crew->AttackInterval < Robot->AttackInterval);
    TestTrue(TEXT("Terminal machinery transfers the larger pathogen dose"),
        Robot->ContactExposurePerAttack > Crew->ContactExposurePerAttack);
    TestTrue(TEXT("Death bursts have a positive radius"),
        Crew->DeathBurstRadius > 0.0f && Robot->DeathBurstRadius > 0.0f);
    return true;
}

#endif
