#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Ship/ShipSection.h"
#include "ShipHardpointPopulationDirector.generated.h"

class ACrewCorpse;
class AShipSection;
class USkeletalMesh;
class UStaticMesh;
class UStaticMeshComponent;

/** Replicated visual used for crate obstacles and non-blocking Bloom growth. */
UCLASS()
class GINNUNGAGAP_API AShipHardpointStaticOccupant : public AActor
{
    GENERATED_BODY()

public:
    AShipHardpointStaticOccupant();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Population")
    TObjectPtr<UStaticMeshComponent> VisualMesh;

    UPROPERTY(ReplicatedUsing=OnRep_OccupantVisual, VisibleInstanceOnly, BlueprintReadOnly,
        Category="Ship Population")
    TObjectPtr<UStaticMesh> MeshAsset;

    UPROPERTY(ReplicatedUsing=OnRep_OccupantVisual, VisibleInstanceOnly, BlueprintReadOnly,
        Category="Ship Population")
    EShipGameplayHardpointType OccupantType = EShipGameplayHardpointType::Obstacle;

    void ConfigureOccupant(EShipGameplayHardpointType Type, UStaticMesh* Mesh);
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    UFUNCTION()
    void OnRep_OccupantVisual();

    void RefreshVisual();
};

USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipHardpointPopulationBinding
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Population")
    TObjectPtr<AShipSection> Section = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Population")
    FName HardpointId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Population")
    EShipGameplayHardpointType HardpointType = EShipGameplayHardpointType::Obstacle;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Population")
    TObjectPtr<AActor> SpawnedActor = nullptr;
};

/** Deterministically consumes typed room/corridor hardpoints for environmental storytelling. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipHardpointPopulationDirector : public AActor
{
    GENERATED_BODY()

public:
    AShipHardpointPopulationDirector();

    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population")
    bool bPopulateOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population")
    int32 PopulationSeed = 81173;

    /** Zero includes every ship section in the world. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population", meta=(ClampMin="0.0"))
    float PopulationRadius = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population", meta=(ClampMin="0"))
    int32 BodyCount = 6;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population", meta=(ClampMin="0"))
    int32 ObstacleCount = 10;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population", meta=(ClampMin="0"))
    int32 BloomGrowthCount = 8;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Bodies")
    TSubclassOf<ACrewCorpse> BodyActorClass;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Bodies")
    TObjectPtr<USkeletalMesh> BodyMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Obstacles")
    TObjectPtr<UStaticMesh> ObstacleMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Obstacles", meta=(ClampMin="0.01"))
    float ObstacleScale = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Bloom")
    TObjectPtr<UStaticMesh> BloomGrowthMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Population|Bloom", meta=(ClampMin="0.01"))
    float BloomGrowthScale = 0.28f;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Ship Population")
    TArray<FShipHardpointPopulationBinding> SpawnedBindings;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Ship Population")
    int32 PopulateHardpoints();

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Ship Population")
    void ClearPopulation();

private:
    int32 PopulateType(EShipGameplayHardpointType Type, int32 RequestedCount,
        FRandomStream& Random);
    AActor* SpawnAtHardpoint(EShipGameplayHardpointType Type, const FTransform& Transform);
};
