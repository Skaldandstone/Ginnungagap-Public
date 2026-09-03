#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/Skeleton.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"

/**
 * That the player is actually wearing the oversuit, and that it can move.
 *
 * The four per-role oversuit slots were declared and never filled, so the resolver returned null
 * and the character ran around in the undersuit. Nothing reported that: an empty soft pointer is a
 * legal value and the component simply drew nothing.
 *
 * The skeleton assertion is the one worth having. The oversuit follows the body through
 * SetLeaderPoseComponent, which requires the *same* skeleton as the leader -- not a similar one,
 * the same one. Assign a mesh built on any other rig and it renders frozen in its own bind pose
 * while the character walks out from under it, silently, at runtime only.
 *
 * That is not hypothetical. Of the seven oversuit meshes in this project, five are on an 80-bone
 * SM_Male_Oversuit_UE5 skeleton and the Space Marshal shell is on its own 89-bone skeleton, against
 * the body's 161-bone SK_Mannequin. Exactly one currently works, and picking any of the others
 * would look like a rendering bug rather than a mismatched asset.
 */

namespace OversuitPie
{
	UWorld* FindPieWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}
		return nullptr;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertPlayerOversuit, FAutomationTestBase*, Test);

bool FAssertPlayerOversuit::Update()
{
	UWorld* World = OversuitPie::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world for the oversuit assertions"));
		return true;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ACoopSurvivalCharacter* Crew = World->SpawnActor<ACoopSurvivalCharacter>(
		ACoopSurvivalCharacter::StaticClass(), FTransform(FVector(0, 0, 400)), Params);

	Test->TestNotNull(TEXT("Spawned a crew member to inspect"), Crew);
	if (!Crew)
	{
		return true;
	}

	// The oversuit is applied through the appearance refresh rather than the constructor, so it has
	// to be asked for before it exists.
	Crew->RefreshEquipmentVisuals();

	USkeletalMeshComponent* Body = Crew->GetMesh();
	USkeletalMeshComponent* Oversuit = Crew->GetPrimaryOversuitMesh();

	Test->TestNotNull(TEXT("The character has a body mesh component"), Body);
	Test->TestNotNull(TEXT("The character has an oversuit component"), Oversuit);

	if (Body && Oversuit)
	{
		USkeletalMesh* BodyMesh = Body->GetSkeletalMeshAsset();
		USkeletalMesh* OversuitMesh = Oversuit->GetSkeletalMeshAsset();

		Test->TestNotNull(TEXT("The body has a mesh"), BodyMesh);
		Test->TestNotNull(
			TEXT("The oversuit slot resolves to a mesh, so the player is wearing something"),
			OversuitMesh);

		if (BodyMesh && OversuitMesh)
		{
			// The whole point. Leader pose binds by skeleton identity, so anything else is a suit
			// that stands still while its wearer walks away.
			Test->TestTrue(
				FString::Printf(TEXT("The oversuit shares the body's skeleton (%s vs %s)"),
					OversuitMesh->GetSkeleton()
						? *OversuitMesh->GetSkeleton()->GetName() : TEXT("none"),
					BodyMesh->GetSkeleton()
						? *BodyMesh->GetSkeleton()->GetName() : TEXT("none")),
				OversuitMesh->GetSkeleton() == BodyMesh->GetSkeleton());
		}

		// Set in the constructor and re-set on every refresh; without it the suit does not follow
		// the body at all, whatever skeleton it is on.
		//
		// Compared as a bool rather than passed to TestEqual, which has no overload for a raw
		// component pointer.
		Test->TestTrue(TEXT("The oversuit follows the body through leader pose"),
			Oversuit->LeaderPoseComponent.Get() == Body);
	}

	Crew->Destroy();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapPlayerOversuitPieTest,
	"Ginnungagap.Smoke.PlayerOversuit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapPlayerOversuitPieTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertPlayerOversuit(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
