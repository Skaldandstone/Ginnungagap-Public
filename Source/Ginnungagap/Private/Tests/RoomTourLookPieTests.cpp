#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "CollisionQueryParams.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "UnrealClient.h"

#include "Bloom/BloomDormantHulk.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

#include "Tests/GinnungagapTestMap.h"

/**
 * A still at every objective beacon in the demo map, plus the hulk: the camera stands off the
 * marker in whichever of four directions has the most clear floor, a little above eye height,
 * looking at it. A look test for the ship's surfaces and lighting away from the cryo bay, which
 * the opening-shot test already covers. Under -nullrhi the pictures are black; the assertions
 * are only that the beacons exist and every shot was set up.
 */
namespace RoomTour
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

	struct FStop { FString Label; FVector Target; };

	TArray<FStop> CollectStops(UWorld* World)
	{
		TArray<FStop> Stops;
		for (TActorIterator<AQuickDemoObjectiveBeacon> It(World); It; ++It)
		{
			Stops.Add({ It->ObjectiveId.ToString(), It->GetActorLocation() });
		}
		Stops.Sort([](const FStop& A, const FStop& B) { return A.Label < B.Label; });
		for (TActorIterator<ABloomDormantHulk> It(World); It; ++It)
		{
			Stops.Add({ TEXT("Hulk"), It->GetActorLocation() });
		}
		return Stops;
	}

	/** The camera spot with the longest clear run from the target among four compass directions. */
	FVector PickCameraSpot(UWorld* World, const FVector& Target)
	{
		const FVector Eye = Target + FVector(0.0f, 0.0f, 120.0f);
		float BestDistance = 0.0f;
		FVector Best = Eye + FVector(-200.0f, 0.0f, 0.0f);
		for (const FVector& Dir : { FVector(1, 0, 0), FVector(-1, 0, 0), FVector(0, 1, 0), FVector(0, -1, 0) })
		{
			FHitResult Hit;
			const FVector End = Eye + Dir * 420.0f;
			const bool bHit = World->LineTraceSingleByChannel(Hit, Eye, End, ECC_Visibility, FCollisionQueryParams(SCENE_QUERY_STAT(RoomTour), false));
			const float Clear = bHit ? Hit.Distance : 420.0f;
			if (Clear > BestDistance)
			{
				BestDistance = Clear;
				Best = Eye + Dir * FMath::Clamp(Clear - 40.0f, 120.0f, 380.0f);
			}
		}
		return Best + FVector(0.0f, 0.0f, 10.0f);
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FTourRooms, FAutomationTestBase*, Test);

bool FTourRooms::Update()
{
	static TArray<RoomTour::FStop> Stops;
	static int32 Index = -1;
	static double StepAt = -1.0;
	static TWeakObjectPtr<ACameraActor> Camera;
	UWorld* World = RoomTour::FindPieWorld();
	APlayerController* PC = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
	if (!World || !PC)
	{
		return false;
	}
	if (Index < 0)
	{
		// The opening would otherwise hold the view on the pod for ten seconds.
		for (TActorIterator<AQuickDemoOpeningSequence> It(World); It; ++It)
		{
			It->Skip();
		}
		Stops = RoomTour::CollectStops(World);
		Test->TestTrue(TEXT("The demo map has objective beacons to tour"), Stops.Num() > 0);
		Index = 0;
	}
	const double Now = World->GetTimeSeconds();
	if (Index >= Stops.Num())
	{
		if (Camera.IsValid()) { Camera->Destroy(); }
		Stops.Reset(); Index = -1; StepAt = -1.0;
		return true;
	}
	const RoomTour::FStop& Stop = Stops[Index];
	if (StepAt < 0.0)
	{
		const FVector Spot = RoomTour::PickCameraSpot(World, Stop.Target);
		const FRotator Look = (Stop.Target + FVector(0.0f, 0.0f, 110.0f) - Spot).Rotation();
		if (!Camera.IsValid())
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Camera = World->SpawnActor<ACameraActor>(Spot, Look, Params);
			if (Camera.IsValid()) { Camera->GetCameraComponent()->SetFieldOfView(80.0f); }
		}
		else
		{
			Camera->SetActorLocationAndRotation(Spot, Look);
		}
		if (Camera.IsValid()) { PC->SetViewTargetWithBlend(Camera.Get(), 0.0f); }
		StepAt = Now;
		return false;
	}
	if (Now - StepAt < 0.6)
	{
		return false;
	}
	UE_LOG(LogTemp, Display, TEXT("ROOMTOUR %02d %s at %s"), Index, *Stop.Label, *Stop.Target.ToCompactString());
	FScreenshotRequest::RequestScreenshot(FString::Printf(TEXT("Tour_%02d_%s"), Index, *Stop.Label), false, false, false, FIntRect(), true);
	++Index; StepAt = -1.0;
	return false;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapRoomTourLookTest,
	"Ginnungagap.Look.RoomTour",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapRoomTourLookTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(GinnungagapTestMap::Path());
	ADD_LATENT_AUTOMATION_COMMAND(FWaitForShadersToFinishCompilingInGame());
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FTourRooms(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
