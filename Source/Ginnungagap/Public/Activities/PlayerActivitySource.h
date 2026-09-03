#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "PlayerActivityTypes.h"
#include "PlayerActivitySource.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UPlayerActivitySource : public UInterface
{
    GENERATED_BODY()
};

class IPlayerActivitySource
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Activity")
    FPlayerActivityDefinition GetActivityDefinition(APawn* Player) const;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Activity")
    bool CanStartActivity(APawn* Player) const;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Activity")
    void OnActivityCompleted(APawn* Player);
};
