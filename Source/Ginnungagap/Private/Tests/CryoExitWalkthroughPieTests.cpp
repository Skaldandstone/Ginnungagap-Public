#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Blueprint/UserWidget.h"
#include "Editor.h"
#include "Editor/UnrealEdEngine.h"
#include "UnrealEdGlobals.h"
#include "Misc/CommandLine.h"
#include "Settings/LevelEditorPlaySettings.h"
#include "CollisionQueryParams.h"
#include "CoopSurvivalCharacter.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "HazardZoneActor.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Meta/MenuManagerSubsystem.h"
#include "Misc/App.h"
#include "UnrealClient.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/ModularShipRoom.h"
#include "Threats/ShipboardThreat.h"
#include "UObject/UnrealType.h"

/**
 * The real player character walks the whole demo, under path following, through its own sequence.
 *
 * Every other check on this path proves a mechanism (ResolveWith flips a flag, a station grants)
 * or a navmesh path (a query returns complete). None of them moves anything. This drives the
 * actual player pawn -- its own capsule, its own movement component -- with SimpleMoveToLocation,
 * leg by leg, and calls each station's real completion trigger only once the pawn is standing at
 * it: suit, boots, cut out of cryo; the workshop bench; down the hatch ramp to deck 2; through the
 * generator's own corridor obstruction to the power station; back up the ramp; the breach; the
 * CIC door override; the console. Arrival is three-dimensional and each leg is asserted at a
 * walking pace. A leg that never arrives reports where the pawn stopped, the path state from
 * there, and a probe along the line, so the cause reads as a place.
 *
 * Two behaviours stand in for the player. A partial path gated by an obstruction is walked to and
 * cleared, because Recast ends a partial path at the reachable point nearest the goal -- a deck up,
 * on this route -- and path following would otherwise drag the pawn back up the ramp. And a pawn
 * stuck beside an uncleared obstruction clears it.
 */

namespace CryoWalk
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

	const FVector Extent(400.0f, 400.0f, 300.0f);
	constexpr float ArriveWithinCm = 150.0f;
	constexpr float ArriveHeightCm = 200.0f;   // capsule centre rides about a metre above the mesh
	constexpr double LegSeconds = 60.0;
	constexpr double TotalSeconds = 240.0;
	constexpr double ReissueSeconds = 3.0;
	// Without magnetic boots the character drifts at about 20 cm/s; a walk is an order of
	// magnitude more. Guards the pace so a silent return to drifting reads as a failure.
	constexpr float WalkingPaceCmPerSec = 100.0f;

	enum class EPhase : uint8 { Settle, Prepare, WaitClear, Walking, WaitTitleCut };

	struct FLeg
	{
		FString Name;
		FVector Goal;
		FVector LookAt;   // what the player's view turns to before the capture at this leg's end
		TFunction<void(APawn*)> OnArrive;
	};

	float ReadFloat(const UObject* Object, const TCHAR* Name)
	{
		const FFloatProperty* Property = FindFProperty<FFloatProperty>(Object->GetClass(), Name);
		return Property ? Property->GetPropertyValue_InContainer(Object) : -1.0f;
	}
	FString ReadBool(const UObject* Object, const TCHAR* Name)
	{
		const FBoolProperty* Property = FindFProperty<FBoolProperty>(Object->GetClass(), Name);
		return Property ? (Property->GetPropertyValue_InContainer(Object) ? TEXT("yes") : TEXT("no")) : TEXT("n/a");
	}
	// Reads a protected UPROPERTY object pointer without a new accessor -- reflection does not
	// enforce C++ access control, only whether the property was ever marked UPROPERTY().
	UObject* ReadObject(const UObject* Object, const TCHAR* Name)
	{
		const FObjectProperty* Property = FindFProperty<FObjectProperty>(Object->GetClass(), Name);
		return Property ? Property->GetObjectPropertyValue_InContainer(Object) : nullptr;
	}
	// The same trace SetMagneticBootsEnabled runs before it agrees to engage.
	FString TraceUnderfoot(UWorld* World, const APawn* Pawn)
	{
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CryoWalkMetalTrace), false, Pawn);
		const FVector Start = Pawn->GetActorLocation();
		if (World->LineTraceSingleByChannel(Hit, Start, Start - Pawn->GetActorUpVector() * 180.0f, ECC_Visibility, Params))
		{
			return FString::Printf(TEXT("hit %s / %s, object type %d, at %.0f cm"),
				Hit.GetActor() ? *Hit.GetActor()->GetName() : TEXT("?"),
				Hit.GetComponent() ? *Hit.GetComponent()->GetName() : TEXT("?"),
				Hit.GetComponent() ? static_cast<int32>(Hit.GetComponent()->GetCollisionObjectType()) : -1,
				Hit.Distance);
		}
		return TEXT("no hit within 180 cm");
	}

	// Recording mode: -GinnungagapRecordWalk on the editor command line. The walk becomes the demo
	// video's source -- every frame of the player's view is written out, PIE runs in its own
	// 1920x1080 window rather than the editor viewport so the frames are the game and nothing
	// else, and the walk keeps time by the world clock rather than the wall clock, because a
	// screenshot every frame drags real time far behind a fixed 30 Hz game step. Pair it with
	// -UseFixedTimeStep -FPS=30, then tools/assemble_demo_video.py turns the frames into an MP4.
	bool IsRecording()
	{
		static const bool bRecording = FParse::Param(FCommandLine::Get(), TEXT("GinnungagapRecordWalk"));
		return bRecording;
	}
	void RecordFrame()
	{
		// Unbuilt-reflection and light-overflow notices are debug text, not the game; keep them out
		// of every frame. (A leading exec on -ExecCmds swallows the automation command, so it is
		// done here rather than on the command line.)
		GAreScreenMessagesEnabled = false;
		static int32 FrameIndex = 0;
		if (!IsRecording() || !FApp::CanEverRender() || !GEngine || !GEngine->GameViewport)
		{
			return;
		}
		FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Frame_%06d"), FrameIndex++), true, false, false, FIntRect(), true);
	}

	// The player's own view, through the game viewport, when the editor can render. Under
	// -NullRHI this is a no-op; under a windowed editor it writes Saved/Screenshots/<Platform>/.
	// These are gameplay evidence in the sense the project's acceptance criteria mean: BeginPlay
	// has run, the pawn is where it walked to, and the camera is the pawn's.
	//
	// bInShowUI stays false. It was tried true, on the theory that Walk_10_title_screen needs UI
	// on to show the UStartScreenWidget the director cuts to. It made every frame worse instead:
	// with PIE running inside the editor's own viewport rather than a separate window, "true"
	// captures the whole editor -- panels, toolbar, the "reflection captures need rebuilt" toast
	// -- baked into what were clean player-view stills, and Walk_10 still did not show the
	// widget itself either way. Whatever is keeping the widget from painting is a separate
	// question from this flag, and false is the setting that does not cost the other ten frames
	// to ask it.
	void Capture(const FString& Name, bool bIncludeUI = false)
	{
		if (!FApp::CanEverRender() || !GEngine || !GEngine->GameViewport)
		{
			return;
		}
		// bInRestrictToGameViewport=true: Slate renders only the SViewport subtree (scene + UMG
		// overlay), not the whole editor window PIE lives inside.
		FScreenshotRequest::RequestScreenshot(Name, bIncludeUI, false, false, FIntRect(), bIncludeUI);
	}
	FString Slug(const FString& In)
	{
		FString Out;
		for (const TCHAR C : In)
		{
			Out.AppendChar(FChar::IsAlnum(C) ? C : TEXT('_'));
		}
		return Out.Left(40);
	}

	template <typename T>
	T* First(UWorld* World)
	{
		for (TActorIterator<T> It(World); It; ++It)
		{
			return *It;
		}
		return nullptr;
	}

	int32 CountUnpowered(UWorld* World, int32& OutTagged)
	{
		OutTagged = 0;
		int32 Unpowered = 0;
		for (TActorIterator<AModularShipRoom> It(World); It; ++It)
		{
			if (!It->ActorHasTag(TEXT("QuickDemoShipRoom"))) { continue; }
			++OutTagged;
			if (It->OperationalState == EShipRoomOperationalState::Unpowered) { ++Unpowered; }
		}
		return Unpowered;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FWalkCryoExit, FAutomationTestBase*, Test, double, StartSeconds);

bool FWalkCryoExit::Update()
{
	static CryoWalk::EPhase Phase = CryoWalk::EPhase::Settle;
	static TArray<CryoWalk::FLeg> Legs;
	static int32 LegIndex = 0;
	static double PhaseSince = 0.0;
	static double LastIssued = 0.0;
	static double LastPathCheck = 0.0;
	static double LastMoveLog = 0.0;
	static double StuckSince = 0.0;
	static int32 NudgeCount = 0;
	static FVector LegStart = FVector::ZeroVector;
	static bool bDetouring = false;
	static TWeakObjectPtr<AObstructionBarrier> DetourGate;
	// A sealed bulkhead's gate is its override station; the door itself is what is in the way.
	static TWeakObjectPtr<AMaintenanceActivityStation> DetourStation;
	static TWeakObjectPtr<ABulkheadDoor> DetourDoor;
	static bool bPendingCapture = false;
	static double CaptureAt = 0.0;

	auto Finish = [&](bool bResult) -> bool
	{
		Phase = CryoWalk::EPhase::Settle;
		Legs.Reset();
		LegIndex = 0;
		bDetouring = false;
		DetourGate = nullptr;
		DetourStation = nullptr;
		DetourDoor = nullptr;
		LastPathCheck = 0.0;
		StuckSince = 0.0;
		bPendingCapture = false;
		return bResult;
	};

	UWorld* World = CryoWalk::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world"));
		return Finish(true);
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!Navigation)
	{
		Test->AddError(TEXT("No navigation system"));
		return Finish(true);
	}

	CryoWalk::RecordFrame();
	// World time when recording (see IsRecording), wall time otherwise. StartSeconds is 0 for a
	// recording, set by RunTest, since the PIE world's clock starts there.
	const double Now = CryoWalk::IsRecording() ? static_cast<double>(World->GetTimeSeconds()) : FPlatformTime::Seconds();
	const bool bExpired = Now >= StartSeconds + CryoWalk::TotalSeconds;
	APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
	APawn* Pawn = PC ? PC->GetPawn() : nullptr;

	auto Issue = [&](const FVector& To)
	{
		UAIBlueprintHelperLibrary::SimpleMoveToLocation(PC, To);
		LastIssued = Now;
	};
	auto BeginLeg = [&](int32 Index)
	{
		UE_LOG(LogTemp, Display, TEXT("WALKLIVE begin leg %d [%s] at t+%.0fs"), Index, *Legs[Index].Name, Now - StartSeconds);
		LegIndex = Index;
		LegStart = Pawn ? Pawn->GetActorLocation() : FVector::ZeroVector;
		PhaseSince = Now;
		LastPathCheck = 0.0;   // gate check on the leg's first tick, from where the leg begins
		StuckSince = 0.0;
		NudgeCount = 0;
		Issue(Legs[Index].Goal);
	};

	switch (Phase)
	{
	case CryoWalk::EPhase::Settle:
	{
		// The opening plays first: third person on the sleeper, the strike, the blackout, the wake,
		// then first person. Each phase change is captured, so the demo's first eight seconds are
		// evidence too, and the walk does not begin until the player has their controls.
		static EQuickDemoOpeningPhase LastOpeningPhase = EQuickDemoOpeningPhase::Idle;
		if (AQuickDemoOpeningSequence* Opening = CryoWalk::First<AQuickDemoOpeningSequence>(World))
		{
			const EQuickDemoOpeningPhase OpeningPhase = Opening->GetPhase();
			if (OpeningPhase != LastOpeningPhase)
			{
				LastOpeningPhase = OpeningPhase;
				Test->AddInfo(FString::Printf(TEXT("OPENING phase %d at t+%.1fs"), static_cast<int32>(OpeningPhase), Now - StartSeconds));
				switch (OpeningPhase)
				{
				case EQuickDemoOpeningPhase::Asleep:   CryoWalk::Capture(TEXT("Open_01_asleep")); break;
				case EQuickDemoOpeningPhase::Blackout: CryoWalk::Capture(TEXT("Open_02_blackout")); break;
				case EQuickDemoOpeningPhase::ClimbOut: CryoWalk::Capture(TEXT("Open_03_climb_out")); break;
				default: break;
				}
			}
			if (!Opening->IsComplete() && !bExpired)
			{
				return false;
			}
		}
		if ((UNavigationSystemV1::IsNavigationBeingBuilt(World) || Now - StartSeconds < 8.0) && !bExpired)
		{
			static double LastSettleLog = 0.0;
			if (Now - LastSettleLog > 5.0)
			{
				LastSettleLog = Now;
				UE_LOG(LogTemp, Display, TEXT("WALKLIVE settling: nav building %s, t+%.0fs"),
					UNavigationSystemV1::IsNavigationBeingBuilt(World) ? TEXT("yes") : TEXT("no"), Now - StartSeconds);
			}
			return false;
		}
		UE_LOG(LogTemp, Display, TEXT("WALKLIVE settled at t+%.0fs; preparing"), Now - StartSeconds);
		Phase = CryoWalk::EPhase::Prepare;
		return false;
	}

	case CryoWalk::EPhase::Prepare:
	{
		if (!Test->TestNotNull(TEXT("There is a possessed player pawn"), Pawn))
		{
			return Finish(true);
		}

		ABulkheadDoor* Door = nullptr;
		for (TActorIterator<ABulkheadDoor> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("QD-03-01"))) { Door = *It; break; }
		}
		AModularShipRoom* Room = nullptr;
		for (TActorIterator<AModularShipRoom> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("QD-03-01"))) { Room = *It; break; }
		}
		AObstructionBarrier* Barrier = nullptr;
		for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
		{
			if (It->ActorHasTag(TEXT("CRYO-EXIT"))) { Barrier = *It; break; }
		}
		AActor* Bench = CryoWalk::First<AQuickDemoWorkshopBench>(World);
		AActor* SuitRepair = CryoWalk::First<AQuickDemoSuitRepairBench>(World);
		AActor* Power = CryoWalk::First<AQuickDemoPowerStation>(World);
		AActor* Breach = CryoWalk::First<AQuickDemoBreachStation>(World);
		AActor* CICAccess = CryoWalk::First<AQuickDemoCICAccessStation>(World);
		AActor* CICConsole = CryoWalk::First<AQuickDemoCICConsole>(World);
		if (!Test->TestNotNull(TEXT("Cryo door"), Door) || !Test->TestNotNull(TEXT("Cryo room"), Room)
			|| !Test->TestNotNull(TEXT("Cryo-exit obstruction"), Barrier) || !Test->TestNotNull(TEXT("Workshop bench"), Bench)
			|| !Test->TestNotNull(TEXT("Suit repair bench"), SuitRepair)
			|| !Test->TestNotNull(TEXT("Power station"), Power) || !Test->TestNotNull(TEXT("Breach station"), Breach)
			|| !Test->TestNotNull(TEXT("CIC access station"), CICAccess) || !Test->TestNotNull(TEXT("CIC console"), CICConsole))
		{
			return Finish(true);
		}

		// Goals, in the order the demo's objectives describe them. Room centres are never used:
		// a hatch room's centre is over its opening, with no floor to project onto.
		const float ThroughY = Door->GetActorLocation().Y < Room->GetActorLocation().Y ? -1.0f : 1.0f;
		struct FWanted { const TCHAR* Name; FVector Point; };
		const TArray<FWanted> Wanted = {
			{TEXT("doorway (corridor past the cryo door)"), Door->GetActorLocation() + FVector(0.0f, ThroughY * 300.0f, 0.0f)},
			{TEXT("workshop bench"), Bench->GetActorLocation()},
			{TEXT("suit repair bench (workshop)"), SuitRepair->GetActorLocation()},
			{TEXT("deck-2 corridor (down the hatch ramp)"), FVector(-1800.0f, 0.0f, 638.0f)},
			{TEXT("power station (through the damaged corridor)"), Power->GetActorLocation()},
			{TEXT("deck-3 corridor (up the hatch ramp)"), FVector(-1800.0f, 0.0f, 1158.0f)},
			{TEXT("breach station"), Breach->GetActorLocation()},
			{TEXT("CIC door override"), CICAccess->GetActorLocation()},
			{TEXT("CIC console"), CICConsole->GetActorLocation()},
		};
		TArray<FVector> Projected;
		FString Missing;
		for (const FWanted& W : Wanted)
		{
			FNavLocation On;
			if (Navigation->ProjectPointToNavigation(W.Point, On, CryoWalk::Extent))
			{
				Projected.Add(On.Location);
			}
			else
			{
				Missing += FString::Printf(TEXT(" [%s]"), W.Name);
			}
		}
		if (!Missing.IsEmpty())
		{
			if (!bExpired) { return false; }
			Test->AddError(FString::Printf(TEXT("Goals never projected onto the navmesh before the deadline:%s"), *Missing));
			return Finish(true);
		}

		Legs.Reset();
		// The override sits beside the CIC door; the frame worth having there looks through it.
		const TArray<FVector> LookAts = {
			Projected[0], Bench->GetActorLocation(), SuitRepair->GetActorLocation(), Projected[3], Power->GetActorLocation(),
			Projected[5], Breach->GetActorLocation(), CICConsole->GetActorLocation(), CICConsole->GetActorLocation(),
		};
		auto Add = [&](int32 Index, TFunction<void(APawn*)> OnArrive)
		{
			Legs.Add({Wanted[Index].Name, Projected[Index], LookAts[Index], MoveTemp(OnArrive)});
		};
		Add(0, nullptr);
		Add(1, [this, World](APawn* P)
		{
			// The workshop's real trigger, now that the pawn is standing at it: grants the tool,
			// advances the chain so the power station is written for.
			if (AQuickDemoWorkshopBench* B = CryoWalk::First<AQuickDemoWorkshopBench>(World)) { B->OnActivityCompleted_Implementation(P); }
			Test->TestTrue(TEXT("RestorePower is the active objective after the bench"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_RestorePower")));
		});
		Add(2, [this, World](APawn* P)
		{
			// The breach room is a vacuum, and suit integrity drains as (1 - integrity) per second,
			// compounding: from the default 0.8 a suit fails in about 1.6 s, at 1.0 it never
			// drains. The workshop's suit repair bench is the demo's own answer; whether it
			// actually raises integrity is measured here rather than assumed.
			const float Before = CryoWalk::ReadFloat(P, TEXT("SuitIntegrity"));
			if (AQuickDemoSuitRepairBench* S = CryoWalk::First<AQuickDemoSuitRepairBench>(World)) { S->OnActivityCompleted_Implementation(P); }
			const float After = CryoWalk::ReadFloat(P, TEXT("SuitIntegrity"));
			Test->AddInfo(FString::Printf(TEXT("WALK suit repair bench: suit integrity %.2f -> %.2f"), Before, After));
			// It measured 0.80 -> 0.80 once. Now it is the bench's job.
			Test->TestTrue(FString::Printf(TEXT("The suit repair bench raises suit integrity (%.2f -> %.2f)"), Before, After), After > Before + 0.05f);
		});
		Add(3, nullptr);
		Add(4, [this, World](APawn* P)
		{
			if (AQuickDemoPowerStation* S = CryoWalk::First<AQuickDemoPowerStation>(World)) { S->OnActivityCompleted_Implementation(P); }
			int32 Tagged = 0;
			const int32 Unpowered = CryoWalk::CountUnpowered(World, Tagged);
			Test->TestTrue(TEXT("There are tagged rooms to power"), Tagged > 0);
			Test->TestEqual(TEXT("After the power station, no tagged room is still Unpowered"), Unpowered, 0);
			// Alert and the fault states outrank emergency power by design (the cryo bay starts in
			// Alert), so the claim is that nothing came up Nominal -- the cold blue the beat sheet
			// never asked for -- and that the rest are on the emergency bus.
			int32 Emergency = 0, Nominal = 0;
			for (TActorIterator<AModularShipRoom> It(World); It; ++It)
			{
				if (!It->ActorHasTag(TEXT("QuickDemoShipRoom"))) { continue; }
				if (It->OperationalState == EShipRoomOperationalState::EmergencyPower) { ++Emergency; }
				if (It->OperationalState == EShipRoomOperationalState::Nominal) { ++Nominal; }
			}
			Test->TestEqual(TEXT("After the power station, no tagged room is Nominal (cold blue)"), Nominal, 0);
			Test->TestTrue(FString::Printf(TEXT("After the power station, the rooms are on emergency power (%d of %d)"), Emergency, Tagged), Emergency >= Tagged - 2);
			Test->TestTrue(TEXT("SealBreach is the active objective after power is restored"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_SealBreach")));
		});
		Add(5, nullptr);
		Add(6, [this, World](APawn* P)
		{
			if (AQuickDemoBreachStation* S = CryoWalk::First<AQuickDemoBreachStation>(World)) { S->OnActivityCompleted_Implementation(P); }
			Test->TestTrue(TEXT("ReachCIC is the active objective after the breach is sealed"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_ReachCIC")));
		});
		Add(7, [this, World](APawn* P)
		{
			if (AQuickDemoCICAccessStation* S = CryoWalk::First<AQuickDemoCICAccessStation>(World)) { S->OnActivityCompleted_Implementation(P); }
		});
		Add(8, [this, World](APawn* P)
		{
			if (AQuickDemoCICConsole* S = CryoWalk::First<AQuickDemoCICConsole>(World)) { S->OnActivityCompleted_Implementation(P); }
			Test->TestFalse(TEXT("ReachCIC is no longer active after the console: the demo's chain is complete"),
				AQuickDemoMissionDirector::IsObjectiveActive(World, TEXT("QD_ReachCIC")));
		});

		Test->AddInfo(FString::Printf(TEXT("WALK pawn %s starts at %s; %d legs"),
			*Pawn->GetClass()->GetName(), *Pawn->GetActorLocation().ToCompactString(), Legs.Num()));

		// This proves traversal, not combat. A threat drawn by the noise of cutting the corridor
		// obstruction killed the pawn at the power station on a loop -- respawning on the very
		// checkpoint it died on -- which is the threat system doing its job and a respawn problem
		// the character now guards against. Combat has its own tests; here the threats are removed
		// up front and the removal is on record.
		int32 Removed = 0;
		FString RemovedWhere;
		for (TActorIterator<AShipboardThreat> It(World); It; ++It)
		{
			RemovedWhere += FString::Printf(TEXT("%s@%s "), *It->GetName(), *It->GetActorLocation().ToCompactString());
			It->Destroy();
			++Removed;
		}
		Test->AddInfo(FString::Printf(TEXT("WALK threats removed for the traversal proof: %d %s"), Removed, *RemovedWhere));

		// The demo's actual first beats, through their real triggers: the suit, then the boots,
		// then the door. Boots refused until the suit was on and a pickup was moved from under
		// the metal trace; without them the character drifts at about 20 cm/s.
		for (TActorIterator<AQuickDemoSuitStation> It(World); It; ++It)
		{
			It->OnActivityCompleted_Implementation(Pawn);
			Test->AddInfo(TEXT("WALK suit station completed through its real trigger"));
			break;
		}
		if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Pawn))
		{
			Crew->SetMagneticBootsEnabled(true);
			Test->AddInfo(FString::Printf(
				TEXT("WALK magnetic boots enabled: %s (suit integrity %.2f, dead %s, oversuit %s, underfoot: %s)"),
				Crew->AreMagneticBootsEnabled() ? TEXT("yes") : TEXT("no"),
				CryoWalk::ReadFloat(Crew, TEXT("SuitIntegrity")), *CryoWalk::ReadBool(Crew, TEXT("bIsDead")),
				*CryoWalk::ReadBool(Crew, TEXT("bPressureOversuitEquipped")), *CryoWalk::TraceUnderfoot(World, Pawn)));
		}
		const EObstructionVerb Verb = Barrier->CanResolveWith(EObstructionVerb::Cut, Pawn)
			? EObstructionVerb::Cut : EObstructionVerb::Squeeze;
		if (!Test->TestTrue(TEXT("The cryo-exit obstruction is cleared before walking"), Barrier->ResolveWith(Verb, Pawn)))
		{
			return Finish(true);
		}
		Phase = CryoWalk::EPhase::WaitClear;
		PhaseSince = Now;
		return false;
	}

	case CryoWalk::EPhase::WaitClear:
		// Let the dirtied tile rebuild before asking for a path through it.
		if (Now - PhaseSince < 1.5 || UNavigationSystemV1::IsNavigationBeingBuilt(World))
		{
			if (!bExpired) { return false; }
			Test->AddError(TEXT("Navmesh never settled after clearing the obstruction"));
			return Finish(true);
		}
		CryoWalk::Capture(TEXT("Walk_00_cryo_wake"));
		Phase = CryoWalk::EPhase::Walking;
		BeginLeg(0);
		return false;

	case CryoWalk::EPhase::Walking:
	{
		if (!Pawn)
		{
			Test->AddError(TEXT("Player pawn vanished mid-walk"));
			return Finish(true);
		}
		const CryoWalk::FLeg& Leg = Legs[LegIndex];

		// Arrived and stopped, facing the station: let motion blur and temporal AA settle for a
		// beat, then take the frame, then move on. Frames taken mid-stride were blurred.
		if (bPendingCapture)
		{
			if (Now < CaptureAt)
			{
				return false;
			}
			bPendingCapture = false;
			CryoWalk::Capture(FString::Printf(TEXT("Walk_%02d_%s"), LegIndex + 1, *CryoWalk::Slug(Leg.Name)));
			if (LegIndex + 1 < Legs.Num())
			{
				BeginLeg(LegIndex + 1);
				return false;
			}
			Test->AddInfo(TEXT("WALK the demo's whole chain was walked and completed by the player pawn"));
			Phase = CryoWalk::EPhase::WaitTitleCut;
			PhaseSince = Now;
			return false;
		}
		const FString& LegName = Leg.Name;
		const FVector& LegGoal = Leg.Goal;
		const FVector Here = Pawn->GetActorLocation();
		const float Remaining = FVector::Dist2D(Here, LegGoal);
		const float HeightOff = FMath::Abs(Here.Z - LegGoal.Z);

		// Death is logged the moment it is seen, not on the five-second cadence: a respawn puts the
		// pawn back at the last checkpoint with its magnetic systems released, which looks exactly
		// like "stuck at the station, drifting" unless the death itself is on record.
		static bool bWasDead = false;
		const bool bDeadNow = CryoWalk::ReadBool(Pawn, TEXT("bIsDead")) == TEXT("yes");
		if (bDeadNow != bWasDead)
		{
			bWasDead = bDeadNow;
			TArray<AActor*> DeathHazards;
			Pawn->GetOverlappingActors(DeathHazards, AHazardZoneActor::StaticClass());
			const FString Where = FString::Printf(TEXT("on [%s] at %s (oxygen %.0f, health %.0f, radiation %.3f Sv, suit %.2f, hazards %d)"),
				*LegName, *Here.ToCompactString(),
				CryoWalk::ReadFloat(Pawn, TEXT("OxygenLevelPercent")), CryoWalk::ReadFloat(Pawn, TEXT("HealthPercent")),
				CryoWalk::ReadFloat(Pawn, TEXT("RadiationDoseSv")), CryoWalk::ReadFloat(Pawn, TEXT("SuitIntegrity")), DeathHazards.Num());
			if (bDeadNow)
			{
				// A death is the finding; walking on from a respawn only obscures it.
				Test->AddError(FString::Printf(TEXT("The player pawn died %s"), *Where));
				bWasDead = false;
				return Finish(true);
			}
			Test->AddInfo(FString::Printf(TEXT("WALK the pawn came back (respawn) %s"), *Where));
		}

		// Boots stay on for the walk. Anything that releases the magnetic systems -- a failed suit,
		// a respawn -- leaves the character drifting, and a player would re-engage at once.
		if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Pawn))
		{
			if (!Crew->AreMagneticBootsEnabled())
			{
				Crew->SetMagneticBootsEnabled(true);
			}
		}

		if (Now - LastMoveLog >= 5.0)
		{
			LastMoveLog = Now;
			const ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Pawn);
			const UCharacterMovementComponent* Move = Crew ? Crew->GetCharacterMovement() : nullptr;
			const AActor* Blocker = Crew ? Crew->GetWeaponTraversalBlocker() : nullptr;
			TArray<AActor*> Hazards;
			Pawn->GetOverlappingActors(Hazards, AHazardZoneActor::StaticClass());
			FString HazardNames;
			for (const AActor* Hazard : Hazards) { HazardNames += Hazard->GetName() + TEXT(" "); }
			// Anything else alive nearby: a threat engaging the pawn reads as unexplained damage.
			FString Nearby;
			for (TActorIterator<APawn> It(World); It; ++It)
			{
				if (*It == Pawn) { continue; }
				const float D = FVector::Dist(It->GetActorLocation(), Here);
				if (D <= 1200.0f)
				{
					Nearby += FString::Printf(TEXT("%s(%s @%.0f) "), *It->GetName(), *It->GetClass()->GetName(), D);
				}
			}
			HazardNames += Nearby.IsEmpty() ? TEXT("| no pawns within 12 m") : *FString::Printf(TEXT("| pawns: %s"), *Nearby);
			// Straight to the log as well as the test record: AddInfo is held until the test ends,
			// and a walk that never ends says nothing. This is the heartbeat that tells a watcher
			// the pawn is still moving.
			UE_LOG(LogTemp, Display, TEXT("WALKLIVE [%s] t+%.0fs at %s remaining %.0f speed %.0f"),
				*LegName, Now - PhaseSince, *Here.ToCompactString(), Remaining, Pawn->GetVelocity().Size());
			Test->AddInfo(FString::Printf(
				TEXT("WALK move [%s] t+%.0fs at %s: remaining %.0f, speed %.0f cm/s, mode %s, gravity %.2f, boots %s, blocked by %s; oxygen %.0f, health %.0f, radiation %.3f Sv, suit %.2f, dead %s, hazards: %s"),
				*LegName, Now - PhaseSince, *Here.ToCompactString(), Remaining, Pawn->GetVelocity().Size(),
				Move ? *UEnum::GetValueAsString(Move->MovementMode) : TEXT("?"), Move ? Move->GravityScale : -1.0f,
				Crew ? (Crew->AreMagneticBootsEnabled() ? TEXT("on") : TEXT("off")) : TEXT("?"),
				Blocker ? *Blocker->GetName() : TEXT("none"),
				CryoWalk::ReadFloat(Pawn, TEXT("OxygenLevelPercent")), CryoWalk::ReadFloat(Pawn, TEXT("HealthPercent")),
				CryoWalk::ReadFloat(Pawn, TEXT("RadiationDoseSv")), CryoWalk::ReadFloat(Pawn, TEXT("SuitIntegrity")),
				bDeadNow ? TEXT("YES") : TEXT("no"), HazardNames.IsEmpty() ? TEXT("none") : *HazardNames));
		}

		if (Remaining <= CryoWalk::ArriveWithinCm && HeightOff <= CryoWalk::ArriveHeightCm)
		{
			const double Seconds = FMath::Max(0.1, Now - PhaseSince);
			const float Pace = FVector::Dist2D(LegStart, Here) / static_cast<float>(Seconds);
			Test->AddInfo(FString::Printf(TEXT("WALK reached [%s] in %.1fs at %.0f cm/s average, pawn at %s"),
				*LegName, Seconds, Pace, *Here.ToCompactString()));
			Test->TestTrue(FString::Printf(TEXT("The player pawn completed the leg: %s"), *LegName), true);
			Test->TestTrue(FString::Printf(TEXT("Leg '%s' covered at a walking pace, not a drift (%.0f >= %.0f cm/s)"),
				*LegName, Pace, CryoWalk::WalkingPaceCmPerSec), Pace >= CryoWalk::WalkingPaceCmPerSec);
			if (Leg.OnArrive)
			{
				Leg.OnArrive(Pawn);
			}
			// Stop, face what this leg was for, and let the frame settle before capturing.
			PC->StopMovement();
			const FVector ToLook = Leg.LookAt - Pawn->GetActorLocation();
			if (!ToLook.IsNearlyZero())
			{
				// Level, not down at the station: a first-person camera pitched at a waist-high
				// station fills the frame with the character's own suit torso.
				FRotator Look = ToLook.Rotation();
				Look.Pitch = FMath::Clamp(Look.Pitch, -8.0f, 8.0f);
				PC->SetControlRotation(Look);
				// The body turns with the view, or a view turned across it frames the suit's torso.
				Pawn->SetActorRotation(FRotator(0.0f, Look.Yaw, 0.0f));
			}
			bPendingCapture = true;
			CaptureAt = Now + 0.8;
			return false;
		}

		// A partial path gated by an obstruction: go to the gate, clear it, carry on. Recast ends
		// a partial path at the reachable point nearest the goal -- a deck up, on this route -- and
		// path following would drag the pawn back up the ramp to stand above its target.
		if (!bDetouring && Now - LastPathCheck >= 3.0)
		{
			LastPathCheck = Now;
			const UNavigationPath* Path = UNavigationSystemV1::FindPathToLocationSynchronously(World, Here, LegGoal);
			if (Path && Path->IsValid() && Path->IsPartial())
			{
				// One rule for both kinds of gate, nearest first. The route along a deck is a line
				// of things that stop it -- corridor barriers, sealed corridor blocks, the sealed
				// door of the room the goal is in -- and the pawn can only ever open the first of
				// them. Picking the barrier beyond a sealed block sent the walk to a place it could
				// not reach and, when that failed, up the ramp; ordering by distance along the deck
				// walks the line in the order a player would meet it. A gate counts when it is on
				// this deck and either between here and the goal in the corridor spine, or where
				// the partial path gave up, or beside the path itself.
				const FVector PathEnd = Path->PathPoints.Num() ? Path->PathPoints.Last() : Here;
				auto OnRoute = [&](const FVector& Loc)
				{
					if (FMath::Abs(Loc.Z - Here.Z) > 300.0f) { return false; }
					const bool bBetween = FMath::Abs(Loc.X - Here.X) + FMath::Abs(Loc.X - LegGoal.X) <= FMath::Abs(Here.X - LegGoal.X) + 250.0f;
					const bool bInSpine = FMath::Abs(Loc.Y) <= 400.0f;
					const bool bAtPathEnd = FVector::Dist(PathEnd, Loc) <= 400.0f;
					bool bNearPath = false;
					for (const FVector& Point : Path->PathPoints) { bNearPath |= FVector::Dist(Loc, Point) <= 350.0f; }
					return (bBetween && bInSpine) || bAtPathEnd || bNearPath;
				};
				struct FGateCandidate
				{
					float Along = 0.0f;
					AObstructionBarrier* Gate = nullptr;
					AMechanicalOverrideStation* Station = nullptr;
					ABulkheadDoor* Door = nullptr;
				};
				TArray<FGateCandidate> Candidates;
				for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
				{
					if (It->bCleared) { continue; }
					if (OnRoute(It->GetActorLocation()))
					{
						Candidates.Add({static_cast<float>(FVector::Dist2D(Here, It->GetActorLocation())), *It, nullptr, nullptr});
					}
				}
				// A door can have a panel on each face; the one to use is the one on this side of
				// it, which is the nearer. Taking the first station found sent the walk at a panel
				// behind the very door it was meant to open.
				TMap<ABulkheadDoor*, AMechanicalOverrideStation*> NearestStationByDoor;
				for (TActorIterator<AMechanicalOverrideStation> It(World); It; ++It)
				{
					ABulkheadDoor* Door = Cast<ABulkheadDoor>(It->TargetActor.Get());
					if (!Door || !Door->bIsSealed || Door->ActorHasTag(TEXT("QuickDemoCICDoor"))) { continue; }   // the CIC door is its own leg
					if (!OnRoute(Door->GetActorLocation())) { continue; }
					AMechanicalOverrideStation*& Best = NearestStationByDoor.FindOrAdd(Door);
					if (!Best || FVector::Dist2D(Here, It->GetActorLocation()) < FVector::Dist2D(Here, Best->GetActorLocation()))
					{
						Best = *It;
					}
				}
				for (const TPair<ABulkheadDoor*, AMechanicalOverrideStation*>& Pair : NearestStationByDoor)
				{
					Candidates.Add({static_cast<float>(FVector::Dist2D(Here, Pair.Key->GetActorLocation())), nullptr, Pair.Value, Pair.Key});
				}
				Candidates.Sort([](const FGateCandidate& A, const FGateCandidate& B) { return A.Along < B.Along; });
				if (Candidates.Num() > 0)
				{
					const FGateCandidate& First = Candidates[0];
					bDetouring = true;
					if (First.Gate)
					{
						DetourGate = First.Gate;
						const FVector GateLoc = First.Gate->GetActorLocation();
						Issue(GateLoc + (Here - GateLoc).GetSafeNormal2D() * 200.0f);
						Test->AddInfo(FString::Printf(TEXT("WALK detouring to %s at %s on [%s] (%d gates on the route)"),
							*First.Gate->GetName(), *GateLoc.ToCompactString(), *LegName, Candidates.Num()));
					}
					else
					{
						DetourStation = First.Station;
						DetourDoor = First.Door;
						// Toward the panel, not onto it: a station's own location is inside its
						// collision against the wall, where no navmesh point projects, and a move
						// issued there simply never starts.
						const FVector StationLoc = First.Station->GetActorLocation();
						Issue(StationLoc + (Here - StationLoc).GetSafeNormal2D() * 150.0f);
						Test->AddInfo(FString::Printf(TEXT("WALK detouring to override station %s for sealed %s at %s on [%s] (%d gates on the route)"),
							*First.Station->GetName(), *First.Door->GetName(), *First.Door->GetActorLocation().ToCompactString(), *LegName, Candidates.Num()));
					}
				}
			}
		}
		// A detour the pawn cannot make is abandoned, not waited on: four seconds without moving
		// hands control back to the leg, whose own stuck handling and timeout then apply. The
		// first version returned from inside the detour every tick, ahead of both, and a pawn
		// pinned on the ramp with a detour pending held the test for fifteen minutes.
		static double DetourStillSince = 0.0;
		if (bDetouring)
		{
			if (Pawn->GetVelocity().Size() > 5.0f) { DetourStillSince = 0.0; }
			else if (DetourStillSince == 0.0) { DetourStillSince = Now; }
			else if (Now - DetourStillSince > 4.0)
			{
				Test->AddInfo(FString::Printf(TEXT("WALK abandoning a detour on [%s]: the pawn has not moved for 4s at %s"), *LegName, *Here.ToCompactString()));
				bDetouring = false;
				DetourGate = nullptr;
				DetourStation = nullptr;
				DetourDoor = nullptr;
				DetourStillSince = 0.0;
				LastPathCheck = Now;
				Issue(LegGoal);
			}
		}
		else
		{
			DetourStillSince = 0.0;
		}
		if (Now - PhaseSince > CryoWalk::LegSeconds || bExpired)
		{
			// Timeout before any detour handling, so that no branch below can keep the walk
			// alive past its budget. The diagnostics are the same as the end-of-leg ones.
			bDetouring = false;
			DetourGate = nullptr;
			DetourStation = nullptr;
			DetourDoor = nullptr;
		}
		if (bDetouring && DetourStation.IsValid())
		{
			const FVector StationLoc = DetourStation->GetActorLocation();
			if (FVector::Dist(Here, StationLoc) <= 350.0f)
			{
				DetourStation->OnActivityCompleted_Implementation(Pawn);
				Test->AddInfo(FString::Printf(TEXT("WALK ran override station %s on [%s]: door %s now %s"),
					*DetourStation->GetName(), *LegName,
					DetourDoor.IsValid() ? *DetourDoor->GetName() : TEXT("?"),
					DetourDoor.IsValid() && DetourDoor->IsPassable() ? TEXT("passable") : TEXT("STILL SEALED")));
				bDetouring = false;
				DetourStation = nullptr;
				DetourDoor = nullptr;
				// Stop here and ask again in a second, once the leaves have moved and the navmesh
				// has caught up -- do not head for the goal yet. With another gate still on the
				// deck the goal's path is still partial, and following it for even three seconds
				// put the pawn up the ramp choosing doors on the wrong deck.
				PC->StopMovement();
				LastPathCheck = Now - 2.0;
				LastIssued = Now;
			}
			else if (Now - LastIssued >= CryoWalk::ReissueSeconds)
			{
				Issue(StationLoc + (Here - StationLoc).GetSafeNormal2D() * 150.0f);
			}
			return false;
		}
		if (bDetouring && DetourGate.IsValid())
		{
			const FVector GateLoc = DetourGate->GetActorLocation();
			if (FVector::Dist(Here, GateLoc) <= 350.0f)
			{
				const EObstructionVerb Verb = DetourGate->CanResolveWith(EObstructionVerb::Cut, Pawn) ? EObstructionVerb::Cut : EObstructionVerb::Squeeze;
				const bool bClearedGate = DetourGate->ResolveWith(Verb, Pawn);
				Test->AddInfo(FString::Printf(TEXT("WALK %s %s on [%s] at %s"),
					bClearedGate ? TEXT("cleared") : TEXT("could not clear"), *DetourGate->GetName(), *LegName, *Here.ToCompactString()));
				bDetouring = false;
				DetourGate = nullptr;
				// As with a station: hold, and re-check for the next gate before moving on.
				PC->StopMovement();
				LastPathCheck = Now - 2.0;
				LastIssued = Now;
			}
			else if (Now - LastIssued >= CryoWalk::ReissueSeconds)
			{
				Issue(GateLoc + (Here - GateLoc).GetSafeNormal2D() * 200.0f);
			}
			return false;
		}

		// Stuck beside an uncleared obstruction: clear it, as the player would.
		if (Pawn->GetVelocity().Size() > 5.0f) { StuckSince = 0.0; }
		else if (StuckSince == 0.0) { StuckSince = Now; }
		else if (Now - StuckSince > 2.0)
		{
			StuckSince = 0.0;
			bool bHandled = false;
			for (TActorIterator<AObstructionBarrier> It(World); It; ++It)
			{
				if (It->bCleared || FVector::Dist(It->GetActorLocation(), Here) > 350.0f) { continue; }
				const EObstructionVerb Verb = It->CanResolveWith(EObstructionVerb::Cut, Pawn) ? EObstructionVerb::Cut : EObstructionVerb::Squeeze;
				if (It->ResolveWith(Verb, Pawn))
				{
					Test->AddInfo(FString::Printf(TEXT("WALK cleared %s (stuck beside it) on [%s]"), *It->GetName(), *LegName));
					Issue(LegGoal);
				}
				bHandled = true;
				break;
			}
			// Stuck beside a sealed bulkhead: its override station is within arm's reach of it.
			if (!bHandled)
			{
				for (TActorIterator<AMechanicalOverrideStation> It(World); It; ++It)
				{
					ABulkheadDoor* Door = Cast<ABulkheadDoor>(It->TargetActor.Get());
					if (!Door || !Door->bIsSealed || Door->ActorHasTag(TEXT("QuickDemoCICDoor"))) { continue; }
					if (FVector::Dist(Door->GetActorLocation(), Here) > 400.0f) { continue; }
					// The panel on this side of the door, within a player's reach of where they stand.
					if (FVector::Dist(It->GetActorLocation(), Here) > 400.0f) { continue; }
					It->OnActivityCompleted_Implementation(Pawn);
					Test->AddInfo(FString::Printf(TEXT("WALK ran override station %s (stuck beside sealed %s) on [%s]"),
						*It->GetName(), *Door->GetName(), *LegName));
					Issue(LegGoal);
					bHandled = true;
					break;
				}
			}
			if (!bHandled)
			{
				// Pinned against something with no gate near -- a rail end at a ramp corner, in
				// the first case. A player steps back or sideways; so does the walk: back onto the
				// navmesh if it has slid off it, otherwise a sidestep, alternating sides.
				FNavLocation OnMesh;
				FVector Nudge = Here;
				if (Navigation->ProjectPointToNavigation(Here, OnMesh, FVector(120.0f, 120.0f, 150.0f))
					&& FVector::Dist2D(OnMesh.Location, Here) > 30.0f)
				{
					Nudge = OnMesh.Location;
				}
				else
				{
					const FVector Dir = (LegGoal - Here).GetSafeNormal2D();
					const FVector Perp(-Dir.Y, Dir.X, 0.0f);
					Nudge = Here + Perp * ((NudgeCount % 2 == 0) ? 120.0f : -120.0f);
				}
				++NudgeCount;
				Issue(Nudge);
				LastIssued = Now - CryoWalk::ReissueSeconds + 1.0;   // the goal again a second later
				Test->AddInfo(FString::Printf(TEXT("WALK stuck with no gate near on [%s] at %s; nudging to %s (nudge %d)"),
					*LegName, *Here.ToCompactString(), *Nudge.ToCompactString(), NudgeCount));
			}
		}

		if (Now - PhaseSince > CryoWalk::LegSeconds || bExpired)
		{
			FString PathInfo = TEXT("no path object");
			if (const UNavigationPath* Path = UNavigationSystemV1::FindPathToLocationSynchronously(World, Here, LegGoal))
			{
				PathInfo = Path->IsValid()
					? FString::Printf(TEXT("path %s, %d points, ends at %s"), Path->IsPartial() ? TEXT("PARTIAL") : TEXT("complete"),
						Path->PathPoints.Num(), Path->PathPoints.Num() ? *Path->PathPoints.Last().ToCompactString() : TEXT("?"))
					: TEXT("path invalid");
			}
			FString Probe;
			for (int32 Step = 1; Step <= 8; ++Step)
			{
				const FVector P = FMath::Lerp(Here, LegGoal, Step / 8.0f);
				FNavLocation On;
				Probe += FString::Printf(TEXT(" %d/8:%s"), Step, Navigation->ProjectPointToNavigation(P, On, FVector(60.0f, 60.0f, 200.0f)) ? TEXT("mesh") : TEXT("GAP"));
			}
			Test->AddInfo(FString::Printf(TEXT("WALK diag from %s: %s; line probe:%s"), *Here.ToCompactString(), *PathInfo, *Probe));
			Test->AddError(FString::Printf(
				TEXT("The player pawn never arrived on [%s]: after %.0fs it is at %s, %.0f cm from the goal %s in plan and %.0f cm off in height. ")
				TEXT("That is where something stops it -- a collider, a step, or no path from there."),
				*LegName, Now - PhaseSince, *Here.ToCompactString(), Remaining, *LegGoal.ToCompactString(), HeightOff));
			return Finish(true);
		}

		// Path following can abort on a dirty tile or a stuck frame; re-issuing is cheap.
		if (Now - LastIssued >= CryoWalk::ReissueSeconds)
		{
			Issue(LegGoal);
		}
		return false;
	}

	case CryoWalk::EPhase::WaitTitleCut:
	{
		// The director waits AQuickDemoMissionDirector::TitleCutDelaySeconds (2.5s default) after
		// ReachCIC completes before calling ShowStartScreen. A fixed margin here, rather than
		// reading the property, keeps this test decoupled from that number's exact value.
		constexpr double TitleCutMarginSeconds = 5.0;
		// A recording holds on the title card so the video ends on it rather than a cut to black.
		constexpr double TitleHoldSeconds = 6.0;
		static bool bHoldingOnTitle = false;
		if (bHoldingOnTitle) { return (Now - PhaseSince >= TitleHoldSeconds || bExpired) ? Finish(true) : false; }
		if (Now - PhaseSince < TitleCutMarginSeconds && !bExpired)
		{
			return false;
		}
		UMenuManagerSubsystem* Menus = World->GetGameInstance()
			? World->GetGameInstance()->GetSubsystem<UMenuManagerSubsystem>() : nullptr;
		UObject* StartScreen = Menus ? CryoWalk::ReadObject(Menus, TEXT("CurrentStartScreen")) : nullptr;
		Test->TestNotNull(TEXT("The demo's own MenuManagerSubsystem cut to the title screen after ReachCIC completed"), StartScreen);
		CryoWalk::Capture(TEXT("Walk_10_title_screen"), true);
		if (CryoWalk::IsRecording())
		{
			bHoldingOnTitle = true;
			PhaseSince = Now;
			return false;
		}
		return Finish(true);
	}
	}
	return Finish(true);
}

// TEMP-LIVE-LOOK: same map, same ShowStartScreen call the director makes, no walk.
DEFINE_LATENT_AUTOMATION_COMMAND_TWO_PARAMETER(FTitleCutLook, FAutomationTestBase*, Test, double, StartSeconds);
bool FTitleCutLook::Update()
{
	static int32 Step = 0; static double StepSince = 0.0;
	UWorld* World = nullptr;
	for (const FWorldContext& Ctx : GEngine->GetWorldContexts()) { if (Ctx.WorldType == EWorldType::PIE && Ctx.World()) { World = Ctx.World(); } }
	if (!World) { return FPlatformTime::Seconds() - StartSeconds > 60.0; }
	const double Now = FPlatformTime::Seconds();
	if (StepSince == 0.0) { StepSince = Now; }
	UMenuManagerSubsystem* Menus = World->GetGameInstance() ? World->GetGameInstance()->GetSubsystem<UMenuManagerSubsystem>() : nullptr;
	switch (Step)
	{
	case 0: if (Now - StepSince < 4.0) return false; Step = 1; StepSince = Now; if (Menus) Menus->ShowStartScreen(); UE_LOG(LogTemp, Display, TEXT("TITLELOOK ShowStartScreen called")); return false;
	case 1: if (Now - StepSince < 3.0) return false; Step = 2; StepSince = Now;
	{
		UObject* StartScreen = Menus ? CryoWalk::ReadObject(Menus, TEXT("CurrentStartScreen")) : nullptr;
		Test->TestNotNull(TEXT("TITLELOOK CurrentStartScreen"), StartScreen);
		if (UUserWidget* W = Cast<UUserWidget>(StartScreen))
		{
			UE_LOG(LogTemp, Display, TEXT("TITLELOOK widget %s InViewport=%d Visible=%d Opacity=%.2f Desired=%s"), *W->GetClass()->GetName(), W->IsInViewport() ? 1 : 0, W->IsVisible() ? 1 : 0, W->GetRenderOpacity(), *W->GetDesiredSize().ToString());
		}
		CryoWalk::Capture(TEXT("TitleLook_noUI"), false);
		return false;
	}
	case 2: if (Now - StepSince < 1.0) return false; Step = 3; StepSince = Now; CryoWalk::Capture(TEXT("TitleLook_UI_viewport"), true); return false;
	case 3: if (Now - StepSince < 1.0) return false; Step = 4; StepSince = Now; FScreenshotRequest::RequestScreenshot(TEXT("TitleLook_UI_window"), true, false); return false;
	default: return Now - StepSince >= 30.0;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapTitleCutLookTest,
	"Ginnungagap.TempLiveLook.TitleCut",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FGinnungagapTitleCutLookTest::RunTest(const FString& Parameters)
{
	const double Start = FPlatformTime::Seconds();
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FTitleCutLook(this, Start));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapCryoExitWalkthroughPieTest,
	"Ginnungagap.Smoke.PlayerWalksOutOfCryo",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

// PIE in its own window at the video's size. FStartPIECommand plays in the editor's level
// viewport, which is whatever is left of the editor window after its panels -- fine for a test,
// wrong for a recording, where every frame should be the game at 1920x1080 and nothing else.
DEFINE_LATENT_AUTOMATION_COMMAND(FStartFloatingPIECommand);
bool FStartFloatingPIECommand::Update()
{
	ULevelEditorPlaySettings* Settings = DuplicateObject<ULevelEditorPlaySettings>(GetDefault<ULevelEditorPlaySettings>(), GetTransientPackage());
	Settings->LastExecutedPlayModeType = PlayMode_InEditorFloating;
	Settings->NewWindowWidth = 1920;
	Settings->NewWindowHeight = 1080;
	Settings->CenterNewWindow = true;
	FRequestPlaySessionParams Params;
	Params.EditorPlaySettings = Settings;
	GUnrealEd->RequestPlaySession(Params);
	return true;
}

bool FGinnungagapCryoExitWalkthroughPieTest::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	const double Start = CryoWalk::IsRecording() ? 0.0 : FPlatformTime::Seconds();
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	// A recording must not show the hand tool untextured while its shaders compile (headless
	// runs compile nothing and pass straight through).
	for (const TCHAR* Path : { TEXT("/Game/Frontier_EngineersToolbox/Materials/M_FrontierTools_1.M_FrontierTools_1"),
		TEXT("/Game/Frontier_EngineersToolbox/Tools/SM_Frontier_Powertool.SM_Frontier_Powertool") })
	{
		LoadObject<UObject>(nullptr, Path);
	}
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForShadersToFinishCompilingInGame());
	if (CryoWalk::IsRecording())
	{
		ADD_LATENT_AUTOMATION_COMMAND(FStartFloatingPIECommand());
	}
	else
	{
		ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	}
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FWalkCryoExit(this, Start));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
