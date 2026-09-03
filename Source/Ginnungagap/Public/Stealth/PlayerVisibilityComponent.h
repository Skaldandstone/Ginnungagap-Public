#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Bloom/BloomDirector.h"
#include "PlayerVisibilityComponent.generated.h"

/**
 * How easy this actor is to see right now, as a single 0..1 multiplier applied on top of the
 * observer's own distance and angle checks.
 *
 * Deliberately derived from gameplay state rather than from rendering. Querying actual scene
 * luminance would be expensive, unavailable on a dedicated server, and impossible to reason about
 * as a designer. Instead darkness comes from the ship's own power state: an unpowered room is
 * dark, which turns "cut the lights" into a real stealth verb built on systems that already exist
 * (UShipPowerGridSubsystem, AModularShipRoom::bPowered) rather than a parallel lighting model.
 *
 * Evaluated on the authority as part of AI perception. Nothing here is client-authoritative.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPlayerVisibilityComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPlayerVisibilityComponent();

    /**
     * Combined 0..1 visibility. 1.0 means "fully exposed": lit room, moving normally.
     * Lower values make an observer take proportionally longer to notice this actor.
     */
    UFUNCTION(BlueprintPure, Category = "Stealth")
    float GetVisibilityMultiplier() const;

    /** Light contribution alone, for HUD tells and debugging. */
    UFUNCTION(BlueprintPure, Category = "Stealth")
    float GetLightExposure() const;

    /** Movement contribution alone, for HUD tells and debugging. */
    UFUNCTION(BlueprintPure, Category = "Stealth")
    float GetMovementExposure() const;

    /**
     * Tells the Bloom which evasion tactics this actor is currently relying on. Called by an
     * observer that is actually perceiving this actor, so a tactic only counts when used against
     * something -- see ReportActiveTacticsToBloom's note on why standing in the dark alone should
     * teach the organism nothing.
     */
    void ReportActiveTacticsToBloom() const;

    /** Current effectiveness of a tactic, or 1.0 where no Bloom director exists. */
    float GetTacticEffectiveness(EBloomStealthTactic Tactic) const;

    /** Visibility multiplier while standing in an unpowered (dark) room. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Light", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float DarkroomVisibility = 0.35f;

    /**
     * Visibility multiplier when effectively motionless. Holding still is the cheapest stealth
     * option available to a player with no dedicated crouch verb.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float StillVisibility = 0.55f;

    /** Speed at or below which the actor counts as motionless. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "0.0"))
    float StillSpeedThreshold = 40.0f;

    /** Speed at or above which the actor is fully exposed by motion. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "1.0"))
    float FullyVisibleSpeed = 450.0f;

    /**
     * Floor on the combined multiplier. Never zero: a player standing perfectly still in a dark
     * room should be very hard to notice, but total invisibility reads as a bug rather than as
     * stealth, and leaves no counterplay for the AI.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.01", ClampMax = "1.0"))
    float MinimumVisibility = 0.12f;
};
