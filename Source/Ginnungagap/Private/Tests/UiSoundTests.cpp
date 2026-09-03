#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Sound/SoundBase.h"
#include "UObject/UObjectGlobals.h"

#include "UI/UiSoundSubsystem.h"

/**
 * That every interface sound actually exists.
 *
 * The project owns 786 UI cues in SciFiUISFX and used none of them until now, which is the same
 * shape as the eleven cryo materials with two wired and the HUD prompt panel nothing ever filled.
 * Having wired six, the failure mode worth guarding is a path typo: a cue that does not resolve
 * plays nothing, logs one warning, and is otherwise indistinguishable from an interface that is
 * simply quiet.
 *
 * Asserts resolution rather than playback. A headless run has no audio device, and whether a sound
 * is audible is not something a test can judge -- whether the asset is there is.
 *
 * Deliberately not asserting *which* cue each event maps to. Those were chosen from folder names
 * rather than by listening, so they should be free to change once somebody has heard them; pinning
 * the filenames here would make an improvement look like a regression.
 */

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGinnungagapUiSoundCuesResolveTest,
	"Ginnungagap.UI.UiSoundCuesResolve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FGinnungagapUiSoundCuesResolveTest::RunTest(const FString& Parameters)
{
	const EUiSoundEvent Events[] = {
		EUiSoundEvent::Select,
		EUiSoundEvent::Confirm,
		EUiSoundEvent::Reject,
		EUiSoundEvent::ObjectiveComplete,
		EUiSoundEvent::Warning,
		EUiSoundEvent::Corruption,
	};

	TSet<FString> SeenPaths;

	for (EUiSoundEvent Event : Events)
	{
		const FString Path = UUiSoundSubsystem::GetCuePathForEvent(Event);

		TestFalse(FString::Printf(TEXT("Event %d has a cue path"), static_cast<int32>(Event)),
			Path.IsEmpty());
		if (Path.IsEmpty())
		{
			continue;
		}

		USoundBase* Cue = LoadObject<USoundBase>(nullptr, *Path);
		TestNotNull(FString::Printf(TEXT("Event %d resolves to a real sound asset (%s)"),
			static_cast<int32>(Event), *Path), Cue);

		SeenPaths.Add(Path);
	}

	// Distinct sounds per event, which is the design rather than an accident. Reject and Warning in
	// particular have to differ: one is the player failing and the other is the ship complaining,
	// and a player mid-repair is listening rather than looking.
	// Cast the array count: UE_ARRAY_COUNT yields size_t and TestEqual has no overload that can pick
	// between int32 and the unsigned conversions without ambiguity.
	TestEqual(TEXT("Every event has its own cue rather than sharing one"),
		SeenPaths.Num(), static_cast<int32>(UE_ARRAY_COUNT(Events)));

	return true;
}

#endif
