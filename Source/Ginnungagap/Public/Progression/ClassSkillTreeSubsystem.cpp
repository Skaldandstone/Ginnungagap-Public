// Copyright Epic Games, Inc. All Rights Reserved.

#include "Progression/ClassSkillTreeSubsystem.h"

#define LOCTEXT_NAMESPACE "ClassSkills"

void UClassSkillTreeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ResetToDefaultSkills();
}

void UClassSkillTreeSubsystem::ResetToDefaultSkills()
{
	AllSkills.Empty();

	// ---------------------------------------------------------------------------------------
	// General training. Anyone who has held a berth on a deep-space salvage crew has done this,
	// so every role can buy it. These are habits and procedure, never carried equipment, which is
	// why they are all passive.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Gen_VacuumDiscipline"),
		LOCTEXT("VacuumDiscipline", "Vacuum Discipline"),
		LOCTEXT("VacuumDisciplineDesc",
			"Drilled handhold-to-handhold movement. You stop rotations before they build instead of "
			"fighting them once they have."),
		1, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::MicrogravityControl, 0.06f, 3, 2);

	AddSkill(TEXT("Gen_BreathingEconomy"),
		LOCTEXT("BreathingEconomy", "Breathing Economy"),
		LOCTEXT("BreathingEconomyDesc",
			"Paced breathing under load. A calm spacer draws measurably less from the tank than one "
			"working at the same rate on adrenaline."),
		1, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::OxygenConsumption, 0.05f, 3, 2);

	AddSkill(TEXT("Gen_SuitFieldRepair"),
		LOCTEXT("SuitFieldRepair", "Suit Field Repair"),
		LOCTEXT("SuitFieldRepairDesc",
			"Finding and sealing a leak by feel, in the dark, before the alarm finishes sounding. "
			"Slows how fast a compromised suit loses pressure."),
		1, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::SuitSealIntegrity, 0.05f, 3, 2);

	AddSkill(TEXT("Gen_PropellantDiscipline"),
		LOCTEXT("PropellantDiscipline", "Propellant Discipline"),
		LOCTEXT("PropellantDisciplineDesc",
			"Short corrective burns and long coasts. Cuts thruster propellant use without giving you "
			"a larger tank."),
		2, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::ThrusterEfficiency, 0.10f, 2, 3, {TEXT("Gen_VacuumDiscipline")});

	AddSkill(TEXT("Gen_HazardProcedure"),
		LOCTEXT("HazardProcedure", "Hazard Procedure"),
		LOCTEXT("HazardProcedureDesc",
			"Approach angles, dwell limits, decontamination order. Procedure keeps exposure down "
			"where improvisation does not."),
		2, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::ExposureResistance, 0.10f, 2, 3, {TEXT("Gen_SuitFieldRepair")});

	// ---------------------------------------------------------------------------------------
	// General procedures. Drilled actions rather than habits: equipping one grants the right to
	// trigger it, not its effect. Magnitudes are large because the window is short and the cooldown
	// means "should I spend it now" is never a free question.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Act_EmergencyReseal"),
		LOCTEXT("EmergencyReseal", "Emergency Reseal"),
		LOCTEXT("EmergencyResealDesc",
			"Slam resin over a breach and hold it while it cures. For as long as your hand is on it the "
			"suit holds pressure far better -- and you are doing nothing else."),
		2, EPressureSuitRole::Scientist, true, ESkillActivation::Active,
		SkillEffects::SuitSealIntegrity, 0.30f, 3, 3, {TEXT("Gen_SuitFieldRepair")},
		45.0f, 180.0f, 2);

	AddSkill(TEXT("Act_ControlledBreathing"),
		LOCTEXT("ControlledBreathing", "Controlled Breathing"),
		LOCTEXT("ControlledBreathingDesc",
			"Deliberately drop your breathing rate and ride it out. Buys a long stretch of very low "
			"consumption, at the cost of doing anything strenuous while it lasts."),
		3, EPressureSuitRole::Scientist, true, ESkillActivation::Active,
		SkillEffects::OxygenConsumption, 0.22f, 3, 5, {TEXT("Gen_BreathingEconomy")},
		60.0f, 150.0f, 0);

	AddSkill(TEXT("Act_ShieldingPosture"),
		LOCTEXT("ShieldingPosture", "Shielding Posture"),
		LOCTEXT("ShieldingPostureDesc",
			"Put the densest part of the suit between you and the source and stay there. Cuts the dose "
			"sharply for a short window, if you know which way the source is."),
		4, EPressureSuitRole::Scientist, true, ESkillActivation::Active,
		SkillEffects::RadiationShielding, 0.18f, 2, 8, {TEXT("Gen_HazardProcedure")},
		30.0f, 210.0f, 3);

	// ---------------------------------------------------------------------------------------
	// Former Crew skills, now general. These were always baseline spacer competence rather than a
	// specialism -- which is why "Standard Crew" duplicated the General tree instead of standing
	// beside it. Rehomed rather than deleted: every one drives an effect with a live consumer.
	//
	// The IDs moved from Crew_ to Gen_ so the prefix keeps telling the truth about which tree a
	// skill is in. Any saved rank against the old IDs is dropped, which is the correct trade this
	// far from release.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Gen_StationKeeping"),
		LOCTEXT("StationKeeping", "Station Keeping"),
		LOCTEXT("StationKeepingDesc",
			"Holding a working position against drift with minimal input, so both hands stay free for "
			"the job instead of the handhold."),
		2, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::MicrogravityControl, 0.08f, 3, 3, {TEXT("Gen_VacuumDiscipline")});

	AddSkill(TEXT("Gen_VeteranSpacer"),
		LOCTEXT("VeteranSpacer", "Veteran Spacer"),
		LOCTEXT("VeteranSpacerDesc",
			"Years of accumulated tolerance. The body stops treating vacuum work as an emergency and "
			"settles into it, drawing less air for the same effort."),
		4, EPressureSuitRole::Scientist, true, ESkillActivation::Passive,
		SkillEffects::OxygenConsumption, 0.06f, 3, 8, {TEXT("Gen_StationKeeping")});

	AddSkill(TEXT("Gen_BurnPlanning"),
		LOCTEXT("BurnPlanning", "Burn Planning"),
		LOCTEXT("BurnPlanningDesc",
			"Work the whole translation out before touching the throttle, then fly it as one clean "
			"sequence instead of correcting the entire way across."),
		3, EPressureSuitRole::Scientist, true, ESkillActivation::Active,
		SkillEffects::ThrusterEfficiency, 0.25f, 3, 5, {TEXT("Gen_PropellantDiscipline")},
		45.0f, 120.0f, 0);

	AddSkill(TEXT("Gen_RunSilent"),
		LOCTEXT("RunSilent", "Run Silent"),
		LOCTEXT("RunSilentDesc",
			"Lamps off, deliberate pace, nothing swinging loose. You become very hard to pick out for a "
			"short while, and nearly blind for the same stretch."),
		5, EPressureSuitRole::Scientist, true, ESkillActivation::Active,
		SkillEffects::VisibilitySignature, 0.35f, 2, 12, {TEXT("Gen_BurnPlanning")},
		30.0f, 180.0f, 2);

	// ---------------------------------------------------------------------------------------
	// Science -- reads the infestation. Every other role learns what the Bloom does to them; this
	// one learns where it is, how much of it there is, and which way it is spreading, early enough
	// for that to still be a choice rather than a report.
	//
	// Both new effects gate something the scanner already does and currently does identically for
	// everyone: it clamps every reading up to a detection floor, and it only reaches one
	// compartment. Neither limit was ever a decision anyone could influence.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Sci_FieldSpectroscopy"),
		LOCTEXT("FieldSpectroscopy", "Field Spectroscopy"),
		LOCTEXT("FieldSpectroscopyDesc",
			"Reading the trace signature rather than the alarm threshold. Below the scanner's floor a "
			"seeded compartment and a clean one look identical to everyone else; you can tell them "
			"apart while there is still time for it to matter."),
		1, EPressureSuitRole::Scientist, false, ESkillActivation::Passive,
		SkillEffects::ScanSensitivity, 0.15f, 3, 3);

	AddSkill(TEXT("Sci_DeepSurvey"),
		LOCTEXT("DeepSurvey", "Deep Survey"),
		LOCTEXT("DeepSurveyDesc",
			"Working a reading outward through the bulkheads instead of standing in each compartment "
			"to learn about it. Turns the scanner from a description of where you are into a reason "
			"to go a different way."),
		2, EPressureSuitRole::Scientist, false, ESkillActivation::Passive,
		SkillEffects::ScanRange, 1.0f, 2, 5, {TEXT("Sci_FieldSpectroscopy")});

	AddSkill(TEXT("Sci_ContaminantProtocols"),
		LOCTEXT("ContaminantProtocols", "Contaminant Protocols"),
		LOCTEXT("ContaminantProtocolsDesc",
			"Knowing exactly what you are standing in changes how you stand in it. Deliberate handling "
			"discipline around a live growth, rather than the general caution everyone else applies to "
			"everything equally."),
		3, EPressureSuitRole::Scientist, false, ESkillActivation::Passive,
		SkillEffects::ExposureResistance, 0.10f, 3, 6, {TEXT("Sci_FieldSpectroscopy")});

	AddSkill(TEXT("Sci_FullSpectrumSweep"),
		LOCTEXT("FullSpectrumSweep", "Full Spectrum Sweep"),
		LOCTEXT("FullSpectrumSweepDesc",
			"Drive the scanner far past its rated duty cycle for a short window and read the whole "
			"deck at once. Answers the question of where it actually is, and announces that you asked."),
		4, EPressureSuitRole::Scientist, false, ESkillActivation::Active,
		SkillEffects::ScanRange, 2.0f, 2, 10, {TEXT("Sci_DeepSurvey")},
		20.0f, 150.0f, 3);

	// ---------------------------------------------------------------------------------------
	// Engineering -- keeps the ship alive. Competence here is measured in what a single pass at a
	// fault actually accomplishes.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Eng_SystemsFamiliarity"),
		LOCTEXT("SystemsFamiliarity", "Systems Familiarity"),
		LOCTEXT("SystemsFamiliarityDesc",
			"Knowing where the fault usually is before opening the panel. Every repair pass accomplishes "
			"more."),
		2, EPressureSuitRole::Engineering, false, ESkillActivation::Passive,
		SkillEffects::RepairEffectiveness, 0.10f, 3, 3, {TEXT("Gen_SuitFieldRepair")});

	AddSkill(TEXT("Eng_SuitTechnician"),
		LOCTEXT("SuitTechnician", "Suit Technician"),
		LOCTEXT("SuitTechnicianDesc",
			"You maintain your own seals to yard standard rather than crew standard, and it shows when "
			"the compartment vents."),
		4, EPressureSuitRole::Engineering, false, ESkillActivation::Passive,
		SkillEffects::SuitSealIntegrity, 0.08f, 3, 8, {TEXT("Eng_SystemsFamiliarity")});

	AddSkill(TEXT("Eng_FieldExpedient"),
		LOCTEXT("FieldExpedient", "Field Expedient"),
		LOCTEXT("FieldExpedientDesc",
			"Stop doing it properly and start doing it now. A burst of work that holds, mostly, long "
			"enough to matter."),
		3, EPressureSuitRole::Engineering, false, ESkillActivation::Active,
		SkillEffects::RepairEffectiveness, 0.40f, 3, 5, {TEXT("Eng_SystemsFamiliarity")},
		60.0f, 150.0f, 0);

	AddSkill(TEXT("Eng_PowerReroute"),
		LOCTEXT("PowerReroute", "Power Reroute"),
		LOCTEXT("PowerRerouteDesc",
			"Jumper the dead section entirely rather than repairing it. Briefly turns a wrecked "
			"distribution path into a working one, and you only get to do it so often."),
		5, EPressureSuitRole::Engineering, false, ESkillActivation::Active,
		SkillEffects::RepairEffectiveness, 0.50f, 2, 12, {TEXT("Eng_FieldExpedient")},
		45.0f, 240.0f, 2);

	// ---------------------------------------------------------------------------------------
	// Medical. Science is its own role now, so this line is purely clinical. Note there is no
	// oxygen *regeneration* anywhere in it: training
	// cannot manufacture air. It lowers what the body spends and improves what treatment achieves.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Med_TraumaResponse"),
		LOCTEXT("TraumaResponse", "Trauma Response"),
		LOCTEXT("TraumaResponseDesc",
			"Triage and stabilisation under pressure, through a suit, with gloves on. Each intervention "
			"achieves more before the patient destabilises."),
		2, EPressureSuitRole::Medical, false, ESkillActivation::Passive,
		SkillEffects::MedicalEffectiveness, 0.12f, 3, 3, {TEXT("Gen_BreathingEconomy")});

	AddSkill(TEXT("Med_MetabolicManagement"),
		LOCTEXT("MetabolicManagement", "Metabolic Management"),
		LOCTEXT("MetabolicManagementDesc",
			"Pacing exertion against the tank rather than against the clock. Lowers consumption without "
			"any change to suit hardware."),
		4, EPressureSuitRole::Medical, false, ESkillActivation::Passive,
		SkillEffects::OxygenConsumption, 0.07f, 3, 8, {TEXT("Med_TraumaResponse")});

	AddSkill(TEXT("Med_TriageFocus"),
		LOCTEXT("TriageFocus", "Triage Focus"),
		LOCTEXT("TriageFocusDesc",
			"Everything else stops existing. For a short stretch you work a casualty with an "
			"effectiveness you cannot sustain, and should not have to."),
		3, EPressureSuitRole::Medical, false, ESkillActivation::Active,
		SkillEffects::MedicalEffectiveness, 0.45f, 3, 5, {TEXT("Med_TraumaResponse")},
		45.0f, 150.0f, 0);

	AddSkill(TEXT("Med_ExposureProtocol"),
		LOCTEXT("ExposureProtocol", "Exposure Protocol"),
		LOCTEXT("ExposureProtocolDesc",
			"Push chelation and countermeasures on the spot rather than after extraction. Blunts what "
			"the environment is doing to a body while it is still doing it."),
		5, EPressureSuitRole::Medical, false, ESkillActivation::Active,
		SkillEffects::ExposureResistance, 0.35f, 2, 12, {TEXT("Gen_HazardProcedure")},
		60.0f, 210.0f, 2);

	// ---------------------------------------------------------------------------------------
	// Security / Recovery. Deliberately grants no movement speed anywhere: armour is mass, and a
	// skill that made heavy protection faster would invert the same rule equipment already follows.
	// ---------------------------------------------------------------------------------------

	AddSkill(TEXT("Sec_ArmorDiscipline"),
		LOCTEXT("ArmorDiscipline", "Armour Discipline"),
		LOCTEXT("ArmorDisciplineDesc",
			"Wearing plate correctly: seated, strapped, and checked. It does not make the plate lighter, "
			"only far more likely to hold."),
		2, EPressureSuitRole::Security, false, ESkillActivation::Passive,
		SkillEffects::SuitSealIntegrity, 0.07f, 3, 3, {TEXT("Gen_SuitFieldRepair")});

	AddSkill(TEXT("Sec_Composure"),
		LOCTEXT("Composure", "Composure"),
		LOCTEXT("ComposureDesc",
			"Staying oriented when something is actively trying to disorient you. Holds your footing "
			"when the deck stops cooperating."),
		4, EPressureSuitRole::Security, false, ESkillActivation::Passive,
		SkillEffects::MicrogravityControl, 0.07f, 3, 8, {TEXT("Sec_ArmorDiscipline")});

	AddSkill(TEXT("Sec_SoundDiscipline"),
		LOCTEXT("SoundDiscipline", "Sound Discipline"),
		LOCTEXT("SoundDisciplineDesc",
			"Move at the pace that makes no noise rather than the pace you want. Almost silent while it "
			"lasts, and considerably slower than walking away would be."),
		3, EPressureSuitRole::Security, false, ESkillActivation::Active,
		SkillEffects::MovementNoise, 0.40f, 3, 5, {TEXT("Gen_VacuumDiscipline")},
		40.0f, 120.0f, 0);

	AddSkill(TEXT("Sec_CasualtyRecovery"),
		LOCTEXT("CasualtyRecovery", "Casualty Recovery"),
		LOCTEXT("CasualtyRecoveryDesc",
			"Get them stable enough to move, then move them. Not a medical specialist's work -- enough "
			"to reach an airlock with someone still breathing."),
		5, EPressureSuitRole::Security, false, ESkillActivation::Active,
		SkillEffects::MedicalEffectiveness, 0.30f, 2, 12, {TEXT("Sec_ArmorDiscipline")},
		45.0f, 240.0f, 2);
}

void UClassSkillTreeSubsystem::AddSkill(const FString& ID, const FText& DisplayName, const FText& Description,
	int32 Tier, EPressureSuitRole Role, bool bGeneral, ESkillActivation Activation,
	FName EffectId, float MagnitudePerRank, int32 MaxRank, int32 PointCost,
	const TArray<FString>& Prerequisites,
	float DurationSeconds, float CooldownSeconds, int32 ChargesPerRun)
{
	FClassSkill Skill;
	Skill.SkillID = ID;
	Skill.DisplayName = DisplayName;
	Skill.Description = Description;
	Skill.Tier = Tier;
	Skill.AssociatedRole = Role;
	Skill.bIsGeneralSkill = bGeneral;
	Skill.Activation = Activation;
	Skill.EffectId = EffectId;
	Skill.MagnitudePerRank = MagnitudePerRank;
	Skill.MaxRank = FMath::Max(1, MaxRank);
	Skill.PointCostToUnlock = PointCost;
	// Currency is the slower alternative route to the same node, priced so that points remain the
	// preferred currency for anyone actually completing runs.
	Skill.CurrencyCostToUnlock = PointCost * 20;
	Skill.Prerequisites = Prerequisites;
	Skill.DurationSeconds = DurationSeconds;
	Skill.CooldownSeconds = CooldownSeconds;
	Skill.ChargesPerRun = ChargesPerRun;
	AllSkills.Add(Skill);
}

const FClassSkill* UClassSkillTreeSubsystem::FindSkill(const FString& SkillID) const
{
	return AllSkills.FindByPredicate(
		[&SkillID](const FClassSkill& Skill) { return Skill.SkillID == SkillID; });
}

bool UClassSkillTreeSubsystem::IsSkillVisibleToRole(const FClassSkill& Skill, EPressureSuitRole Role) const
{
	return Skill.bIsGeneralSkill || Skill.AssociatedRole == Role;
}

TArray<FClassSkill> UClassSkillTreeSubsystem::GetAllSkillsForRole(EPressureSuitRole Role) const
{
	TArray<FClassSkill> RoleSkills;
	for (const FClassSkill& Skill : AllSkills)
	{
		if (IsSkillVisibleToRole(Skill, Role))
		{
			RoleSkills.Add(Skill);
		}
	}
	return RoleSkills;
}

TArray<FClassSkill> UClassSkillTreeSubsystem::GetSkillsForRoleAndTier(EPressureSuitRole Role, int32 Tier) const
{
	TArray<FClassSkill> TierSkills;
	for (const FClassSkill& Skill : AllSkills)
	{
		if (Skill.Tier == Tier && IsSkillVisibleToRole(Skill, Role))
		{
			TierSkills.Add(Skill);
		}
	}
	return TierSkills;
}

TArray<FClassSkill> UClassSkillTreeSubsystem::GetGeneralSkills() const
{
	TArray<FClassSkill> General;
	for (const FClassSkill& Skill : AllSkills)
	{
		if (Skill.bIsGeneralSkill)
		{
			General.Add(Skill);
		}
	}
	return General;
}

TArray<FClassSkill> UClassSkillTreeSubsystem::GetAvailableActiveSkills(EPressureSuitRole Role,
	const FClassSkillsArray& Owned) const
{
	TArray<FClassSkill> Available;
	for (const FClassSkill& Skill : AllSkills)
	{
		if (Skill.Activation == ESkillActivation::Active
			&& IsSkillVisibleToRole(Skill, Role)
			&& GetOwnedRank(Skill.SkillID, Owned) > 0)
		{
			Available.Add(Skill);
		}
	}
	return Available;
}

FClassSkill UClassSkillTreeSubsystem::GetSkillByID(const FString& SkillID) const
{
	if (const FClassSkill* Found = FindSkill(SkillID))
	{
		return *Found;
	}
	return FClassSkill();
}

bool UClassSkillTreeSubsystem::DoesSkillExist(const FString& SkillID) const
{
	return FindSkill(SkillID) != nullptr;
}

int32 UClassSkillTreeSubsystem::GetOwnedRank(const FString& SkillID, const FClassSkillsArray& Owned) const
{
	const int32* Rank = Owned.SkillRanks.Find(SkillID);
	return Rank ? FMath::Max(0, *Rank) : 0;
}

bool UClassSkillTreeSubsystem::IsSkillUnlocked(const FString& SkillID, const FClassSkillsArray& Owned) const
{
	return GetOwnedRank(SkillID, Owned) > 0;
}

bool UClassSkillTreeSubsystem::ArePrerequisitesMet(const FString& SkillID, const FClassSkillsArray& Owned) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill)
	{
		return false;
	}

	for (const FString& Prerequisite : Skill->Prerequisites)
	{
		if (GetOwnedRank(Prerequisite, Owned) <= 0)
		{
			return false;
		}
	}
	return true;
}

TArray<FString> UClassSkillTreeSubsystem::GetMissingPrerequisites(const FString& SkillID,
	const FClassSkillsArray& Owned) const
{
	TArray<FString> Missing;
	if (const FClassSkill* Skill = FindSkill(SkillID))
	{
		for (const FString& Prerequisite : Skill->Prerequisites)
		{
			if (GetOwnedRank(Prerequisite, Owned) <= 0)
			{
				Missing.Add(Prerequisite);
			}
		}
	}
	return Missing;
}

int32 UClassSkillTreeSubsystem::GetNextRankCost(const FString& SkillID, const FClassSkillsArray& Owned) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill)
	{
		return 0;
	}

	const int32 CurrentRank = GetOwnedRank(SkillID, Owned);
	if (CurrentRank >= Skill->MaxRank)
	{
		return 0;
	}

	// Each rank costs one base increment more than the last, so deepening a skill you already have
	// competes honestly against opening a new one rather than always being the cheaper habit.
	return Skill->PointCostToUnlock * (CurrentRank + 1);
}

int32 UClassSkillTreeSubsystem::GetNextRankCurrencyCost(const FString& SkillID, const FClassSkillsArray& Owned) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill)
	{
		return 0;
	}

	const int32 CurrentRank = GetOwnedRank(SkillID, Owned);
	if (CurrentRank >= Skill->MaxRank)
	{
		return 0;
	}
	return Skill->CurrencyCostToUnlock * (CurrentRank + 1);
}

bool UClassSkillTreeSubsystem::CanUnlockSkill(EPressureSuitRole Role, const FString& SkillID,
	const FClassSkillsArray& Owned, int32 AvailablePoints) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill || !IsSkillVisibleToRole(*Skill, Role))
	{
		return false;
	}

	if (GetOwnedRank(SkillID, Owned) >= Skill->MaxRank)
	{
		return false;
	}

	if (!ArePrerequisitesMet(SkillID, Owned))
	{
		return false;
	}

	return AvailablePoints >= GetNextRankCost(SkillID, Owned);
}

bool UClassSkillTreeSubsystem::CanEquipActiveSkill(EPressureSuitRole Role, const FString& SkillID,
	const FClassSkillsArray& Owned) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill || Skill->Activation != ESkillActivation::Active || !IsSkillVisibleToRole(*Skill, Role))
	{
		return false;
	}

	if (GetOwnedRank(SkillID, Owned) <= 0 || Owned.EquippedActiveSkills.Contains(SkillID))
	{
		return false;
	}

	return Owned.EquippedActiveSkills.Num() < FClassProgression::MaxEquippedActiveSkills;
}

TArray<int32> UClassSkillTreeSubsystem::GetAvailableTiersForRole(EPressureSuitRole Role) const
{
	TArray<int32> Tiers;
	for (const FClassSkill& Skill : AllSkills)
	{
		if (IsSkillVisibleToRole(Skill, Role))
		{
			Tiers.AddUnique(Skill.Tier);
		}
	}
	Tiers.Sort();
	return Tiers;
}

int32 UClassSkillTreeSubsystem::GetTotalSkillPointsSpentOnRole(EPressureSuitRole Role,
	const FClassSkillsArray& Owned) const
{
	int32 TotalSpent = 0;
	for (const TPair<FString, int32>& Entry : Owned.SkillRanks)
	{
		const FClassSkill* Skill = FindSkill(Entry.Key);
		// General skills count here too. They are bought out of the same pool while playing this
		// role, so omitting them understates what the role actually cost -- the bug in the old
		// AssociatedClass-only filter.
		if (!Skill || !IsSkillVisibleToRole(*Skill, Role))
		{
			continue;
		}

		const int32 OwnedRank = FMath::Clamp(Entry.Value, 0, Skill->MaxRank);
		for (int32 Rank = 1; Rank <= OwnedRank; ++Rank)
		{
			TotalSpent += Skill->PointCostToUnlock * Rank;
		}
	}
	return TotalSpent;
}

float UClassSkillTreeSubsystem::GetPassiveEffectMagnitude(FName EffectId, const FClassSkillsArray& Owned) const
{
	float Total = 0.0f;
	for (const TPair<FString, int32>& Entry : Owned.SkillRanks)
	{
		const FClassSkill* Skill = FindSkill(Entry.Key);
		if (!Skill || Skill->EffectId != EffectId || Skill->Activation != ESkillActivation::Passive)
		{
			continue;
		}

		const int32 OwnedRank = FMath::Clamp(Entry.Value, 0, Skill->MaxRank);
		Total += Skill->MagnitudePerRank * static_cast<float>(OwnedRank);
	}
	return Total;
}

float UClassSkillTreeSubsystem::GetSkillEffectMagnitude(const FString& SkillID, int32 Rank) const
{
	const FClassSkill* Skill = FindSkill(SkillID);
	if (!Skill)
	{
		return 0.0f;
	}

	const int32 ClampedRank = FMath::Clamp(Rank, 0, Skill->MaxRank);
	return Skill->MagnitudePerRank * static_cast<float>(ClampedRank);
}

#undef LOCTEXT_NAMESPACE
