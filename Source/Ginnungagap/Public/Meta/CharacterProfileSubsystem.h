#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CharacterProfile.h"
#include "CharacterProfileSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCharacterProfileChanged, const FCharacterProfile&, NewProfile);

UCLASS()
class GINNUNGAGAP_API UCharacterProfileSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	void LoadProfile();

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	void SaveProfile();

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	void CreateProfile(const FString& InCharacterName, ECharacterAppearance InAppearance, EPressureSuitRole InSuitRole);

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	void CreateProfileWithPreset(const FString& InCharacterName, ECharacterAppearance InAppearance,
		EPressureSuitRole InSuitRole, FName InMetaHumanPresetId);

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	void CreateProfileFromDraft(const FCharacterProfile& InProfile);

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	FString GetCharacterName() const { return CurrentProfile.CharacterName; }

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	ECharacterAppearance GetAppearanceVariant() const { return CurrentProfile.AppearanceVariant; }

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	EPressureSuitRole GetSuitRole() const { return CurrentProfile.SuitRole; }

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	FName GetMetaHumanPresetId() const { return CurrentProfile.MetaHumanPresetId; }

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	bool HasCreatedCharacter() const { return CurrentProfile.bHasBeenCreated; }

	UFUNCTION(BlueprintCallable, Category = "Character Profile")
	const FCharacterProfile& GetProfile() const { return CurrentProfile; }

	UPROPERTY(BlueprintAssignable, Category = "Character Profile")
	FOnCharacterProfileChanged OnCharacterProfileChanged;

private:
	UPROPERTY()
	FCharacterProfile CurrentProfile;

	void BroadcastProfileChanged();

	static constexpr const TCHAR* SAVE_SLOT_NAME = TEXT("CharacterProfile");
	static constexpr int32 USER_INDEX = 0;
};
