#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "LevelSetup/QuickDemoMissionDirector.h"
#include "LevelSetup/QuickDemoPowerStation.h"
#include "NavigationSystem.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavMesh/RecastNavMesh.h"

/**
 * That the demo is navigable at level start: the player start, the corridor and every station
 * project onto the navmesh once its build has settled.
 *
 * Written when the player start stopped projecting after a scripted doorway repair, while a solid
 * greybox floor sat under it. The cause was a stale saved navmesh: maps edited and saved from
 * headless sessions never get the rebuild an interactive editor would do, a headless Build()
 * produces nothing at all, and Dynamic runtime generation trusts what is saved. The demo director
 * now rebuilds from live geometry at level start; this asserts that the result actually covers
 * the demo, so the same silent failure cannot come back through another script.
 */

namespace NavmeshCoverage
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
}

DEFINE_LATENT_AUTOMATION_COMMAND_THREE_PARAMETER(FReportNavmeshCoverage, FAutomationTestBase*, Test, double, DeadlineSeconds, double, StartSeconds);

bool FReportNavmeshCoverage::Update()
{
	UWorld* World = NavmeshCoverage::FindPieWorld();
	if (!World)
	{
		Test->AddError(TEXT("No PIE world"));
		return true;
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!Navigation)
	{
		Test->AddError(TEXT("No navigation system"));
		return true;
	}
	Navigation->SetMaxSimultaneousTileGenerationJobsCount(16);

	const double Now = FPlatformTime::Seconds();
	const bool bExpired = Now >= DeadlineSeconds;
	// Settle: past an early window where "not being built" just means "not started yet".
	if ((UNavigationSystemV1::IsNavigationBeingBuilt(World) || Now - StartSeconds < 8.0) && !bExpired)
	{
		return false;
	}

	Test->AddInfo(FString::Printf(TEXT("COVER settled after %.0fs, being built now: %s, expired: %s"),
		Now - StartSeconds,
		UNavigationSystemV1::IsNavigationBeingBuilt(World) ? TEXT("yes") : TEXT("no"),
		bExpired ? TEXT("yes") : TEXT("no")));

	int32 NavDataCount = 0;
	for (TActorIterator<ARecastNavMesh> It(World); It; ++It)
	{
		++NavDataCount;
		Test->AddInfo(FString::Printf(
			TEXT("COVER RecastNavMesh %s: tiles %d, fixed pool %s, pool size %d, hard limit %d, runtime mode %d, tile size %.0f, cell %.0f, agent radius %.0f"),
			*It->GetName(), It->GetNavMeshTilesCount(),
			It->bFixedTilePoolSize ? TEXT("yes") : TEXT("no"), It->TilePoolSize, It->TileNumberHardLimit,
			static_cast<int32>(It->GetRuntimeGenerationMode()), It->TileSizeUU, It->GetCellSize(ENavigationDataResolution::Default),
			It->AgentRadius));
		Test->TestTrue(TEXT("The navmesh has tiles"), It->GetNavMeshTilesCount() > 0);
	}
	Test->AddInfo(FString::Printf(TEXT("COVER nav data actors: %d"), NavDataCount));

	for (TActorIterator<ANavMeshBoundsVolume> It(World); It; ++It)
	{
		FVector Origin, BoxExtent;
		It->GetActorBounds(false, Origin, BoxExtent);
		Test->AddInfo(FString::Printf(TEXT("COVER bounds volume %s origin %s extent %s tags %d"),
			*It->GetName(), *Origin.ToCompactString(), *BoxExtent.ToCompactString(), It->Tags.Num()));
	}

	// The greybox floors under the start and the corridor: are they even exported to the navmesh?
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		const FString Label = It->GetActorLabel();
		if (!Label.Contains(TEXT("Floor_QD-03-01")) && !Label.Contains(TEXT("CorridorFloor_D03"))
			&& !Label.Contains(TEXT("InnerWall_QD-03-01")))
		{
			continue;
		}
		for (UActorComponent* Component : It->GetComponents())
		{
			if (const UPrimitiveComponent* Prim = Cast<UPrimitiveComponent>(Component))
			{
				Test->AddInfo(FString::Printf(
					TEXT("COVER greybox %s: CanEverAffectNavigation %s, IsNavigationRelevant %s, collision %d, profile %s, hiddenInGame %s"),
					*Label,
					Prim->CanEverAffectNavigation() ? TEXT("yes") : TEXT("no"),
					Prim->IsNavigationRelevant() ? TEXT("yes") : TEXT("no"),
					static_cast<int32>(Prim->GetCollisionEnabled()),
					*Prim->GetCollisionProfileName().ToString(),
					Prim->bHiddenInGame ? TEXT("yes") : TEXT("no")));
			}
		}
	}

	TArray<TPair<FString, FVector>> Probes;
	for (TActorIterator<APlayerStart> It(World); It; ++It)
	{
		const FVector S = It->GetActorLocation();
		Probes.Add({TEXT("PlayerStart"), S});
		Probes.Add({TEXT("Start -200x"), S + FVector(-200, 0, 0)});
		Probes.Add({TEXT("Start +100y (toward wall)"), S + FVector(0, 100, 0)});
		Probes.Add({TEXT("Start -300y (toward pods)"), S + FVector(0, -300, 0)});
		Probes.Add({TEXT("Cryo centre"), FVector(-6600, -680, S.Z)});
		Probes.Add({TEXT("Corridor at cryo door"), FVector(-6600, 0, S.Z)});
		Probes.Add({TEXT("Corridor mid-ship"), FVector(0, 0, S.Z)});
		break;
	}
	for (TActorIterator<AQuickDemoSuitStation> It(World); It; ++It) { Probes.Add({TEXT("SuitStation"), It->GetActorLocation()}); break; }
	for (TActorIterator<AQuickDemoWorkshopBench> It(World); It; ++It) { Probes.Add({TEXT("WorkshopBench"), It->GetActorLocation()}); break; }
	for (TActorIterator<AQuickDemoPowerStation> It(World); It; ++It) { Probes.Add({TEXT("PowerStation"), It->GetActorLocation()}); break; }

	for (const auto& Probe : Probes)
	{
		FNavLocation OnMesh;
		const bool bOk = Navigation->ProjectPointToNavigation(Probe.Value, OnMesh, NavmeshCoverage::Extent);
		Test->AddInfo(FString::Printf(TEXT("COVER %-26s at %s -> %s"),
			*Probe.Key, *Probe.Value.ToCompactString(),
			bOk ? *FString::Printf(TEXT("projects to %s"), *OnMesh.Location.ToCompactString()) : TEXT("NO navmesh within extent")));
		Test->TestTrue(FString::Printf(TEXT("%s is on the navmesh at level start"), *Probe.Key), bOk);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapNavmeshCoverageDiagnostic,
	"Ginnungagap.Smoke.NavmeshCoversDemo",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapNavmeshCoverageDiagnostic::RunTest(const FString& Parameters)
{
	UGameplayStatics::DeleteGameInSlot(TEXT("GinnungagapShipCheckpoint"), 0);
	const double Start = FPlatformTime::Seconds();
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(2.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FReportNavmeshCoverage(this, Start + 150.0, Start));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
