#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Bloom/BloomDirector.h"
#include "ShipEnvironmentController.generated.h"

class UAudioComponent;
class UDecalComponent;
class UExponentialHeightFogComponent;
class UMaterialInterface;
class UPointLightComponent;
class UPostProcessComponent;
class USceneComponent;
class USoundBase;
class UStaticMesh;
class UStaticMeshComponent;
class UBloomDirector;
class UShipDamageComponent;
class AShipSection;

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipEnvironmentController : public AActor
{
    GENERATED_BODY()

public:
    AShipEnvironmentController();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Environment State")
    EBloomStage PreviewBloomStage = EBloomStage::Latent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Environment State")
    bool bAlertActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Environment State")
    bool bDamageActive = false;

    /** When enabled, the controller follows the game-instance Bloom director instead of remaining on its authored preview stage. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Environment State|Runtime")
    bool bFollowLiveBloomState = false;

    /** When enabled, the controller follows a ship section's aggregate damage danger score. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Environment State|Runtime")
    bool bFollowShipDamageState = false;

    /** Optional explicit section. If unset, the controller locates the section whose bounds contain it. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Environment State|Runtime")
    TObjectPtr<AShipSection> MonitoredSection;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UStaticMesh> BloomNoduleMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UStaticMesh> BloomTendrilMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UStaticMesh> BloomRibMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UMaterialInterface> BloomColonyMaterial;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UMaterialInterface> BloomAdvancedMaterial;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Assets")
    TObjectPtr<UMaterialInterface> DamageDecalMaterial;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Audio")
    TObjectPtr<USoundBase> ShipHumSound;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Audio")
    TObjectPtr<USoundBase> AlarmSound;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Environment Audio")
    TObjectPtr<USoundBase> BloomSound;

    UFUNCTION(BlueprintCallable, Category="Environment State")
    void ApplyEnvironmentState(EBloomStage BloomStage, bool bInAlert, bool bInDamage);

    /** Converts gameplay signals into the visual state policy used by live controllers. */
    UFUNCTION(BlueprintCallable, Category="Environment State")
    void ApplyGameplaySignals(EBloomStage BloomStage, float DamageDangerScore);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TObjectPtr<UExponentialHeightFogComponent> AtmosphereFog;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TObjectPtr<UPostProcessComponent> PostProcess;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TObjectPtr<UAudioComponent> AmbientAudio;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TArray<TObjectPtr<UStaticMeshComponent>> BloomGrowths;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TArray<TObjectPtr<UPointLightComponent>> StateLights;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Environment Components")
    TArray<TObjectPtr<UDecalComponent>> DamageDecals;

private:
    UFUNCTION()
    void HandleBloomStageChanged(EBloomStage NewStage);

    UFUNCTION()
    void HandleDamageStateChanged();

    void BindRuntimeState();
    void RefreshEnvironment();

    UPROPERTY(Transient)
    TObjectPtr<UBloomDirector> BoundBloomDirector;

    UPROPERTY(Transient)
    TObjectPtr<UShipDamageComponent> BoundDamageState;
};
