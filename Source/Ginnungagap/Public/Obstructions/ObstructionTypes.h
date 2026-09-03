#pragma once

#include "CoreMinimal.h"
#include "ObstructionTypes.generated.h"

/**
 * The ways past something in the way.
 *
 * From James's direction: an obstruction "could be destructible (risks damaging the ship and nearby
 * systems), it could be cut through, a hole can be made to squeeze through, the player can redirect
 * around it, in most cases, though we probably want some cases where they do have to go through it."
 *
 * Each verb is a different bad trade rather than a different amount of the same one. That is the
 * whole design: a blockage with one answer is a locked door with extra steps, and a blockage whose
 * answers differ only in duration is a menu of waiting.
 */
UENUM(BlueprintType)
enum class EObstructionVerb : uint8
{
	/** Blow it. Fastest and loudest, and it damages whatever ship systems are standing nearby. */
	Breach,

	/** Cut through. Quiet-ish and slow, spends tool condition, and worn gear can burn the welder. */
	Cut,

	/** Squeeze past. Needs a gap and a light load; getting most of the way through and stuck is its
	    own cost, and the one the player will remember. */
	Squeeze
};

/**
 * What one verb costs at one obstruction.
 *
 * Per-instance rather than per-verb-global, because the same verb should mean different things in
 * different places: cutting a thin panel is not cutting a structural rib, and the level is where
 * that difference lives.
 */
USTRUCT(BlueprintType)
struct FObstructionVerbOption
{
	GENERATED_BODY()

	/** Whether this obstruction can be passed this way at all. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction")
	bool bAllowed = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0"))
	float DurationSeconds = 6.0f;

	/**
	 * Equipment condition needed to attempt this, 0..1.
	 *
	 * A floor rather than a switch. Below it the verb is refused outright; above it the verb is
	 * allowed and may still go wrong, which is what makes worn gear a risk the player is taking
	 * rather than a door the game has locked.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MinimumEquipmentCondition = 0.0f;

	/** How loud this is, on the noise subsystem's 0..1 scale. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0", ClampMax="1.0"))
	float NoiseLoudness = 0.4f;

	/** Ship systems within this radius take collateral damage. Breach only, in practice. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0"))
	float CollateralRadius = 0.0f;

	/** How much of a nearby system this ruins, 0..1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0", ClampMax="1.0"))
	float CollateralSeverity = 0.0f;

	/**
	 * Chance the player nearly does not get through, 0..1. Squeeze only.
	 *
	 * "Nearly" is the point -- this is not a fail state, it is the near miss that feeds acute
	 * stress. A squeeze that can kill you is a trap; a squeeze that can frighten you is a corridor.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction", meta=(ClampMin="0.0", ClampMax="1.0"))
	float NearEntrapmentChance = 0.0f;
};

/**
 * Why a verb is not available right now.
 *
 * Returned rather than a bare bool so the prompt can say what is wrong. "You cannot cut this" tells
 * a player nothing; "your gear is too worn to cut" tells them what to go and fix.
 */
UENUM(BlueprintType)
enum class EObstructionRefusal : uint8
{
	None,
	/** This obstruction cannot be passed that way at all. */
	NotPossibleHere,
	/** Possible, but the player's equipment is in no state for it. */
	EquipmentTooWorn,
	/** Already dealt with. */
	AlreadyCleared
};
