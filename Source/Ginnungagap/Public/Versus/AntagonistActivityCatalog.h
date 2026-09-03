#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Versus/AntagonistActivityTypes.h"
#include "AntagonistActivityCatalog.generated.h"

UCLASS()
class GINNUNGAGAP_API UAntagonistActivityCatalog : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	static FAntagonistActivityDefinition GetActivity(FName ActivityId);

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	static TArray<FAntagonistActivityDefinition> GetActivitiesForFaction(EAntagonistFaction Faction);

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	static bool CanFactionPerformActivity(EAntagonistFaction Faction, FName ActivityId);

private:
	static TArray<FAntagonistActivityDefinition> BuildCatalog();
};

