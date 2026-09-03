#include "Versus/AntagonistActivityComponent.h"

#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "Versus/AntagonistActivitySource.h"
#include "Versus/VersusGameState.h"
#include "Versus/VersusPlayerState.h"

UAntagonistActivityComponent::UAntagonistActivityComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = 0.05f;
	SetIsReplicatedByDefault(true);
}

void UAntagonistActivityComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UAntagonistActivityComponent, Snapshot);
	DOREPLIFETIME(UAntagonistActivityComponent, ActivitySource);
}

bool UAntagonistActivityComponent::StartActivity(AActor* Source)
{
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		ServerStartActivity(Source);
		return Source != nullptr && !IsActivityActive();
	}
	return StartAuthoritative(Source);
}

void UAntagonistActivityComponent::ServerStartActivity_Implementation(AActor* Source)
{
	StartAuthoritative(Source);
}

bool UAntagonistActivityComponent::StartAuthoritative(AActor* Source)
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn || !Source || IsActivityActive() || !Source->Implements<UAntagonistActivitySource>()
		|| !IAntagonistActivitySource::Execute_CanStartAntagonistActivity(Source, Pawn))
	{
		return false;
	}

	const FAntagonistActivityDefinition Definition =
		IAntagonistActivitySource::Execute_GetAntagonistActivityDefinition(Source, Pawn);
	const AVersusPlayerState* State = Pawn->GetPlayerState<AVersusPlayerState>();
	if (!Definition.IsDefined() || !State || State->AntagonistFaction != Definition.Faction
		|| FVector::DistSquared(Pawn->GetActorLocation(), Source->GetActorLocation()) > FMath::Square(Definition.MaxRange))
	{
		return false;
	}

	ActivitySource = Source;
	ActiveDefinition = Definition;
	ElapsedSeconds = 0.0f;
	Snapshot = FAntagonistActivitySnapshot();
	Snapshot.State = EPlayerActivityState::Active;
	Snapshot.ActivityId = Definition.ActivityId;
	Snapshot.DisplayName = Definition.DisplayName;
	Snapshot.Motivation = Definition.Motivation;
	Snapshot.Mechanic = Definition.Mechanic;
	Snapshot.Faction = Definition.Faction;
	Snapshot.TotalSteps = FMath::Max(1, Definition.PuzzleSteps);
	Snapshot.ResourceBalance = Definition.Faction == EAntagonistFaction::Alien
		? FVector(0.25f, 0.72f, 0.45f) : FVector(0.2f, 0.8f, 0.5f);
	BuildSequence();

	if (ACharacter* Character = Cast<ACharacter>(Pawn))
	{
		PreviousMovementMode = static_cast<uint8>(Character->GetCharacterMovement()->MovementMode);
		PreviousCustomMovementMode = Character->GetCharacterMovement()->CustomMovementMode;
		Character->GetCharacterMovement()->DisableMovement();
	}
	BroadcastChanged();
	return true;
}

void UAntagonistActivityComponent::BuildSequence()
{
	InputSequence.Reset();
	if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::TimedExtraction
		|| ActiveDefinition.Mechanic == EAntagonistActivityMechanic::MetabolicBalance
		|| ActiveDefinition.Mechanic == EAntagonistActivityMechanic::AmbushTiming)
	{
		return;
	}
	FRandomStream Random(GetTypeHash(ActiveDefinition.ActivityId) ^ GetTypeHash(ActivitySource->GetFName()));
	for (int32 Index = 0; Index < Snapshot.TotalSteps; ++Index)
	{
		InputSequence.Add(static_cast<EActivityInput>(Random.RandRange(0, 3)));
	}
	Snapshot.ExpectedInput = InputSequence[0];
}

void UAntagonistActivityComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!GetOwner() || !GetOwner()->HasAuthority() || !IsActivityActive())
	{
		return;
	}
	if (!IsValid(ActivitySource)
		|| FVector::DistSquared(GetOwner()->GetActorLocation(), ActivitySource->GetActorLocation())
			> FMath::Square(ActiveDefinition.MaxRange))
	{
		Finish(EPlayerActivityState::Cancelled);
		return;
	}

	ElapsedSeconds += DeltaTime;
	if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::TimedExtraction)
	{
		Snapshot.Progress = FMath::Clamp(ElapsedSeconds / FMath::Max(0.1f, ActiveDefinition.DurationSeconds), 0.0f, 1.0f);
		BroadcastChanged();
		if (Snapshot.Progress >= 1.0f) Finish(EPlayerActivityState::Completed);
	}
	else if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::AmbushTiming)
	{
		Snapshot.TimingCursor = FMath::Fmod(ElapsedSeconds, 1.8f) / 1.8f;
		BroadcastChanged();
	}
}

void UAntagonistActivityComponent::SubmitInput(EActivityInput Input)
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) ServerSubmitInput(Input);
	else SubmitAuthoritative(Input);
}

void UAntagonistActivityComponent::ServerSubmitInput_Implementation(EActivityInput Input)
{
	SubmitAuthoritative(Input);
}

void UAntagonistActivityComponent::SubmitAuthoritative(EActivityInput Input)
{
	if (!IsActivityActive()) return;

	if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::MetabolicBalance)
	{
		if (Input == EActivityInput::Primary)
		{
			Snapshot.ResourceBalance.X += 0.12f; Snapshot.ResourceBalance.Y -= 0.06f;
		}
		else if (Input == EActivityInput::Secondary)
		{
			Snapshot.ResourceBalance.Y += 0.12f; Snapshot.ResourceBalance.Z -= 0.06f;
		}
		else if (Input == EActivityInput::Tertiary)
		{
			Snapshot.ResourceBalance.Z += 0.12f; Snapshot.ResourceBalance.X -= 0.06f;
		}
		else if (IsBalanceStable())
		{
			++Snapshot.CurrentStep;
			Snapshot.Progress = static_cast<float>(Snapshot.CurrentStep) / Snapshot.TotalSteps;
			Snapshot.ResourceBalance += FVector(-0.08f, 0.10f, -0.04f);
		}
		else
		{
			++Snapshot.Mistakes;
		}
		Snapshot.ResourceBalance.X = FMath::Clamp(Snapshot.ResourceBalance.X, 0.0f, 1.0f);
		Snapshot.ResourceBalance.Y = FMath::Clamp(Snapshot.ResourceBalance.Y, 0.0f, 1.0f);
		Snapshot.ResourceBalance.Z = FMath::Clamp(Snapshot.ResourceBalance.Z, 0.0f, 1.0f);
	}
	else if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::AmbushTiming)
	{
		const bool bInsideWindow = FMath::Abs(Snapshot.TimingCursor - Snapshot.TimingWindowCenter)
			<= Snapshot.TimingWindowWidth * 0.5f;
		if (Input == EActivityInput::Primary && bInsideWindow)
		{
			++Snapshot.CurrentStep;
			Snapshot.Progress = static_cast<float>(Snapshot.CurrentStep) / Snapshot.TotalSteps;
			Snapshot.TimingWindowCenter = FMath::FRandRange(0.25f, 0.75f);
			Snapshot.TimingWindowWidth = FMath::Max(0.08f, Snapshot.TimingWindowWidth - 0.02f);
		}
		else
		{
			++Snapshot.Mistakes;
		}
	}
	else
	{
		SubmitSequenceInput(Input);
	}

	if (Snapshot.Mistakes >= ActiveDefinition.AllowedMistakes)
	{
		Finish(EPlayerActivityState::Failed);
	}
	else if (Snapshot.Progress >= 1.0f)
	{
		Finish(EPlayerActivityState::Completed);
	}
	else
	{
		BroadcastChanged();
	}
}

bool UAntagonistActivityComponent::SubmitSequenceInput(EActivityInput Input)
{
	if (!InputSequence.IsValidIndex(Snapshot.CurrentStep)) return false;
	if (Input != InputSequence[Snapshot.CurrentStep])
	{
		++Snapshot.Mistakes;
		if (ActiveDefinition.Mechanic == EAntagonistActivityMechanic::NeuralMimicry && Snapshot.CurrentStep > 0)
		{
			--Snapshot.CurrentStep;
		}
	}
	else
	{
		++Snapshot.CurrentStep;
	}
	Snapshot.Progress = static_cast<float>(Snapshot.CurrentStep) / Snapshot.TotalSteps;
	if (InputSequence.IsValidIndex(Snapshot.CurrentStep)) Snapshot.ExpectedInput = InputSequence[Snapshot.CurrentStep];
	return Input == Snapshot.ExpectedInput;
}

bool UAntagonistActivityComponent::IsBalanceStable() const
{
	return Snapshot.ResourceBalance.X >= 0.35f && Snapshot.ResourceBalance.X <= 0.68f
		&& Snapshot.ResourceBalance.Y >= 0.35f && Snapshot.ResourceBalance.Y <= 0.68f
		&& Snapshot.ResourceBalance.Z >= 0.35f && Snapshot.ResourceBalance.Z <= 0.68f;
}

void UAntagonistActivityComponent::CancelActivity()
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) ServerCancelActivity();
	else Finish(EPlayerActivityState::Cancelled);
}

void UAntagonistActivityComponent::ServerCancelActivity_Implementation()
{
	Finish(EPlayerActivityState::Cancelled);
}

void UAntagonistActivityComponent::Finish(EPlayerActivityState FinalState)
{
	if (!IsActivityActive()) return;
	Snapshot.State = FinalState;
	if (FinalState == EPlayerActivityState::Completed)
	{
		APawn* Pawn = Cast<APawn>(GetOwner());
		if (AVersusPlayerState* State = Pawn ? Pawn->GetPlayerState<AVersusPlayerState>() : nullptr)
		{
			State->GrantAntagonistSkillPoints(ActiveDefinition.SkillPointReward);
		}
		if (AVersusGameState* GameState = GetWorld() ? GetWorld()->GetGameState<AVersusGameState>() : nullptr)
		{
			GameState->AddCommandResource(ActiveDefinition.Faction, ActiveDefinition.CommandResourceReward);
		}
		if (IsValid(ActivitySource) && ActivitySource->Implements<UAntagonistActivitySource>())
		{
			IAntagonistActivitySource::Execute_OnAntagonistActivityCompleted(
				ActivitySource, Pawn, ActiveDefinition.CompletionEffectId);
		}
	}

	if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		Character->GetCharacterMovement()->SetMovementMode(
			static_cast<EMovementMode>(PreviousMovementMode), PreviousCustomMovementMode);
	}
	ActivitySource = nullptr;
	BroadcastChanged();
}

void UAntagonistActivityComponent::OnRep_Snapshot()
{
	BroadcastChanged();
}

void UAntagonistActivityComponent::BroadcastChanged()
{
	OnActivityChanged.Broadcast(Snapshot);
	if (GetOwner()) GetOwner()->ForceNetUpdate();
}
