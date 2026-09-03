#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UiSoundSubsystem.generated.h"

class USoundBase;

/**
 * What the interface sounds like.
 *
 * Named for the moment rather than for the sound, so a caller says what happened and this decides
 * what it sounds like. The alternative -- callers naming cue assets -- spreads asset paths through
 * gameplay code and makes changing the palette a search-and-replace.
 */
UENUM(BlueprintType)
enum class EUiSoundEvent : uint8
{
	/** A prompt appears, an option is selected. The smallest sound in the set. */
	Select,

	/** Something the player did worked: an activity completed, an obstruction cleared. */
	Confirm,

	/** Something the player did failed. Distinct from Warning, which is the ship's opinion. */
	Reject,

	/** A mission objective completed. Bigger than Confirm because it is rarer. */
	ObjectiveComplete,

	/** The ship reporting a problem: a status effect landing, a system failing. */
	Warning,

	/** The Bloom, or anything that should feel wrong. */
	Corruption
};

/**
 * Plays the interface's non-diegetic sounds.
 *
 * The project owns 786 UI cues in SciFiUISFX and used none of them -- the same shape as the eleven
 * cryo materials with two wired, and the HUD's interaction prompt panel that nothing ever filled.
 * A demo recorded for a grant is watched *and heard*, and silence on every interaction is a thing
 * reviewers notice without being able to say why.
 *
 * A GameInstance subsystem rather than a component: UI sound is 2D, has no position, and should not
 * die with a pawn. Cues resolve lazily and cache, so a missing asset costs one failed load and a
 * warning rather than a hitch per press.
 */
UCLASS()
class GINNUNGAGAP_API UUiSoundSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Plays the cue mapped to an event. Silently does nothing if the cue is missing. */
	UFUNCTION(BlueprintCallable, Category = "UI|Sound")
	void PlayUiSound(EUiSoundEvent Event);

	/**
	 * The asset path an event maps to. Exposed so a test can assert every event resolves without
	 * needing an audio device -- which is what a headless run has.
	 */
	UFUNCTION(BlueprintPure, Category = "UI|Sound")
	static FString GetCuePathForEvent(EUiSoundEvent Event);

	/** Loads and caches a cue. Public so a test can check resolution without playing anything. */
	USoundBase* ResolveCue(EUiSoundEvent Event);

private:
	UPROPERTY(Transient)
	TMap<EUiSoundEvent, TObjectPtr<USoundBase>> CueCache;

	/** Events whose cue failed to load, so the warning is logged once rather than per press. */
	TSet<EUiSoundEvent> FailedEvents;
};
