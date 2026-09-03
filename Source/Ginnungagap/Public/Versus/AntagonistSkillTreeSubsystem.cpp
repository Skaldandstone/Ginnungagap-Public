#include "Versus/AntagonistSkillTreeSubsystem.h"

void UAntagonistSkillTreeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ResetToDefaultSkillTrees();
}

void UAntagonistSkillTreeSubsystem::ResetToDefaultSkillTrees()
{
	Skills.Reset();

	AddSkill(EAntagonistFaction::Bloom, TEXT("Bloom_CreepingMycelium"),
		NSLOCTEXT("VersusSkills", "BloomCreepingMycelium", "Creeping Mycelium"),
		NSLOCTEXT("VersusSkills", "BloomCreepingMyceliumDesc", "Corruption spreads farther from each established node."),
		1, 1, TEXT("CorruptionRadius"), 0.20f);
	AddSkill(EAntagonistFaction::Bloom, TEXT("Bloom_MimeticSpores"),
		NSLOCTEXT("VersusSkills", "BloomMimeticSpores", "Mimetic Spores"),
		NSLOCTEXT("VersusSkills", "BloomMimeticSporesDesc", "Spores create more convincing sensor echoes and false contacts."),
		2, 2, TEXT("SensorDeception"), 0.25f, {TEXT("Bloom_CreepingMycelium")});
	AddSkill(EAntagonistFaction::Bloom, TEXT("Bloom_PuppeteerNetwork"),
		NSLOCTEXT("VersusSkills", "BloomPuppeteerNetwork", "Puppeteer Network"),
		NSLOCTEXT("VersusSkills", "BloomPuppeteerNetworkDesc", "Possessed hosts share awareness and recover abilities faster."),
		3, 3, TEXT("HostAbilityCooldown"), -0.20f, {TEXT("Bloom_MimeticSpores")});
	AddSkill(EAntagonistFaction::Bloom, TEXT("Bloom_OneOrganism"),
		NSLOCTEXT("VersusSkills", "BloomOneOrganism", "One Organism"),
		NSLOCTEXT("VersusSkills", "BloomOneOrganismDesc", "The Bloom may shift control between viable hosts after a host is destroyed."),
		5, 5, TEXT("HostTransfer"), 1.0f, {TEXT("Bloom_PuppeteerNetwork")});

	AddSkill(EAntagonistFaction::Pirates, TEXT("Pirate_BreachCharges"),
		NSLOCTEXT("VersusSkills", "PirateBreachCharges", "Shaped Breach Charges"),
		NSLOCTEXT("VersusSkills", "PirateBreachChargesDesc", "Doors and repairable ship fixtures take increased sabotage damage."),
		1, 1, TEXT("SabotageDamage"), 0.20f);
	AddSkill(EAntagonistFaction::Pirates, TEXT("Pirate_BlackMarketOptics"),
		NSLOCTEXT("VersusSkills", "PirateOptics", "Black-Market Optics"),
		NSLOCTEXT("VersusSkills", "PirateOpticsDesc", "Boarders identify isolated crew at greater range."),
		2, 2, TEXT("DetectionRange"), 0.25f, {TEXT("Pirate_BreachCharges")});
	AddSkill(EAntagonistFaction::Pirates, TEXT("Pirate_PrizeCrew"),
		NSLOCTEXT("VersusSkills", "PiratePrizeCrew", "Prize Crew"),
		NSLOCTEXT("VersusSkills", "PiratePrizeCrewDesc", "Captured systems generate reinforcement charge for the pirate team."),
		4, 4, TEXT("ReinforcementCharge"), 0.30f, {TEXT("Pirate_BlackMarketOptics")});

	AddSkill(EAntagonistFaction::Rebels, TEXT("Rebel_InsideKnowledge"),
		NSLOCTEXT("VersusSkills", "RebelInsideKnowledge", "Inside Knowledge"),
		NSLOCTEXT("VersusSkills", "RebelInsideKnowledgeDesc", "Reveal nearby maintenance routes and vulnerable power nodes."),
		1, 1, TEXT("SystemIntelRange"), 0.25f);
	AddSkill(EAntagonistFaction::Rebels, TEXT("Rebel_CascadeFailure"),
		NSLOCTEXT("VersusSkills", "RebelCascadeFailure", "Cascade Failure"),
		NSLOCTEXT("VersusSkills", "RebelCascadeFailureDesc", "Sabotaged power nodes impose a short repair penalty on connected systems."),
		3, 3, TEXT("ConnectedRepairPenalty"), 0.25f, {TEXT("Rebel_InsideKnowledge")});
	AddSkill(EAntagonistFaction::Rebels, TEXT("Rebel_MutinyProtocol"),
		NSLOCTEXT("VersusSkills", "RebelMutinyProtocol", "Mutiny Protocol"),
		NSLOCTEXT("VersusSkills", "RebelMutinyProtocolDesc", "Coordinated sabotage briefly obscures crew objective telemetry."),
		5, 5, TEXT("ObjectiveBlackout"), 1.0f, {TEXT("Rebel_CascadeFailure")});

	AddSkill(EAntagonistFaction::Alien, TEXT("Alien_PackScent"),
		NSLOCTEXT("VersusSkills", "AlienPackScent", "Pack Scent"),
		NSLOCTEXT("VersusSkills", "AlienPackScentDesc", "Damaged crew remain trackable for longer."),
		1, 1, TEXT("TrackDuration"), 0.30f);
	AddSkill(EAntagonistFaction::Alien, TEXT("Alien_VentStalker"),
		NSLOCTEXT("VersusSkills", "AlienVentStalker", "Vent Stalker"),
		NSLOCTEXT("VersusSkills", "AlienVentStalkerDesc", "Traversal through ambush routes is faster and quieter."),
		2, 2, TEXT("AmbushTraversalSpeed"), 0.25f, {TEXT("Alien_PackScent")});
	AddSkill(EAntagonistFaction::Alien, TEXT("Alien_ApexBrood"),
		NSLOCTEXT("VersusSkills", "AlienApexBrood", "Apex Brood"),
		NSLOCTEXT("VersusSkills", "AlienApexBroodDesc", "Nearby creatures gain resilience while the player remains alive."),
		5, 5, TEXT("PackDamageResistance"), 0.20f, {TEXT("Alien_VentStalker")});
}

void UAntagonistSkillTreeSubsystem::AddSkill(EAntagonistFaction Faction, FName Id, const FText& Name,
	const FText& Description, int32 Tier, int32 Cost, FName EffectId, float Magnitude,
	TArray<FName> Prerequisites)
{
	FAntagonistSkill& Skill = Skills.AddDefaulted_GetRef();
	Skill.SkillId = Id;
	Skill.DisplayName = Name;
	Skill.Description = Description;
	Skill.Faction = Faction;
	Skill.Tier = Tier;
	Skill.PointCost = Cost;
	Skill.EffectId = EffectId;
	Skill.EffectMagnitude = Magnitude;
	Skill.PrerequisiteSkillIds = MoveTemp(Prerequisites);
}

TArray<FAntagonistSkill> UAntagonistSkillTreeSubsystem::GetSkillsForFaction(EAntagonistFaction Faction) const
{
	TArray<FAntagonistSkill> Result;
	for (const FAntagonistSkill& Skill : Skills)
	{
		if (Skill.Faction == Faction)
		{
			Result.Add(Skill);
		}
	}
	return Result;
}

TArray<FAntagonistSkill> UAntagonistSkillTreeSubsystem::GetSkillsForFactionAndTier(
	EAntagonistFaction Faction, int32 Tier) const
{
	TArray<FAntagonistSkill> Result;
	for (const FAntagonistSkill& Skill : Skills)
	{
		if (Skill.Faction == Faction && Skill.Tier == Tier)
		{
			Result.Add(Skill);
		}
	}
	return Result;
}

FAntagonistSkill UAntagonistSkillTreeSubsystem::GetSkill(FName SkillId) const
{
	for (const FAntagonistSkill& Skill : Skills)
	{
		if (Skill.SkillId == SkillId)
		{
			return Skill;
		}
	}
	return FAntagonistSkill();
}

bool UAntagonistSkillTreeSubsystem::CanUnlockSkill(FName SkillId, EAntagonistFaction Faction,
	const TArray<FName>& UnlockedSkillIds, int32 AvailablePoints) const
{
	const FAntagonistSkill Skill = GetSkill(SkillId);
	if (!Skill.IsDefined() || Skill.Faction != Faction || UnlockedSkillIds.Contains(SkillId)
		|| AvailablePoints < Skill.PointCost)
	{
		return false;
	}
	for (const FName Prerequisite : Skill.PrerequisiteSkillIds)
	{
		if (!UnlockedSkillIds.Contains(Prerequisite))
		{
			return false;
		}
	}
	return true;
}
