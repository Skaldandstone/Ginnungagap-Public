#pragma once

#include "CoreMinimal.h"
#include "Meta/CharacterProfile.h"
#include "PlayerClass.generated.h"

/**
 * Skills are defined against named effect IDs rather than one anonymous magnitude, so a skill's
 * meaning lives in the catalogue and the consumer decides how to apply it.
 *
 * Every ID here has a live consumer -- none are aspirational. If you add one, wire it in the same
 * change or it is just text on a button.
 *
 * Sign convention: magnitude is always the *beneficial* fraction, never a raw delta. A 0.05 on
 * OxygenConsumption means five percent less oxygen used, not five percent more. Consumers apply
 * the direction, so no catalogue entry ever carries a negative number and no skill can be made
 * accidentally harmful by a sign slip.
 */
namespace SkillEffects
{
	/** Reduces ACoopSurvivalCharacter::OxygenDrainMultiplier. Breathing economy, CO2 scrubbing. */
	const FName OxygenConsumption(TEXT("OxygenConsumption"));

	/** Raises the ShieldingFactor passed to ComputeRadiationDoseSv. Dosimetry, shelter discipline. */
	const FName RadiationShielding(TEXT("RadiationShielding"));

	/** Raises the integrity ComputePressureFailure sees. Field patching, seal maintenance. */
	const FName SuitSealIntegrity(TEXT("SuitSealIntegrity"));

	/** Raises the stability ComputeMicrogravityInstability sees. EVA and station-keeping training. */
	const FName MicrogravityControl(TEXT("MicrogravityControl"));

	/** Reduces ThrusterFuelDrainPerSecond. Propellant discipline, not a bigger tank. */
	const FName ThrusterEfficiency(TEXT("ThrusterEfficiency"));

	/** Reduces PlayerNoiseEmitterComponent movement loudness. Deliberate, quiet movement. */
	const FName MovementNoise(TEXT("MovementNoise"));

	/** Reduces PlayerVisibilityComponent exposure. Light discipline and use of cover. */
	const FName VisibilitySignature(TEXT("VisibilitySignature"));

	/** Scales maintenance-station EffectStrength. More accomplished per repair action. */
	const FName RepairEffectiveness(TEXT("RepairEffectiveness"));

	/** Scales treatment EffectStrength. Better trauma outcomes per intervention. */
	const FName MedicalEffectiveness(TEXT("MedicalEffectiveness"));

	/** Reduces the Intensity passed to ApplyEnvironmentalExposure. Correct protective procedure. */
	const FName ExposureResistance(TEXT("ExposureResistance"));

	/**
	 * How faint a contamination reading can be and still be told apart from nothing.
	 *
	 * The scanner clamps every reading up to its detection floor, so below that floor a seeded
	 * compartment and a clean one are indistinguishable to everyone. Lowering the floor is what
	 * lets a trained eye see the difference before it is obvious.
	 */
	const FName ScanSensitivity(TEXT("ScanSensitivity"));

	/**
	 * How many compartment hops the bio scanner reaches.
	 *
	 * Baseline is adjacent only, so the ship is read one room at a time. Extra reach is what turns
	 * scanning from a description of where you are standing into a routing decision.
	 */
	const FName ScanRange(TEXT("ScanRange"));
}

/**
 * Passive skills are training -- once learned they are simply true of the character, and they stay
 * in force on every run with no slot spent.
 *
 * Active skills are drilled procedures the player triggers deliberately. Equipping one does not
 * grant its effect; it grants the right to trigger it. The effect applies only for DurationSeconds
 * after activation, then lapses until the cooldown clears. That is what lets an active carry a far
 * larger magnitude than any passive without unbalancing the run: it is brief, deliberate, and
 * unavailable exactly when it has just been used.
 */
UENUM(BlueprintType)
enum class ESkillActivation : uint8
{
	Passive UMETA(DisplayName = "Passive (always in force once unlocked)"),
	Active  UMETA(DisplayName = "Active (equipped, then triggered)")
};

/**
 * One skill node. Prerequisites make this a tree rather than a shop: a tier-5 capstone cannot be
 * bought first simply because the points have accumulated.
 */
USTRUCT(BlueprintType)
struct FClassSkill
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	FString SkillID;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	int32 Tier = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	ESkillActivation Activation = ESkillActivation::Passive;

	/**
	 * Which role this belongs to. Meaningless when bIsGeneralSkill is true -- general skills are
	 * offered to every role, so read bIsGeneralSkill first.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	// Not the character starting default: this is which tree a skill belongs to, and AddSkill
	// always sets it. Borrowing the character default here would imply a link that is not real.
	EPressureSuitRole AssociatedRole = EPressureSuitRole::Engineering;

	/** General skills appear in every role's tree. Baseline competence any spacer would train. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	bool bIsGeneralSkill = false;

	/** One of SkillEffects. Empty means the skill is inert -- the catalogue should have none. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	FName EffectId;

	/**
	 * Beneficial fraction granted *per rank*. Total contribution is this times the owned rank, so
	 * levelling a skill deepens it rather than unlocking a separate node.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	float MagnitudePerRank = 0.0f;

	/** Ranks purchasable. Rank 1 is the initial unlock; each further rank costs progressively more. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	int32 MaxRank = 1;

	/** All must be owned at rank 1 or better before this becomes purchasable. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	TArray<FString> Prerequisites;

	/**
	 * Seconds the effect stays in force after triggering. Actives only; ignored for passives.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill|Activation")
	float DurationSeconds = 0.0f;

	/**
	 * Seconds before it can be triggered again, timed from activation rather than from expiry, so
	 * the figure a player reads is the full cycle rather than the gap after it lapses.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill|Activation")
	float CooldownSeconds = 0.0f;

	/**
	 * Triggers available per run. Zero means limited only by the cooldown. A charge count is the
	 * stronger constraint: it makes the decision "is this the moment", not "has it come back yet".
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill|Activation")
	int32 ChargesPerRun = 0;

	/** Cost of rank 1. Each subsequent rank costs one more increment than the last. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	int32 PointCostToUnlock = 2;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Skill")
	int32 CurrencyCostToUnlock = 0;
};

/** Ranks the player owns, keyed by SkillID. Absent or zero means not unlocked. */
USTRUCT(BlueprintType)
struct FClassSkillsArray
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Progression")
	TMap<FString, int32> SkillRanks;

	/**
	 * The payload: active skills brought into the run, in order. Never longer than
	 * FClassProgression::MaxEquippedActiveSkills; the subsystem enforces that on equip rather than
	 * trusting callers.
	 */
	UPROPERTY(BlueprintReadWrite, Category = "Progression")
	TArray<FString> EquippedActiveSkills;
};

USTRUCT(BlueprintType)
struct FClassProgression
{
	GENERATED_BODY()

	/** Payload size. Passives are unaffected; only triggered procedures compete for these slots. */
	static constexpr int32 MaxEquippedActiveSkills = 3;

	UPROPERTY(BlueprintReadWrite, Category = "Progression")
	EPressureSuitRole SelectedRole = GinnungagapDefaults::StartingSuitRole;

	UPROPERTY(BlueprintReadWrite, Category = "Progression")
	int32 TotalSkillPoints = 0;

	UPROPERTY(BlueprintReadWrite, Category = "Progression")
	FClassSkillsArray Skills;
};
