#pragma once

#include "CoreMinimal.h"
#include "Activities/MaintenanceActivityStations.h"
#include "QuickDemoPowerStation.generated.h"

/** Restores the authored quick-demo ship's utility lights after its breaker activity succeeds. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoPowerStation : public ABreakerReroutingStation
{
    GENERATED_BODY()

public:
    AQuickDemoPowerStation();
    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FName UtilityLightTag = TEXT("QuickDemoUtilityLight");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo", meta=(ClampMin="0.0"))
    float RestoredLightIntensity = 280.0f;

    /** Emergency red. See OnActivityCompleted for why this is not white. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quick Demo")
    FLinearColor RestoredLightColor = FLinearColor(1.0f, 0.16f, 0.06f);
};
