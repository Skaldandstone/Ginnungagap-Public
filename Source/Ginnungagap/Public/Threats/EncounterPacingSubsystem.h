#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "EncounterPacingSubsystem.generated.h"

class ACoopSurvivalCharacter;

/**
 * Where a run currently sits in its own rhythm.
 *
 * Named for what the player is experiencing rather than for what the system is doing, because that
 * is the thing being designed. A phase called "cooldown" invites tuning the timer; a phase called
 * Relief invites asking whether the player is actually relieved.
 */
UENUM(BlueprintType)
enum class EEncounterPhase : uint8
{
	/** Nothing is looking for anyone. The floor of the cycle, and the only place work gets done. */
	Quiet,

	/** Something has begun to take an interest. Perception climbing, nothing committed yet. */
	Building,

	/** Being hunted. The top of the cycle, and deliberately the shortest phase. */
	Pressure,

	/** It has stopped, and the player is allowed to believe that. Perception suppressed outright. */
	Relief
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEncounterPhaseChanged, EEncounterPhase, NewPhase);

/**
 * Decides when the ship presses and when it lets go.
 *
 * The demo has five hunters in it that patrol, perceive, and give up. What it has not had is anyone
 * deciding *when* -- so pressure arrives whenever a patrol route happens to cross the player, which
 * is not pacing, it is weather. A creature that appears on a schedule of its own is not a scare.
 *
 * ## Why this reads the player rather than a timer
 *
 * The obvious version of this system is a cycle: quiet for ninety seconds, hunt for thirty, repeat.
 * That produces a rhythm the player learns in two loops and then plans around, and the horror is
 * gone the moment it becomes predictable.
 *
 * So the phase transitions are driven by the player's actual condition, which this project already
 * models in detail. Acute stress escalates across near misses and decays when nothing is happening,
 * which makes it a far better read on "has this person had enough" than elapsed time -- a player
 * who has escaped three things in a minute and one who has been walking an empty corridor for the
 * same minute deserve very different next minutes, and a timer cannot tell them apart.
 *
 * ## The mercy rule
 *
 * Relief is extended, not shortened, when the player is in a bad way. That is the opposite of what a
 * difficulty system would do, and it is deliberate.
 *
 * Stress already degrades coordination, which loses activities, which raises stress. Pressing a
 * player who is deep in that spiral does not make the game frightening, it makes it unwinnable on a
 * schedule -- and a run that is lost before the player knows it is lost reads as unfair rather than
 * as tense. The scare works because there was a chance.
 */
UCLASS()
class GINNUNGAGAP_API UEncounterPacingSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickable() const override { return !IsTemplate(); }

	UFUNCTION(BlueprintPure, Category="Threat|Pacing")
	EEncounterPhase GetPhase() const { return Phase; }

	UFUNCTION(BlueprintPure, Category="Threat|Pacing")
	float GetSecondsInPhase() const { return SecondsInPhase; }

	/**
	 * Multiplier on how fast a hunter builds certainty about the player, and how far it hears.
	 *
	 * The single number the pacing exports. Everything else here exists to decide it.
	 */
	UFUNCTION(BlueprintPure, Category="Threat|Pacing")
	float GetPerceptionScale() const;

	/** Forces a phase. For scripted beats -- a scare on a specific objective -- and for tests. */
	UFUNCTION(BlueprintCallable, Category="Threat|Pacing")
	void SetPhase(EEncounterPhase NewPhase);

	/**
	 * Told when a hunter gives up on the player, which ends the pressure.
	 *
	 * Reported rather than detected, because "the player got away" is a thing the AI knows and this
	 * system cannot see: it happens when an enemy's interest expires, not when the player stops
	 * being visible.
	 */
	UFUNCTION(BlueprintCallable, Category="Threat|Pacing")
	void NotifyEncounterSurvived();

	/** Told when something has confirmed the player. Escalates immediately. */
	UFUNCTION(BlueprintCallable, Category="Threat|Pacing")
	void NotifyPlayerDetected();

	UPROPERTY(BlueprintAssignable, Category="Threat|Pacing")
	FOnEncounterPhaseChanged OnEncounterPhaseChanged;

	// --- tuning -----------------------------------------------------------------------------------

	/** Perception multiplier in each phase. Relief is well under 1: the ship genuinely stops looking. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="0.0"))
	float QuietPerceptionScale = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="0.0"))
	float BuildingPerceptionScale = 1.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="0.0"))
	float PressurePerceptionScale = 1.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="0.0"))
	float ReliefPerceptionScale = 0.35f;

	/** How long a quiet stretch lasts before the ship starts taking an interest again. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="1.0"))
	float QuietSecondsBeforeBuilding = 55.0f;

	/** How long Building runs before it gives up and drops back to Quiet with nothing found. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="1.0"))
	float BuildingSecondsBeforeQuiet = 40.0f;

	/**
	 * How long being hunted lasts before the ship loses interest on its own.
	 *
	 * A ceiling rather than a duration. Pressure normally ends because a hunter gave up, and this
	 * only catches the case where one is stuck somewhere it cannot reach the player -- which
	 * otherwise leaves the run pinned at maximum forever.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="1.0"))
	float MaximumPressureSeconds = 75.0f;

	/** Baseline relief after an encounter, before the mercy extension. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="1.0"))
	float BaseReliefSeconds = 30.0f;

	/** Extra relief at full acute stress. See the mercy rule in the class comment. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Pacing", meta=(ClampMin="0.0"))
	float MaximumMercySeconds = 45.0f;

	/** How long the relief for the current stress level should be. Public because it is testable. */
	UFUNCTION(BlueprintPure, Category="Threat|Pacing")
	float GetReliefSecondsForStress(float StressSeverity) const;

private:
	EEncounterPhase Phase = EEncounterPhase::Quiet;
	float SecondsInPhase = 0.0f;

	/** Relief length chosen when the current relief began, so mid-phase stress changes do not move it. */
	float CurrentReliefSeconds = 0.0f;

	ACoopSurvivalCharacter* FindLocalPlayer() const;
	float ReadPlayerStress() const;
};
