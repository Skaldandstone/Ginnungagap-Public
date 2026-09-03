#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "CharacterProfile.h"
#include "CharacterProfileSave.generated.h"

UCLASS()
class GINNUNGAGAP_API UCharacterProfileSave : public USaveGame
{
	GENERATED_BODY()

public:
	UPROPERTY()
	FCharacterProfile Profile;
};
