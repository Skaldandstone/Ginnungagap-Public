#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Interaction/BioScannerComponent.h"
#include "Progression/ClassSkillTreeSubsystem.h"
#include "Progression/PlayerClass.h"
#include "Engine/GameInstance.h"

/**
 * The two effects that make Science a class rather than a relabel.
 *
 * Both gate something the scanner already did identically for everyone: it clamps every reading up
 * to a detection floor, so below that floor a seeded compartment and a clean one are the same
 * number, and it reached exactly one compartment. Neither limit was something any player could
 * influence.
 *
 * These assert the tuning holds its shape rather than exact magnitudes -- that training lowers the
 * floor without ever reaching zero, and extends reach in whole compartments up to a ceiling. A test
 * pinned to the current numbers would fail on every balance pass and teach nobody anything.
 *
 * The scanner half is checked through the component's own defaults, since a component with no
 * owning character must still answer with the untrained values rather than crash.
 */

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScienceScannerDefaultsTest,
	"Ginnungagap.Progression.Science.ScannerDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FScienceScannerDefaultsTest::RunTest(const FString& Parameters)
{
	UBioScannerComponent* Scanner = NewObject<UBioScannerComponent>();
	TestNotNull(TEXT("Scanner component constructs"), Scanner);

	// No owning character, so no skills. An untrained reading is the baseline every other role
	// gets, and it must be exactly what the tuning says rather than a degraded fallback.
	TestEqual(TEXT("With no training the floor is the raw detection floor"),
		Scanner->GetEffectiveDetectionFloor(), Scanner->DetectionFloor);
	TestEqual(TEXT("With no training the scanner reaches the base hop count"),
		Scanner->GetEffectiveScanHops(), Scanner->BaseScanHops);

	// The baseline has to actually be "adjacent only", or Deep Survey is buying something the
	// player already had.
	TestEqual(TEXT("The untrained scanner reaches adjacent compartments only"),
		Scanner->BaseScanHops, 1);

	// A floor that could reach zero would report every compartment as contaminated, since the
	// clamp is what turns sensor noise into a clean reading.
	TestTrue(TEXT("The trained floor can never reach zero"),
		Scanner->MinDetectionFloorFraction > 0.0f);
	TestTrue(TEXT("The trained floor is genuinely lower than the untrained one"),
		Scanner->MinDetectionFloorFraction < 1.0f);

	// Reach is capped so that stacking the passive and the active sweep cannot read a whole ship.
	TestTrue(TEXT("Scan reach has a ceiling above the baseline"),
		Scanner->MaxScanHops > Scanner->BaseScanHops);

	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FScienceSkillTreeTest,
	"Ginnungagap.Progression.Science.SkillTree",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FScienceSkillTreeTest::RunTest(const FString& Parameters)
{
	// A GameInstanceSubsystem needs a UGameInstance outer; constructing it bare trips a
	// CoreUObject ensure on ClassWithin.
	UGameInstance* TestGameInstance = NewObject<UGameInstance>();
	UClassSkillTreeSubsystem* Tree = NewObject<UClassSkillTreeSubsystem>(TestGameInstance);
	Tree->ResetToDefaultSkills();

	const TArray<FClassSkill> Science = Tree->GetAllSkillsForRole(EPressureSuitRole::Scientist);
	TestTrue(TEXT("Science has skills of its own"), Science.Num() > 0);

	// The point of the class. If neither new effect appears, Science is Medical with a new label.
	bool bHasSensitivity = false;
	bool bHasRange = false;
	bool bHasActive = false;
	int32 RoleSpecific = 0;

	for (const FClassSkill& Skill : Science)
	{
		if (!Skill.bIsGeneralSkill)
		{
			++RoleSpecific;
		}
		if (Skill.EffectId == SkillEffects::ScanSensitivity)
		{
			bHasSensitivity = true;
		}
		if (Skill.EffectId == SkillEffects::ScanRange)
		{
			bHasRange = true;
			if (Skill.Activation == ESkillActivation::Active)
			{
				bHasActive = true;
			}
		}
	}

	TestTrue(TEXT("Science can see fainter traces than anyone else"), bHasSensitivity);
	TestTrue(TEXT("Science can read further than one compartment"), bHasRange);
	TestTrue(TEXT("Science has an active of its own to bring on a run"), bHasActive);
	TestTrue(TEXT("Science has skills that are not merely the shared tree"), RoleSpecific > 0);

	// The four rehomed spacer skills have to be reachable by everyone now, or moving them to the
	// General tree silently deleted them from the game.
	const TArray<FClassSkill> Medical = Tree->GetAllSkillsForRole(EPressureSuitRole::Medical);
	auto MedicalHas = [&Medical](const TCHAR* Id)
	{
		for (const FClassSkill& Skill : Medical)
		{
			if (Skill.SkillID == Id)
			{
				return true;
			}
		}
		return false;
	};

	for (const TCHAR* Id : {TEXT("Gen_StationKeeping"), TEXT("Gen_VeteranSpacer"),
	                        TEXT("Gen_BurnPlanning"), TEXT("Gen_RunSilent")})
	{
		TestTrue(FString::Printf(TEXT("%s survived the move to the General tree"), Id),
			MedicalHas(Id));
	}

	// And nothing should still be advertising the tree it left.
	const TArray<FClassSkill> General = Tree->GetGeneralSkills();

	TSet<FString> GeneralIds;
	for (const FClassSkill& Skill : General)
	{
		GeneralIds.Add(Skill.SkillID);
		TestFalse(FString::Printf(TEXT("No skill still carries a Crew_ id (%s)"), *Skill.SkillID),
			Skill.SkillID.StartsWith(TEXT("Crew_")));
	}

	// A general skill gated behind a role-locked one is unreachable for every other role, which is
	// the quiet way a rehoming goes wrong: the skill is present in the list and can never be bought.
	for (const FClassSkill& Skill : General)
	{
		for (const FString& Prerequisite : Skill.Prerequisites)
		{
			TestTrue(FString::Printf(TEXT("General skill %s depends only on general skills, not %s"),
				*Skill.SkillID, *Prerequisite), GeneralIds.Contains(Prerequisite));
		}
	}

	return true;
}

#endif
