// Copyright Epic Games, Inc. All Rights Reserved.

#include "Meta/RunSeedSubsystem.h"

#include "Misc/DateTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogRunSeed, Log, All);

void URunSeedSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Seed immediately rather than waiting for a run to start. Anything that draws before then
	// would otherwise fall back to an unseeded stream and be irreproducible, which is exactly the
	// failure this subsystem exists to remove.
	SeedRun(0);
}

int32 URunSeedSubsystem::SeedRun(int32 InSeed)
{
	// A caller-supplied seed of 0 means "pick one". Deriving it from the clock keeps normal runs
	// varied, and logging it keeps them reproducible after the fact -- which matters more, because
	// nobody knows a run is worth reproducing until it has already gone wrong.
	RunSeed = InSeed != 0 ? InSeed : static_cast<int32>(FDateTime::UtcNow().GetTicks() & 0x7FFFFFFF);
	if (RunSeed == 0)
	{
		RunSeed = 1;
	}

	Channels.Empty();

	// The command named here is the one that exists: SeedRun on the survival player controller.
	// A log line advertising a command nobody can run is worse than no line at all.
	UE_LOG(LogRunSeed, Log, TEXT("Run seed %d (%s). Reproduce with console command: SeedRun %d"),
		RunSeed, InSeed != 0 ? TEXT("explicit") : TEXT("generated"), RunSeed);

	return RunSeed;
}

int32 URunSeedSubsystem::DeriveChannelSeed(FName Channel) const
{
	// Hashing the name means a channel's stream does not depend on when it was first used, so
	// touching a new system mid-run cannot shift an existing one.
	const uint32 Combined = HashCombine(static_cast<uint32>(RunSeed), GetTypeHash(Channel));
	const int32 Derived = static_cast<int32>(Combined & 0x7FFFFFFF);
	return Derived != 0 ? Derived : 1;
}

URunSeedSubsystem::FChannelState& URunSeedSubsystem::GetChannel(FName Channel)
{
	if (FChannelState* Existing = Channels.Find(Channel))
	{
		return *Existing;
	}

	FChannelState State;
	State.InitialSeed = DeriveChannelSeed(Channel);
	State.Stream.Initialize(State.InitialSeed);
	return Channels.Add(Channel, State);
}

float URunSeedSubsystem::FRand(FName Channel)
{
	FChannelState& State = GetChannel(Channel);
	++State.DrawCount;
	return State.Stream.GetFraction();
}

float URunSeedSubsystem::FRandRange(FName Channel, float Min, float Max)
{
	FChannelState& State = GetChannel(Channel);
	++State.DrawCount;
	return State.Stream.FRandRange(Min, Max);
}

int32 URunSeedSubsystem::RandRange(FName Channel, int32 Min, int32 Max)
{
	// Guard the inverted range rather than trusting callers: FRandomStream::RandRange on Max < Min
	// returns nonsense quietly, and a silently wrong count is far harder to trace than a clamp.
	if (Max < Min)
	{
		Swap(Min, Max);
	}

	FChannelState& State = GetChannel(Channel);
	++State.DrawCount;
	return State.Stream.RandRange(Min, Max);
}

bool URunSeedSubsystem::RollChance(FName Channel, float Chance)
{
	// A chance of zero or less must never succeed and one or more must never fail, without
	// consuming a draw -- otherwise a disabled mechanic still shifts every later roll on its
	// channel, and turning a feature off changes an unrelated outcome.
	if (Chance <= 0.0f)
	{
		return false;
	}
	if (Chance >= 1.0f)
	{
		return true;
	}

	return FRand(Channel) < Chance;
}

void URunSeedSubsystem::ResetChannel(FName Channel)
{
	FChannelState& State = GetChannel(Channel);
	State.Stream.Initialize(State.InitialSeed);
	State.DrawCount = 0;
}

int32 URunSeedSubsystem::GetChannelDrawCount(FName Channel) const
{
	const FChannelState* State = Channels.Find(Channel);
	return State ? State->DrawCount : 0;
}
