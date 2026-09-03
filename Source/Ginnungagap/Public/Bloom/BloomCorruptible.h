#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "BloomCorruptible.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UBloomCorruptible : public UInterface
{
    GENERATED_BODY()
};

class GINNUNGAGAP_API IBloomCorruptible
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Bloom")
    void OnBloomCorruption();

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Bloom")
    void OnBloomPurged();

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "Bloom")
    bool CanBeBloomCorrupted() const;
};
