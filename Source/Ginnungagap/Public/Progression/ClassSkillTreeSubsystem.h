#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Progression/PlayerClass.h"
#include "ClassSkillTreeSubsystem.generated.h"

/**
 * The skill catalogue and the rules for spending on it.
 *
 * Roles mirror EPressureSuitRole so the tree a player picks matches the oversuit they wear; there
 * is deliberately no second role vocabulary. Purchase rules live here rather than in the widget so
 * the UI and the save-side model cannot drift apart on what is legal.
 */
UCLASS()
class GINNUNGAGAP_API UClassSkillTreeSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Rebuilds the catalogue from code. Public so tests can populate without a subsystem collection. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	void ResetToDefaultSkills();

	/** Everything a role can see: its own skills plus the general set. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<FClassSkill> GetAllSkillsForRole(EPressureSuitRole Role) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<FClassSkill> GetSkillsForRoleAndTier(EPressureSuitRole Role, int32 Tier) const;

	/** The general set alone -- baseline competence shared by every role. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<FClassSkill> GetGeneralSkills() const;

	/** Unlocked actives a role may choose between when building a loadout. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<FClassSkill> GetAvailableActiveSkills(EPressureSuitRole Role, const FClassSkillsArray& Owned) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	FClassSkill GetSkillByID(const FString& SkillID) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool DoesSkillExist(const FString& SkillID) const;

	/** Ranks owned in SkillID; 0 when not unlocked. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	int32 GetOwnedRank(const FString& SkillID, const FClassSkillsArray& Owned) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool IsSkillUnlocked(const FString& SkillID, const FClassSkillsArray& Owned) const;

	/** True when every prerequisite of SkillID is owned at rank 1 or better. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool ArePrerequisitesMet(const FString& SkillID, const FClassSkillsArray& Owned) const;

	/** Prerequisites still missing, for explaining a locked node in the UI. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<FString> GetMissingPrerequisites(const FString& SkillID, const FClassSkillsArray& Owned) const;

	/**
	 * Cost of the *next* rank. Ranks get progressively more expensive, so deepening one skill
	 * competes honestly against broadening into a new one. Returns 0 when already at MaxRank.
	 */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	int32 GetNextRankCost(const FString& SkillID, const FClassSkillsArray& Owned) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	int32 GetNextRankCurrencyCost(const FString& SkillID, const FClassSkillsArray& Owned) const;

	/**
	 * Full purchase gate: the skill exists, belongs to this role, is below MaxRank, has its
	 * prerequisites met, and the next rank is affordable.
	 */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool CanUnlockSkill(EPressureSuitRole Role, const FString& SkillID,
		const FClassSkillsArray& Owned, int32 AvailablePoints) const;

	/** Whether SkillID may be added to the loadout: unlocked, active, role-legal, and slots free. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool CanEquipActiveSkill(EPressureSuitRole Role, const FString& SkillID, const FClassSkillsArray& Owned) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	TArray<int32> GetAvailableTiersForRole(EPressureSuitRole Role) const;

	/** Points sunk into a role's tree, counting general skills bought while playing it. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	int32 GetTotalSkillPointsSpentOnRole(EPressureSuitRole Role, const FClassSkillsArray& Owned) const;

	/**
	 * Summed magnitude of EffectId across unlocked *passives* only.
	 *
	 * Actives are deliberately excluded: equipping one grants the right to trigger it, not its
	 * effect, so whether it is contributing depends on runtime state this subsystem does not hold.
	 * UClassSkillComponent combines this with its own live activation windows -- ask it, not this,
	 * for what a character is actually benefiting from.
	 */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	float GetPassiveEffectMagnitude(FName EffectId, const FClassSkillsArray& Owned) const;

	/** Magnitude one skill contributes at a given rank, for the activation runtime and for UI. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	float GetSkillEffectMagnitude(const FString& SkillID, int32 Rank) const;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool IsSkillVisibleToRole(const FClassSkill& Skill, EPressureSuitRole Role) const;

private:
	UPROPERTY()
	TArray<FClassSkill> AllSkills;

	void AddSkill(const FString& ID, const FText& DisplayName, const FText& Description,
		int32 Tier, EPressureSuitRole Role, bool bGeneral, ESkillActivation Activation,
		FName EffectId, float MagnitudePerRank, int32 MaxRank, int32 PointCost,
		const TArray<FString>& Prerequisites = {},
		float DurationSeconds = 0.0f, float CooldownSeconds = 0.0f, int32 ChargesPerRun = 0);

	const FClassSkill* FindSkill(const FString& SkillID) const;
};
