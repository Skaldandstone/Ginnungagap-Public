#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "Versus/AntagonistPlayerCharacter.h"
#include "Versus/AntagonistActivityCatalog.h"
#include "Versus/AntagonistSkillTreeSubsystem.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Versus/VersusGameMode.h"
#include "Versus/VersusGameState.h"
#include "Versus/VersusPlayerState.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVersusMatchSettingsTest,
	"Ginnungagap.Versus.MatchSettingsAndLimits",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FVersusMatchSettingsTest::RunTest(const FString& Parameters)
{
	FVersusMatchSettings Settings;
	Settings.ProtagonistSlots = 99;
	Settings.AntagonistSlots = 0;
	Settings.PlayerAntagonistFaction = EAntagonistFaction::Bloom;
	Settings.IndependentAIFactions = {
		EAntagonistFaction::Bloom,
		EAntagonistFaction::Pirates,
		EAntagonistFaction::Pirates,
		EAntagonistFaction::None
	};
	Settings.Sanitize();

	TestEqual(TEXT("Protagonist team caps at eight"), Settings.ProtagonistSlots, 8);
	TestEqual(TEXT("Antagonist team has at least one slot"), Settings.AntagonistSlots, 1);
	TestEqual(TEXT("An 8v1 setup exposes nine player slots"), Settings.GetMaxPlayers(), 9);
	TestEqual(TEXT("Only a distinct independent faction remains"), Settings.IndependentAIFactions.Num(), 1);
	TestEqual(TEXT("Pirates remain independently eligible"), Settings.IndependentAIFactions[0], EAntagonistFaction::Pirates);
	TestTrue(TEXT("Sanitized settings are valid"), Settings.IsValid());

	const AVersusGameMode* Mode = GetDefault<AVersusGameMode>();
	TestTrue(TEXT("Versus mode uses replicated versus game state"), Mode->GameStateClass == AVersusGameState::StaticClass());
	TestTrue(TEXT("Versus mode uses versus player state"), Mode->PlayerStateClass == AVersusPlayerState::StaticClass());
	TestTrue(TEXT("Versus mode has a controllable antagonist pawn"), Mode->AntagonistPawnClass.Get() == AAntagonistPlayerCharacter::StaticClass());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVersusHostilityRulesTest,
	"Ginnungagap.Versus.FactionHostilityRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FVersusHostilityRulesTest::RunTest(const FString& Parameters)
{
	using Team = EVersusTeam;
	using Faction = EAntagonistFaction;
	TestFalse(TEXT("Crew are allied to crew"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::Protagonist, Faction::None, Team::Protagonist, Faction::None));
	TestTrue(TEXT("Crew are hostile to player Bloom"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::Protagonist, Faction::None, Team::Antagonist, Faction::Bloom));
	TestFalse(TEXT("Bloom players cooperate with Bloom"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::Antagonist, Faction::Bloom, Team::Antagonist, Faction::Bloom));
	TestTrue(TEXT("AI pirates attack player Bloom"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::IndependentAI, Faction::Pirates, Team::Antagonist, Faction::Bloom));
	TestTrue(TEXT("AI pirates attack crew"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::IndependentAI, Faction::Pirates, Team::Protagonist, Faction::None));
	TestFalse(TEXT("Spectators are never combat targets"), UTeamAffiliationComponent::AreAffiliationsHostile(
		Team::Antagonist, Faction::Bloom, Team::Spectator, Faction::None));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAntagonistSkillTreeRulesTest,
	"Ginnungagap.Versus.AntagonistSkillTrees",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAntagonistSkillTreeRulesTest::RunTest(const FString& Parameters)
{
	UGameInstance* TestGameInstance = NewObject<UGameInstance>();
	UAntagonistSkillTreeSubsystem* Tree = NewObject<UAntagonistSkillTreeSubsystem>(TestGameInstance);
	Tree->ResetToDefaultSkillTrees();
	TestTrue(TEXT("Bloom has a multi-tier skill tree"), Tree->GetSkillsForFaction(EAntagonistFaction::Bloom).Num() >= 4);
	TestTrue(TEXT("Pirates have a distinct skill tree"), Tree->GetSkillsForFaction(EAntagonistFaction::Pirates).Num() >= 3);
	TestTrue(TEXT("Rebels have a distinct skill tree"), Tree->GetSkillsForFaction(EAntagonistFaction::Rebels).Num() >= 3);
	TestTrue(TEXT("Aliens have a distinct skill tree"), Tree->GetSkillsForFaction(EAntagonistFaction::Alien).Num() >= 3);

	TArray<FName> Unlocked;
	TestTrue(TEXT("Bloom root can be unlocked with one point"), Tree->CanUnlockSkill(
		TEXT("Bloom_CreepingMycelium"), EAntagonistFaction::Bloom, Unlocked, 1));
	TestFalse(TEXT("Bloom tier two requires its prerequisite"), Tree->CanUnlockSkill(
		TEXT("Bloom_MimeticSpores"), EAntagonistFaction::Bloom, Unlocked, 3));
	Unlocked.Add(TEXT("Bloom_CreepingMycelium"));
	TestTrue(TEXT("Bloom tier two unlocks after its prerequisite"), Tree->CanUnlockSkill(
		TEXT("Bloom_MimeticSpores"), EAntagonistFaction::Bloom, Unlocked, 2));
	TestFalse(TEXT("Faction skills cannot cross-unlock"), Tree->CanUnlockSkill(
		TEXT("Pirate_BreachCharges"), EAntagonistFaction::Bloom, Unlocked, 10));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAntagonistActivityCatalogTest,
	"Ginnungagap.Versus.AntagonistActivities",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAntagonistActivityCatalogTest::RunTest(const FString& Parameters)
{
	using Faction = EAntagonistFaction;
	using Mechanic = EAntagonistActivityMechanic;
	const TArray<FAntagonistActivityDefinition> Pirates = UAntagonistActivityCatalog::GetActivitiesForFaction(Faction::Pirates);
	const TArray<FAntagonistActivityDefinition> Rebels = UAntagonistActivityCatalog::GetActivitiesForFaction(Faction::Rebels);
	const TArray<FAntagonistActivityDefinition> Bloom = UAntagonistActivityCatalog::GetActivitiesForFaction(Faction::Bloom);
	const TArray<FAntagonistActivityDefinition> Alien = UAntagonistActivityCatalog::GetActivitiesForFaction(Faction::Alien);

	TestEqual(TEXT("Pirates have four authored activities"), Pirates.Num(), 4);
	TestEqual(TEXT("Rebels have four authored activities"), Rebels.Num(), 4);
	TestEqual(TEXT("Bloom has four authored activities"), Bloom.Num(), 4);
	TestEqual(TEXT("Aliens have four authored activities"), Alien.Num(), 4);
	TestTrue(TEXT("Pirates can reuse some crew-facing stations"), Pirates.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.bCanReuseHumanStation; }));
	TestTrue(TEXT("Rebels can reuse some crew-facing stations"), Rebels.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.bCanReuseHumanStation; }));
	TestFalse(TEXT("Bloom activities are never reskinned crew procedures"), Bloom.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.bCanReuseHumanStation; }));
	TestFalse(TEXT("Alien activities are never reskinned crew procedures"), Alien.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.bCanReuseHumanStation; }));
	TestTrue(TEXT("Bloom includes metabolic survival gameplay"), Bloom.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.Mechanic == Mechanic::MetabolicBalance; }));
	TestTrue(TEXT("Bloom includes biological territory gameplay"), Bloom.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.Mechanic == Mechanic::TerritoryWeave; }));
	TestTrue(TEXT("Alien includes scent tracking gameplay"), Alien.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.Mechanic == Mechanic::ScentTriangulation; }));
	TestTrue(TEXT("Alien includes patient ambush gameplay"), Alien.ContainsByPredicate(
		[](const FAntagonistActivityDefinition& Activity) { return Activity.Mechanic == Mechanic::AmbushTiming; }));
	TestFalse(TEXT("Bloom cannot perform pirate activities"), UAntagonistActivityCatalog::CanFactionPerformActivity(
		Faction::Bloom, TEXT("Pirate_StripCargo")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAntagonistCommanderRulesTest,
	"Ginnungagap.Versus.AntagonistCommanderRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAntagonistCommanderRulesTest::RunTest(const FString& Parameters)
{
	using Faction = EAntagonistFaction;
	using Order = EAntagonistOrderType;
	TestTrue(TEXT("Scouting costs less than a full rally"),
		AVersusGameState::GetOrderResourceCost(Order::Scout) < AVersusGameState::GetOrderResourceCost(Order::Rally));
	TestTrue(TEXT("Bloom commanders can order infestation"), AVersusGameState::CanFactionIssueOrder(Faction::Bloom, Order::Infest));
	TestFalse(TEXT("Bloom commanders do not use technical sabotage"), AVersusGameState::CanFactionIssueOrder(Faction::Bloom, Order::Sabotage));
	TestTrue(TEXT("Pirate commanders can order sabotage"), AVersusGameState::CanFactionIssueOrder(Faction::Pirates, Order::Sabotage));
	TestFalse(TEXT("Pirate commanders cannot order infestation"), AVersusGameState::CanFactionIssueOrder(Faction::Pirates, Order::Infest));
	TestFalse(TEXT("Alien commanders cannot order technical sabotage"), AVersusGameState::CanFactionIssueOrder(Faction::Alien, Order::Sabotage));
	TestFalse(TEXT("Alien commanders cannot order Bloom infestation"), AVersusGameState::CanFactionIssueOrder(Faction::Alien, Order::Infest));
	return true;
}

#endif
