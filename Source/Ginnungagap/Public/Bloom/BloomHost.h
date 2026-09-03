#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "BloomHost.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UBloomHost : public UInterface
{
    GENERATED_BODY()
};

class GINNUNGAGAP_API IBloomHost
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Bloom")
    void OnBloomPossession();

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Bloom")
    bool CanBeBloomPossessed() const;
};
