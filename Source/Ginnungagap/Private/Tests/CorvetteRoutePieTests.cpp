#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NavigationSystem.h"
#include "NavigationPath.h"

#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Activities/WeldableBulkheadDoor.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "NavigationData.h"

/**
 * The corvette's decks connect by ramps in the access trunk, and the objective chain sends the
 * player down two decks and then up six. This asks the navmesh whether those legs exist: from
 * the player start, a complete path to the engineering bench (down one deck), to the power
 * station (down two), and then -- with the security deck's buckled trunk cleared -- up to the
 * comms deck's breach station and on to the CIC door override. A missing or partial path is a
 * ramp that does not meet its floor, a doorway too narrow, or an opening in the wrong lane.
 *
 * Runs on the map -GinnungagapMap names, default the corvette stack.
 */
namespace CorvetteRoute
{
	FString MapPath()
	{
		FString Override;
		if (FParse::Value(FCommandLine::Get(), TEXT("GinnungagapMap="), Override) && !Override.IsEmpty())
		{
			return Override;
		}
		return TEXT("/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack");
	}

	UWorld* FindPieWorld()
	{
		if (!GEngine) return nullptr;
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World()) return Context.World();
		}
		return nullptr;
	}

	template <typename T> AActor* First(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It) { return *It; }
		return nullptr;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertCorvetteRoutes, FAutomationTestBase*, Test);

bool FAssertCorvetteRoutes::Update()
{
	static double StartedAt = -1.0;
	static bool bPrepared = false;
	UWorld* World = CorvetteRoute::FindPieWorld();
	if (!World)
	{
		return false;
	}
	UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);
	if (!Nav || !Pawn)
	{
		if (StartedAt < 0.0) { StartedAt = World->GetTimeSeconds(); }
		if (World->GetTimeSeconds() - StartedAt > 20.0) { Test->AddError(TEXT("No navigation system or pawn after 20s")); StartedAt = -1.0; return true; }
		return false;
	}
	if (!bPrepared)
	{
		// Out of the pod and onto the deck: the opening holds the pawn inside the pod, off the mesh.
		for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It) { It->Skip(); }
		// Any gate on the way up is opened for the reachability question; the stations are the
		// chain's business, this is the ship's.
		for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
		{
			It->SetActorEnableCollision(false);
			It->SetActorHiddenInGame(true);
		}
		Nav->Build();
		bPrepared = true;
		StartedAt = World->GetTimeSeconds();
		return false;
	}
	// Runtime generation is asynchronous; give it up to 30 s.
	if (Nav->IsNavigationBuildInProgress() && World->GetTimeSeconds() - StartedAt < 30.0)
	{
		return false;
	}
	const ANavigationData* NavData = Nav->GetDefaultNavDataInstance();
	Test->TestNotNull(TEXT("The map has navigation data"), NavData);
	UE_LOG(LogTemp, Display, TEXT("CORVETTEROUTE nav data %s, build in progress %d, %.1fs after prepare"),
		NavData ? *NavData->GetName() : TEXT("none"), Nav->IsNavigationBuildInProgress() ? 1 : 0, World->GetTimeSeconds() - StartedAt);

	struct FLeg { FString Name; AActor* Target; };
	const TArray<FLeg> Legs = {
		{ TEXT("engineering bench (one deck down)"), CorvetteRoute::First<AQuickDemoWorkshopBench>(World) },
		{ TEXT("power station (two decks down)"), CorvetteRoute::First<AQuickDemoPowerStation>(World) },
		{ TEXT("breach station (four decks up)"), CorvetteRoute::First<AQuickDemoBreachStation>(World) },
		{ TEXT("CIC door override (five decks up)"), CorvetteRoute::First<AQuickDemoCICAccessStation>(World) },
	};
	FNavLocation StartOnMesh;
	const bool bStartOnMesh = Nav->ProjectPointToNavigation(Pawn->GetActorLocation(), StartOnMesh, FVector(200.0f, 200.0f, 300.0f));
	// Where a route breaks: probe points down the intended path from the casualty station (deck
	// 3, floor at 860) through its door, along the corridor, into the trunk landing, down the ramp
	// to deck 2's landing, and on to deck 2's main room door.
	{
		const float D3 = 860.0f, D2 = 430.0f;
		const TArray<TPair<FString, FVector>> Probes = {
			{ TEXT("D3 main room door (inside)"), FVector(750.0f, 1080.0f, D3) },
			{ TEXT("D3 corridor at the door"), FVector(750.0f, 800.0f, D3) },
			{ TEXT("D3 trunk landing"), FVector(900.0f, 425.0f, D3) },
			{ TEXT("D3 lane foot (flat)"), FVector(1200.0f, 150.0f, D3) },
			{ TEXT("D3 ramp, one third up"), FVector(770.0f, 150.0f, D3 + 143.0f) },
			{ TEXT("D3 ramp, near the head"), FVector(340.0f, 150.0f, D3 + 405.0f) },
			{ TEXT("D3 lane head (flat, from below)"), FVector(150.0f, 150.0f, D3) },
			{ TEXT("D2 ramp near its head (just under D3)"), FVector(340.0f, 150.0f, D2 + 405.0f) },
			{ TEXT("D2 landing beside the head"), FVector(150.0f, 425.0f, D2) },
			{ TEXT("D2 landing beside the foot"), FVector(1200.0f, 425.0f, D2) },
			{ TEXT("D2 corridor at the door"), FVector(750.0f, 800.0f, D2) },
			{ TEXT("D2 in the doorway"), FVector(750.0f, 1000.0f, D2) },
			{ TEXT("D2 main room just inside"), FVector(750.0f, 1100.0f, D2) },
			{ TEXT("D2 main room centre"), FVector(750.0f, 1400.0f, D2) },
			{ TEXT("D2 in front of the bench"), FVector(550.0f, 1560.0f, D2) },
			{ TEXT("D1 in the doorway"), FVector(750.0f, 1000.0f, 0.0f) },
			{ TEXT("D1 main room centre"), FVector(750.0f, 1400.0f, 0.0f) },
		};
		for (const TPair<FString, FVector>& Probe : Probes)
		{
			FNavLocation On;
			const bool bOn = Nav->ProjectPointToNavigation(Probe.Value, On, FVector(120.0f, 120.0f, 120.0f));
			UNavigationPath* P = bOn ? Nav->FindPathToLocationSynchronously(World, StartOnMesh.Location, On.Location, Pawn) : nullptr;
			const bool bReach = P && P->IsValid() && !P->IsPartial() && P->PathPoints.Num() > 1;
			UE_LOG(LogTemp, Display, TEXT("CORVETTEROUTE probe %-45s on mesh %d (%s) reachable %d"), *Probe.Key, bOn ? 1 : 0,
				bOn ? *On.Location.ToCompactString() : TEXT("-"), bReach ? 1 : 0);
		}
	}
	Test->TestTrue(FString::Printf(TEXT("The player start projects onto the navmesh (pawn at %s)"), *Pawn->GetActorLocation().ToCompactString()), bStartOnMesh);
	for (const FLeg& Leg : Legs)
	{
		if (!Test->TestNotNull(FString::Printf(TEXT("The map has the %s"), *Leg.Name), Leg.Target)) continue;
		FNavLocation GoalOnMesh;
		const bool bGoalOnMesh = Nav->ProjectPointToNavigation(Leg.Target->GetActorLocation(), GoalOnMesh, FVector(250.0f, 250.0f, 300.0f));
		Test->TestTrue(FString::Printf(TEXT("The %s projects onto the navmesh (at %s)"), *Leg.Name, *Leg.Target->GetActorLocation().ToCompactString()), bGoalOnMesh);
		UNavigationPath* Path = Nav->FindPathToLocationSynchronously(World, StartOnMesh.Location, bGoalOnMesh ? GoalOnMesh.Location : Leg.Target->GetActorLocation(), Pawn);
		const bool bComplete = Path && Path->IsValid() && !Path->IsPartial() && Path->PathPoints.Num() > 1;
		const FVector End = (Path && Path->PathPoints.Num() > 0) ? Path->PathPoints.Last() : FVector::ZeroVector;
		FString Points;
		if (Path) { for (const FVector& Pt : Path->PathPoints) { Points += Pt.ToCompactString() + TEXT(" "); } }
		UE_LOG(LogTemp, Display, TEXT("CORVETTEROUTE leg %s: goal %s projects %d -> %s; path %s"), *Leg.Name,
			*Leg.Target->GetActorLocation().ToCompactString(), bGoalOnMesh ? 1 : 0, *GoalOnMesh.Location.ToCompactString(), *Points);
		Test->TestTrue(FString::Printf(TEXT("A complete walkable path exists from the start to the %s (path ends %.0f cm from it, %d points, partial %d)"),
			*Leg.Name, FVector::Dist(End, Leg.Target->GetActorLocation()), Path ? Path->PathPoints.Num() : 0, (Path && Path->IsPartial()) ? 1 : 0), bComplete);
	}
	// The optional work on every deck (tagged CorvetteSideStation by the generator) must be
	// walkable too, or a deck is just a corridor with a locked room.
	int32 SideStations = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (!It->ActorHasTag(TEXT("CorvetteSideStation"))) continue;
		++SideStations;
		FNavLocation GoalOnMesh;
		const bool bGoalOnMesh = Nav->ProjectPointToNavigation(It->GetActorLocation(), GoalOnMesh, FVector(250.0f, 250.0f, 300.0f));
		UNavigationPath* Path = bGoalOnMesh ? Nav->FindPathToLocationSynchronously(World, StartOnMesh.Location, GoalOnMesh.Location, Pawn) : nullptr;
		const bool bComplete = Path && Path->IsValid() && !Path->IsPartial() && Path->PathPoints.Num() > 1;
		Test->TestTrue(FString::Printf(TEXT("Side station %s at %s is reachable from the start"), *It->GetName(), *It->GetActorLocation().ToCompactString()), bComplete);
	}
	Test->TestTrue(FString::Printf(TEXT("The corvette has side stations to find (%d)"), SideStations), SideStations >= 8);
	// The obstacles beyond the security deck: a bypassable cable tray in the tactical corridor and
	// the observation deck's welded secondary door. They were hidden for the reachability question
	// above; here they must exist and be what they claim.
	int32 Barriers = 0, Bypassable = 0;
	for (TActorIterator<AObstructionBarrier> It(World); It; ++It) { ++Barriers; if (It->bBypassable) { ++Bypassable; } }
	Test->TestTrue(FString::Printf(TEXT("The corvette has obstruction barriers (%d, %d bypassable)"), Barriers, Bypassable), Barriers >= 2 && Bypassable >= 1);
	int32 Welded = 0;
	for (TActorIterator<AWeldableBulkheadDoor> It(World); It; ++It)
	{
		if (!It->ActorHasTag(TEXT("CorvetteWeldedDoor"))) continue;
		++Welded;
		Test->TestTrue(FString::Printf(TEXT("%s is welded shut and impassable"), *It->GetName()), It->bWeldedShut && !It->IsPassable());
	}
	Test->TestTrue(FString::Printf(TEXT("The corvette has a welded door to cut free (%d)"), Welded), Welded >= 1);
	int32 Supplies = 0;
	for (TActorIterator<AActor> It(World); It; ++It) { if (It->ActorHasTag(TEXT("CorvetteSupply"))) { ++Supplies; } }
	Test->TestTrue(FString::Printf(TEXT("The corvette has supplies to find (%d)"), Supplies), Supplies >= 20);
	bPrepared = false; StartedAt = -1.0;
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCorvetteRoutesTest,
	"Ginnungagap.Smoke.CorvetteRoutesReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCorvetteRoutesTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(CorvetteRoute::MapPath());
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertCorvetteRoutes(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
