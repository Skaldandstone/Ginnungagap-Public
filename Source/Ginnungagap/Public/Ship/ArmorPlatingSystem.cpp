// Copyright Epic Games, Inc. All Rights Reserved.

#include "Ship/ArmorPlatingSystem.h"
#include "../CoopSurvivalCharacter.h"
#include "../StarSystem/ShipResourceInventorySubsystem.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

AArmorPlatingSystem::AArmorPlatingSystem()
{
	PrimaryActorTick.bCanEverTick = false;

	SystemType = EShipSystemType::Armor;
	SystemName = TEXT("Armor Plating");
}

void AArmorPlatingSystem::BeginPlay()
{
	Super::BeginPlay();
	ArmorIntegrity = 1.0f;
}

void AArmorPlatingSystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}

void AArmorPlatingSystem::OnThermalHazardExposure(float Severity, float DeltaTime)
{
	if (ArmorIntegrity > 0.0f)
	{
		const float DamageAmount = ThermalDegradationPerSecond * Severity * DeltaTime;
		DegradeArmor(DamageAmount);
	}
}

void AArmorPlatingSystem::OnPressureHazardExposure(float Severity, float DeltaTime)
{
	if (ArmorIntegrity > 0.0f)
	{
		const float DamageAmount = PressureDegradationPerSecond * Severity * DeltaTime;
		DegradeArmor(DamageAmount);
	}
}

bool AArmorPlatingSystem::RepairArmor(int32 StructuralAlloyAmount)
{
	if (ArmorIntegrity >= 1.0f)
	{
		return false;
	}

	UGameInstance* GI = GetGameInstance();
	if (!GI)
	{
		return false;
	}

	UShipResourceInventorySubsystem* Inventory = GI->GetSubsystem<UShipResourceInventorySubsystem>();
	if (!Inventory)
	{
		return false;
	}

	const int32 AlloyNeeded = StructuralAlloyPerRepairPoint;
	if (!Inventory->TrySpendResource(EStarSystemResourceType::StructuralAlloy, AlloyNeeded))
	{
		return false;
	}

	// Repair 1% integrity per resource point spent
	ArmorIntegrity = FMath::Clamp(ArmorIntegrity + 0.01f, 0.0f, 1.0f);
	return true;
}

float AArmorPlatingSystem::GetEffectiveResistanceMultiplier(bool bForThermal) const
{
	const float BaseMultiplier = bForThermal ? ThermalResistanceMultiplier : PressureResistanceMultiplier;

	if (bIsCorrupted)
	{
		return FMath::Lerp(BaseMultiplier, 1.0f, CorruptionIntegrityPenalty);
	}

	return BaseMultiplier;
}

bool AArmorPlatingSystem::IsFunctioning() const
{
	return !bIsCorrupted && ArmorIntegrity > 0.01f;
}

void AArmorPlatingSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
	if (bIsCorrupted)
	{
		OnArmorConsoleOpened();
		return;
	}

	OnArmorConsoleOpened();
}

void AArmorPlatingSystem::ApplyCorruptionEffects()
{
	// Corruption reduces effective armor protection
}

void AArmorPlatingSystem::RemoveCorruptionEffects()
{
	// Armor protection restored
}

void AArmorPlatingSystem::DegradeArmor(float DamageAmount)
{
	ArmorIntegrity = FMath::Clamp(ArmorIntegrity - DamageAmount, 0.0f, 1.0f);
}
