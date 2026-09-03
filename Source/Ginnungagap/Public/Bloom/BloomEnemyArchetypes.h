#pragma once

#include "CoreMinimal.h"
#include "AI/HorrorEnemy.h"
#include "BloomEnemyArchetypes.generated.h"

class UStaticMeshComponent;
class USkeletalMeshComponent;
class UAnimationAsset;
class UPathogenLoadComponent;
class UPointLightComponent;
class USceneComponent;

UENUM(BlueprintType)
enum class EBloomEnemyInfectionPhase : uint8
{
    Seeded,
    Colonizing,
    Puppeteered,
    Overgrown
};

/** Shared replicated progression for every articulated Bloom host. */
UCLASS(Abstract, Blueprintable)
class GINNUNGAGAP_API AProgressiveBloomEnemy : public AHorrorEnemy
{
    GENERATED_BODY()

public:
    AProgressiveBloomEnemy();

    virtual void Tick(float DeltaTime) override;
    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
        class AController* EventInstigator, AActor* DamageCauser) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Bloom|Progression")
    void SetInfectionProgress(float NewProgress);

    UFUNCTION(BlueprintPure, Category = "Bloom|Progression")
    float GetInfectionProgress() const { return InfectionProgress; }

    UFUNCTION(BlueprintPure, Category = "Bloom|Progression")
    EBloomEnemyInfectionPhase GetInfectionPhase() const;

    UFUNCTION(BlueprintPure, Category = "Bloom|Progression")
    virtual float CalculateProgressForGlobalStage(EBloomStage GlobalStage) const;

    UFUNCTION(BlueprintCallable, Category = "Bloom|Progression")
    void RefreshInfectionPresentation();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Progression")
    bool bTrackGlobalBloomStage = true;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Progression")
    TObjectPtr<UPathogenLoadComponent> PathogenLoadComponent;

    /** Local infection light used as a dark-environment readability and danger cue. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UPointLightComponent> BloomGlowLight;

    /** Moves the complete authored silhouette during native windup and death poses. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<USceneComponent> AttackPoseRoot;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Combat", meta = (ClampMin = "0.1"))
    float AttackInterval = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Combat", meta = (ClampMin = "0.05"))
    float AttackTelegraphDuration = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Combat", meta = (ClampMin = "0.0"))
    float ContactExposurePerAttack = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Combat", meta = (ClampMin = "0.0"))
    float DeathBurstExposure = 18.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Combat", meta = (ClampMin = "0.0"))
    float DeathBurstRadius = 360.0f;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void ApplyProgressiveVisualsAndTuning(float Progress);
    virtual void ApplyNativeAttackPose(float PoseAlpha);
    virtual void ApplyNativeDeathPose(float PoseAlpha);
    virtual void ApplyFabDeathPose(int32 PoseVariant);

    UPROPERTY(EditAnywhere, ReplicatedUsing = OnRep_InfectionProgress, BlueprintReadOnly,
        Category = "Bloom|Progression", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float InfectionProgress = 1.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Bloom|Visuals")
    float MatureGlowIntensity = 900.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Bloom|Visuals")
    float MatureGlowRadius = 300.0f;

    UFUNCTION()
    void OnRep_InfectionProgress();

    UFUNCTION()
    void HandleGlobalBloomStageChanged(EBloomStage NewStage);

    UFUNCTION(BlueprintImplementableEvent, Category = "Bloom|Progression")
    void ReceiveInfectionProgressChanged(float NewProgress, EBloomEnemyInfectionPhase NewPhase);

    UFUNCTION(BlueprintImplementableEvent, Category = "Bloom|Combat")
    void ReceiveBloomAttackTelegraph(AActor* TargetActor, float TelegraphDuration);

    UFUNCTION(BlueprintImplementableEvent, Category = "Bloom|Combat")
    void ReceiveBloomAttackCommitted(AActor* TargetActor, EBloomEnemyInfectionPhase InfectionPhase);

    UFUNCTION(BlueprintImplementableEvent, Category = "Bloom|Combat")
    void ReceiveBloomDeathBurst(float ExposureAmount, float BurstRadius, int32 FabPoseVariant);

private:
    AActor* FindAttackTarget() const;
    void UpdateAttackTelegraphLight(float DeltaTime);
    void UpdateNativeMotion(float DeltaTime);
    void TriggerDeathBurst();

    UFUNCTION(NetMulticast, Unreliable)
    void MulticastBeginAttackTelegraph(AActor* TargetActor);

    UFUNCTION(NetMulticast, Unreliable)
    void MulticastCommitBloomAttack(AActor* TargetActor);

    UFUNCTION(NetMulticast, Reliable)
    void MulticastBloomDeathBurst(float ExposureAmount, float BurstRadius, int32 FabPoseVariant);

    float TimeUntilNextAttack = 0.0f;
    float LocalTelegraphTimeRemaining = 0.0f;
    float LocalAttackRecoveryTimeRemaining = 0.0f;
    float LocalDeathBurstTimeRemaining = 0.0f;
    float LocalDeathPoseAlpha = 0.0f;
    bool bAttackTelegraphSent = false;
    bool bDeathBurstTriggered = false;
};

/**
 * Manny-compatible Bloom host built from the local Fab mannequin and biomass packs.
 * Infection pieces remain separate components so the underlying skeleton can animate.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ABloomReanimatedCrewEnemy : public AProgressiveBloomEnemy
{
    GENERATED_BODY()

public:
    ABloomReanimatedCrewEnemy();

    virtual float CalculateProgressForGlobalStage(EBloomStage GlobalStage) const override;

    /** Evaluates a pack-native death pose immediately for editor review tooling. */
    UFUNCTION(BlueprintCallable, CallInEditor, Category = "Bloom|Animation")
    void PreviewFabDeathPose(int32 PoseVariant = 0);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> ChestGrowth;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> HeadGrowth;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> RightArmGrowth;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> LeftLegGrowth;

    /** Pack-native mesh used only for compatible Dead Bodies Fab terminal poses. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Animation")
    TObjectPtr<USkeletalMeshComponent> FabCorpseMesh;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Bloom|Animation")
    TArray<TObjectPtr<UAnimationAsset>> FabDeathPoseAssets;

protected:
    virtual void ApplyProgressiveVisualsAndTuning(float Progress) override;
    virtual void ApplyNativeAttackPose(float PoseAlpha) override;
    virtual void ApplyNativeDeathPose(float PoseAlpha) override;
    virtual void ApplyFabDeathPose(int32 PoseVariant) override;

private:
    bool bUsingFabDeathPose = false;
};

/**
 * Rigid-part Bloom robot built from the local Fab modular mechanic pack.
 * Parts intentionally stay independent for a later Control Rig or rigid skeletal bind.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ABloomMechanizedEnemy : public AProgressiveBloomEnemy
{
    GENERATED_BODY()

public:
    ABloomMechanizedEnemy();

    virtual float CalculateProgressForGlobalStage(EBloomStage GlobalStage) const override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> RobotBody;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> RobotHead;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> LeftArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> RightArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> LeftLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> RightLeg;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> CoreGrowth;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> CrownGrowth;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Visuals")
    TObjectPtr<UStaticMeshComponent> ArmGrowth;

protected:
    virtual void ApplyProgressiveVisualsAndTuning(float Progress) override;
    virtual void ApplyNativeAttackPose(float PoseAlpha) override;
    virtual void ApplyNativeDeathPose(float PoseAlpha) override;
};
