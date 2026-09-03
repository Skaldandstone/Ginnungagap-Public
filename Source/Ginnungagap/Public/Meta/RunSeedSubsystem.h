#pragma once

#include "CoreMinimal.h"
#include "Math/RandomStream.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "RunSeedSubsystem.generated.h"

/**
 * Named draw channels. Each gets its own stream from the run seed.
 *
 * Separate streams rather than one shared source, because a single stream makes seeds nearly
 * useless for reproduction: adding one extra roll anywhere shifts every later draw in the run, so a
 * seed stops reproducing the bug the moment anything unrelated changes. Per-channel streams mean a
 * change to jump generation cannot move a Bloom roll.
 *
 * Adding a channel is safe. Reordering or renaming one is not -- the hash of the name is what fixes
 * the stream, so an existing seed stops reproducing what it used to.
 */
namespace RunSeedChannels
{
	/** Candidate systems, their hazards, resources and danger tiers. */
	const FName JumpGeneration(TEXT("JumpGeneration"));

	/** Whether a destination reading is falsified. */
	const FName Falsification(TEXT("Falsification"));

	/** What happens to each character during a jump: cryo, no pod, EVA, landing error. */
	const FName JumpFate(TEXT("JumpFate"));

	/** Bloom sabotage and self-destruct counter rolls. */
	const FName BloomRolls(TEXT("BloomRolls"));

	/** Where arrival actors, hazards and resource nodes get placed. */
	const FName ArrivalPlacement(TEXT("ArrivalPlacement"));
}

/**
 * The single source of run randomness, so a run can be reproduced from one number.
 *
 * Systems draw from a named channel instead of calling FMath::FRand directly. Nothing forces this
 * -- global random still works -- but any call site that bypasses the subsystem is a call site that
 * makes its run irreproducible, which is the whole thing this exists to prevent.
 *
 * The seed is logged whenever it is set, so the number needed to reproduce a run is in the log of
 * the run that went wrong rather than something someone has to have thought to capture in advance.
 */
UCLASS()
class GINNUNGAGAP_API URunSeedSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/**
	 * Seeds a new run and resets every channel.
	 *
	 * Pass 0 to draw a fresh seed from the clock, which is what a normal run does. The chosen seed
	 * is returned and logged either way, so an unseeded run is still reproducible after the fact.
	 */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	int32 SeedRun(int32 InSeed = 0);

	/** The seed this run is using. */
	UFUNCTION(BlueprintPure, Category = "Run|Seed")
	int32 GetRunSeed() const { return RunSeed; }

	/** A float in [0,1) from a channel. Replaces FMath::FRand. */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	float FRand(FName Channel);

	/** A float in [Min,Max] from a channel. Replaces FMath::FRandRange. */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	float FRandRange(FName Channel, float Min, float Max);

	/** An int in [Min,Max] inclusive from a channel. Replaces FMath::RandRange. */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	int32 RandRange(FName Channel, int32 Min, int32 Max);

	/**
	 * Rewinds one channel to where it started this run, leaving the others untouched.
	 *
	 * For tests and for reproducing a single decision without replaying everything that led to it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	void ResetChannel(FName Channel);

	/** How many draws a channel has served this run. Useful when a repro stops lining up. */
	UFUNCTION(BlueprintPure, Category = "Run|Seed")
	int32 GetChannelDrawCount(FName Channel) const;

	/** Convenience for the common "did this chance succeed" roll. */
	UFUNCTION(BlueprintCallable, Category = "Run|Seed")
	bool RollChance(FName Channel, float Chance);

private:
	/** A channel's stream plus the bookkeeping that makes a mismatch diagnosable. */
	struct FChannelState
	{
		FRandomStream Stream;
		int32 InitialSeed = 0;
		int32 DrawCount = 0;
	};

	FChannelState& GetChannel(FName Channel);

	/**
	 * Channel seed is derived from the run seed and the channel name, so every channel is
	 * reproducible from the one number and no channel depends on the order channels were first
	 * touched.
	 */
	int32 DeriveChannelSeed(FName Channel) const;

	UPROPERTY()
	int32 RunSeed = 0;

	TMap<FName, FChannelState> Channels;
};
