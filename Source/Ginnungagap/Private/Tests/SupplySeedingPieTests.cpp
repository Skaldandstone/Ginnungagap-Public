#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Tests/AutomationEditorCommon.h"

#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

#include "Inventory/InventoryItemPickup.h"
#include "Inventory/ItemDefinition.h"
#include "Meta/RunSeedSubsystem.h"
#include "WorldItems/WorldItemSeedCatalog.h"
#include "WorldItems/WorldItemSeedPoint.h"

/**
 * Supplies are findable, and finding them is not the same every run.
 *
 * Ten pickup Blueprints existed and nothing placed a single one, so the only supplies in the game
 * were the ones the workshop bench handed over. Once that bench was used the ship held nothing else
 * to find, which makes searching it pointless in the most literal sense.
 *
 * The reseeding assertions cover a bug rather than a feature. The seed stream was built from a
 * hardcoded constant and the actor's path, so every run of every playthrough placed identical loot
 * in identical spots. A layout nobody could vary is not randomness, and it was invisible from
 * inside a single run -- you would only ever notice by playing twice and recognising the shelf.
 */

namespace SupplySeedPie
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

	TArray<AWorldItemSeedPoint*> AllSeedPoints(UWorld* World)
	{
		TArray<AWorldItemSeedPoint*> Points;
		for (TActorIterator<AWorldItemSeedPoint> It(World); It; ++It)
		{
			Points.Add(*It);
		}
		return Points;
	}

	/**
	 * A stable description of what a run produced: which item, in what quantity, where.
	 *
	 * Compared as a whole rather than counted, because a count alone would call two completely
	 * different layouts identical as long as they happened to spawn the same number of things.
	 */
	FString DescribeLayout(const TArray<AWorldItemSeedPoint*>& Points)
	{
		TArray<FString> Lines;
		for (const AWorldItemSeedPoint* Point : Points)
		{
			for (const TObjectPtr<AActor>& Spawned : Point->SpawnedItems)
			{
				const AInventoryItemPickup* Pickup = Cast<AInventoryItemPickup>(Spawned);
				if (!Pickup)
				{
					continue;
				}

				const FVector Location = Pickup->GetActorLocation();
				Lines.Add(FString::Printf(TEXT("%s:%s:%d:%.0f,%.0f"),
					*Point->GetName(),
					Pickup->ItemDefinition ? *Pickup->ItemDefinition->ItemId.ToString() : TEXT("none"),
					Pickup->Quantity, Location.X, Location.Y));
			}
		}

		// Sorted so the comparison is about what was placed, not the order actors were iterated in.
		Lines.Sort();
		return FString::Join(Lines, TEXT("|"));
	}

	/** Re-rolls every point under a given run seed and returns what that produced. */
	FString LayoutForSeed(UWorld* World, URunSeedSubsystem* Seeds,
		const TArray<AWorldItemSeedPoint*>& Points, int32 RunSeed)
	{
		Seeds->SeedRun(RunSeed);
		for (AWorldItemSeedPoint* Point : Points)
		{
			// SeedNow refuses to run while anything it spawned is still alive, so the clear is what
			// makes a re-roll possible at all.
			Point->ClearSpawnedItems();
			Point->SeedNow();
		}
		return DescribeLayout(Points);
	}
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(FAssertSupplySeeding, FAutomationTestBase*, Test);

bool FAssertSupplySeeding::Update()
{
	UWorld* World = SupplySeedPie::FindPieWorld();
	UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	if (!GameInstance)
	{
		Test->AddError(TEXT("No PIE game instance for the supply seeding assertions"));
		return true;
	}

	URunSeedSubsystem* Seeds = GameInstance->GetSubsystem<URunSeedSubsystem>();
	if (!Seeds)
	{
		Test->AddError(TEXT("No run seed subsystem"));
		return true;
	}

	TArray<AWorldItemSeedPoint*> Points = SupplySeedPie::AllSeedPoints(World);
	Test->TestTrue(TEXT("The ship has supply seed points in it"), Points.Num() > 0);
	if (Points.Num() == 0)
	{
		return true;
	}

	// --- The points are configured to be able to produce anything -------------------------------
	int32 WithCatalog = 0;
	for (const AWorldItemSeedPoint* Point : Points)
	{
		if (!Point->Catalog)
		{
			continue;
		}
		++WithCatalog;

		// A point whose filters exclude everything is worse than no point: it looks like it works
		// and can only ever produce nothing.
		Test->TestTrue(
			FString::Printf(TEXT("%s has something it could actually spawn"), *Point->GetName()),
			Point->GetEligibleEntries().Num() > 0);
	}
	Test->TestTrue(TEXT("Seed points carry a catalogue"), WithCatalog > 0);

	// --- Room profiles actually gate what appears where -----------------------------------------
	// The point of profiles is that a coolant pack belongs near the reactor rather than in a bunk
	// room. If every room could produce everything, the profile data is decorative.
	const AWorldItemSeedPoint* Berthing = nullptr;
	const AWorldItemSeedPoint* Engineering = nullptr;
	for (const AWorldItemSeedPoint* Point : Points)
	{
		if (Point->RoomProfile == FName(TEXT("Berthing")) && !Berthing) { Berthing = Point; }
		if (Point->RoomProfile == FName(TEXT("Engineering")) && !Engineering) { Engineering = Point; }
	}

	if (Berthing && Engineering)
	{
		auto CanSpawn = [](const AWorldItemSeedPoint* Point, const TCHAR* ContentId)
		{
			for (const FWorldItemSeedEntry& Entry : Point->GetEligibleEntries())
			{
				if (Entry.ContentId == FName(ContentId))
				{
					return true;
				}
			}
			return false;
		};

		Test->TestTrue(TEXT("A reactor room can yield a coolant pack"),
			CanSpawn(Engineering, TEXT("CoolantGelPack")));
		Test->TestFalse(TEXT("A bunk room cannot yield a coolant pack"),
			CanSpawn(Berthing, TEXT("CoolantGelPack")));

		// The untargeted supplies have no profile list, so they must survive the filter everywhere
		// -- otherwise a room could offer nothing a crew member always wants.
		Test->TestTrue(TEXT("A bunk room can still yield oxygen"),
			CanSpawn(Berthing, TEXT("EmergencyOxygenCartridge")));
	}
	else
	{
		Test->AddError(TEXT("Expected both a Berthing and an Engineering seed point in the map"));
	}

	// --- Seeding actually places things ----------------------------------------------------------
	const FString First = SupplySeedPie::LayoutForSeed(World, Seeds, Points, 20001);
	Test->TestFalse(TEXT("Seeding puts supplies in the ship"), First.IsEmpty());

	// --- The same run seed reproduces the same ship ----------------------------------------------
	const FString Repeat = SupplySeedPie::LayoutForSeed(World, Seeds, Points, 20001);
	Test->TestEqual(TEXT("The same run seed lays the ship out identically"), Repeat, First);

	// --- A different run seed lays it out differently ---------------------------------------------
	// This is the assertion that fails against the old code, where the stream ignored the run seed
	// entirely and every run was the same ship.
	const FString Different = SupplySeedPie::LayoutForSeed(World, Seeds, Points, 87654);
	Test->TestNotEqual(TEXT("A different run seed lays the ship out differently"), Different, First);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapSupplySeedingPieTest,
	"Ginnungagap.Smoke.SupplySeeding",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapSupplySeedingPieTest::RunTest(const FString& Parameters)
{
	AutomationOpenMap(TEXT("/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(1.0f));
	ADD_LATENT_AUTOMATION_COMMAND(FAssertSupplySeeding(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());

	return true;
}

#endif
