#pragma once

#include "CoreMinimal.h"
#include "CharacterProfile.generated.h"

UENUM(BlueprintType)
enum class ECharacterAppearance : uint8
{
	Default,        // Standard suit color
	ArcticCamo,     // White/light blue (cold theme)
	DeepSea,        // Dark blue/black (stealth theme)
	Hazmat,         // Yellow/orange (hazard theme)
	Veteran,        // Scarred/battle-worn (cosmetic variant)
	Specter         // Translucent/ghostly (rare cosmetic)
};

UENUM(BlueprintType)
enum class EPressureSuitRole : uint8
{
	// Was "Standard Crew", which was not a job. The General tree already covers what any berth
	// holder has done -- its own comment says so -- so a Crew class was the shared tree twice, and
	// the one specialism the ship actually needs had nowhere to live. Science was previously bolted
	// onto Medical's display name and had no skills of its own.
	//
	// Kept at index 0 so existing saved profiles and placed actors still resolve to the same slot.
	Scientist   UMETA(DisplayName="Science"),
	Engineering UMETA(DisplayName="Engineering"),
	Medical     UMETA(DisplayName="Medical"),
	Security    UMETA(DisplayName="Security / Recovery")
};

/**
 * The role a character starts as before anyone chooses otherwise.
 *
 * Declared once because eight separate headers used to carry their own copy of this default, all
 * of which silently changed meaning together when the enum's first entry was renamed. A default
 * that lives in eight places is eight places to disagree.
 *
 * Engineering because the demo is engineering work end to end -- restore power, seal the breach,
 * patch worn gear -- so a character who starts as anything else is doing someone else's job for
 * the whole run.
 */
namespace GinnungagapDefaults
{
	constexpr EPressureSuitRole StartingSuitRole = EPressureSuitRole::Engineering;
}

UENUM(BlueprintType)
enum class ECharacterBodyPreset : uint8 { Light, Average, Broad, Heavy };
UENUM(BlueprintType)
enum class ECharacterFacePreset : uint8
{
	Face01, Face02, Face03, Face04, Face05, Face06,
	Face07, Face08, Face09, Face10, Face11, Face12
};
UENUM(BlueprintType)
enum class ECharacterSkinTone : uint8 { Tone01, Tone02, Tone03, Tone04, Tone05, Tone06, Tone07, Tone08 };
UENUM(BlueprintType)
enum class ECharacterHairStyle : uint8 { Shaved, Short, Medium, Long, Braided, Covered };
UENUM(BlueprintType)
enum class ECharacterVoiceProfile : uint8 { Voice01, Voice02, Voice03, Voice04 };

USTRUCT(BlueprintType)
struct FCharacterProfile
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Character")
	FString CharacterName = "Unnamed";

	UPROPERTY(BlueprintReadWrite, Category = "Character")
	ECharacterAppearance AppearanceVariant = ECharacterAppearance::Default;

	UPROPERTY(BlueprintReadWrite, Category = "Character")
	EPressureSuitRole SuitRole = GinnungagapDefaults::StartingSuitRole;

	/** Stable library identifier; resolved to an assembled MetaHuman Blueprint at runtime. */
	UPROPERTY(BlueprintReadWrite, Category = "Character")
	FName MetaHumanPresetId = TEXT("PlayerFace01");

	UPROPERTY(BlueprintReadWrite, Category = "Character|Identity")
	ECharacterBodyPreset BodyPreset = ECharacterBodyPreset::Average;
	UPROPERTY(BlueprintReadWrite, Category = "Character|Identity")
	ECharacterFacePreset FacePreset = ECharacterFacePreset::Face01;
	UPROPERTY(BlueprintReadWrite, Category = "Character|Identity")
	ECharacterSkinTone SkinTone = ECharacterSkinTone::Tone04;
	UPROPERTY(BlueprintReadWrite, Category = "Character|Identity")
	ECharacterHairStyle HairStyle = ECharacterHairStyle::Short;
	UPROPERTY(BlueprintReadWrite, Category = "Character|Identity")
	ECharacterVoiceProfile VoiceProfile = ECharacterVoiceProfile::Voice01;

	UPROPERTY(BlueprintReadWrite, Category = "Character")
	bool bHasBeenCreated = false;
};

/**
 * MetaHumanPresetId ("PlayerFaceNN") and FacePreset (Face01..Face12) are two independently-built
 * encodings of the same underlying choice: which of the 12 MetaHuman source faces the character
 * uses. Character-creation UI should keep both fields in sync via these helpers, regardless of
 * which preset it lets the player pick from directly, so any downstream code that resolves either
 * field sees the player's actual selection.
 */
inline FName MetaHumanPresetIdFromFacePreset(ECharacterFacePreset FacePreset)
{
	return FName(*FString::Printf(TEXT("PlayerFace%02d"), static_cast<int32>(FacePreset) + 1));
}

inline ECharacterFacePreset FacePresetFromMetaHumanPresetId(FName PresetId)
{
	const FString Value = PresetId.ToString();
	const int32 Index = FCString::Atoi(*Value.Right(2));
	const int32 Clamped = FMath::Clamp(Index, 1, 12);
	return static_cast<ECharacterFacePreset>(Clamped - 1);
}
