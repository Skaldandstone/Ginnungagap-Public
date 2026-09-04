#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "Editor.h"
#include "Engine/World.h"
#include "FileHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NavigationData.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"

/**
 * Not a test of the game: a build step that runs where builds can. The map generators spawn a
 * NavMeshBoundsVolume and ask for a rebuild, but a commandlet exits before the asynchronous
 * navmesh generation finishes, so the saved map has navigation data with no tiles and nothing in
 * PIE can path. This opens the map in the editor world, kicks the build, waits for it to finish
 * (the automation framework ticks the editor between latent commands), saves the level, and
 * reports the tile count.
 *
 *   UnrealEditor-Cmd.exe <project> -ExecCmds="Automation RunTests Ginnungagap.Tools.BakeNavmesh; Quit"
 *       -GinnungagapMap=/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack -nullrhi ...
 */
namespace BakeNavmesh
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

	UWorld* EditorWorld()
	{
		return GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FBuildAndSaveNavmesh, FAutomationTestBase*, Test);

bool FBuildAndSaveNavmesh::Update()
{
	static double StartedAt = -1.0;
	static bool bKicked = false;
	UWorld* World = BakeNavmesh::EditorWorld();
	UNavigationSystemV1* Nav = World ? FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) : nullptr;
	if (!World || !Nav)
	{
		if (StartedAt < 0.0) { StartedAt = FPlatformTime::Seconds(); }
		if (FPlatformTime::Seconds() - StartedAt > 30.0)
		{
			Test->AddError(TEXT("No editor world with a navigation system after 30s"));
			StartedAt = -1.0; bKicked = false;
			return true;
		}
		return false;
	}
	if (!bKicked)
	{
		// An unattended editor holds the "no update in editor" building lock, and Build() refuses
		// while any lock is held ("NOT building because navigation build is locked (flags: 0x4)").
		// Dropping every lock with the Rebuild action is the editor's own "Build Paths".
		Nav->RemoveNavigationBuildLock(0xFF, UNavigationSystemV1::ELockRemovalRebuildAction::Rebuild);
		Nav->Build();
		bKicked = true;
		StartedAt = FPlatformTime::Seconds();
		UE_LOG(LogTemp, Display, TEXT("BAKENAV build kicked on %s"), *World->GetMapName());
		return false;
	}
	if (Nav->IsNavigationBuildInProgress() && FPlatformTime::Seconds() - StartedAt < 600.0)
	{
		return false;
	}
	Test->TestFalse(TEXT("The navmesh build finished within ten minutes"), Nav->IsNavigationBuildInProgress());
	int32 Tiles = 0;
	if (const ANavigationData* NavData = Nav->GetDefaultNavDataInstance())
	{
		if (const ARecastNavMesh* Recast = Cast<ARecastNavMesh>(NavData))
		{
			Tiles = Recast->GetNavMeshTilesCount();
		}
	}
	Test->TestTrue(FString::Printf(TEXT("The navmesh has tiles after the build (%d)"), Tiles), Tiles > 0);
	// A tile can be empty; the proof is a floor point that projects. Deck 1's corridor centre.
	FNavLocation Projected;
	const FVector Probe(1200.0f, 800.0f, 5.0f);
	const bool bProjects = Nav->ProjectPointToNavigation(Probe, Projected, FVector(300.0f, 300.0f, 300.0f));
	if (const ANavigationData* NavData = Nav->GetDefaultNavDataInstance())
	{
		UE_LOG(LogTemp, Display, TEXT("BAKENAV nav data %s bounds %s; probe %s projects=%d -> %s"), *NavData->GetName(),
			*NavData->GetBounds().ToString(), *Probe.ToCompactString(), bProjects ? 1 : 0, *Projected.Location.ToCompactString());
	}
	Test->TestTrue(TEXT("Deck 1's corridor centre projects onto the baked navmesh"), bProjects);
	const bool bSaved = FEditorFileUtils::SaveLevel(World->PersistentLevel);
	Test->TestTrue(TEXT("The level saved with its navmesh"), bSaved);
	UE_LOG(LogTemp, Display, TEXT("BAKENAV %s: %d tiles, %.1fs, saved=%d"), *World->GetMapName(), Tiles, FPlatformTime::Seconds() - StartedAt, bSaved ? 1 : 0);
	StartedAt = -1.0; bKicked = false;
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapBakeNavmeshTest,
	"Ginnungagap.Tools.BakeNavmesh",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapBakeNavmeshTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(BakeNavmesh::MapPath());
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FBuildAndSaveNavmesh(this));
	return true;
}

#endif
