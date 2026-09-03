#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "EpidemiologySubsystem.generated.h"

class AShipSection;

UCLASS()
class GINNUNGAGAP_API UEpidemiologySubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category = "Epidemiology")
    void SeedOutbreak(AShipSection* Section, float Amount);

    UPROPERTY(EditDefaultsOnly, Category = "Epidemiology")
    float StepInterval = 1.0f;

private:
    void StepSimulation();
    void StepExposure(float DeltaTime);
    void StepShedding(float DeltaTime);
    void StepDiffusionAndDecay(float DeltaTime);

    FTimerHandle StepTimerHandle;
};
