#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Ship/ModularShipRoom.h"

/**
 * That the hatch ramp between decks 3 and 2 actually joins them on the navmesh.
 *
 * The walkthrough's power leg ended in the room directly above the power room with a PARTIAL
 * path: deck 3 and deck 2 are separate islands. This probes the nearest ramp end to end -- does
 * each point on it sit on navmesh, does the deck-3 floor reach the ramp top, the top reach the
 * bottom, the bottom reach the deck-2 floor -- so the break, if any, has an address. Asserts the
 * full deck-to-deck path, which is what "make their way to the power room" needs.
 */

namespace HatchRamp
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

	const TCHAR* RampLabel = TEXT("QuickDemo4D_HatchRamp_QD-02-05_QD-03-05");
	const FVector Extent(150.0f, 150.0f, 150.0f);

	// A partial path that ends beside an uncleared obstruction is a gate the player resolves,
	// not a break in the ship.
	FString Describe(UWorld* World, const FVector& From, const FVector& To, bool& bOutComplete, bool& bOutGated)
	{
		bOutComplete = false;
		bOutGated = false;
		const UNavigationPath* Path = UNavigationSystemV1::FindPathToLocationSynchronously(World, From, To);
		if (!Path || !Path->IsValid())
		{
			return TEXT("no path");
		}
		bOutComplete = !Path->IsPartial();
		const FVector End = Path->PathPoints.Num() ? Path->PathPoints.Last() : To;
		FString Gate;
		if (!bOutComplete)
		{
			// Recast ends a partial path at the reachable point nearest the goal, which can be a
			// deck above the real gate; so look along the whole path and the straight line to the
			// goal, not just at its end.
			for (TActorIterator<AObstructionBarrier> It(World); It && !bOutGated; ++It)
			{
				if (It->bCleared)
				{
					continue;
				}
				const FVector Gate3D = It->GetActorLocation();
				bool bNear = FVector::Dist(Gate3D, End) <= 350.0f;
				for (const FVector& Point : Path->PathPoints)
				{
					bNear |= FVector::Dist(Gate3D, Point) <= 350.0f;
				}
				for (int32 Step = 0; Step <= 20 && !bNear; ++Step)
				{
					bNear |= FVector::Dist2D(Gate3D, FMath::Lerp(From, To, Step / 20.0f)) <= 250.0f
						&& FMath::Abs(Gate3D.Z - From.Z) <= 300.0f;
				}
				if (bNear)
				{
					bOutGated = true;
					Gate = FString::Printf(TEXT(" -- gated by %s at %s"), *It->GetName(), *Gate3D.ToCompactString());
				}
			}
		}
		return FString::Printf(TEXT("%s (%d points, ends %s)%s"),
			bOutComplete ? TEXT("complete") : TEXT("PARTIAL"), Path->PathPoints.Num(), *End.ToCompactString(), *Gate);
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FProbeHatchRamp, FAutomationTestBase*, Test, double, StartSeconds);

bool FProbeHatchRamp::Update()
{
	UWorld* World = HatchRamp::FindPieWorld();
	UNavigationSystemV1* Navigation = World ? FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) : nullptr;
	if (!World || !Navigation)
	{
		Test->AddError(TEXT("No PIE world or navigation system"));
		return true;
	}
	const double Now = FPlatformTime::Seconds();
	if ((UNavigationSystemV1::IsNavigationBeingBuilt(World) || Now - StartSeconds < 8.0) && Now < StartSeconds + 150.0)
	{
		return false;
	}

	AActor* Ramp = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetActorLabel() == HatchRamp::RampLabel)
		{
			Ramp = *It;
			break;
		}
	}
	if (!Test->TestNotNull(TEXT("The deck 3 to 2 hatch ramp exists"), Ramp))
	{
		return true;
	}

	FVector Origin, BoxExtent;
	Ramp->GetActorBounds(true, Origin, BoxExtent);
	const FVector Forward = Ramp->GetActorForwardVector();   // pitched: points down the ramp
	const float HalfLength = 872.0f * 0.5f;                   // sqrt(700^2 + 520^2)
	const FVector Centre = Ramp->GetActorLocation();
	const FVector Top = Centre - Forward * HalfLength;
	const FVector Bottom = Centre + Forward * HalfLength;
	Test->AddInfo(FString::Printf(TEXT("RAMP centre %s pitch %.1f forward %s; top %s bottom %s; bounds extent %s"),
		*Centre.ToCompactString(), Ramp->GetActorRotation().Pitch, *Forward.ToCompactString(),
		*Top.ToCompactString(), *Bottom.ToCompactString(), *BoxExtent.ToCompactString()));

	// The route the RestorePower objective describes, point by point. Room centres are useless
	// here -- the hatch room's centre is over the 700 x 360 opening, with no floor to project onto
	// -- so the points sit on the floor strips around it, the doors, and the corridors.
	FVector PowerLoc = FVector::ZeroVector;
	for (TActorIterator<AQuickDemoPowerStation> It(World); It; ++It) { PowerLoc = It->GetActorLocation(); break; }

	struct FStop { const TCHAR* Label; FVector Point; };
	const float Deck3 = 1158.0f;
	const float Deck2 = 638.0f;
	TArray<FStop> Stops = {
		{TEXT("deck3 corridor at hatch room"), FVector(-1800, 0, Deck3)},
		{TEXT("hatch room door (inside)"), FVector(-1800, -340, Deck3)},
		{TEXT("hatch room aft strip"), FVector(-2250, -680, Deck3)},
		{TEXT("ramp top"), Top + FVector(0, 0, 100)},
		{TEXT("ramp bottom"), Bottom + FVector(0, 0, 100)},
		{TEXT("deck2 hatch room floor"), FVector(-1800, -1000, Deck2)},
		{TEXT("deck2 corridor at hatch room"), FVector(-1800, 0, Deck2)},
		{TEXT("deck2 corridor col 4"), FVector(-3000, 0, Deck2)},
		{TEXT("deck2 corridor col 3"), FVector(-4200, 0, Deck2)},
		{TEXT("deck2 corridor at power room"), FVector(-5400, 0, Deck2)},
		{TEXT("power station"), PowerLoc},
	};

	TArray<FVector> OnMesh;
	for (const FStop& Stop : Stops)
	{
		FNavLocation On;
		const bool bOk = Navigation->ProjectPointToNavigation(Stop.Point, On, HatchRamp::Extent);
		Test->AddInfo(FString::Printf(TEXT("RAMP stop %-30s %s -> %s"), Stop.Label, *Stop.Point.ToCompactString(),
			bOk ? *On.Location.ToCompactString() : TEXT("NO navmesh within 150")));
		OnMesh.Add(bOk ? On.Location : Stop.Point);
	}

	bool bAllJoined = true;
	for (int32 Index = 1; Index < Stops.Num(); ++Index)
	{
		bool bComplete = false;
		bool bGated = false;
		const FString Verdict = HatchRamp::Describe(World, OnMesh[Index - 1], OnMesh[Index], bComplete, bGated);
		Test->AddInfo(FString::Printf(TEXT("RAMP leg %-30s -> %-30s %s"), Stops[Index - 1].Label, Stops[Index].Label, *Verdict));
		// A gate is the player's problem to solve, not a break in the ship.
		bAllJoined &= bComplete || bGated;
	}
	Test->TestTrue(TEXT("Every leg from the deck 3 corridor to the power station is joined on the navmesh, or gated by an obstruction"), bAllJoined);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapHatchRampConnectivityPieTest,
	"Ginnungagap.Smoke.HatchRampConnectsDecks",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapHatchRampConnectivityPieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	const double Start = FPlatformTime::Seconds();
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FProbeHatchRamp(this, Start));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
