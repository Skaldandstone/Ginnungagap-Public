#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "Interfaces/Interactable.h"
#include "ArmorPlatingSystem.generated.h"

UCLASS()
class GINNUNGAGAP_API AArmorPlatingSystem : public AShipSystemActor, public IInteractable
{
	GENERATED_BODY()

public:
	AArmorPlatingSystem();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(BlueprintReadOnly, Category = "Armor")
	float ArmorIntegrity = 1.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	float ThermalResistanceMultiplier = 0.7f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	float PressureResistanceMultiplier = 0.8f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	float CorruptionIntegrityPenalty = 0.5f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	float ThermalDegradationPerSecond = 0.05f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	float PressureDegradationPerSecond = 0.04f;

	UPROPERTY(EditDefaultsOnly, Category = "Armor")
	int32 StructuralAlloyPerRepairPoint = 5;

	UFUNCTION(BlueprintCallable, Category = "Armor")
	void OnThermalHazardExposure(float Severity, float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "Armor")
	void OnPressureHazardExposure(float Severity, float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "Armor")
	bool RepairArmor(int32 StructuralAlloyAmount);

	UFUNCTION(BlueprintCallable, Category = "Armor")
	float GetEffectiveResistanceMultiplier(bool bForThermal) const;

	UFUNCTION(BlueprintCallable, Category = "Armor")
	bool IsFunctioning() const;

	UFUNCTION(BlueprintImplementableEvent, Category = "Armor")
	void OnArmorConsoleOpened();

protected:
	virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
	virtual void ApplyCorruptionEffects() override;
	virtual void RemoveCorruptionEffects() override;

private:
	void DegradeArmor(float DamageAmount);
};
