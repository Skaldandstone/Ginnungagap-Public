#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Versus/VersusTypes.h"
#include "AntagonistSkillTreeSubsystem.generated.h"

UCLASS()
class GINNUNGAGAP_API UAntagonistSkillTreeSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Restores the native faction trees; useful when a live ruleset or editor preview is reset. */
	UFUNCTION(BlueprintCallable, Category="Versus|Progression")
	void ResetToDefaultSkillTrees();

	UFUNCTION(BlueprintPure, Category="Versus|Progression")
	TArray<FAntagonistSkill> GetSkillsForFaction(EAntagonistFaction Faction) const;

	UFUNCTION(BlueprintPure, Category="Versus|Progression")
	TArray<FAntagonistSkill> GetSkillsForFactionAndTier(EAntagonistFaction Faction, int32 Tier) const;

	UFUNCTION(BlueprintPure, Category="Versus|Progression")
	FAntagonistSkill GetSkill(FName SkillId) const;

	UFUNCTION(BlueprintPure, Category="Versus|Progression")
	bool CanUnlockSkill(FName SkillId, EAntagonistFaction Faction,
		const TArray<FName>& UnlockedSkillIds, int32 AvailablePoints) const;

private:
	UPROPERTY()
	TArray<FAntagonistSkill> Skills;

	void AddSkill(EAntagonistFaction Faction, FName Id, const FText& Name, const FText& Description,
		int32 Tier, int32 Cost, FName EffectId, float Magnitude, TArray<FName> Prerequisites = {});
};
