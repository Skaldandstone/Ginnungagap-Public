#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "BioScannerComponent.generated.h"

class AShipSection;
class ACoopSurvivalCharacter;

USTRUCT(BlueprintType)
struct FSectionScanReading
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    int32 SectionID = -1;

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    float Concentration = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    bool bSealedFromHere = false;

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    bool bIsAdjacent = false;
};

USTRUCT(BlueprintType)
struct FPatientScanReading
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    bool bValidPatient = false;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    float HealthPercent = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    float OxygenPercent = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    float RadiationDoseSv = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    TArray<FPlayerStatusEffectState> Conditions;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    int32 CriticalConditionCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    EPlayerStatusEffect MostUrgentCondition = EPlayerStatusEffect::Hypoxia;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    bool bHasUrgentCondition = false;

    UPROPERTY(BlueprintReadOnly, Category="Bio Scanner|Patient")
    FText RecommendedAction;
};

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UBioScannerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UBioScannerComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "Bio Scanner")
    bool IsLocalSectionContaminated() const;

    UFUNCTION(BlueprintCallable, Category="Bio Scanner|Patient")
    FPatientScanReading ScanPatient(const ACoopSurvivalCharacter* Patient) const;

    UFUNCTION(BlueprintPure, Category="Bio Scanner|Patient")
    FPatientScanReading GetOwnerPatientReading() const;

    /**
     * Readings below this are clamped up to it, so anything fainter is indistinguishable from a
     * clean compartment. Science training lowers the effective floor; see GetEffectiveDetectionFloor.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bio Scanner")
    float DetectionFloor = 0.05f;

    /** Floor a fully trained scientist can reach, as a fraction of the untrained floor. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bio Scanner", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MinDetectionFloorFraction = 0.15f;

    /** Compartment hops the scanner reaches before training. One means adjacent only. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bio Scanner", meta = (ClampMin = "1"))
    int32 BaseScanHops = 1;

    /** Hard ceiling on reach however much training is stacked, so a sweep cannot read a whole ship. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Bio Scanner", meta = (ClampMin = "1"))
    int32 MaxScanHops = 4;

    /** The floor actually in force for this owner, after Science training. */
    UFUNCTION(BlueprintPure, Category = "Bio Scanner")
    float GetEffectiveDetectionFloor() const;

    /** How many compartment hops this owner's scanner currently reaches. */
    UFUNCTION(BlueprintPure, Category = "Bio Scanner")
    int32 GetEffectiveScanHops() const;

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    FSectionScanReading LocalReading;

    UPROPERTY(BlueprintReadOnly, Category = "Bio Scanner")
    TArray<FSectionScanReading> AdjacentReadings;

private:
    void UpdateReadings();
};
