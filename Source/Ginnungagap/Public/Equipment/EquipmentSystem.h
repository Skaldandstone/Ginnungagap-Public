#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "EquipmentSystem.generated.h"

UENUM(BlueprintType)
enum class EEquipmentType : uint8
{
    HelmetVisor UMETA(DisplayName="Helmet Visor"),
    ThermalPlating UMETA(DisplayName="Thermal Plating"),
    RadiationShield UMETA(DisplayName="Radiation Shield"),
    PressureSeal UMETA(DisplayName="Pressure Seal"),
    ArmorPlating UMETA(DisplayName="Armor Plating"),
    OxygenFilter UMETA(DisplayName="Oxygen Filter")
};

UENUM(BlueprintType)
enum class EEquipmentSlot : uint8
{
    Head UMETA(DisplayName="Head"),
    Chest UMETA(DisplayName="Chest"),
    Arms UMETA(DisplayName="Arms"),
    Legs UMETA(DisplayName="Legs"),
    Accessory UMETA(DisplayName="Accessory")
};

USTRUCT(BlueprintType)
struct FEquipmentStats
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float RadiationResistance = 0.0f; // Percentage (0-100)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float ThermalResistance = 0.0f; // Temperature offset in Celsius

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float PressureResistance = 0.0f; // kPa threshold

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float SuitIntegrityBonus = 0.0f; // Percentage boost (0-50)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float MovementSpeedBonus = 0.0f; // Percentage (negative = slowdown)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float DustProtection = 0.0f; // Percentage reduction in dust damage (0-100)
};

USTRUCT(BlueprintType)
struct FEquipmentItem
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    EEquipmentType Type = EEquipmentType::HelmetVisor;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    EEquipmentSlot Slot = EEquipmentSlot::Head;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    FString DisplayName = TEXT("Equipment");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    FString Description;

    /** Pre-expedition quartermaster budget consumed while this item is in the loadout. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment", meta=(ClampMin="0"))
    int32 SupplyCost = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    FEquipmentStats Stats;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float MaxDurability = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float CurrentDurability = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    float DurabilityLossPerSecond = 0.1f; // Degrades over time in hazardous zones
};

USTRUCT(BlueprintType)
struct FEquipmentSlotState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    bool bEquipped = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Equipment")
    FEquipmentItem EquippedItem;
};
