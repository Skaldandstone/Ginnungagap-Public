#pragma once

#include "CoreMinimal.h"
#include "GinnungagapGameMode.h"
#include "Versus/VersusTypes.h"
#include "VersusGameMode.generated.h"

class AAntagonistPlayerCharacter;

UCLASS()
class GINNUNGAGAP_API AVersusGameMode : public AGinnungagapGameMode
{
	GENERATED_BODY()

public:
	AVersusGameMode();

	virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
	virtual void BeginPlay() override;
	virtual void PreLogin(const FString& Options, const FString& Address,
		const FUniqueNetIdRepl& UniqueId, FString& ErrorMessage) override;
	virtual FString InitNewPlayer(APlayerController* NewPlayerController, const FUniqueNetIdRepl& UniqueId,
		const FString& Options, const FString& Portal = TEXT("")) override;
	virtual void PostLogin(APlayerController* NewPlayer) override;
	virtual void Logout(AController* Exiting) override;
	virtual UClass* GetDefaultPawnClassForController_Implementation(AController* InController) override;
	virtual void RestartPlayer(AController* NewPlayer) override;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Versus")
	TSubclassOf<AAntagonistPlayerCharacter> AntagonistPawnClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Versus")
	int32 StartingAntagonistSkillPoints = 3;

	UFUNCTION(BlueprintPure, Category="Versus")
	const FVersusMatchSettings& GetVersusSettings() const { return VersusSettings; }

private:
	FVersusMatchSettings VersusSettings;

	EVersusTeam ChooseTeam(const FString& Options) const;
	void ApplyPlayerAffiliation(AController* Controller) const;
	void RefreshMatchPhase() const;
	void SpawnIndependentFactions();

	static EAntagonistFaction ParseFaction(const FString& Value);
};
