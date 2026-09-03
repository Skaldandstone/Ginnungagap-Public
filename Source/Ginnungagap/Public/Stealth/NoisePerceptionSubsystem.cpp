#include "Stealth/NoisePerceptionSubsystem.h"

#include "Engine/World.h"
#include "CollisionQueryParams.h"

void UNoisePerceptionSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    ActiveNoise.Reserve(MaxTrackedNoiseEvents);
}

void UNoisePerceptionSubsystem::ReportNoise(const FVector& Location, float Loudness,
    ENoiseCategory Category, AActor* Instigator)
{
    UWorld* World = GetWorld();
    if (!World || Loudness < MinimumReportableLoudness)
    {
        return;
    }

    // Stealth must resolve identically for every client, so only the server records stimuli.
    if (World->GetNetMode() == NM_Client)
    {
        return;
    }

    PruneExpiredNoise();

    const float Now = World->GetTimeSeconds();

    // Continuous sources (footsteps, a live microphone) would otherwise push an event every tick.
    // Collapse to one entry per instigator+category, keeping whichever is louder while fresh.
    if (Instigator)
    {
        for (FNoiseEvent& Existing : ActiveNoise)
        {
            if (Existing.Instigator.Get() == Instigator && Existing.Category == Category)
            {
                Existing.Location = Location;
                Existing.Loudness = FMath::Max(Existing.Loudness, Loudness);
                Existing.WorldTimeSeconds = Now;
                return;
            }
        }
    }

    if (ActiveNoise.Num() >= MaxTrackedNoiseEvents)
    {
        // Full: evict the quietest entry rather than the oldest, so a loud gunshot is never
        // dropped in favour of a stale footstep.
        int32 QuietestIndex = 0;
        for (int32 Index = 1; Index < ActiveNoise.Num(); ++Index)
        {
            if (ActiveNoise[Index].Loudness < ActiveNoise[QuietestIndex].Loudness)
            {
                QuietestIndex = Index;
            }
        }
        if (ActiveNoise[QuietestIndex].Loudness >= Loudness)
        {
            return;
        }
        ActiveNoise.RemoveAtSwap(QuietestIndex);
    }

    FNoiseEvent Event;
    Event.Location = Location;
    Event.Loudness = FMath::Clamp(Loudness, 0.0f, 1.0f);
    Event.Category = Category;
    Event.Instigator = Instigator;
    Event.WorldTimeSeconds = Now;
    ActiveNoise.Add(Event);
}

bool UNoisePerceptionSubsystem::QueryLoudestAudibleNoise(const FVector& ListenerLocation,
    float HearingRangeScale, AActor* ListenerToIgnore, FNoiseEvent& OutNoise,
    float& OutPerceivedStrength) const
{
    const UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    const float Now = World->GetTimeSeconds();
    const float SafeScale = FMath::Max(HearingRangeScale, KINDA_SMALL_NUMBER);

    bool bFound = false;
    float BestStrength = 0.0f;

    for (const FNoiseEvent& Event : ActiveNoise)
    {
        const float Age = Now - Event.WorldTimeSeconds;
        if (Age > NoiseMemorySeconds)
        {
            continue;
        }
        if (ListenerToIgnore && Event.Instigator.Get() == ListenerToIgnore)
        {
            continue;
        }

        const float AudibleRadius = Event.Loudness * MaxPropagationDistance * SafeScale;
        if (AudibleRadius <= KINDA_SMALL_NUMBER)
        {
            continue;
        }

        const float Distance = FVector::Dist(ListenerLocation, Event.Location);
        if (Distance > AudibleRadius)
        {
            continue;
        }

        // Linear falloff to the audible edge, then fade with age so a listener naturally loses
        // interest instead of snapping from "certain" to "forgotten".
        float Strength = 1.0f - (Distance / AudibleRadius);
        Strength *= 1.0f - FMath::Clamp(Age / NoiseMemorySeconds, 0.0f, 1.0f);

        if (Strength > BestStrength && IsPathOccluded(Event.Location, ListenerLocation, ListenerToIgnore))
        {
            Strength *= OcclusionAttenuation;
        }

        if (Strength > BestStrength && Strength >= AudibilityThreshold)
        {
            BestStrength = Strength;
            OutNoise = Event;
            bFound = true;
        }
    }

    OutPerceivedStrength = BestStrength;
    return bFound;
}

void UNoisePerceptionSubsystem::PruneExpiredNoise()
{
    const UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    const float Now = World->GetTimeSeconds();
    ActiveNoise.RemoveAll([this, Now](const FNoiseEvent& Event)
    {
        return (Now - Event.WorldTimeSeconds) > NoiseMemorySeconds;
    });
}

bool UNoisePerceptionSubsystem::IsPathOccluded(const FVector& From, const FVector& To,
    AActor* ActorToIgnore) const
{
    const UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    FCollisionQueryParams Params(SCENE_QUERY_STAT(NoiseOcclusion), /*bTraceComplex=*/false);
    if (ActorToIgnore)
    {
        Params.AddIgnoredActor(ActorToIgnore);
    }

    // Static geometry only: a crew member standing in the doorway should not muffle the noise
    // behind them, and pawns move too often for that to read as a consistent rule anyway.
    return World->LineTraceTestByChannel(From, To, ECC_WorldStatic, Params);
}
