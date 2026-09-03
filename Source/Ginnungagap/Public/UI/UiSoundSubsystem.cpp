#include "UI/UiSoundSubsystem.h"

#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

FString UUiSoundSubsystem::GetCuePathForEvent(EUiSoundEvent Event)
{
	// Chosen by category rather than by audition, and that limit is worth stating: these were picked
	// from a pack of 786 cues by what the folders promise, not by listening. The folders are
	// semantic -- Clicks, Impacts, Rings, Glitches -- so the mapping is defensible, but anyone with
	// speakers should second-guess the specific files.
	//
	// The shape of the palette is the part that is not guesswork. Select is the smallest sound
	// because it happens constantly; ObjectiveComplete is the largest because it happens five times
	// in the demo; Reject and Warning are deliberately different sounds because one is the player
	// failing and the other is the ship complaining, and a player needs to tell those apart without
	// looking.
	static const TCHAR* Root = TEXT("/Game/SciFiUISFX/Cues/");

	switch (Event)
	{
	case EUiSoundEvent::Select:
		return FString(Root) + TEXT("Clicks/Click_Low_Cue.Click_Low_Cue");
	case EUiSoundEvent::Confirm:
		return FString(Root) + TEXT("Clicks/Click_2_Cue.Click_2_Cue");
	case EUiSoundEvent::Reject:
		return FString(Root) + TEXT("Impacts/Impact_1_Low_Cue.Impact_1_Low_Cue");
	case EUiSoundEvent::ObjectiveComplete:
		return FString(Root) + TEXT("Rings/Reverse_Ring_2_Cue.Reverse_Ring_2_Cue");
	case EUiSoundEvent::Warning:
		return FString(Root) + TEXT("Impacts/Impact_2_Mid_Cue.Impact_2_Mid_Cue");
	case EUiSoundEvent::Corruption:
		return FString(Root) + TEXT("Glitches/Glitch_10_Cue.Glitch_10_Cue");
	}
	return FString();
}

USoundBase* UUiSoundSubsystem::ResolveCue(EUiSoundEvent Event)
{
	if (const TObjectPtr<USoundBase>* Cached = CueCache.Find(Event))
	{
		return Cached->Get();
	}

	// Already known bad. Returning early keeps a missing asset to one warning for the life of the
	// run instead of one per keypress, which is the difference between a note and a flooded log.
	if (FailedEvents.Contains(Event))
	{
		return nullptr;
	}

	const FString Path = GetCuePathForEvent(Event);
	USoundBase* Cue = Path.IsEmpty() ? nullptr : LoadObject<USoundBase>(nullptr, *Path);

	if (!Cue)
	{
		FailedEvents.Add(Event);
		UE_LOG(LogTemp, Warning, TEXT("UI sound missing for event %d at %s"),
			static_cast<int32>(Event), *Path);
		return nullptr;
	}

	CueCache.Add(Event, Cue);
	return Cue;
}

void UUiSoundSubsystem::PlayUiSound(EUiSoundEvent Event)
{
	USoundBase* Cue = ResolveCue(Event);
	if (!Cue)
	{
		return;
	}

	// 2D, so it has no position and does not attenuate. Interface sound is not in the world; a
	// confirmation tone that got quieter as the player walked away from a console would be a bug.
	UGameplayStatics::PlaySound2D(GetGameInstance(), Cue);
}
