#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "../StarSystem/StarSystemTypes.h"
#include "SensorArraySystem.generated.h"

class USensorSurveyWidget;

USTRUCT(BlueprintType)
struct FSensorContact
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    FName DisplayName;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    ESystemPointOfInterestType Type = ESystemPointOfInterestType::Unknown;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    FVector WorldLocation = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    float DistanceKilometers = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    float BearingDegrees = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    bool bIdentified = false;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    bool bCriticalResource = false;
};

UCLASS()
class GINNUNGAGAP_API ASensorArraySystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    ASensorArraySystem();

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    int32 ShortRangeLevel = 1;

    UPROPERTY(BlueprintReadOnly, Category = "Sensors")
    int32 LongRangeLevel = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sensors")
    int32 MaxSensorLevel = 3;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sensors")
    int32 UpgradeCostSensorComponents = 15;

    UFUNCTION(BlueprintCallable, Category = "Sensors")
    bool UpgradeShortRange();

    UFUNCTION(BlueprintCallable, Category = "Sensors")
    bool UpgradeLongRange();

    // Fraction of a jump candidate's hazard/resource detail revealed vs. shown as "UNKNOWN".
    UFUNCTION(BlueprintCallable, Category = "Sensors")
    float GetCandidateRevealFraction() const;

    // Multiplier applied to base falsification chance; 1.0 = no protection, lower = harder to fool.
    UFUNCTION(BlueprintCallable, Category = "Sensors")
    float GetFalsificationResistance() const;

    /** Returns distance-sorted contacts from the current generated map, filtered by sensor capability. */
    UFUNCTION(BlueprintCallable, Category = "Sensors")
    TArray<FSensorContact> ScanCurrentSystem() const;

    UFUNCTION(BlueprintCallable, Category = "Sensors|Tracking")
    void TrackContact(const FSensorContact& Contact);

    UFUNCTION(BlueprintCallable, Category = "Sensors|Tracking")
    bool TrackNearestCriticalResource();

    UFUNCTION(BlueprintCallable, Category = "Sensors|Tracking")
    void ClearTrackedContact();

    UFUNCTION(BlueprintPure, Category = "Sensors|Tracking")
    bool HasTrackedContact() const { return bHasTrackedContact; }

    UFUNCTION(BlueprintPure, Category = "Sensors|Tracking")
    FSensorContact GetTrackedContact();

    UFUNCTION(BlueprintImplementableEvent, Category = "Sensors|Tracking")
    void OnTrackedContactChanged(bool bHasContact, const FSensorContact& Contact);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Sensors|Survey")
    float ScanRangePerLongRangeLevel = 1500000.0f;

    UFUNCTION(BlueprintNativeEvent, Category = "Sensors")
    void OnSensorConsoleOpened();
    virtual void OnSensorConsoleOpened_Implementation();

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    UPROPERTY()
    TObjectPtr<USensorSurveyWidget> ActiveSurveyWidget;

    UPROPERTY()
    FSensorContact TrackedContact;

    UPROPERTY()
    bool bHasTrackedContact = false;
};
