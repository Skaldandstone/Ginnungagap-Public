#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Stealth/StealthTypes.h"
#include "NoisePerceptionSubsystem.generated.h"

/**
 * Server-authoritative record of recent noise in the world, plus the rules for who can hear what.
 *
 * Noise is reported as fire-and-forget world events and decays on its own. Listeners pull with
 * QueryLoudestAudibleNoise rather than being pushed to, so distance falloff, occlusion, and decay
 * live in exactly one place instead of being re-implemented per AI controller.
 */
UCLASS()
class GINNUNGAGAP_API UNoisePerceptionSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /**
     * Record a noise at a world location. Safe to call every frame; sub-threshold noise is
     * discarded and repeat noise from the same instigator coalesces instead of flooding the list.
     * Authority only -- clients reporting noise directly would let a modified client fake or
     * suppress stimuli for everyone.
     */
    UFUNCTION(BlueprintCallable, Category = "Stealth")
    void ReportNoise(const FVector& Location, float Loudness, ENoiseCategory Category, AActor* Instigator);

    /**
     * Find the most attention-worthy noise this listener can currently hear.
     * Returns false when nothing is audible. Ranks by perceived strength after falloff and
     * occlusion, not raw loudness, so a quiet noise next door beats a loud one across the ship.
     */
    UFUNCTION(BlueprintCallable, Category = "Stealth")
    bool QueryLoudestAudibleNoise(const FVector& ListenerLocation, float HearingRangeScale,
        AActor* ListenerToIgnore, FNoiseEvent& OutNoise, float& OutPerceivedStrength) const;

    /** Distance in cm at which a Loudness of exactly 1.0 stops being audible. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "100.0"))
    float MaxPropagationDistance = 4000.0f;

    /** How long a reported noise stays in the list before it is forgotten. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.1"))
    float NoiseMemorySeconds = 6.0f;

    /** Noise quieter than this is never recorded, keeping idle movement from spamming the list. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0"))
    float MinimumReportableLoudness = 0.05f;

    /** Multiplier applied when geometry blocks the straight line between noise and listener. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float OcclusionAttenuation = 0.45f;

    /** Perceived strength below this is treated as inaudible after falloff and occlusion. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float AudibilityThreshold = 0.08f;

private:
    /** Drops events older than NoiseMemorySeconds. Called on report so the list self-limits. */
    void PruneExpiredNoise();

    /** True when static geometry blocks the direct path, used for the occlusion penalty. */
    bool IsPathOccluded(const FVector& From, const FVector& To, AActor* ActorToIgnore) const;

    UPROPERTY()
    TArray<FNoiseEvent> ActiveNoise;

    /**
     * A single instigator collapses to one live entry. Without this, continuous sources like
     * footsteps or a held microphone would push a new event every tick and starve older,
     * more significant noise out of the list.
     */
    static constexpr int32 MaxTrackedNoiseEvents = 64;
};
