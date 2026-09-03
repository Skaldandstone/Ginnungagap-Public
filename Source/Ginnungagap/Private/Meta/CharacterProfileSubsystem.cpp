#include "Meta/CharacterProfileSubsystem.h"
#include "Meta/CharacterProfileSave.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	const FName DefaultMetaHumanPreset(TEXT("PlayerFace01"));

	bool IsValidMetaHumanPresetId(const FName PresetId)
	{
		const FString Value = PresetId.ToString();
		if (!Value.StartsWith(TEXT("PlayerFace")) || Value.Len() > 32)
		{
			return false;
		}
		for (const TCHAR Character : Value)
		{
			if (!FChar::IsAlnum(Character) && Character != TEXT('_'))
			{
				return false;
			}
		}
		return true;
	}
}

void UCharacterProfileSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	LoadProfile();
}

void UCharacterProfileSubsystem::Deinitialize()
{
	SaveProfile();
	Super::Deinitialize();
}

void UCharacterProfileSubsystem::LoadProfile()
{
	if (UGameplayStatics::DoesSaveGameExist(SAVE_SLOT_NAME, USER_INDEX))
	{
		if (UCharacterProfileSave* SaveData = Cast<UCharacterProfileSave>(
			UGameplayStatics::LoadGameFromSlot(SAVE_SLOT_NAME, USER_INDEX)))
		{
			const FCharacterProfile& Loaded = SaveData->Profile;
			const bool bValidAppearance = StaticEnum<ECharacterAppearance>()->IsValidEnumValue(static_cast<int64>(Loaded.AppearanceVariant));
			const bool bValidRole = StaticEnum<EPressureSuitRole>()->IsValidEnumValue(static_cast<int64>(Loaded.SuitRole));
			if (Loaded.bHasBeenCreated && !Loaded.CharacterName.TrimStartAndEnd().IsEmpty() && Loaded.CharacterName.Len() <= 20 && bValidAppearance && bValidRole)
			{
				CurrentProfile = Loaded;
				if (!IsValidMetaHumanPresetId(CurrentProfile.MetaHumanPresetId))
				{
					CurrentProfile.MetaHumanPresetId = DefaultMetaHumanPreset;
				}
				return;
			}
			UE_LOG(LogTemp, Warning, TEXT("Character profile save was invalid; restoring first-launch defaults."));
		}
	}

	// First launch: initialize with defaults
	CurrentProfile = FCharacterProfile();
	CurrentProfile.bHasBeenCreated = false;
}

void UCharacterProfileSubsystem::SaveProfile()
{
	if (UCharacterProfileSave* SaveData = NewObject<UCharacterProfileSave>())
	{
		SaveData->Profile = CurrentProfile;
		if (!UGameplayStatics::SaveGameToSlot(SaveData, SAVE_SLOT_NAME, USER_INDEX))
		{
			UE_LOG(LogTemp, Error, TEXT("Unable to persist character profile."));
		}
	}
}

void UCharacterProfileSubsystem::CreateProfile(const FString& InCharacterName, ECharacterAppearance InAppearance, EPressureSuitRole InSuitRole)
{
	CreateProfileWithPreset(InCharacterName, InAppearance, InSuitRole, DefaultMetaHumanPreset);
}

void UCharacterProfileSubsystem::CreateProfileWithPreset(const FString& InCharacterName,
	ECharacterAppearance InAppearance, EPressureSuitRole InSuitRole, FName InMetaHumanPresetId)
{
	FString SanitizedName = InCharacterName.TrimStartAndEnd().Left(20);
	CurrentProfile.CharacterName = SanitizedName.IsEmpty() ? TEXT("Unnamed") : SanitizedName;
	CurrentProfile.AppearanceVariant = InAppearance;
	CurrentProfile.SuitRole = InSuitRole;
	CurrentProfile.MetaHumanPresetId = IsValidMetaHumanPresetId(InMetaHumanPresetId)
		? InMetaHumanPresetId : DefaultMetaHumanPreset;
	CurrentProfile.bHasBeenCreated = true;

	SaveProfile();
	BroadcastProfileChanged();
}

void UCharacterProfileSubsystem::CreateProfileFromDraft(const FCharacterProfile& InProfile)
{
	CurrentProfile = InProfile;
	const FString SanitizedName = InProfile.CharacterName.TrimStartAndEnd().Left(20);
	CurrentProfile.CharacterName = SanitizedName.IsEmpty() ? TEXT("Unnamed") : SanitizedName;
	CurrentProfile.bHasBeenCreated = true;
	SaveProfile();
	BroadcastProfileChanged();
}

void UCharacterProfileSubsystem::BroadcastProfileChanged()
{
	OnCharacterProfileChanged.Broadcast(CurrentProfile);
}
