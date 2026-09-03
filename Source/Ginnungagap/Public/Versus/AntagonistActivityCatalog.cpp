#include "Versus/AntagonistActivityCatalog.h"

namespace
{
FAntagonistActivityDefinition Activity(FName Id, EAntagonistActivityType Type,
	EAntagonistActivityMechanic Mechanic, EAntagonistFaction Faction, const FText& Name,
	const FText& Motivation, float Duration, int32 Steps, int32 Mistakes, int32 CommandReward,
	int32 SkillReward, FName Effect, bool bHumanOverlap)
{
	FAntagonistActivityDefinition Result;
	Result.ActivityId = Id;
	Result.Type = Type;
	Result.Mechanic = Mechanic;
	Result.Faction = Faction;
	Result.DisplayName = Name;
	Result.Motivation = Motivation;
	Result.DurationSeconds = Duration;
	Result.PuzzleSteps = Steps;
	Result.AllowedMistakes = Mistakes;
	Result.CommandResourceReward = CommandReward;
	Result.SkillPointReward = SkillReward;
	Result.CompletionEffectId = Effect;
	Result.bCanReuseHumanStation = bHumanOverlap;
	return Result;
}
}

TArray<FAntagonistActivityDefinition> UAntagonistActivityCatalog::BuildCatalog()
{
	using Type = EAntagonistActivityType;
	using Mechanic = EAntagonistActivityMechanic;
	using Faction = EAntagonistFaction;
	return {
		Activity(TEXT("Pirate_BreachLock"), Type::BreachLock, Mechanic::CircuitIntrusion, Faction::Pirates,
			NSLOCTEXT("AntagonistActivities", "PirateBreach", "Defeat Lock Controller"),
			NSLOCTEXT("AntagonistActivities", "PirateBreachWhy", "Open a route for the prize crew."), 6, 5, 3, 12, 0, TEXT("OpenBoardingRoute"), true),
		Activity(TEXT("Pirate_StripCargo"), Type::StripCargo, Mechanic::TimedExtraction, Faction::Pirates,
			NSLOCTEXT("AntagonistActivities", "PirateCargo", "Strip Valuable Cargo"),
			NSLOCTEXT("AntagonistActivities", "PirateCargoWhy", "Convert stolen stores into reinforcement capacity."), 9, 1, 3, 18, 1, TEXT("LootCargo"), true),
		Activity(TEXT("Pirate_JamComms"), Type::JamCommunications, Mechanic::SignalSpoof, Faction::Pirates,
			NSLOCTEXT("AntagonistActivities", "PirateJam", "Jam Crew Communications"),
			NSLOCTEXT("AntagonistActivities", "PirateJamWhy", "Break crew coordination before the next push."), 7, 6, 2, 15, 0, TEXT("JamCrewComms"), true),
		Activity(TEXT("Pirate_RallyBoarders"), Type::RallyBoarders, Mechanic::CommandUplink, Faction::Pirates,
			NSLOCTEXT("AntagonistActivities", "PirateRally", "Rally Boarding Party"),
			NSLOCTEXT("AntagonistActivities", "PirateRallyWhy", "Synchronize boarders around a command order."), 6, 5, 3, 14, 0, TEXT("ReinforceOrder"), false),

		Activity(TEXT("Rebel_SpoofCredentials"), Type::SpoofCredentials, Mechanic::SignalSpoof, Faction::Rebels,
			NSLOCTEXT("AntagonistActivities", "RebelSpoof", "Spoof Crew Credentials"),
			NSLOCTEXT("AntagonistActivities", "RebelSpoofWhy", "Move through secured systems as a trusted operator."), 7, 6, 2, 14, 0, TEXT("SpoofAccess"), true),
		Activity(TEXT("Rebel_CascadePower"), Type::CascadePowerGrid, Mechanic::CircuitIntrusion, Faction::Rebels,
			NSLOCTEXT("AntagonistActivities", "RebelCascade", "Engineer Cascade Failure"),
			NSLOCTEXT("AntagonistActivities", "RebelCascadeWhy", "Turn the crew's infrastructure against itself."), 9, 8, 2, 20, 1, TEXT("CascadePower"), true),
		Activity(TEXT("Rebel_FalseTelemetry"), Type::PlantFalseTelemetry, Mechanic::SignalSpoof, Faction::Rebels,
			NSLOCTEXT("AntagonistActivities", "RebelTelemetry", "Plant False Telemetry"),
			NSLOCTEXT("AntagonistActivities", "RebelTelemetryWhy", "Make the crew spend time solving the wrong emergency."), 8, 7, 2, 18, 0, TEXT("FalseObjective"), true),
		Activity(TEXT("Rebel_ScuttleRelay"), Type::ArmScuttleRelay, Mechanic::CircuitIntrusion, Faction::Rebels,
			NSLOCTEXT("AntagonistActivities", "RebelScuttle", "Arm Scuttle Relay"),
			NSLOCTEXT("AntagonistActivities", "RebelScuttleWhy", "Create strategic leverage over the entire vessel."), 11, 9, 1, 25, 1, TEXT("ArmScuttleRelay"), true),

		Activity(TEXT("Bloom_ConsumeBiomass"), Type::ConsumeBiomass, Mechanic::MetabolicBalance, Faction::Bloom,
			NSLOCTEXT("AntagonistActivities", "BloomConsume", "Assimilate Biomass"),
			NSLOCTEXT("AntagonistActivities", "BloomConsumeWhy", "Balance hunger, exposure, and cohesion while consuming a viable host."), 8, 4, 3, 16, 1, TEXT("GainBiomass"), false),
		Activity(TEXT("Bloom_SeedMycelium"), Type::SeedMycelium, Mechanic::TerritoryWeave, Faction::Bloom,
			NSLOCTEXT("AntagonistActivities", "BloomSeed", "Weave Mycelial Route"),
			NSLOCTEXT("AntagonistActivities", "BloomSeedWhy", "Spread through pressure seams without exposing the growth front."), 9, 7, 2, 20, 0, TEXT("SpreadTerritory"), false),
		Activity(TEXT("Bloom_MimicNeural"), Type::MimicNeuralPattern, Mechanic::NeuralMimicry, Faction::Bloom,
			NSLOCTEXT("AntagonistActivities", "BloomMimic", "Mimic Neural Pattern"),
			NSLOCTEXT("AntagonistActivities", "BloomMimicWhy", "Learn a host's cadence well enough to deceive nearby crew."), 8, 8, 2, 18, 1, TEXT("MimicCrewSignal"), false),
		Activity(TEXT("Bloom_EstablishNode"), Type::EstablishBloomNode, Mechanic::MetabolicBalance, Faction::Bloom,
			NSLOCTEXT("AntagonistActivities", "BloomNode", "Establish Bloom Node"),
			NSLOCTEXT("AntagonistActivities", "BloomNodeWhy", "Create a resilient organ that anchors survival and future spread."), 12, 5, 2, 28, 1, TEXT("CreateBloomNode"), false),

		Activity(TEXT("Alien_ReadScent"), Type::ReadScentTrail, Mechanic::ScentTriangulation, Faction::Alien,
			NSLOCTEXT("AntagonistActivities", "AlienScent", "Triangulate Scent Trail"),
			NSLOCTEXT("AntagonistActivities", "AlienScentWhy", "Separate the freshest prey trail from machinery and old blood."), 6, 5, 3, 12, 0, TEXT("RevealPreyTrail"), false),
		Activity(TEXT("Alien_Feed"), Type::FeedOnPrey, Mechanic::MetabolicBalance, Faction::Alien,
			NSLOCTEXT("AntagonistActivities", "AlienFeed", "Feed Without Exposure"),
			NSLOCTEXT("AntagonistActivities", "AlienFeedWhy", "Recover strength while keeping scent and noise below the crew's threshold."), 8, 4, 2, 16, 1, TEXT("RecoverPack"), false),
		Activity(TEXT("Alien_PrepareAmbush"), Type::PrepareAmbush, Mechanic::AmbushTiming, Faction::Alien,
			NSLOCTEXT("AntagonistActivities", "AlienAmbush", "Prepare Ambush"),
			NSLOCTEXT("AntagonistActivities", "AlienAmbushWhy", "Hold still, read vibration, and commit only when prey enters the kill lane."), 7, 4, 2, 20, 0, TEXT("PrimeAmbush"), false),
		Activity(TEXT("Alien_MarkPackRoute"), Type::MarkPackRoute, Mechanic::ScentTriangulation, Faction::Alien,
			NSLOCTEXT("AntagonistActivities", "AlienRoute", "Mark Pack Route"),
			NSLOCTEXT("AntagonistActivities", "AlienRouteWhy", "Leave a coordinated hunting path for packmates and creatures."), 7, 6, 2, 18, 0, TEXT("CreatePackRoute"), false)
	};
}

FAntagonistActivityDefinition UAntagonistActivityCatalog::GetActivity(FName ActivityId)
{
	for (const FAntagonistActivityDefinition& Definition : BuildCatalog())
	{
		if (Definition.ActivityId == ActivityId)
		{
			return Definition;
		}
	}
	return FAntagonistActivityDefinition();
}

TArray<FAntagonistActivityDefinition> UAntagonistActivityCatalog::GetActivitiesForFaction(EAntagonistFaction Faction)
{
	TArray<FAntagonistActivityDefinition> Result;
	for (const FAntagonistActivityDefinition& Definition : BuildCatalog())
	{
		if (Definition.Faction == Faction)
		{
			Result.Add(Definition);
		}
	}
	return Result;
}

bool UAntagonistActivityCatalog::CanFactionPerformActivity(EAntagonistFaction Faction, FName ActivityId)
{
	const FAntagonistActivityDefinition Definition = GetActivity(ActivityId);
	return Definition.IsDefined() && Definition.Faction == Faction;
}

