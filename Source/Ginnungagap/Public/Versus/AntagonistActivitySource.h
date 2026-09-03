#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "Versus/AntagonistActivityTypes.h"
#include "AntagonistActivitySource.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UAntagonistActivitySource : public UInterface
{
	GENERATED_BODY()
};

class IAntagonistActivitySource
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Versus|Activities")
	FAntagonistActivityDefinition GetAntagonistActivityDefinition(APawn* InstigatorPawn) const;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Versus|Activities")
	bool CanStartAntagonistActivity(APawn* InstigatorPawn) const;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Versus|Activities")
	void OnAntagonistActivityCompleted(APawn* InstigatorPawn, FName CompletionEffectId);
};

