#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Equipment/EquipmentSystem.h"
#include "ExpeditionLoadoutSubsystem.generated.h"

class UEquipmentComponent;

/**
 * Owns the operator's pre-expedition equipment choices. Game-instance lifetime keeps the
 * selection intact while the menu travels into the expedition map.
 */
UCLASS()
class GINNUNGAGAP_API UExpeditionLoadoutSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintCallable, Category="Loadout")
	void ResetToStarterLoadout();

	UFUNCTION(BlueprintCallable, Category="Loadout")
	TArray<FEquipmentItem> GetEquipmentCatalog() const { return EquipmentCatalog; }

	UFUNCTION(BlueprintCallable, Category="Loadout")
	TArray<FEquipmentItem> GetEquippedItems() const;

	UFUNCTION(BlueprintCallable, Category="Loadout")
	bool ToggleEquipment(EEquipmentType Type);

	UFUNCTION(BlueprintCallable, Category="Loadout")
	bool IsEquipmentSelected(EEquipmentType Type) const;

	UFUNCTION(BlueprintCallable, Category="Loadout")
	int32 GetUsedSupply() const;

	UFUNCTION(BlueprintCallable, Category="Loadout")
	int32 GetRemainingSupply() const { return FMath::Max(0, SupplyBudget - GetUsedSupply()); }

	UFUNCTION(BlueprintCallable, Category="Loadout")
	FEquipmentStats GetSelectedStats() const;

	UFUNCTION(BlueprintCallable, Category="Loadout")
	void ApplyLoadout(UEquipmentComponent* EquipmentComponent) const;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Loadout", meta=(ClampMin="1"))
	int32 SupplyBudget = 8;

private:
	UPROPERTY()
	TArray<FEquipmentItem> EquipmentCatalog;

	UPROPERTY()
	TMap<EEquipmentSlot, FEquipmentItem> SelectedEquipment;

	void BuildDefaultCatalog();
	const FEquipmentItem* FindCatalogItem(EEquipmentType Type) const;
};
