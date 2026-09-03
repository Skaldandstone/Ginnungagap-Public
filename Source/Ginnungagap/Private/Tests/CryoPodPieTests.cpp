#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"

#include "Ship/CryoPodSystem.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"

/**
 * The cryo bay, which is the first thing anyone sees of this game.
 *
 * Everything asserted here was broken at some point today and none of it was caught by anything.
 * The pods had six components with **no material assigned at all**, rendering in the engine default
 * -- eleven cryo materials were authored for them and two were wired. The status panel had three
 * authored colours and a pod class carrying occupancy, lid and corruption state, and nothing
 * connected the two. And every lid stood open because the constructor forced it, so a bay meant to
 * show one person having climbed out claimed four had.
 *
 * All three are invisible to a compiler and to every other test in the suite: the actors spawn, the
 * class works, the map opens. They are only visible by looking, which is an expensive way to find
 * out and does not run in CI.
 *
 * PIE rather than a constructed component because the lid is animated on tick, and because the
 * assertions worth having are about the *demo map's* pods rather than about a pod in the abstract.
 */

namespace CryoPie
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

	/** Every visual component a pod draws with, in the order the class declares them. */
	TArray<UStaticMeshComponent*> VisualComponents(ACryoPodSystem* Pod)
	{
		TArray<UStaticMeshComponent*> Found;
		for (UStaticMeshComponent* Component : { Pod->VisualMesh, Pod->BedInsert, Pod->DetailTrim,
			Pod->HingeAssembly, Pod->Restraints, Pod->StatusLights, Pod->LidFrame, Pod->LidGlass })
		{
			if (Component)
			{
				Found.Add(Component);
			}
		}
		return Found;
	}

	/**
	 * Whether a component draws something other than the engine default material.
	 *
	 * The default is what an unassigned slot falls back to, and it is the exact failure this test
	 * exists for: it renders, it looks like flat plastic, and nothing reports it.
	 */
	bool HasRealMaterial(const UStaticMeshComponent* Component)
	{
		UMaterialInterface* Material = Component->GetMaterial(0);
		if (!Material)
		{
			return false;
		}

		const FString Name = Material->GetName();
		return !Name.Contains(TEXT("WorldGridMaterial"))
			&& !Name.Contains(TEXT("DefaultMaterial"))
			&& !Name.Equals(TEXT("BasicShapeMaterial"));
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertCryoPods, FAutomationTestBase*, Test);

bool FAssertCryoPods::Update()
{
	UWorld* World = CryoPie::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world for the cryo pod assertions"));
		return true;
	}

	TArray<ACryoPodSystem*> Pods;
	for (TActorIterator<ACryoPodSystem> It(World); It; ++It)
	{
		if (IsValid(*It))
		{
			Pods.Add(*It);
		}
	}

	Test->TestTrue(TEXT("The demo map has cryo pods"), Pods.Num() > 0);
	if (Pods.Num() == 0)
	{
		return true;
	}

	// --- every component is surfaced ---------------------------------------------------------------
	// Six of eight were unassigned. Asserted per component rather than per pod so a failure names
	// the one that regressed instead of only saying a pod is wrong.
	for (ACryoPodSystem* Pod : Pods)
	{
		for (UStaticMeshComponent* Component : CryoPie::VisualComponents(Pod))
		{
			Test->TestTrue(
				FString::Printf(TEXT("%s's %s draws an authored material, not the engine default"),
					*Pod->GetActorLabel(), *Component->GetName()),
				CryoPie::HasRealMaterial(Component));
		}
	}

	// --- the bay tells the right story --------------------------------------------------------------
	// One person climbed out. Any other count is a different scene: zero says nobody woke, and more
	// than one says the player is not alone, which the demo does not mean.
	int32 Open = 0;
	for (const ACryoPodSystem* Pod : Pods)
	{
		if (Pod->IsLidOpen())
		{
			++Open;
		}
	}
	Test->TestEqual(TEXT("Exactly one pod in the bay stands open"), Open, 1);

	// --- the status panel follows the pod ------------------------------------------------------------
	// Three authored colours and a state model that nothing connected. Compared between two pods in
	// different states rather than against a named asset, so the test survives the materials being
	// renamed or re-authored and only fails if the panel stops responding at all.
	ACryoPodSystem* OpenPod = nullptr;
	ACryoPodSystem* ShutPod = nullptr;
	for (ACryoPodSystem* Pod : Pods)
	{
		(Pod->IsLidOpen() ? OpenPod : ShutPod) = Pod;
	}

	if (OpenPod && ShutPod && OpenPod->StatusLights && ShutPod->StatusLights)
	{
		// Both are unoccupied and uncorrupted at map start, so they should agree. The assertion that
		// matters is the next one; this one catches a refresh that never runs at all.
		Test->TestNotNull(TEXT("A pod's status panel has a material"),
			OpenPod->StatusLights->GetMaterial(0));

		UMaterialInterface* Before = ShutPod->StatusLights->GetMaterial(0);
		ShutPod->bIsOccupied = true;
		ShutPod->RefreshStatusLights();
		UMaterialInterface* After = ShutPod->StatusLights->GetMaterial(0);

		Test->TestTrue(TEXT("Occupying a pod changes what its status panel shows"), Before != After);

		ShutPod->bIsOccupied = false;
		ShutPod->RefreshStatusLights();
	}

	// --- the lid still moves ---------------------------------------------------------------------------
	// The lid animation is the one piece of this the pods have always had, and the material and
	// default-state work today went near enough to it to be worth guarding. Asserted as a state
	// change rather than a final pose, because the pose arrives over LidAnimationDuration and this
	// runs in one frame.
	if (ShutPod)
	{
		Test->TestFalse(TEXT("A shut pod reports its lid shut"), ShutPod->IsLidOpen());
		ShutPod->SetLidOpen(true);
		Test->TestTrue(TEXT("Asking a lid to open opens it"), ShutPod->IsLidOpen());
		ShutPod->SetLidOpen(false);
		Test->TestFalse(TEXT("and asking it to shut shuts it again"), ShutPod->IsLidOpen());
	}

	return true;
}

/**
 * The demo map now opens on the player asleep in a shut pod: the opening sequence strikes the ship,
 * wakes them and climbs them out, and only then does the bay tell the story the assertions below
 * expect (one lid open, the sleeper's). Waits for that sequence to report complete, or for a map
 * without one, before asserting; gives up after a bounded time so a stalled opening fails here
 * rather than hanging the runner.
 */
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FWaitForCryoOpening, FAutomationTestBase*, Test);

bool FWaitForCryoOpening::Update()
{
	UWorld* World = CryoPie::FindPieWorld();
	if (!World)
	{
		return false;
	}
	AQuickDemoOpeningSequence* Opening = nullptr;
	for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It)
	{
		Opening = *It;
		break;
	}
	const bool bDone = !Opening || Opening->IsComplete();
	const bool bExpired = World->GetTimeSeconds() > 25.0f;
	if (!bDone && !bExpired)
	{
		return false;
	}
	if (!bDone)
	{
		Test->AddError(FString::Printf(TEXT("The opening sequence did not complete in 25s (phase %d)"),
			static_cast<int32>(Opening->GetPhase())));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCryoPodPieTest,
	"Ginnungagap.Smoke.CryoPods",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCryoPodPieTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForCryoOpening(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(0.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertCryoPods(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
