#pragma once

#include "CoreMinimal.h"
#include "ThreatTypes.generated.h"

UENUM(BlueprintType)
enum class EThreatFaction : uint8
{
    Pirates,
    Rebels,
    Alien
};

UENUM(BlueprintType)
enum class EThreatBodyPlan : uint8
{
    Bipedal,
    Quadrupedal,
    Arachnoped
};

UENUM(BlueprintType)
enum class EThreatCombatRole : uint8
{
    Breacher,
    Gunner,
    Saboteur,
    Heavy,
    Hunter,
    Stalker,
    Ambusher
};

UENUM(BlueprintType)
enum class EThreatArchetype : uint8
{
    PirateBreacher,
    PirateGunner,
    RebelSaboteur,
    RebelHeavy,
    AlienBipedHunter,
    AlienQuadrupedStalker,
    AlienArachnopedAmbusher
};

UENUM(BlueprintType)
enum class EThreatEncounterPreset : uint8
{
    Custom,
    PirateBoarding,
    RebelTakeover,
    AlienHuntingPack,
    AlienBrood,
    MixedAlienIncursion
};

UENUM(BlueprintType)
enum class EThreatEncounterState : uint8
{
    Dormant,
    Active,
    Completed,
    Cancelled
};

USTRUCT(BlueprintType)
struct FThreatSpawnGroup
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    EThreatArchetype Archetype = EThreatArchetype::PirateBreacher;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat", meta=(ClampMin="1", ClampMax="32"))
    int32 Count = 1;
};

USTRUCT(BlueprintType)
struct FThreatEncounterDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    FName EncounterId = TEXT("MissionThreat");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    FText DisplayName = NSLOCTEXT("Threats", "DefaultEncounter", "Hostile incursion");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    TArray<FThreatSpawnGroup> SpawnGroups;

    /** A primary antagonist registers a required eliminate/repel objective. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Mission")
    bool bPrimaryAntagonist = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Mission")
    bool bBlocksJumpWhileActive = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Mission", meta=(ClampMin="0"))
    int32 CurrencyReward = 300;

    /** Most non-Bloom encounters leave this false, so they can exist in a clean run. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Bloom")
    bool bRequiresBloom = false;

    /** If true, this encounter remains eligible while the Bloom is also active. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Bloom")
    bool bCanOverlapBloom = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Spawning")
    bool bPreferShipSections = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Spawning", meta=(ClampMin="100.0"))
    float FallbackSpawnRadius = 1400.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Spawning")
    int32 RandomSeed = 9173;

    int32 GetTotalThreatCount() const
    {
        int32 Total = 0;
        for (const FThreatSpawnGroup& Group : SpawnGroups)
        {
            Total += FMath::Max(0, Group.Count);
        }
        return Total;
    }
};

USTRUCT(BlueprintType)
struct FThreatArchetypeTuning
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    FText DisplayName;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    EThreatFaction Faction = EThreatFaction::Pirates;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    EThreatBodyPlan BodyPlan = EThreatBodyPlan::Bipedal;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    EThreatCombatRole CombatRole = EThreatCombatRole::Breacher;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float MaxHealth = 100.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float DamagePerAttack = 10.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float AttackRange = 150.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float AttackInterval = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float PatrolSpeed = 280.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float ChaseSpeed = 480.0f;

    UPROPERTY(BlueprintReadOnly, Category="Threat")
    float DetectionRange = 1500.0f;
};
