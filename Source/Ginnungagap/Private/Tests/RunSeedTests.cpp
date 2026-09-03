#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Meta/RunSeedSubsystem.h"

/**
 * The properties that make a seed worth recording.
 *
 * A seed that does not reproduce is worse than no seed: it invites someone to trust a repro that
 * silently diverged. These pin the guarantees the rest of the debug workflow rests on.
 */

namespace
{
	URunSeedSubsystem* MakeSeeds(int32 Seed)
	{
		UGameInstance* GameInstance = NewObject<UGameInstance>();
		URunSeedSubsystem* Seeds = NewObject<URunSeedSubsystem>(GameInstance);
		Seeds->SeedRun(Seed);
		return Seeds;
	}

	/** Draws a fixed pattern from a channel, so two runs can be compared as a sequence. */
	TArray<float> DrawSequence(URunSeedSubsystem* Seeds, FName Channel, int32 Count)
	{
		TArray<float> Out;
		for (int32 Index = 0; Index < Count; ++Index)
		{
			Out.Add(Seeds->FRand(Channel));
		}
		return Out;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRunSeedReproducibilityTest,
	"Ginnungagap.Debug.RunSeed.Reproducibility",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRunSeedReproducibilityTest::RunTest(const FString& Parameters)
{
	// The whole point: the same seed twice is the same run twice.
	URunSeedSubsystem* First = MakeSeeds(12345);
	URunSeedSubsystem* Second = MakeSeeds(12345);

	const TArray<float> A = DrawSequence(First, RunSeedChannels::JumpGeneration, 16);
	const TArray<float> B = DrawSequence(Second, RunSeedChannels::JumpGeneration, 16);
	TestEqual(TEXT("The same seed produces the same sequence"), A, B);

	// And a different seed is a different run, or the seed is not doing anything.
	URunSeedSubsystem* Other = MakeSeeds(54321);
	const TArray<float> C = DrawSequence(Other, RunSeedChannels::JumpGeneration, 16);
	TestNotEqual(TEXT("A different seed produces a different sequence"), A, C);

	// Seed 0 means "pick one", and the picked value must be reported -- an unseeded run still has
	// to be reproducible after the fact, because nobody knows a run mattered until it went wrong.
	URunSeedSubsystem* Generated = MakeSeeds(0);
	TestNotEqual(TEXT("An unseeded run still reports a usable seed"), Generated->GetRunSeed(), 0);

	// Feeding that reported seed back must reproduce it exactly.
	URunSeedSubsystem* Replayed = MakeSeeds(Generated->GetRunSeed());
	TestEqual(TEXT("Replaying a generated seed reproduces its sequence"),
		DrawSequence(Generated, RunSeedChannels::JumpFate, 8),
		DrawSequence(Replayed, RunSeedChannels::JumpFate, 8));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRunSeedChannelIsolationTest,
	"Ginnungagap.Debug.RunSeed.ChannelIsolation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRunSeedChannelIsolationTest::RunTest(const FString& Parameters)
{
	// Channels must not share a stream, or a run of the same seed would produce the same numbers in
	// two unrelated systems -- visibly correlated hazards and Bloom rolls.
	URunSeedSubsystem* Seeds = MakeSeeds(777);
	const TArray<float> Generation = DrawSequence(Seeds, RunSeedChannels::JumpGeneration, 12);
	const TArray<float> Bloom = DrawSequence(Seeds, RunSeedChannels::BloomRolls, 12);
	TestNotEqual(TEXT("Two channels do not produce the same numbers"), Generation, Bloom);

	// The property that makes seeds survive development: drawing from one channel must not shift
	// another. Without this, adding a single roll anywhere invalidates every recorded seed.
	URunSeedSubsystem* Clean = MakeSeeds(777);
	URunSeedSubsystem* Disturbed = MakeSeeds(777);

	// Disturb one channel heavily before reading the other.
	DrawSequence(Disturbed, RunSeedChannels::JumpGeneration, 500);

	TestEqual(TEXT("Heavy use of one channel leaves another untouched"),
		DrawSequence(Clean, RunSeedChannels::Falsification, 10),
		DrawSequence(Disturbed, RunSeedChannels::Falsification, 10));

	// A channel touched for the first time late in a run must give the same numbers as one touched
	// early, since its stream comes from the name rather than from when it was created.
	URunSeedSubsystem* Early = MakeSeeds(999);
	const TArray<float> EarlyDraws = DrawSequence(Early, RunSeedChannels::ArrivalPlacement, 6);

	URunSeedSubsystem* Late = MakeSeeds(999);
	DrawSequence(Late, RunSeedChannels::JumpGeneration, 40);
	DrawSequence(Late, RunSeedChannels::BloomRolls, 40);
	TestEqual(TEXT("A channel is independent of when it is first used"),
		EarlyDraws, DrawSequence(Late, RunSeedChannels::ArrivalPlacement, 6));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRunSeedRollBehaviourTest,
	"Ginnungagap.Debug.RunSeed.RollBehaviour",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRunSeedRollBehaviourTest::RunTest(const FString& Parameters)
{
	URunSeedSubsystem* Seeds = MakeSeeds(2468);

	// Certain outcomes must not consume a draw. If a disabled mechanic still advanced its channel,
	// turning a feature off would change an unrelated outcome on the same channel -- which makes a
	// seed reproduce a different run than the one it was recorded from.
	const int32 Before = Seeds->GetChannelDrawCount(RunSeedChannels::BloomRolls);
	TestFalse(TEXT("A zero chance never succeeds"), Seeds->RollChance(RunSeedChannels::BloomRolls, 0.0f));
	TestFalse(TEXT("A negative chance never succeeds"), Seeds->RollChance(RunSeedChannels::BloomRolls, -1.0f));
	TestTrue(TEXT("A certain chance always succeeds"), Seeds->RollChance(RunSeedChannels::BloomRolls, 1.0f));
	TestTrue(TEXT("A chance above one always succeeds"), Seeds->RollChance(RunSeedChannels::BloomRolls, 5.0f));
	TestEqual(TEXT("Certain outcomes consume no randomness"),
		Seeds->GetChannelDrawCount(RunSeedChannels::BloomRolls), Before);

	// An inverted range is a caller mistake, but returning nonsense quietly is worse than clamping:
	// a silently wrong count is far harder to trace back than an obviously ordered one.
	for (int32 Index = 0; Index < 20; ++Index)
	{
		const int32 Value = Seeds->RandRange(RunSeedChannels::JumpGeneration, 10, 2);
		TestTrue(TEXT("An inverted range still returns a value inside it"), Value >= 2 && Value <= 10);
	}

	// Ranges hold.
	for (int32 Index = 0; Index < 50; ++Index)
	{
		const float Fraction = Seeds->FRand(RunSeedChannels::JumpFate);
		TestTrue(TEXT("FRand stays within [0,1)"), Fraction >= 0.0f && Fraction < 1.0f);

		const float Ranged = Seeds->FRandRange(RunSeedChannels::JumpFate, -3.0f, 7.0f);
		TestTrue(TEXT("FRandRange stays within its bounds"), Ranged >= -3.0f && Ranged <= 7.0f);
	}

	// Rewinding one channel must put it back exactly, and leave the others where they were.
	URunSeedSubsystem* Rewind = MakeSeeds(1357);
	const TArray<float> Original = DrawSequence(Rewind, RunSeedChannels::JumpGeneration, 8);
	DrawSequence(Rewind, RunSeedChannels::Falsification, 8);

	Rewind->ResetChannel(RunSeedChannels::JumpGeneration);
	TestEqual(TEXT("A reset channel replays from the beginning"),
		DrawSequence(Rewind, RunSeedChannels::JumpGeneration, 8), Original);
	TestEqual(TEXT("A reset channel restarts its draw count"),
		Rewind->GetChannelDrawCount(RunSeedChannels::JumpGeneration), 8);

	return true;
}

#endif
