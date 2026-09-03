#pragma once

#include "CoreMinimal.h"
#include "StealthTypes.generated.h"

/** What produced a noise. Categories let AI and UI react differently to the same loudness. */
UENUM(BlueprintType)
enum class ENoiseCategory : uint8
{
    /** Footsteps, magnetic boot clamps, brushing past geometry. */
    Movement,
    /** Player voice picked up by an opted-in microphone, or in-fiction radio chatter. */
    Voice,
    /** Dropped or thrown objects, collisions, breaking glass. */
    Impact,
    /** Repair tools, welding, activity stations. */
    Tool,
    /** Weapon discharge. Loud and unambiguous. */
    Weapon,
    /** Alarms, venting atmosphere, machinery failure. Not attributable to a crew member. */
    Environment
};

/** How much an AI currently knows about a target. Drives behavior and player-facing tells. */
UENUM(BlueprintType)
enum class EEnemyAwareness : uint8
{
    /** No current stimulus. Patrolling normally. */
    Unaware,
    /** Heard something but has no confirmed target. Moves to investigate the last noise. */
    Suspicious,
    /** Has a confirmed visible target and is actively pursuing. */
    Alert
};

/**
 * A single reported noise. Noise is a world event, not an actor: it is reported once at a
 * location, then decays. Listeners query for what they can currently hear rather than being
 * pushed to, so hearing rules stay in one place.
 */
USTRUCT(BlueprintType)
struct FNoiseEvent
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Stealth")
    FVector Location = FVector::ZeroVector;

    /**
     * Abstract 0..1 scale. 1.0 means "audible at the subsystem's maximum propagation distance";
     * 0.25 means audible at a quarter of it. Not decibels, and deliberately not tied to the
     * audio engine's mix so design can tune stealth without touching sound assets.
     */
    UPROPERTY(BlueprintReadOnly, Category = "Stealth")
    float Loudness = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Stealth")
    ENoiseCategory Category = ENoiseCategory::Movement;

    /** Who made the noise. May be null for environmental noise with no responsible actor. */
    UPROPERTY(BlueprintReadOnly, Category = "Stealth")
    TWeakObjectPtr<AActor> Instigator = nullptr;

    /** World seconds when reported. Used for decay and for preferring fresher stimuli. */
    UPROPERTY(BlueprintReadOnly, Category = "Stealth")
    float WorldTimeSeconds = 0.0f;
};
