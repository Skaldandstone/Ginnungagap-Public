#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CGITrailerDirector.generated.h"

class ACameraActor;
class ASkeletalMeshActor;
class UAnimationAsset;
class UMaterialInterface;
class UPointLightComponent;
class UStaticMesh;
class USkeletalMesh;

/**
 * Runtime-only cinematic director used by the -CGITrailer command-line render.
 * It turns the procedural corvette into a deterministic 3D trailer set without
 * changing normal play sessions or requiring a hand-authored Level Sequence.
 */
UCLASS()
class GINNUNGAGAP_API ACGITrailerDirector : public AActor
{
    GENERATED_BODY()

public:
    ACGITrailerDirector();

protected:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

private:
    ASkeletalMeshActor* SpawnPerformer(USkeletalMesh* Mesh, UAnimationAsset* Animation,
        UMaterialInterface* Material, const FVector& Location, const FRotator& Rotation,
        const FVector& Scale, bool bLoopAnimation);
    AActor* SpawnRobot(const FVector& Location, const FRotator& Rotation, float Scale);
    AActor* SpawnPropWeapon();
    void AddRobotPart(AActor* Robot, UStaticMesh* Mesh, const FVector& RelativeLocation,
        const FVector& RelativeScale, const FRotator& RelativeRotation,
        UMaterialInterface* Material);
    void SpawnTrailerCast();
    void SpawnCinematicLighting();
    void SpawnReactorBloom();
    void SetCameraPose(const FVector& Location, const FVector& LookAt, float FOV, float Roll = 0.0f);
    void UpdateCamera(float TrailerTime);
    void UpdateCast(float TrailerTime);
    void UpdateLighting(float TrailerTime);

    UPROPERTY()
    TObjectPtr<ACameraActor> Camera;

    UPROPERTY()
    TObjectPtr<ASkeletalMeshActor> PlayerPerformer;

    UPROPERTY()
    TArray<TObjectPtr<ASkeletalMeshActor>> InfectedPerformers;

    UPROPERTY()
    TArray<TObjectPtr<ASkeletalMeshActor>> CorpsePerformers;

    UPROPERTY()
    TArray<TObjectPtr<AActor>> RobotPerformers;

    UPROPERTY()
    TObjectPtr<AActor> PlayerWeapon;

    UPROPERTY()
    TArray<TObjectPtr<AActor>> BloomSpores;

    UPROPERTY()
    TArray<TObjectPtr<UPointLightComponent>> CinematicLights;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CubeMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CylinderMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> SphereMesh;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> HullMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> DeckMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> SuitMaterial;

    UPROPERTY()
    TObjectPtr<UMaterialInterface> BloomMaterial;

    UPROPERTY()
    TObjectPtr<UAnimationAsset> CombatAnimation;

    float ElapsedSeconds = 0.0f;
    float StartDelaySeconds = 4.0f;
    float TrailerDurationSeconds = 34.0f;
    float RenderTimeDilation = 1.0f;
    bool bActivated = false;
    bool bTimelineStarted = false;
    bool bCombatAnimationSet = false;
};
