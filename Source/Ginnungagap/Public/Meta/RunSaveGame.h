#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Progression/PlayerClass.h"
#include "RunSaveGame.generated.h"

UCLASS()
class GINNUNGAGAP_API URunSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadWrite, Category = "Meta")
    int32 BankedCurrency = 0;

    UPROPERTY(BlueprintReadWrite, Category = "Progression")
    EPressureSuitRole SelectedRole = GinnungagapDefaults::StartingSuitRole;

    /** Owned ranks and equipped active loadout, per role. */
    UPROPERTY(BlueprintReadWrite, Category = "Progression")
    TMap<EPressureSuitRole, FClassSkillsArray> RoleSkills;

    UPROPERTY(BlueprintReadWrite, Category = "Progression")
    TMap<EPressureSuitRole, int32> RoleSkillPoints;

    UPROPERTY(BlueprintReadWrite, Category = "Progression")
    int32 ProgressionTier = 0;

    UPROPERTY(BlueprintReadWrite, Category = "Progression")
    int32 TotalProgressionPoints = 0;
};
