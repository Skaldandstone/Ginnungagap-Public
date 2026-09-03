#include "Threats/EncounterPacingSubsystem.h"

#include "EngineUtils.h"
#include "Engine/World.h"

#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"

void UEncounterPacingSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// A run opens quiet. Waking up in a cryo pod to something already hunting you is not an opening,
	// it is a fail state with a cutscene.
	Phase = EEncounterPhase::Quiet;
	SecondsInPhase = 0.0f;
}

TStatId UEncounterPacingSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UEncounterPacingSubsystem, STATGROUP_Tickables);
}

ACoopSurvivalCharacter* UEncounterPacingSubsystem::FindLocalPlayer() const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	// First is correct for the solo slice this exists to pace. Co-op is a later vertical and will
	// want a different question anyway -- "has the party had enough" is not the maximum or the mean
	// of four people's stress, and guessing at that now would be inventing an answer to a design
	// question nobody has asked yet.
	for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
	{
		if (IsValid(*It))
		{
			return *It;
		}
	}
	return nullptr;
}

float UEncounterPacingSubsystem::ReadPlayerStress() const
{
	const ACoopSurvivalCharacter* Player = FindLocalPlayer();
	if (!Player)
	{
		return 0.0f;
	}

	const UPlayerStatusEffectComponent* Status =
		Player->FindComponentByClass<UPlayerStatusEffectComponent>();
	return Status ? Status->GetStatusSeverity(EPlayerStatusEffect::AcuteStress) : 0.0f;
}

float UEncounterPacingSubsystem::GetReliefSecondsForStress(float StressSeverity) const
{
	// Linear in stress, which is enough: the shape of this curve matters far less than the fact
	// that it slopes the right way. What it must never do is slope the other way.
	const float Stress = FMath::Clamp(StressSeverity, 0.0f, 1.0f);
	return BaseReliefSeconds + MaximumMercySeconds * Stress;
}

float UEncounterPacingSubsystem::GetPerceptionScale() const
{
	switch (Phase)
	{
	case EEncounterPhase::Quiet:    return QuietPerceptionScale;
	case EEncounterPhase::Building: return BuildingPerceptionScale;
	case EEncounterPhase::Pressure: return PressurePerceptionScale;
	case EEncounterPhase::Relief:   return ReliefPerceptionScale;
	}
	return 1.0f;
}

void UEncounterPacingSubsystem::SetPhase(EEncounterPhase NewPhase)
{
	if (Phase == NewPhase)
	{
		return;
	}

	Phase = NewPhase;
	SecondsInPhase = 0.0f;

	// The relief length is fixed when relief begins rather than recomputed every frame. Stress
	// decays continuously, so a live reading would shorten the player's own mercy while they were
	// receiving it -- the calmer they got, the sooner it would end.
	if (Phase == EEncounterPhase::Relief)
	{
		CurrentReliefSeconds = GetReliefSecondsForStress(ReadPlayerStress());
	}

	OnEncounterPhaseChanged.Broadcast(Phase);
}

void UEncounterPacingSubsystem::NotifyPlayerDetected()
{
	// From any phase, including Relief. The suppression during relief is why a hunter is unlikely
	// to find the player, not a guarantee that it cannot -- a player who walks straight into one
	// should be seen, or the mercy becomes invisibility and the ship stops being dangerous.
	SetPhase(EEncounterPhase::Pressure);
}

void UEncounterPacingSubsystem::NotifyEncounterSurvived()
{
	// Only from Pressure. An enemy losing interest during a patrol it never committed to is not an
	// encounter the player survived, and crediting it would hand out relief for nothing happening.
	if (Phase == EEncounterPhase::Pressure)
	{
		SetPhase(EEncounterPhase::Relief);
	}
}

void UEncounterPacingSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (DeltaTime <= 0.0f)
	{
		return;
	}

	SecondsInPhase += DeltaTime;

	switch (Phase)
	{
	case EEncounterPhase::Quiet:
		if (SecondsInPhase >= QuietSecondsBeforeBuilding)
		{
			SetPhase(EEncounterPhase::Building);
		}
		break;

	case EEncounterPhase::Building:
		// Falls back to Quiet rather than escalating to Pressure on a timer. Pressure is entered by
		// something actually finding the player, never by the clock -- otherwise the ship produces
		// a hunt whether or not there is anyone to hunt, and the player learns the interval.
		if (SecondsInPhase >= BuildingSecondsBeforeQuiet)
		{
			SetPhase(EEncounterPhase::Quiet);
		}
		break;

	case EEncounterPhase::Pressure:
		// The stuck-hunter ceiling. Normally NotifyEncounterSurvived ends this.
		if (SecondsInPhase >= MaximumPressureSeconds)
		{
			SetPhase(EEncounterPhase::Relief);
		}
		break;

	case EEncounterPhase::Relief:
		if (SecondsInPhase >= CurrentReliefSeconds)
		{
			SetPhase(EEncounterPhase::Quiet);
		}
		break;
	}
}
