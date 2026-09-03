#pragma once

#include "CoreMinimal.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Actor.h"
#include "Curves/CurveFloat.h"
#include "AstrophysicsHazardComponent.h"
#include "HazardZoneActor.generated.h"

class AHorrorEnemy;
class AShipSection;

UCLASS()
class GINNUNGAGAP_API AHazardZoneActor : public AActor
{
    GENERATED_BODY()

public:
    AHazardZoneActor();

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone")
    FPhysicsEnvironmentState EnvironmentState;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone|Falloff")
    UCurveFloat* IntensityCurve;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone|Falloff")
    float MaxFalloffDistance = 500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone|Falloff")
    bool bUseDistanceFalloff = true;

    /**
     * The temperature at which a zone starts burning the people standing in it.
     *
     * 50 C rather than anything hotter because that is roughly where contact time starts mattering
     * to skin. Below it the zone is merely unpleasant and costs the player nothing, which keeps
     * every default 20 C zone in the ship exactly as harmless as it is today.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone|Thermal")
    float BurnThresholdC = 50.0f;

    /** Where heat stops getting worse. Above this the zone is already as bad as it can be. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zone|Thermal")
    float BurnSaturationC = 200.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Components")
    UBoxComponent* ZoneBounds;
    
    UPROPERTY()
    TArray<class ACoopSurvivalCharacter*> OverlappingSurvivors;

    UPROPERTY()
    TArray<AHorrorEnemy*> OverlappingManifestations;

    UFUNCTION(BlueprintCallable, Category="Zone")
    float CalculateIntensityAtDistance(float Distance) const;

    /**
     * How hot this zone is on a 0..1 scale, before distance is considered.
     *
     * Separated from the burn itself so the curve can be asserted without a world -- the zone needs
     * one to have anybody standing in it, the arithmetic does not.
     */
    UFUNCTION(BlueprintPure, Category="Zone|Thermal")
    float GetNormalizedHeat() const;

    UFUNCTION()
    void OnZoneBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void OnZoneEndOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

private:
    /** Turns this zone's temperature and a survivor's distance into accrued BurnTrauma. */
    void ApplyThermalExposure(class ACoopSurvivalCharacter* Survivor, float Intensity, float DeltaTime);

    void DecayHazardContamination(float DeltaTime);

    UPROPERTY()
    TObjectPtr<AShipSection> CachedSection;
};
