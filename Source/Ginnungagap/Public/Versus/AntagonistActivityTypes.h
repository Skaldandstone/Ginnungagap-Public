#pragma once

#include "CoreMinimal.h"
#include "Activities/PlayerActivityTypes.h"
#include "Versus/VersusTypes.h"
#include "AntagonistActivityTypes.generated.h"

UENUM(BlueprintType)
enum class EAntagonistActivityType : uint8
{
	BreachLock,
	StripCargo,
	JamCommunications,
	RallyBoarders,
	SpoofCredentials,
	CascadePowerGrid,
	PlantFalseTelemetry,
	ArmScuttleRelay,
	ConsumeBiomass,
	SeedMycelium,
	MimicNeuralPattern,
	EstablishBloomNode,
	ReadScentTrail,
	FeedOnPrey,
	PrepareAmbush,
	MarkPackRoute
};

UENUM(BlueprintType)
enum class EAntagonistActivityMechanic : uint8
{
	CircuitIntrusion,
	TimedExtraction,
	SignalSpoof,
	CommandUplink,
	MetabolicBalance,
	TerritoryWeave,
	NeuralMimicry,
	ScentTriangulation,
	AmbushTiming
};

USTRUCT(BlueprintType)
struct FAntagonistActivityDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	FName ActivityId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	EAntagonistActivityType Type = EAntagonistActivityType::BreachLock;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	EAntagonistActivityMechanic Mechanic = EAntagonistActivityMechanic::CircuitIntrusion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	EAntagonistFaction Faction = EAntagonistFaction::Pirates;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	FText Motivation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="0.1"))
	float DurationSeconds = 6.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="1", ClampMax="16"))
	int32 PuzzleSteps = 5;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="1", ClampMax="10"))
	int32 AllowedMistakes = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="50.0"))
	float MaxRange = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="0"))
	int32 CommandResourceReward = 10;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity", meta=(ClampMin="0"))
	int32 SkillPointReward = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	FName CompletionEffectId;

	/** Pirates and rebels may expose an equivalent crew-style procedure for shared terminals. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Activity")
	bool bCanReuseHumanStation = false;

	bool IsDefined() const { return !ActivityId.IsNone() && Faction != EAntagonistFaction::None; }
};

USTRUCT(BlueprintType)
struct FAntagonistActivitySnapshot
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	EPlayerActivityState State = EPlayerActivityState::Idle;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	FName ActivityId;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	FText DisplayName;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	FText Motivation;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	EAntagonistActivityMechanic Mechanic = EAntagonistActivityMechanic::CircuitIntrusion;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	EAntagonistFaction Faction = EAntagonistFaction::None;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	float Progress = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	int32 CurrentStep = 0;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	int32 TotalSteps = 0;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	int32 Mistakes = 0;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	EActivityInput ExpectedInput = EActivityInput::Primary;

	/** Mechanic-specific gauges: nutrient/exposure/cohesion, signal channels, or scent bearings. */
	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	FVector ResourceBalance = FVector(0.2f, 0.8f, 0.5f);

	/** Moving timing cursor used by ambush and scent pulse mechanics. */
	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	float TimingCursor = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	float TimingWindowCenter = 0.5f;

	UPROPERTY(BlueprintReadOnly, Category="Antagonist Activity")
	float TimingWindowWidth = 0.18f;
};
