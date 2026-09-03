#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Progression/ClassSkillTreeSubsystem.h"

/**
 * The class tree previously defined effects nothing consumed and gated nothing, so a tier-5
 * capstone could be bought first and half the catalogue was decorative. These pin the structural
 * rules and the design rules that are easy to undo by accident later.
 */

namespace
{
	UClassSkillTreeSubsystem* MakeSkillTree()
	{
		// A GameInstanceSubsystem needs a UGameInstance outer; constructing it bare trips a
		// CoreUObject ensure on ClassWithin.
		UGameInstance* TestGameInstance = NewObject<UGameInstance>();
		UClassSkillTreeSubsystem* Tree = NewObject<UClassSkillTreeSubsystem>(TestGameInstance);
		Tree->ResetToDefaultSkills();
		return Tree;
	}

	void Grant(FClassSkillsArray& Owned, const FString& SkillID, int32 Rank = 1)
	{
		Owned.SkillRanks.Add(SkillID, Rank);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClassSkillCatalogueIntegrityTest,
	"Ginnungagap.Progression.SkillTree.CatalogueIntegrity",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FClassSkillCatalogueIntegrityTest::RunTest(const FString& Parameters)
{
	UClassSkillTreeSubsystem* Tree = MakeSkillTree();

	const TArray<EPressureSuitRole> Roles = {
		EPressureSuitRole::Scientist, EPressureSuitRole::Engineering,
		EPressureSuitRole::Medical, EPressureSuitRole::Security
	};

	// Every role must have a real tree of its own, not just the shared general set.
	const int32 GeneralCount = Tree->GetGeneralSkills().Num();
	TestTrue(TEXT("A general skill set exists"), GeneralCount >= 5);

	for (EPressureSuitRole Role : Roles)
	{
		const TArray<FClassSkill> RoleSkills = Tree->GetAllSkillsForRole(Role);
		TestTrue(TEXT("Role sees the general set plus its own skills"), RoleSkills.Num() > GeneralCount);

		int32 RoleSpecific = 0;
		int32 ActiveCount = 0;
		for (const FClassSkill& Skill : RoleSkills)
		{
			if (!Skill.bIsGeneralSkill) { ++RoleSpecific; }
			if (Skill.Activation == ESkillActivation::Active) { ++ActiveCount; }

			// A skill with no effect ID is text on a button. This is the exact failure the old
			// catalogue shipped, where Scientist skills had no implementation at all.
			TestTrue(TEXT("Every skill names an effect"), !Skill.EffectId.IsNone());
			TestTrue(TEXT("Every skill grants a non-zero magnitude"), Skill.MagnitudePerRank > 0.0f);
			TestTrue(TEXT("Every skill costs something"), Skill.PointCostToUnlock > 0);

			// Prerequisites must resolve, or a node is permanently unreachable.
			for (const FString& Prerequisite : Skill.Prerequisites)
			{
				TestTrue(TEXT("Prerequisite refers to a real skill"), Tree->DoesSkillExist(Prerequisite));
				const FClassSkill Required = Tree->GetSkillByID(Prerequisite);
				TestTrue(TEXT("Prerequisite is not from a later tier"), Required.Tier <= Skill.Tier);
				TestTrue(TEXT("A skill is not its own prerequisite"), Prerequisite != Skill.SkillID);
			}
		}

		TestTrue(TEXT("Role has skills unique to it"), RoleSpecific >= 4);

		// More actives available than loadout slots, or the choice is not a choice.
		TestTrue(TEXT("Role can choose between more actives than it can bring"),
			ActiveCount > FClassProgression::MaxEquippedActiveSkills);
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClassSkillDesignRulesTest,
	"Ginnungagap.Progression.SkillTree.DesignRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FClassSkillDesignRulesTest::RunTest(const FString& Parameters)
{
	UClassSkillTreeSubsystem* Tree = MakeSkillTree();

	const TArray<EPressureSuitRole> Roles = {
		EPressureSuitRole::Scientist, EPressureSuitRole::Engineering,
		EPressureSuitRole::Medical, EPressureSuitRole::Security
	};

	TSet<FName> UsedEffects;
	for (EPressureSuitRole Role : Roles)
	{
		for (const FClassSkill& Skill : Tree->GetAllSkillsForRole(Role))
		{
			UsedEffects.Add(Skill.EffectId);

			// Armour is mass. A skill that made heavy protection faster would invert the rule
			// equipment already follows, where a damaged heavy suit still weighs what it weighs.
			TestTrue(TEXT("No skill grants movement speed"),
				!Skill.EffectId.ToString().Contains(TEXT("MovementSpeed")));

			// Training cannot manufacture air. Oxygen skills reduce consumption; they never
			// regenerate a tank, which is what the old Medical line claimed to do.
			TestTrue(TEXT("No skill regenerates oxygen"),
				!Skill.EffectId.ToString().Contains(TEXT("Regen")));
		}
	}

	// Every effect the catalogue uses must be one of the declared, wired IDs. A typo would
	// otherwise produce a skill that aggregates into a bucket nothing reads.
	const TSet<FName> WiredEffects = {
		SkillEffects::OxygenConsumption, SkillEffects::RadiationShielding,
		SkillEffects::SuitSealIntegrity, SkillEffects::MicrogravityControl,
		SkillEffects::ThrusterEfficiency, SkillEffects::MovementNoise,
		SkillEffects::VisibilitySignature, SkillEffects::RepairEffectiveness,
		SkillEffects::MedicalEffectiveness, SkillEffects::ExposureResistance,
		SkillEffects::ScanSensitivity, SkillEffects::ScanRange
	};
	for (const FName& Effect : UsedEffects)
	{
		TestTrue(TEXT("Effect is one of the wired IDs"), WiredEffects.Contains(Effect));
	}

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClassSkillPrerequisiteGateTest,
	"Ginnungagap.Progression.SkillTree.PrerequisiteGate",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FClassSkillPrerequisiteGateTest::RunTest(const FString& Parameters)
{
	UClassSkillTreeSubsystem* Tree = MakeSkillTree();
	FClassSkillsArray Owned;

	// A capstone must not be purchasable first however many points have accumulated. Without
	// prerequisites the tree is a shop, which is what it was.
	TestFalse(TEXT("A capstone cannot be bought with points alone"),
		Tree->CanUnlockSkill(EPressureSuitRole::Engineering, TEXT("Eng_PowerRoutingKit"), Owned, 9999));

	TestTrue(TEXT("A root skill needs no prerequisite"),
		Tree->CanUnlockSkill(EPressureSuitRole::Engineering, TEXT("Gen_SuitFieldRepair"), Owned, 2));

	// Cost must still bite: one point short is a refusal.
	TestFalse(TEXT("A root skill still requires the points"),
		Tree->CanUnlockSkill(EPressureSuitRole::Engineering, TEXT("Gen_SuitFieldRepair"), Owned, 1));

	Grant(Owned, TEXT("Gen_SuitFieldRepair"));
	TestTrue(TEXT("The next tier opens once its prerequisite is owned"),
		Tree->CanUnlockSkill(EPressureSuitRole::Engineering, TEXT("Eng_SystemsFamiliarity"), Owned, 3));

	// Roles cannot reach into each other's trees.
	TestFalse(TEXT("A role cannot buy another role's skill"),
		Tree->CanUnlockSkill(EPressureSuitRole::Medical, TEXT("Eng_SystemsFamiliarity"), Owned, 9999));

	// General skills are reachable from every role.
	TestTrue(TEXT("General skills are open to any role"),
		Tree->CanUnlockSkill(EPressureSuitRole::Medical, TEXT("Gen_VacuumDiscipline"), Owned, 2));

	// Ranks cost progressively more and stop at the ceiling.
	FClassSkillsArray Ranked;
	Grant(Ranked, TEXT("Gen_VacuumDiscipline"), 1);
	const int32 SecondRankCost = Tree->GetNextRankCost(TEXT("Gen_VacuumDiscipline"), Ranked);
	TestTrue(TEXT("Rank two costs more than rank one"), SecondRankCost > 2);

	Grant(Ranked, TEXT("Gen_VacuumDiscipline"), Tree->GetSkillByID(TEXT("Gen_VacuumDiscipline")).MaxRank);
	TestEqual(TEXT("A maxed skill has no next rank cost"),
		Tree->GetNextRankCost(TEXT("Gen_VacuumDiscipline"), Ranked), 0);
	TestFalse(TEXT("A maxed skill cannot be bought again"),
		Tree->CanUnlockSkill(EPressureSuitRole::Scientist, TEXT("Gen_VacuumDiscipline"), Ranked, 9999));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClassSkillLoadoutTest,
	"Ginnungagap.Progression.SkillTree.ActiveLoadout",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FClassSkillLoadoutTest::RunTest(const FString& Parameters)
{
	UClassSkillTreeSubsystem* Tree = MakeSkillTree();
	FClassSkillsArray Owned;

	// Passive: in force from the moment it is owned, with no payload slot spent.
	Grant(Owned, TEXT("Gen_BreathingEconomy"), 2);
	const float PassiveMagnitude = Tree->GetPassiveEffectMagnitude(SkillEffects::OxygenConsumption, Owned);
	TestTrue(TEXT("An owned passive applies without being equipped"), PassiveMagnitude > 0.0f);

	// Rank scales the contribution rather than unlocking a separate node.
	FClassSkillsArray SingleRank;
	Grant(SingleRank, TEXT("Gen_BreathingEconomy"), 1);
	TestTrue(TEXT("Rank two of a passive is worth more than rank one"),
		PassiveMagnitude > Tree->GetPassiveEffectMagnitude(SkillEffects::OxygenConsumption, SingleRank));

	// An active must never leak into the passive total, however it is owned or equipped. Equipping
	// grants the right to trigger, not the effect.
	Grant(Owned, TEXT("Act_ControlledBreathing"), 1);
	Owned.EquippedActiveSkills.Add(TEXT("Act_ControlledBreathing"));
	TestEqual(TEXT("An equipped but untriggered active adds nothing to the passive total"),
		Tree->GetPassiveEffectMagnitude(SkillEffects::OxygenConsumption, Owned), PassiveMagnitude);

	// The three-slot payload is the constraint that makes unlocking more than three worthwhile.
	Grant(Owned, TEXT("Act_EmergencyReseal"), 1);
	Grant(Owned, TEXT("Act_ShieldingPosture"), 1);
	Grant(Owned, TEXT("Gen_BurnPlanning"), 1);
	Owned.EquippedActiveSkills.Add(TEXT("Act_EmergencyReseal"));
	Owned.EquippedActiveSkills.Add(TEXT("Act_ShieldingPosture"));

	TestEqual(TEXT("Three actives fill the payload"),
		Owned.EquippedActiveSkills.Num(), FClassProgression::MaxEquippedActiveSkills);
	TestFalse(TEXT("A fourth active cannot be equipped"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Scientist, TEXT("Gen_BurnPlanning"), Owned));

	Owned.EquippedActiveSkills.Remove(TEXT("Act_ShieldingPosture"));
	TestTrue(TEXT("Freeing a slot allows a different active in"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Scientist, TEXT("Gen_BurnPlanning"), Owned));

	// Unowned or wrong-kind picks are refused rather than silently accepted.
	TestFalse(TEXT("An unowned active cannot be equipped"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Scientist, TEXT("Gen_RunSilent"), Owned));
	TestFalse(TEXT("A passive cannot occupy a payload slot"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Scientist, TEXT("Gen_BreathingEconomy"), Owned));

	// Another role's procedure stays out even when owned, so a role swap cannot smuggle it in.
	//
	// Deliberately a Science active rather than Burn Planning, which used to be role-locked to Crew
	// and is now general -- a general skill is equippable by everyone by definition, so asserting it
	// against Medical would have passed for the wrong reason and stopped testing the rule.
	Grant(Owned, TEXT("Sci_FullSpectrumSweep"), 1);
	TestFalse(TEXT("Another role's active cannot be equipped"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Medical, TEXT("Sci_FullSpectrumSweep"), Owned));
	TestTrue(TEXT("A general active is equippable by any role"),
		Tree->CanEquipActiveSkill(EPressureSuitRole::Medical, TEXT("Gen_BurnPlanning"), Owned));

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClassSkillActivationTest,
	"Ginnungagap.Progression.SkillTree.Activation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FClassSkillActivationTest::RunTest(const FString& Parameters)
{
	UClassSkillTreeSubsystem* Tree = MakeSkillTree();

	// Every active must be triggerable and must lapse. A zero duration or cooldown would make it
	// either instantaneous-and-free or permanently on, neither of which is an active skill.
	const TArray<EPressureSuitRole> Roles = {
		EPressureSuitRole::Scientist, EPressureSuitRole::Engineering,
		EPressureSuitRole::Medical, EPressureSuitRole::Security
	};

	for (EPressureSuitRole Role : Roles)
	{
		for (const FClassSkill& Skill : Tree->GetAllSkillsForRole(Role))
		{
			if (Skill.Activation == ESkillActivation::Active)
			{
				TestTrue(TEXT("An active has a duration"), Skill.DurationSeconds > 0.0f);
				TestTrue(TEXT("An active has a cooldown"), Skill.CooldownSeconds > 0.0f);

				// The window must close before the skill returns, or it is passive with extra steps.
				TestTrue(TEXT("Cooldown outlasts the effect window"),
					Skill.CooldownSeconds > Skill.DurationSeconds);

				// Actives are brief and gated, so they are allowed to be far stronger than passives.
				TestTrue(TEXT("An active is worth spending a payload slot on"),
					Skill.MagnitudePerRank >= 0.15f);
			}
			else if (Skill.EffectId == SkillEffects::ScanRange)
			{
				// Scan range is counted in whole compartments, not as a fraction of anything, so the
				// modesty cap below would be comparing against the wrong units. Its own bound is
				// enforced where it is consumed -- the scanner clamps to MaxScanHops -- so what is
				// worth asserting here is that the catalogue keeps it a small whole number rather
				// than that it is under 0.15 of nothing in particular.
				TestTrue(TEXT("Scan range is a whole number of compartments"),
					FMath::IsNearlyEqual(Skill.MagnitudePerRank,
						FMath::RoundToFloat(Skill.MagnitudePerRank)));
				TestTrue(TEXT("Scan range stays a short reach per rank"),
					Skill.MagnitudePerRank >= 1.0f && Skill.MagnitudePerRank <= 2.0f);
				TestEqual(TEXT("A passive has no cooldown"), Skill.CooldownSeconds, 0.0f);
				TestEqual(TEXT("A passive has no duration"), Skill.DurationSeconds, 0.0f);
			}
			else
			{
				// A passive is permanent, so its per-rank magnitude has to stay modest.
				TestTrue(TEXT("A passive stays modest"), Skill.MagnitudePerRank <= 0.15f);
				TestEqual(TEXT("A passive has no cooldown"), Skill.CooldownSeconds, 0.0f);
				TestEqual(TEXT("A passive has no duration"), Skill.DurationSeconds, 0.0f);
			}
		}
	}

	// Rank deepens an active rather than opening a new node.
	const float RankOne = Tree->GetSkillEffectMagnitude(TEXT("Med_TriageFocus"), 1);
	const float RankThree = Tree->GetSkillEffectMagnitude(TEXT("Med_TriageFocus"), 3);
	TestTrue(TEXT("A higher rank of an active is stronger"), RankThree > RankOne);

	// Rank is clamped to the ceiling, so a corrupt save cannot inflate an effect without limit.
	const FClassSkill Focus = Tree->GetSkillByID(TEXT("Med_TriageFocus"));
	TestEqual(TEXT("Rank beyond the maximum is clamped"),
		Tree->GetSkillEffectMagnitude(TEXT("Med_TriageFocus"), Focus.MaxRank + 5), RankThree);

	// Charge-limited actives are the scarcer kind; at least one must exist or "limited uses" is
	// a claim the catalogue does not honour.
	int32 ChargeLimited = 0;
	for (const FClassSkill& Skill : Tree->GetAllSkillsForRole(EPressureSuitRole::Scientist))
	{
		if (Skill.Activation == ESkillActivation::Active && Skill.ChargesPerRun > 0)
		{
			++ChargeLimited;
		}
	}
	TestTrue(TEXT("Some actives are limited by charges, not just cooldown"), ChargeLimited > 0);

	return true;
}

#endif
