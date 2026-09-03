#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "StarSystem/StarSystemTypes.h"
#include "ShipHelmSystem.generated.h"

class ASensorArraySystem;
class AResourceNodeActor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnOperationsTargetChanged, ESystemPointOfInterestType, ContactType, AActor*, TargetActor);

USTRUCT(BlueprintType)
struct FHelmNavigationSolution
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bValid = false;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FName ContactName;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    ESystemPointOfInterestType ContactType = ESystemPointOfInterestType::Unknown;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FVector DesiredDirection = FVector::ForwardVector;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    float RangeKilometers = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    float HeadingErrorDegrees = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    float EstimatedTravelSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bHazardNearDestination = false;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bRouteIntersectsHazard = false;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FName ClosestHazardName;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    float ClosestHazardClearanceKilometers = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bUsingSafeDetour = false;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FVector SafeDetourWaypoint = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    float DetourTravelSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bBraking = false;
};

UCLASS()
class GINNUNGAGAP_API AShipHelmSystem : public AShipSystemActor
{
    GENERATED_BODY()

public:
    AShipHelmSystem();

    virtual void Tick(float DeltaTime) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Navigation System")
    FVector IntendedDestination = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FVector CurrentHeadingOffset = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System")
    float MaxDriftPerSecond = 50.0f;

    UFUNCTION(BlueprintCallable, Category = "Navigation System")
    void TickNavigationDrift(float DeltaTime);

    UFUNCTION(BlueprintCallable, Category = "Navigation System")
    void ConsumeHeadingOffset(float ReductionFraction = 1.0f);

    UFUNCTION(BlueprintCallable, Category = "Navigation System")
    FHelmNavigationSolution UpdateTrackedContactSolution();

    UFUNCTION(BlueprintCallable, Category = "Navigation System")
    bool BeginHeadingAssist();

    UFUNCTION(BlueprintCallable, Category = "Navigation System")
    void EndHeadingAssist();

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    FHelmNavigationSolution CurrentNavigationSolution;

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System")
    bool bHeadingAssistActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System", meta = (ClampMin = "0.1"))
    float CruiseSpeedKilometersPerSecond = 0.75f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System", meta = (ClampMin = "0.0"))
    float HeadingAssistAcceleration = 5000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System", meta = (ClampMin = "100.0"))
    float ContactArrivalTolerance = 30000.0f;

    UFUNCTION(BlueprintNativeEvent, Category = "Navigation System")
    void OnNavigationContactArrived(FName ContactName);
    virtual void OnNavigationContactArrived_Implementation(FName ContactName);

    UPROPERTY(BlueprintReadOnly, Category = "Navigation System|Operations")
    TObjectPtr<AActor> ActiveOperationsTarget;

    UPROPERTY(BlueprintAssignable, Category = "Navigation System|Operations")
    FOnOperationsTargetChanged OnOperationsTargetChanged;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System|Operations")
    float OperationsTargetResolveRadius = 100000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Navigation System", meta = (ClampMin = "0.0"))
    float DestinationHazardWarningRadius = 250000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Navigation System")
    bool bAllowHazardousHeadingAssist = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Navigation System")
    bool bUseAutomaticSafeDetours = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Navigation System", meta = (ClampMin = "1.05", ClampMax = "4.0"))
    float DetourClearanceMultiplier = 1.45f;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    UFUNCTION()
    void HandleResourceNodeDepleted(AResourceNodeActor* ResourceNode);

    UPROPERTY()
    TObjectPtr<ASensorArraySystem> CachedSensorArray;

    FName LastArrivalContactName;
};
