#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/Engine.h"
#include "Engine/OverlapResult.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/TextRenderActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "UnrealClient.h"

#include "Activities/ActivityStation.h"
#include "Activities/WeldableBulkheadDoor.h"
#include "Activities/PlayerActivitySource.h"
#include "CoopSurvivalCharacter.h"
#include "Inventory/InventoryItemPickup.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/CryoPodSystem.h"

/**
 * The ship surveyed the way a player meets it: the character is driven on foot along the real
 * paths, up the chain of objectives and back down again, then out to every side station, and
 * everything met on the way is written down -- where each thing is, how long the walk was, where
 * the character snagged, clipped or lost the floor, what blocked the route, and which of the
 * ship's interactables are static props that only speak through a text prompt. The record is
 * docs/CorvetteSurvey.md, the list the next pass of work is drawn from. Stills of each arrival
 * land in Saved/Screenshots when the editor has a window.
 */
namespace Survey
{
	UWorld* FindPieWorld()
	{
		if (!GEngine) { return nullptr; }
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World()) { return Context.World(); }
		}
		return nullptr;
	}

	FString MapPath()
	{
		FString Override;
		if (FParse::Value(FCommandLine::Get(), TEXT("GinnungagapMap="), Override) && !Override.IsEmpty()) { return Override; }
		return TEXT("/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack");
	}

	template <typename T> AActor* First(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It) { return *It; }
		return nullptr;
	}

	struct FLeg
	{
		FString Name;
		TWeakObjectPtr<AActor> Target;
		bool bPlay = false;   // fire the station's completion on arrival (the chain's stations, on the way up)
	};

	struct FLegRecord
	{
		FString Name;
		FVector Where = FVector::ZeroVector;
		float PathLength = -1.0f;
		float Seconds = 0.0f;
		int32 Snags = 0;
		FString Outcome;
	};

	FString Compact(const FVector& V)
	{
		return FString::Printf(TEXT("(%.0f, %.0f, %.0f)"), V.X, V.Y, V.Z);
	}

	int32 DeckOf(float Z)
	{
		return FMath::Clamp(FMath::RoundToInt(Z / 430.0f) + 1, 1, 11);
	}

	/** The nearest actor with collision to a point, for naming what the character ran into. */
	FString NearestBlocker(UWorld* World, const FVector& At, AActor* Ignore, float Radius = 70.0f)
	{
		TArray<FOverlapResult> Overlaps;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(Survey), false, Ignore);
		World->OverlapMultiByChannel(Overlaps, At, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Radius, 90.0f), Params);
		FString Best; float BestDist = TNumericLimits<float>::Max();
		for (const FOverlapResult& O : Overlaps)
		{
			if (!O.bBlockingHit || !O.GetActor()) { continue; }
			const float D = FVector::Dist(O.GetActor()->GetActorLocation(), At);
			if (D < BestDist) { BestDist = D; Best = O.GetActor()->GetActorNameOrLabel(); }
		}
		return Best;
	}

	/** A standing spot a step and a half off the target, on the navmesh, on whichever side has one. */
	bool SpotBefore(UWorld* World, UNavigationSystemV1* Nav, AActor* Target, FVector& OutSpot)
	{
		const FVector At = Target->GetActorLocation();
		const FVector Forward = Target->GetActorForwardVector().GetSafeNormal2D();
		for (const float Distance : { 150.0f, 110.0f, 200.0f })
		for (const FVector& Dir : { Forward, -Forward, FVector(Forward.Y, -Forward.X, 0.0f), FVector(-Forward.Y, Forward.X, 0.0f) })
		{
			FNavLocation OnMesh;
			if (Nav->ProjectPointToNavigation(At + Dir * Distance, OnMesh, FVector(60.0f, 60.0f, 260.0f)))
			{
				OutSpot = OnMesh.Location;
				return true;
			}
		}
		FNavLocation OnMesh;
		if (Nav->ProjectPointToNavigation(At, OnMesh, FVector(250.0f, 250.0f, 300.0f)))
		{
			OutSpot = OnMesh.Location;
			return true;
		}
		return false;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FSurveyWalk, FAutomationTestBase*, Test);

bool FSurveyWalk::Update()
{
	using namespace Survey;
	static bool bPrepared = false;
	static double StartedAt = -1.0;
	static double LegStartedAt = -1.0;
	static double LastProbeAt = -1.0;
	static double LastMoveCheckAt = -1.0;
	static FVector LastMoveCheckLocation = FVector::ZeroVector;
	static int32 Index = 0;
	static int32 Phase = 0;   // 0: issue the move, 1: walking, 2: arrived (still + note), 3: dwell
	static double PhaseAt = -1.0;
	static TArray<FLeg> Legs;
	static TArray<FLegRecord> Records;
	static TArray<FString> Findings;
	static TArray<FString> Audit;
	static TSet<FString> Seen;
	static FLegRecord Current;
	static FVector Goal = FVector::ZeroVector;
	static const double Budget = 420.0;

	UWorld* World = FindPieWorld();
	if (!World) { return false; }
	const double Now = World->GetTimeSeconds();
	UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	ACoopSurvivalCharacter* Pawn = PC ? Cast<ACoopSurvivalCharacter>(PC->GetPawn()) : nullptr;
	if (!Nav || !PC || !Pawn)
	{
		if (StartedAt < 0.0) { StartedAt = Now; }
		if (Now - StartedAt > 20.0) { Test->AddError(TEXT("No navigation, controller or crew after 20 s")); bPrepared = false; StartedAt = -1.0; return true; }
		return false;
	}

	auto Finish = [&]()
	{
		// Figures, listed now that the crew has walked the ship: every skeletal mesh that is not
		// the crew's own, with where it stands and what it is attached to. A body far from the crew
		// that claims to be attached to them is a child actor that never moved.
		// Floating props: anything with a mesh whose underside is well off the deck and whose sides
		// touch no wall. A console hanging in the air reads as a placeholder, not a fixture.
		Audit.Add(TEXT(""));
		Audit.Add(TEXT("| Floating prop | Class | Deck | Where | Mesh | Under it (cm) | Nearest wall (cm) |"));
		Audit.Add(TEXT("|---------------|-------|------|-------|------|---------------|-------------------|"));
		int32 Floating = 0;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (*It == Pawn || It->IsA<ABulkheadDoor>() || It->IsA<ATextRenderActor>() || It->IsA<AQuickDemoObjectiveBeacon>()) { continue; }
			const UStaticMeshComponent* SM = It->FindComponentByClass<UStaticMeshComponent>();
			if (!SM || !SM->GetStaticMesh() || !SM->IsVisible() || !SM->IsCollisionEnabled()) { continue; }
			const FString Label = It->GetActorNameOrLabel();
			// The ship's own shell and its rails, lamps and cabling are not props.
			if (Label.Contains(TEXT("_Hull")) || Label.Contains(TEXT("Floor")) || Label.Contains(TEXT("Ceiling")) || Label.Contains(TEXT("Corridor"))
				|| Label.Contains(TEXT("Rooms")) || Label.Contains(TEXT("Partition")) || Label.Contains(TEXT("Trunk")) || Label.Contains(TEXT("Service"))
				|| Label.Contains(TEXT("Ramp")) || Label.Contains(TEXT("Rail")) || Label.Contains(TEXT("Lane")) || Label.Contains(TEXT("Main")) || Label.Contains(TEXT("Second"))
				|| Label.Contains(TEXT("Lamp")) || Label.Contains(TEXT("Cable")) || Label.Contains(TEXT("Duct")) || Label.Contains(TEXT("Pipe")) || Label.Contains(TEXT("SignPlate"))
				|| Label.Contains(TEXT("Space")) || Label.Contains(TEXT("Window")) || Label.Contains(TEXT("Breach")) || Label.Contains(TEXT("Glass")) || Label.Contains(TEXT("Seal")))
			{
				continue;
			}
			const FBox Box = SM->Bounds.GetBox();
			if (Box.GetSize().Z < 10.0f) { continue; }
			FCollisionQueryParams Params(SCENE_QUERY_STAT(Survey), false, *It);
			const FVector Foot(Box.GetCenter().X, Box.GetCenter().Y, Box.Min.Z + 1.0f);
			FHitResult Down;
			float Under = -1.0f;
			if (World->LineTraceSingleByChannel(Down, Foot, Foot - FVector(0.0f, 0.0f, 400.0f), ECC_Visibility, Params)) { Under = Down.Distance; }
			float NearestWall = 9999.0f;
			const FVector Mid = Box.GetCenter();
			for (const FVector& Dir : { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) })
			{
				FHitResult Side;
				const FVector Edge = Mid + Dir * (FMath::Abs(FVector::DotProduct(Box.GetExtent(), Dir)) + 1.0f);
				if (World->LineTraceSingleByChannel(Side, Edge, Edge + Dir * 300.0f, ECC_Visibility, Params)) { NearestWall = FMath::Min(NearestWall, Side.Distance); }
			}
			if (Under > 12.0f && NearestWall > 12.0f)
			{
				++Floating;
				if (Floating <= 60)
				{
					Audit.Add(FString::Printf(TEXT("| %s | %s | %d | %s | %s | %.0f | %s |"), *Label, *It->GetClass()->GetName(), DeckOf(It->GetActorLocation().Z),
						*Compact(It->GetActorLocation()), *SM->GetStaticMesh()->GetName(), Under, NearestWall < 9000.0f ? *FString::Printf(TEXT("%.0f"), NearestWall) : TEXT(">300")));
				}
			}
		}
		Audit.Add(FString::Printf(TEXT("| (%d floating props in all) | | | | | | |"), Floating));
		Audit.Add(TEXT(""));
		Audit.Add(FString::Printf(TEXT("Figures at the end of the walk; the crew stands at %s."), *Compact(Pawn->GetActorLocation())));
		Audit.Add(TEXT("| Figure | Class | Deck | Where | Mesh | Attached to |"));
		Audit.Add(TEXT("|--------|-------|------|-------|------|-------------|"));
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (*It == Pawn || It->IsA<ACryoPodSystem>()) { continue; }
			for (const USkeletalMeshComponent* SK : TInlineComponentArray<USkeletalMeshComponent*>(*It))
			{
				if (!SK || !SK->GetSkeletalMeshAsset() || !SK->IsVisible()) { continue; }
				const AActor* Parent = It->GetAttachParentActor();
				Audit.Add(FString::Printf(TEXT("| %s | %s | %d | %s | %s | %s |"), *It->GetActorNameOrLabel(), *It->GetClass()->GetName(), DeckOf(It->GetActorLocation().Z),
					*Compact(SK->GetComponentLocation()), *SK->GetSkeletalMeshAsset()->GetName(), Parent ? *Parent->GetActorNameOrLabel() : TEXT("nothing")));
			}
		}
		for (const FString& A : Audit)
		{
			if (A.StartsWith(TEXT("| BP_")) || A.Contains(TEXT("| nothing |")))
			{
				// A figure attached to the crew but more than three metres from them.
				FString Where;
				const int32 Open = A.Find(TEXT("| ("));
				if (Open != INDEX_NONE)
				{
					float X = 0, Y = 0, Z = 0;
					if (swscanf_s(*A + Open + 3, TEXT("%f, %f, %f"), &X, &Y, &Z) == 3 && A.Contains(*Pawn->GetActorNameOrLabel()) && FVector::Dist(FVector(X, Y, Z), Pawn->GetActorLocation()) > 300.0f)
					{
						Findings.Add(FString::Printf(TEXT("Body left behind: %s"), *A));
					}
				}
			}
		}
		// The record.
		TArray<FString> Lines;
		Lines.Add(TEXT("# Corvette survey"));
		Lines.Add(TEXT(""));
		Lines.Add(FString::Printf(TEXT("Written by `Ginnungagap.Survey.CorvetteWalkthrough` on %s from `%s`. The character was driven on foot up the objective chain, back down it, and out to every side station; everything below was met on the way. Regenerate with the test, do not edit by hand."), *FDateTime::Now().ToString(TEXT("%Y-%m-%d %H:%M")), *MapPath()));
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("## The walk"));
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("| # | Leg | Deck | Where | Path (m) | Walk (s) | Snags | Outcome |"));
		Lines.Add(TEXT("|---|-----|------|-------|----------|----------|-------|---------|"));
		for (int32 i = 0; i < Records.Num(); ++i)
		{
			const FLegRecord& R = Records[i];
			Lines.Add(FString::Printf(TEXT("| %d | %s | %d | %s | %s | %.0f | %d | %s |"), i + 1, *R.Name, DeckOf(R.Where.Z), *Compact(R.Where),
				R.PathLength >= 0.0f ? *FString::Printf(TEXT("%.1f"), R.PathLength / 100.0f) : TEXT("no path"), R.Seconds, R.Snags, *R.Outcome));
		}
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("## Collision and movement findings"));
		Lines.Add(TEXT(""));
		if (Findings.IsEmpty()) { Lines.Add(TEXT("None: no snags, penetrations, floor gaps or low clearance on the walk.")); }
		for (const FString& F : Findings) { Lines.Add(FString::Printf(TEXT("- %s"), *F)); }
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("## Asset audit"));
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("What each interactable is made of. A station with a static mesh and no skeletal mesh is a prop that speaks only through its prompt: the activity plays as a timer or a button sequence with nothing moving on it."));
		Lines.Add(TEXT(""));
		for (const FString& A : Audit) { Lines.Add(A); }
		Lines.Add(TEXT(""));
		Lines.Add(TEXT("## Next work drawn from this survey"));
		Lines.Add(TEXT(""));
		int32 StaticStations = 0, NoMeshStations = 0, Untextured = 0;
		for (const FString& A : Audit)
		{
			if (A.Contains(TEXT("| static prop |"))) { ++StaticStations; }
			if (A.Contains(TEXT("| no mesh |"))) { ++NoMeshStations; }
			if (A.Contains(TEXT("default material"))) { ++Untextured; }
		}
		Lines.Add(FString::Printf(TEXT("- %d activity stations are static props with a text prompt: each wants a purpose-built asset with an animation for its activity (panel opening, lever, weld arc, console boot)."), StaticStations));
		if (NoMeshStations > 0) { Lines.Add(FString::Printf(TEXT("- %d activity stations have no mesh at all and are invisible until the prompt appears."), NoMeshStations)); }
		if (Untextured > 0) { Lines.Add(FString::Printf(TEXT("- %d placed meshes render with the engine default material (grey, reads as collision)."), Untextured)); }
		for (const FString& A : Audit)
		{
			if (A.StartsWith(TEXT("| ("))) { Lines.Add(FString::Printf(TEXT("- Floating props: %s: each wants a stand, a bracket or a move to the wall or deck."), *A.Replace(TEXT("|"), TEXT("")).TrimStartAndEnd())); }
		}
		for (const FString& F : Findings)
		{
			if (F.StartsWith(TEXT("Blocked"))) { Lines.Add(FString::Printf(TEXT("- %s"), *F)); }
		}
		Lines.Add(TEXT("- Every snag, penetration and floor gap above is a place to stand in the editor and look."));
		const FString Path = FPaths::Combine(FPaths::ProjectDir(), TEXT("docs"), TEXT("CorvetteSurvey.md"));
		const bool bWritten = FFileHelper::SaveStringArrayToFile(Lines, *Path);
		Test->TestTrue(FString::Printf(TEXT("Survey written to %s"), *Path), bWritten);
		Test->AddInfo(FString::Printf(TEXT("SURVEY %d legs, %d findings, %d audited actors, %.0f s"), Records.Num(), Findings.Num(), Audit.Num(), Now - StartedAt));
		bPrepared = false; StartedAt = -1.0; Index = 0; Phase = 0; Legs.Reset(); Records.Reset(); Findings.Reset(); Audit.Reset(); Seen.Reset();
	};

	if (!bPrepared)
	{
		StartedAt = Now;
		for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It) { It->Skip(); }
		Pawn->SetFirstPersonView(true);

		// The route: up the chain, back down it, then every side station in deck order.
		auto Add = [&](const TCHAR* Name, AActor* A, bool bPlay = false) { if (A) { Legs.Add({ Name, A, bPlay }); } };
		AActor* Suit = First<AQuickDemoSuitStation>(World);
		AActor* Bench = First<AQuickDemoWorkshopBench>(World);
		AActor* Power = First<AQuickDemoPowerStation>(World);
		AActor* Breach = First<AQuickDemoBreachStation>(World);
		AActor* Access = First<AQuickDemoCICAccessStation>(World);
		AActor* Console = First<AQuickDemoCICConsole>(World);
		Add(TEXT("suit rack"), Suit, true); Add(TEXT("workshop bench"), Bench, true); Add(TEXT("power station"), Power, true);
		Add(TEXT("breach patch"), Breach, true); Add(TEXT("CIC access panel"), Access, true); Add(TEXT("CIC console"), Console, true);
		Add(TEXT("back to the breach patch"), Breach); Add(TEXT("back to the power station"), Power);
		Add(TEXT("back to the workshop bench"), Bench); Add(TEXT("back to the suit rack"), Suit);
		TArray<AActor*> Sides;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("CorvetteSideStation")) || It->ActorHasTag(TEXT("CorvetteWeldedDoor"))) { Sides.Add(*It); }
		}
		Sides.Sort([](const AActor& A, const AActor& B) { return A.GetActorLocation().Z < B.GetActorLocation().Z; });
		for (AActor* S : Sides) { Legs.Add({ FString::Printf(TEXT("side: %s"), *S->GetActorNameOrLabel()), S }); }

		// The audit: every interactable and every placed mesh, by what it is made of.
		Audit.Add(TEXT("| Actor | Class | Deck | Where | Made of | Note |"));
		Audit.Add(TEXT("|-------|-------|------|-------|---------|------|"));
		auto Describe = [&](AActor* A, const FString& Note)
		{
			const UStaticMeshComponent* SM = A->FindComponentByClass<UStaticMeshComponent>();
			const USkeletalMeshComponent* SK = A->FindComponentByClass<USkeletalMeshComponent>();
			FString MadeOf;
			if (SK && SK->GetSkeletalMeshAsset()) { MadeOf = FString::Printf(TEXT("skeletal %s"), *SK->GetSkeletalMeshAsset()->GetName()); }
			else if (SM && SM->GetStaticMesh()) { MadeOf = FString::Printf(TEXT("static prop | %s"), *SM->GetStaticMesh()->GetName()); }
			else { MadeOf = TEXT("no mesh | -"); }
			Audit.Add(FString::Printf(TEXT("| %s | %s | %d | %s | %s | %s |"), *A->GetActorNameOrLabel(), *A->GetClass()->GetName(), DeckOf(A->GetActorLocation().Z),
				*Compact(A->GetActorLocation()), *MadeOf, *Note));
		};
		for (TActorIterator<AActivityStation> It(World); It; ++It) { Describe(*It, TEXT("activity station: prompt + timer/sequence, nothing animates")); }
		for (TActorIterator<AInventoryItemPickup> It(World); It; ++It) { Describe(*It, TEXT("pickup")); }
		for (TActorIterator<AObstructionBarrier> It(World); It; ++It) { Describe(*It, TEXT("obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier")); }
		int32 Doors = 0, Pods = 0, Signs = 0, Beacons = 0, DefaultMaterials = 0;
		for (TActorIterator<ABulkheadDoor> It(World); It; ++It) { ++Doors; }
		for (TActorIterator<ACryoPodSystem> It(World); It; ++It) { ++Pods; }
		for (TActorIterator<ATextRenderActor> It(World); It; ++It) { ++Signs; }
		for (TActorIterator<AQuickDemoObjectiveBeacon> It(World); It; ++It) { ++Beacons; }
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			const UStaticMeshComponent* SM = It->GetStaticMeshComponent();
			if (!SM || !SM->GetStaticMesh()) { continue; }
			for (int32 Slot = 0; Slot < SM->GetNumMaterials(); ++Slot)
			{
				const UMaterialInterface* M = SM->GetMaterial(Slot);
				if (!M || M->GetName().Contains(TEXT("DefaultMaterial")) || M->GetName().Contains(TEXT("WorldGridMaterial")))
				{
					++DefaultMaterials;
					if (DefaultMaterials <= 25) { Describe(*It, TEXT("default material on a slot")); }
					break;
				}
			}
		}
		Audit.Add(TEXT(""));
		Audit.Add(FString::Printf(TEXT("Also aboard: %d bulkhead doors (sliding leaves animate, sound on open/close), %d cryo pods (lid animates), %d text signs (TextRender on plates: no printed asset), %d objective beacons (TextRender), %d placed meshes with the engine default material."), Doors, Pods, Signs, Beacons, DefaultMaterials));

		Index = 0; Phase = 0; PhaseAt = Now;
		bPrepared = true;
		Test->AddInfo(FString::Printf(TEXT("SURVEY %d legs, %d interactables audited"), Legs.Num(), Audit.Num()));
		return false;
	}

	if (Now - StartedAt > Budget)
	{
		Findings.Add(FString::Printf(TEXT("The survey ran out of its %.0f s budget at leg %d of %d (%s)."), Budget, Index + 1, Legs.Num(), Index < Legs.Num() ? *Legs[Index].Name : TEXT("-")));
		Finish();
		return true;
	}
	if (Index >= Legs.Num())
	{
		Finish();
		return true;
	}

	const FLeg& Leg = Legs[Index];
	AActor* Target = Leg.Target.Get();
	if (!Target)
	{
		++Index; Phase = 0; PhaseAt = Now;
		return false;
	}

	switch (Phase)
	{
	case 0:
	{
		Current = FLegRecord();
		Current.Name = Leg.Name;
		Current.Where = Target->GetActorLocation();
		LegStartedAt = Now; LastProbeAt = Now; LastMoveCheckAt = Now; LastMoveCheckLocation = Pawn->GetActorLocation();
		if (!SpotBefore(World, Nav, Target, Goal))
		{
			Current.Outcome = TEXT("no navmesh at the target");
			Findings.Add(FString::Printf(TEXT("No navmesh around %s at %s (deck %d)."), *Leg.Name, *Compact(Current.Where), DeckOf(Current.Where.Z)));
			Records.Add(Current);
			++Index; return false;
		}
		FNavLocation From;
		if (Nav->ProjectPointToNavigation(Pawn->GetActorLocation(), From, FVector(150.0f, 150.0f, 300.0f)))
		{
			UNavigationPath* Path = Nav->FindPathToLocationSynchronously(World, From.Location, Goal, Pawn);
			if (Path && Path->IsValid() && !Path->IsPartial()) { Current.PathLength = Path->GetPathLength(); }
			else
			{
				// What is in the way: the nearest obstruction to the far end of whatever partial path exists.
				FString Blocker;
				if (Path && Path->IsValid() && Path->PathPoints.Num() > 0)
				{
					const FVector End = Path->PathPoints.Last();
					float Best = TNumericLimits<float>::Max();
					for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
					{
						const float D = FVector::Dist(It->GetActorLocation(), End);
						if (D < Best) { Best = D; Blocker = FString::Printf(TEXT("%s (%s, %.1f m from the path's end)"), *It->GetActorNameOrLabel(), *It->DisplayName.ToString(), D / 100.0f); }
					}
					for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
					{
						const float D = FVector::Dist(It->GetActorLocation(), End);
						if (D < Best && D < 400.0f) { Best = D; Blocker = FString::Printf(TEXT("door %s (%.1f m from the path's end)"), *It->GetActorNameOrLabel(), D / 100.0f); }
					}
				}
				Findings.Add(FString::Printf(TEXT("Blocked: no complete path from %s to %s; nearest obstacle %s. A player cuts, squeezes or overrides here."),
					*Compact(Pawn->GetActorLocation()), *Leg.Name, Blocker.IsEmpty() ? TEXT("unknown") : *Blocker));
				// As the player would: clear it and walk on.
				for (TActorIterator<AObstructionBarrier> It(World); It; ++It) { It->SetActorEnableCollision(false); It->SetActorHiddenInGame(true); }
				for (TActorIterator<ABulkheadDoor> It(World); It; ++It) { if (It->bLocked) { It->SetLocked(false); } }
				Nav->Build();
			}
		}
		UAIBlueprintHelperLibrary::SimpleMoveToLocation(PC, Goal);
		Phase = 1; PhaseAt = Now;
		return false;
	}
	case 1:
	{
		const FVector At = Pawn->GetActorLocation();
		const float Remaining = FVector::Dist2D(At, Goal);
		// Probes on the way: the capsule against the ship, the floor under it, the ceiling over it.
		if (Now - LastProbeAt > 0.4)
		{
			LastProbeAt = Now;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(Survey), false, Pawn);
			TArray<FOverlapResult> Overlaps;
			const UCapsuleComponent* Capsule = Pawn->GetCapsuleComponent();
			const float R = Capsule ? Capsule->GetScaledCapsuleRadius() : 40.0f;
			const float H = Capsule ? Capsule->GetScaledCapsuleHalfHeight() : 94.0f;
			World->OverlapMultiByChannel(Overlaps, At, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(R - 4.0f, H - 12.0f), Params);
			for (const FOverlapResult& O : Overlaps)
			{
				if (O.bBlockingHit && O.GetActor())
				{
					const FString Key = FString::Printf(TEXT("pen:%s"), *O.GetActor()->GetActorNameOrLabel());
					if (!Seen.Contains(Key))
					{
						Seen.Add(Key);
						Findings.Add(FString::Printf(TEXT("Penetration: the character's capsule overlaps %s at %s (deck %d) on the way to %s."), *O.GetActor()->GetActorNameOrLabel(), *Compact(At), DeckOf(At.Z), *Leg.Name));
						FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("SurveyPen_%02d_%d"), Index, Seen.Num()), false, false, false, FIntRect(), true);
						++Current.Snags;
					}
					break;
				}
			}
			FHitResult Floor;
			if (!World->LineTraceSingleByChannel(Floor, At, At - FVector(0.0f, 0.0f, H + 40.0f), ECC_Visibility, Params))
			{
				const FString Key = FString::Printf(TEXT("gap:%d:%d"), FMath::RoundToInt(At.X / 200.0f), FMath::RoundToInt(At.Y / 200.0f));
				if (!Seen.Contains(Key))
				{
					Seen.Add(Key);
					const UCharacterMovementComponent* Move = Pawn->GetCharacterMovement();
					Findings.Add(FString::Printf(TEXT("Floor gap: nothing within %.0f cm under the character at %s (deck %d) on the way to %s; movement %s, velocity %s."),
						H + 40.0f, *Compact(At), DeckOf(At.Z), *Leg.Name, Move ? *UEnum::GetValueAsString(Move->MovementMode) : TEXT("?"), *Compact(Pawn->GetVelocity())));
					FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("SurveyGap_%02d_%d"), Index, Seen.Num()), false, false, false, FIntRect(), true);
					++Current.Snags;
				}
			}
			FHitResult Over;
			// Pickups are walked through (overlap, not block); one over the head is not a low ceiling.
			FCollisionQueryParams OverParams = Params;
			for (TActorIterator<AInventoryItemPickup> Pick(World); Pick; ++Pick) { OverParams.AddIgnoredActor(*Pick); }
			if (World->LineTraceSingleByChannel(Over, At, At + FVector(0.0f, 0.0f, H + 110.0f), ECC_Visibility, OverParams) && Over.GetActor())
			{
				const float Clearance = Over.ImpactPoint.Z - (At.Z - H);
				if (Clearance < 200.0f)
				{
					const FString Key = FString::Printf(TEXT("low:%s"), *Over.GetActor()->GetActorNameOrLabel());
					if (!Seen.Contains(Key)) { Seen.Add(Key); Findings.Add(FString::Printf(TEXT("Low clearance: %.0f cm under %s at %s (deck %d)."), Clearance, *Over.GetActor()->GetActorNameOrLabel(), *Compact(At), DeckOf(At.Z))); }
				}
			}
		}
		// Stuck: hardly moving for three seconds with distance still to cover.
		if (Now - LastMoveCheckAt > 3.0)
		{
			if (FVector::Dist(At, LastMoveCheckLocation) < 25.0f && Remaining > 130.0f)
			{
				// A door that will not open is the ship's doing, not the character's: note which,
				// then do what the crew does (cut the weld, work the override) and walk on.
				bool bDoorOpened = false;
				for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
				{
					if (FVector::Dist2D(It->GetActorLocation(), At) > 320.0f) { continue; }
					AWeldableBulkheadDoor* Welded = Cast<AWeldableBulkheadDoor>(*It);
					if (Welded && Welded->bWeldedShut)
					{
						Findings.Add(FString::Printf(TEXT("Blocked: welded door %s at %s (deck %d) on the way to %s; cut through with the tool."), *It->GetActorNameOrLabel(), *Compact(It->GetActorLocation()), DeckOf(At.Z), *Leg.Name));
						Welded->CutEmergencyWeld(); Welded->Unseal(); bDoorOpened = true;
					}
					else if (It->bLocked)
					{
						Findings.Add(FString::Printf(TEXT("Blocked: locked door %s at %s (deck %d) on the way to %s (%s); the override panel releases it."), *It->GetActorNameOrLabel(), *Compact(It->GetActorLocation()), DeckOf(At.Z), *Leg.Name, *It->LockedReason.ToString()));
						It->SetLocked(false); It->Unseal(); bDoorOpened = true;
					}
					else if (It->bIsSealed)
					{
						// A sealed bulkhead: a player presses E; the walker does the same.
						It->Unseal(); bDoorOpened = true;
					}
				}
				if (bDoorOpened)
				{
					LastMoveCheckAt = Now; LastMoveCheckLocation = At;
					UAIBlueprintHelperLibrary::SimpleMoveToLocation(PC, Goal);
					return false;
				}
				const FString Near = NearestBlocker(World, At, Pawn);
				Findings.Add(FString::Printf(TEXT("Snag: stuck at %s (deck %d) on the way to %s, %.1f m short, against %s."), *Compact(At), DeckOf(At.Z), *Leg.Name, Remaining / 100.0f, Near.IsEmpty() ? TEXT("nothing solid (a navmesh or path-following stall)") : *Near));
				++Current.Snags;
				// On as the player would, over the snag.
				Pawn->SetBase(static_cast<UPrimitiveComponent*>(nullptr), NAME_None);
				Pawn->SetActorLocation(Goal + FVector(0.0f, 0.0f, 98.0f), false, nullptr, ETeleportType::TeleportPhysics);
				if (UCharacterMovementComponent* Move = Pawn->GetCharacterMovement()) { Move->StopMovementImmediately(); Move->SetMovementMode(MOVE_Walking); }
			}
			LastMoveCheckAt = Now; LastMoveCheckLocation = Pawn->GetActorLocation();
		}
		if (Remaining < 130.0f || Now - LegStartedAt > 75.0)
		{
			if (Remaining >= 130.0f)
			{
				Findings.Add(FString::Printf(TEXT("Timeout: %s not reached in 75 s; the character was at %s (deck %d), %.1f m short."), *Leg.Name, *Compact(At), DeckOf(At.Z), Remaining / 100.0f));
				Pawn->SetBase(static_cast<UPrimitiveComponent*>(nullptr), NAME_None);
				Pawn->SetActorLocation(Goal + FVector(0.0f, 0.0f, 98.0f), false, nullptr, ETeleportType::TeleportPhysics);
				Current.Outcome = TEXT("timed out, carried on");
			}
			else
			{
				Current.Outcome = Current.Snags > 0 ? TEXT("arrived with snags") : TEXT("arrived");
			}
			Current.Seconds = Now - LegStartedAt;
			// Face it, and the eye against the wall behind it.
			const FRotator Face = (Target->GetActorLocation() - Pawn->GetActorLocation()).Rotation();
			Pawn->SetActorRotation(FRotator(0.0f, Face.Yaw, 0.0f));
			PC->SetControlRotation(FRotator(FMath::Clamp(Face.Pitch, -35.0f, 10.0f), Face.Yaw, 0.0f));
			if (UCharacterMovementComponent* Move = Pawn->GetCharacterMovement()) { Move->StopMovementImmediately(); }
			Phase = 2; PhaseAt = Now;
		}
		return false;
	}
	case 2:
		if (Now - PhaseAt < 0.6) { return false; }
		{
			FVector Eye; FRotator EyeRot;
			Pawn->GetActorEyesViewPoint(Eye, EyeRot);
			FHitResult Wall;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(Survey), false, Pawn);
			if (World->LineTraceSingleByChannel(Wall, Eye, Eye + EyeRot.Vector() * 30.0f, ECC_Visibility, Params) && Wall.GetActor())
			{
				Findings.Add(FString::Printf(TEXT("Eye in geometry: standing before %s the eye is %.0f cm from %s."), *Leg.Name, Wall.Distance, *Wall.GetActor()->GetActorNameOrLabel()));
			}
			// The character's own body across the eye: any of its visible meshes within arm's reach of
			// the camera, on the line of sight, is what a player sees as a dark shape in the frame.
			for (const UPrimitiveComponent* Prim : TInlineComponentArray<UPrimitiveComponent*>(Pawn))
			{
				if (!Prim || !Prim->IsVisible() || Prim->bHiddenInGame || Prim->bOwnerNoSee || !Prim->IsRegistered()) { continue; }
				if (Prim->IsA<UCapsuleComponent>()) { continue; }
				const FBoxSphereBounds B = Prim->Bounds;
				const FVector Ahead = Eye + EyeRot.Vector() * 40.0f;
				if (B.SphereRadius > 1.0f && B.GetBox().IsInside(Ahead) && FVector::Dist(B.Origin, Eye) < 120.0f)
				{
					const FString Key = FString::Printf(TEXT("body:%s"), *Prim->GetName());
					if (!Seen.Contains(Key))
					{
						Seen.Add(Key);
						Findings.Add(FString::Printf(TEXT("Own body in view: %s (%s) sits across the first-person eye line before %s."), *Prim->GetName(), *Prim->GetClass()->GetName(), *Leg.Name));
					}
				}
			}
			if (const UCharacterMovementComponent* Move = Pawn->GetCharacterMovement())
			{
				if (Move->MovementMode != MOVE_Walking)
				{
					Findings.Add(FString::Printf(TEXT("Not walking: at %s the character is in %s (magnetic boots %s)."), *Leg.Name, *UEnum::GetValueAsString(Move->MovementMode), Pawn->AreMagneticBootsEnabled() ? TEXT("on") : TEXT("off")));
				}
			}
			FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Survey_%02d_%s"), Index, *Leg.Name.Replace(TEXT(" "), TEXT("_")).Replace(TEXT(":"), TEXT(""))), false, false, false, FIntRect(), true);
		}
		// Play the chain as a player would, so the ship changes under the walk: the suit rack seals
		// the suit before the vacuum deck, the breach patch clears the hazard, the CIC panel
		// releases the door. Fired as the station's own completion, which is what the activity
		// ends in; the keyboard path into each one is the station test's business.
		if (Leg.bPlay)
		{
			if (Target->GetClass()->ImplementsInterface(UPlayerActivitySource::StaticClass()))
			{
				IPlayerActivitySource::Execute_OnActivityCompleted(Target, Pawn);
				Current.Outcome += TEXT(", played");
			}
		}
		Records.Add(Current);
		Phase = 3; PhaseAt = Now;
		return false;
	case 3:
		if (Now - PhaseAt < 0.4) { return false; }
		++Index; Phase = 0; PhaseAt = Now;
		return false;
	default:
		return false;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCorvetteSurveyTest,
	"Ginnungagap.Survey.CorvetteWalkthrough",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapCorvetteSurveyTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	AutomationOpenMap(Survey::MapPath());
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.5f));
	ADD_LATENT_AUTOMATION_COMMAND(FSurveyWalk(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
