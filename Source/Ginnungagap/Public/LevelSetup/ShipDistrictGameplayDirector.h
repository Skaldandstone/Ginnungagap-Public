#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include "Mission/MissionTypes.h"
#include "Threats/ThreatTypes.h"
#include "ShipDistrictGameplayDirector.generated.h"

class UBoxComponent;
class UWorldItemSeedCatalog;

UENUM(BlueprintType)
enum class EShipDistrictScale : uint8
{
    Small,
    Medium,
    Large
};

UCLASS(BlueprintType)
class GINNUNGAGAP_API UShipDistrictBudgetData : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    int32 MaxVisibleTriangles = 3000000;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    int32 MaxDrawCalls = 1800;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    int32 MaxShadowedMovableLights = 8;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    int32 MaxActiveAudioSources = 32;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    int32 MaxActiveEnemies = 12;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance Budget")
    float StreamingCellSizeMeters = 64.0f;
};

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipDistrictGameplayDirector : public AActor
{
    GENERATED_BODY()

public:
    AShipDistrictGameplayDirector();

    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="District")
    TObjectPtr<UBoxComponent> DistrictBounds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="District")
    EShipDistrictScale DistrictScale = EShipDistrictScale::Small;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="District")
    FVector DistrictExtent = FVector(2600.0f, 600.0f, 215.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    FName PrimaryObjectiveId = TEXT("RestoreDistrictSystems");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    FText PrimaryObjectiveTitle = NSLOCTEXT("ShipDistrict", "RestoreDistrict", "Restore district systems");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    EMissionObjectiveType ObjectiveType = EMissionObjectiveType::Repair;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Mission")
    int32 ObjectiveReward = 250;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    int32 EncounterCount = 3;

    /** Custom preserves the legacy Bloom patrol. Any other value seeds an independent mission threat. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    EThreatEncounterPreset ThreatPreset = EThreatEncounterPreset::Custom;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    int32 OxygenPickupCount = 2;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    int32 HealthPickupCount = 2;

    /** Optional weighted catalog used to distribute physical tools, weapons, pickups, and props. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="World Items")
    TObjectPtr<UWorldItemSeedCatalog> WorldItemCatalog = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="World Items", meta=(ClampMin="0"))
    int32 WorldItemSeedCount = 0;

    /** Room profiles are selected deterministically per seed point and filter the shared catalog. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="World Items")
    TArray<FName> WorldItemRoomProfiles;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    int32 LayoutSeed = 4103;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Performance")
    TObjectPtr<UShipDistrictBudgetData> PerformanceBudget;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Encounters")
    bool bSpawnGameplayOnBeginPlay = true;

    /** Adds the complete sensor/resource/jump/cryo demo loop to an authored district. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Demo")
    bool bSpawnDemoSystems = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Demo", meta=(ClampMin="10.0"))
    float DemoJumpCountdownSeconds = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Demo", meta=(ClampMin="1"))
    int32 DemoJumpsToDestination = 2;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Checkpoint")
    bool bRestoreCheckpointOnBeginPlay = true;

    UFUNCTION(BlueprintCallable, Category="District")
    void SeedDistrictGameplay();

private:
    FVector RandomPointOnDeck(FRandomStream& Random, float EdgeMargin) const;
    void RegisterPrimaryObjective();
    void RestoreCheckpointState();
    void SpawnDemoSystems();
};
