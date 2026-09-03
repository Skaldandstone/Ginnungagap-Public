#pragma once

#include "CoreMinimal.h"
#include "Ship/ShipSystemActor.h"
#include "Interfaces/Interactable.h"
#include "ShipInteractiveFixture.generated.h"

class UPointLightComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;

UENUM(BlueprintType)
enum class EShipFixtureType : uint8
{
    Terminal,
    EmergencyLight,
    VentControl,
    PurgeStation,
    Machinery
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FShipFixtureStateChanged, AShipInteractiveFixture*, Fixture, bool, bEnabled);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FShipFixtureActivated, AShipInteractiveFixture*, Fixture);

UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipInteractiveFixture : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    AShipInteractiveFixture();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    EShipFixtureType FixtureType = EShipFixtureType::Terminal;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    bool bEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    bool bLocked = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    bool bToggleOnInteract = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UStaticMesh> FixtureMeshAsset;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UMaterialInterface> NormalMaterial;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UMaterialInterface> ActiveMaterial;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UMaterialInterface> CorruptedMaterial;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UStaticMeshComponent> FixtureMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Ship Fixture")
    TObjectPtr<UPointLightComponent> StatusLight;

    UPROPERTY(BlueprintAssignable, Category="Ship Fixture")
    FShipFixtureStateChanged OnStateChanged;

    UPROPERTY(BlueprintAssignable, Category="Ship Fixture")
    FShipFixtureActivated OnActivated;

    UFUNCTION(BlueprintCallable, Category="Ship Fixture")
    void SetFixtureEnabled(bool bNewEnabled);

    UFUNCTION(BlueprintPure, Category="Ship Fixture")
    bool CanInteractWithFixture() const;

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    void RefreshVisualState();
};
