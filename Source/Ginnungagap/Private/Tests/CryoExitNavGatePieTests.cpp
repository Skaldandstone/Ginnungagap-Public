#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "CollisionQueryParams.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/ModularShipRoom.h"

/**
 * That the cryo-exit obstruction physically gates the way out, and that clearing it opens it.
 *
 * Every other check on this obstruction proves a mechanism: ResolveWith flips bCleared. None of
 * them proves the thing the beat depends on -- that a pawn cannot walk past it before, and can
 * after. DemoReachability does not either: its one real path query runs PlayerStart to the suit
 * station and stops there on purpose, before any door. So its passing after the obstruction was
 * placed said nothing about the obstruction at all.
 *
 * The navmesh is runtime-generated, and the Blocker is a WorldStatic box that blocks every channel,
 * which the generator rasterises as an obstacle once its tile builds. Clearing sets NoCollision,
 * which dirties the tile and reopens it. Both are expectations until measured; this measures them.
 *
 * Endpoints are the beat's own: the player start inside cryo, and a point in the corridor just past
 * where the box sits, derived from the cryo door's transform. Not the workshop bench: the bench is
 * inside its own room behind a second door of the same kind, so a path to it would fail for that
 * door and say nothing about this one. The bench path is logged as a diagnostic instead.
 *
 * ABulkheadDoor's Seal and Unseal are atmospheric (leak factor, power draw) and touch neither
 * collision nor navigation; the production door Blueprint contains no opening logic of its own. So
 * as far as the code knows, the doorway is whatever its leaf mesh makes it. Three outcomes:
 *   no path before, path after   -- the obstruction gates the exit and clearing opens it.
 *   no path before, none after   -- the doorway itself is not navigable; the leaf or frame blocks
 *                                   it regardless of the obstruction, and the player cannot leave
 *                                   cryo on the navmesh at all. That finding outranks this test.
 *   path before                  -- the obstruction is not rasterised, or does not seal the doorway;
 *                                   a real placement finding.
 *
 * Retries until a deadline, as DemoReachability does: a runtime navmesh fills in progressively and
 * a single sample is a race. Gating on IsNavigationBeingBuilt keeps a "no path" from meaning "tile
 * not built yet", and a minimum settle after clearing keeps the second query from racing the dirty
 * marking.
 */

namespace CryoExitNavGate
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

	// Same extent DemoReachability uses for these same two actors.
	const FVector ProjectionExtent(400.0f, 400.0f, 300.0f);

	bool IsComplete(const UNavigationPath* Path)
	{
		return Path && Path->IsValid() && !Path->IsPartial();
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FAssertCryoExitGatesNavmesh, FAutomationTestBase*, Test, double, DeadlineSeconds);

bool FAssertCryoExitGatesNavmesh::Update()
{
	// Per-command state, kept static because the latent command object is recreated by the
	// framework between ticks in some configurations; keyed on nothing because only one instance
	// of this command runs at a time.
	static bool bCleared = false;
	static double ClearedAtSeconds = 0.0;
	static FVector Near = FVector::ZeroVector;
	static FVector Far = FVector::ZeroVector;

	UWorld* World = CryoExitNavGate::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world"));
		bCleared = false;
		return true;
	}

	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!Navigation)
	{
		Test->AddError(TEXT("No navigation system in the demo level"));
		bCleared = false;
		return true;
	}
	Navigation->SetMaxSimultaneousTileGenerationJobsCount(16);

	AObstructionBarrier* Barrier = nullptr;
	for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
	{
		if (It->ActorHasTag(TEXT("CRYO-EXIT")))
		{
			Barrier = *It;
			break;
		}
	}
	if (!Barrier || !Barrier->Blocker)
	{
		Test->AddError(TEXT("No CRYO-EXIT obstruction with a Blocker in the running level"));
		bCleared = false;
		return true;
	}

	const bool bExpired = FPlatformTime::Seconds() >= DeadlineSeconds;
	const bool bBuilding = UNavigationSystemV1::IsNavigationBeingBuilt(World);

	// ---- phase 1: before clearing ------------------------------------------------------------
	if (!bCleared)
	{
		if (bBuilding && !bExpired)
		{
			return false;
		}
		if (bBuilding)
		{
			Test->AddError(TEXT("Navmesh never finished building before the deadline (phase 1)"));
			return true;
		}

		APlayerStart* Start = nullptr;
		for (TActorIterator<APlayerStart> It(World); It; ++It)
		{
			Start = *It;
			break;
		}
		ABulkheadDoor* Door = nullptr;
		for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("QD-03-01")))
			{
				Door = *It;
				break;
			}
		}
		if (!Start || !Door)
		{
			Test->AddError(FString::Printf(TEXT("Endpoints missing (player start %s, cryo door %s)"),
				Start ? TEXT("ok") : TEXT("NO"), Door ? TEXT("ok") : TEXT("NO")));
			return true;
		}

		// Through the doorway is +/-Y toward the corridor -- not the door actor's forward, which the
		// generator leaves at yaw 0 (+X, along the wall) for every door. Derived from the room's
		// own position, as the doorway audit does. +300 is a clear 120cm past the box's far face
		// at +180; the extent reaches back over the box but not the 300cm to the room.
		AModularShipRoom* Room = nullptr;
		for (TActorIterator<AModularShipRoom> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("QD-03-01")))
			{
				Room = *It;
				break;
			}
		}
		const float ThroughY = (Room && Door->GetActorLocation().Y < Room->GetActorLocation().Y) ? -1.0f : 1.0f;
		const FVector CorridorPoint = Door->GetActorLocation() + FVector(0.0f, ThroughY * 300.0f, 0.0f);

		FNavLocation NearOnMesh;
		FNavLocation FarOnMesh;
		const bool bNearOk = Navigation->ProjectPointToNavigation(
			Start->GetActorLocation(), NearOnMesh, CryoExitNavGate::ProjectionExtent);
		const bool bFarOk = Navigation->ProjectPointToNavigation(
			CorridorPoint, FarOnMesh, FVector(150.0f, 150.0f, 200.0f));
		if (!bNearOk || !bFarOk)
		{
			// IsNavigationBeingBuilt is false before generation has started as well as after it has
			// finished, so an early tick can find no tiles at all. Retry, as DemoReachability does,
			// and only call it a failure at the deadline.
			if (!bExpired)
			{
				return false;
			}
			Test->AddError(FString::Printf(
				TEXT("Endpoint never projected before the deadline (player start %s, corridor point past the box %s at %s). ")
				TEXT("The start projects in DemoReachability; a corridor point that does not means the corridor ")
				TEXT("outside the cryo door is not navmeshed there."),
				bNearOk ? TEXT("ok") : TEXT("NO"), bFarOk ? TEXT("ok") : TEXT("NO"),
				*CorridorPoint.ToCompactString()));
			return true;
		}
		Near = NearOnMesh.Location;
		Far = FarOnMesh.Location;

		// Diagnostics for the "no path after" case, so a failure names its cause instead of
		// leaving three hypotheses standing.
		if (const ARecastNavMesh* Recast = Cast<ARecastNavMesh>(Navigation->GetDefaultNavDataInstance()))
		{
			Test->AddInfo(FString::Printf(
				TEXT("NavGate: runtime generation mode %d (0 Static, 1 DynamicModifiersOnly, 2 Dynamic)"),
				static_cast<int32>(Recast->GetRuntimeGenerationMode())));
		}
		Test->AddInfo(FString::Printf(TEXT("NavGate: Blocker CanEverAffectNavigation %s"),
			Barrier->Blocker->CanEverAffectNavigation() ? TEXT("yes") : TEXT("no")));
		for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("QD-03-01")))
			{
				continue;
			}
			FNavLocation DoorOnMesh;
			const bool bDoorOnMesh = Navigation->ProjectPointToNavigation(
				It->GetActorLocation(), DoorOnMesh, FVector(100.0f, 100.0f, 200.0f));
			const UStaticMeshComponent* Leaf = It->FindComponentByClass<UStaticMeshComponent>();
			Test->AddInfo(FString::Printf(
				TEXT("NavGate: cryo door threshold on navmesh %s; IsPassable %s; leaf collision %d (0 none, 1 query, 2 physics, 3 both)"),
				bDoorOnMesh ? TEXT("yes") : TEXT("no"),
				It->IsPassable() ? TEXT("yes") : TEXT("no"),
				Leaf ? static_cast<int32>(Leaf->GetCollisionEnabled()) : -1));
			break;
		}

		Test->TestEqual(TEXT("Before: the Blocker physically collides"),
			Barrier->Blocker->GetCollisionEnabled(), ECollisionEnabled::QueryAndPhysics);

		UNavigationPath* Before = UNavigationSystemV1::FindPathToLocationSynchronously(World, Near, Far);
		Test->TestFalse(
			TEXT("Before: no complete navmesh path across the obstruction. If this fails, the box either ")
			TEXT("is not rasterised into the navmesh or does not seal the doorway frontage -- a real placement finding, not test noise."),
			CryoExitNavGate::IsComplete(Before));

		APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);
		const EObstructionVerb Verb = Barrier->CanResolveWith(EObstructionVerb::Cut, Pawn)
			? EObstructionVerb::Cut : EObstructionVerb::Squeeze;
		if (!Test->TestTrue(TEXT("ResolveWith succeeds"), Barrier->ResolveWith(Verb, Pawn)))
		{
			return true;
		}
		Test->TestEqual(TEXT("After clearing: the Blocker no longer collides"),
			Barrier->Blocker->GetCollisionEnabled(), ECollisionEnabled::NoCollision);

		bCleared = true;
		ClearedAtSeconds = FPlatformTime::Seconds();
		return false;
	}

	// ---- phase 2: after clearing ---------------------------------------------------------------
	// Retries until a path appears or the deadline passes, as DemoReachability does. A single
	// sample after "not building" is a race against the dirty-area being queued at all.
	const bool bSettled = FPlatformTime::Seconds() - ClearedAtSeconds >= 1.0;
	if (bSettled && !bBuilding)
	{
		UNavigationPath* After = UNavigationSystemV1::FindPathToLocationSynchronously(World, Near, Far);
		if (CryoExitNavGate::IsComplete(After))
		{
			Test->TestTrue(TEXT("After: a complete navmesh path now crosses where the obstruction was"), true);
			bCleared = false;
			return true;
		}
	}
	if (!bExpired)
	{
		return false;
	}

	// Diagnostic only: whether the workshop bench, behind its own door, is reachable now.
	for (TActorIterator<AQuickDemoWorkshopBench> It(World); It; ++It)
	{
		FNavLocation BenchOnMesh;
		if (Navigation->ProjectPointToNavigation(It->GetActorLocation(), BenchOnMesh, CryoExitNavGate::ProjectionExtent))
		{
			const UNavigationPath* ToBench = UNavigationSystemV1::FindPathToLocationSynchronously(World, Near, BenchOnMesh.Location);
			Test->AddInfo(FString::Printf(TEXT("NavGate: start -> workshop bench path complete after clear: %s"),
				CryoExitNavGate::IsComplete(ToBench) ? TEXT("yes") : TEXT("no")));
		}
		break;
	}

	// Physical probe, independent of the navmesh: can a pawn-sized capsule pass the doorway at all?
	// A doorway too narrow for the navmesh's agent erosion can still admit the capsule -- then the
	// player can leave but no AI can ever follow. Both are worth knowing, and separately.
	{
		ABulkheadDoor* DoorActor = nullptr;
		for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("QD-03-01")))
			{
				DoorActor = *It;
				break;
			}
		}
		APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);
		const ACharacter* Character = Cast<ACharacter>(Pawn);
		if (DoorActor && Character && Character->GetCapsuleComponent())
		{
			const float Radius = Character->GetCapsuleComponent()->GetScaledCapsuleRadius();
			const float HalfHeight = Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
			const FVector Fwd = DoorActor->GetActorForwardVector();
			const FVector DoorLoc = DoorActor->GetActorLocation();
			// Near is the projected player start, so its Z is the room floor.
			const float CentreZ = Near.Z + HalfHeight + 2.0f;
			FVector From = DoorLoc - Fwd * 150.0f;
			FVector To = DoorLoc + Fwd * 300.0f;
			From.Z = CentreZ;
			To.Z = CentreZ;

			FCollisionQueryParams Params(SCENE_QUERY_STAT(CryoExitNavGateSweep), false);
			Params.AddIgnoredActor(Pawn);
			FHitResult Hit;
			const bool bBlocked = World->SweepSingleByChannel(Hit, From, To, FQuat::Identity, ECC_Pawn,
				FCollisionShape::MakeCapsule(Radius, HalfHeight), Params);
			Test->AddInfo(FString::Printf(
				TEXT("NavGate: pawn capsule (r %.0f, hh %.0f) swept through the doorway at floor z %.0f: %s"),
				Radius, HalfHeight, Near.Z,
				bBlocked
					? *FString::Printf(TEXT("BLOCKED by %s / %s at %s"),
						Hit.GetActor() ? *Hit.GetActor()->GetName() : TEXT("?"),
						Hit.GetComponent() ? *Hit.GetComponent()->GetName() : TEXT("?"),
						*Hit.ImpactPoint.ToCompactString())
					: TEXT("clear -- the capsule fits; only the navmesh is closed")));
		}
	}

	Test->AddError(
		TEXT("After: no complete navmesh path from the player start to the corridor just past the cleared ")
		TEXT("obstruction, before the deadline. With runtime generation Dynamic and the box nav-relevant, the ")
		TEXT("cleared box is not what blocks it: the cryo doorway itself is not navigable, and the player ")
		TEXT("cannot leave the cryo bay on the navmesh regardless of the obstruction."));
	bCleared = false;
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCryoExitNavGatePieTest,
	"Ginnungagap.Smoke.CryoExitObstructionGatesNavmesh",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCryoExitNavGatePieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);

	const double Deadline = FPlatformTime::Seconds() + 150.0;

	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertCryoExitGatesNavmesh(this, Deadline));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
