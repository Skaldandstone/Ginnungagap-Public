#include "Versus/VersusGameState.h"

#include "Net/UnrealNetwork.h"
#include "Versus/VersusPlayerState.h"

void AVersusGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AVersusGameState, MatchSettings);
	DOREPLIFETIME(AVersusGameState, MatchPhase);
	DOREPLIFETIME(AVersusGameState, AntagonistCommander);
	DOREPLIFETIME(AVersusGameState, AntagonistCommandResource);
	DOREPLIFETIME(AVersusGameState, ActiveCommandOrders);
}

int32 AVersusGameState::GetTeamPlayerCount(EVersusTeam Team) const
{
	int32 Count = 0;
	for (const APlayerState* State : PlayerArray)
	{
		const AVersusPlayerState* VersusState = Cast<AVersusPlayerState>(State);
		Count += VersusState && VersusState->VersusTeam == Team ? 1 : 0;
	}
	return Count;
}

bool AVersusGameState::HasMinimumPlayers() const
{
	return GetTeamPlayerCount(EVersusTeam::Protagonist) > 0
		&& GetTeamPlayerCount(EVersusTeam::Antagonist) > 0;
}

int32 AVersusGameState::GetOrderResourceCost(EAntagonistOrderType OrderType)
{
	switch (OrderType)
	{
	case EAntagonistOrderType::Scout: return 5;
	case EAntagonistOrderType::Attack: return 8;
	case EAntagonistOrderType::Defend: return 8;
	case EAntagonistOrderType::Harvest: return 10;
	case EAntagonistOrderType::Sabotage: return 12;
	case EAntagonistOrderType::Infest: return 14;
	case EAntagonistOrderType::Rally: return 16;
	default: return 10;
	}
}

bool AVersusGameState::HasCommander() const
{
	return IsValid(AntagonistCommander.Get());
}

bool AVersusGameState::CanFactionIssueOrder(EAntagonistFaction Faction, EAntagonistOrderType OrderType)
{
	if (Faction == EAntagonistFaction::None) return false;
	if (Faction == EAntagonistFaction::Alien)
	{
		return OrderType != EAntagonistOrderType::Sabotage && OrderType != EAntagonistOrderType::Infest;
	}
	if (Faction == EAntagonistFaction::Bloom)
	{
		return OrderType != EAntagonistOrderType::Sabotage;
	}
	return OrderType != EAntagonistOrderType::Infest;
}

void AVersusGameState::AddCommandResource(EAntagonistFaction Faction, int32 Amount)
{
	if (!HasAuthority() || Faction != MatchSettings.PlayerAntagonistFaction || Amount <= 0) return;
	AntagonistCommandResource = FMath::Clamp(AntagonistCommandResource + Amount, 0, 999);
	OnRep_MatchState();
	ForceNetUpdate();
}

bool AVersusGameState::TryClaimCommander(AVersusPlayerState* Candidate)
{
	if (!HasAuthority() || !Candidate || Candidate->VersusTeam != EVersusTeam::Antagonist
		|| (IsValid(AntagonistCommander.Get()) && AntagonistCommander != Candidate))
	{
		return false;
	}
	AntagonistCommander = Candidate;
	Candidate->SetAntagonistTeamRole(EAntagonistTeamRole::Commander);
	OnRep_MatchState();
	ForceNetUpdate();
	return true;
}

void AVersusGameState::ReleaseCommander(AVersusPlayerState* Candidate)
{
	if (!HasAuthority() || AntagonistCommander != Candidate) return;
	if (Candidate) Candidate->SetAntagonistTeamRole(EAntagonistTeamRole::Operative);
	AntagonistCommander = nullptr;
	OnRep_MatchState();
	ForceNetUpdate();
}

bool AVersusGameState::TryIssueCommandOrder(AVersusPlayerState* Issuer,
	EAntagonistOrderType OrderType, const FVector& TargetLocation, AActor* TargetActor, int32 Priority)
{
	if (!HasAuthority() || Issuer != AntagonistCommander
		|| !CanFactionIssueOrder(Issuer ? Issuer->AntagonistFaction : EAntagonistFaction::None, OrderType))
	{
		return false;
	}
	const int32 Cost = GetOrderResourceCost(OrderType);
	if (AntagonistCommandResource < Cost) return false;

	ActiveCommandOrders.RemoveAll([](const FAntagonistCommandOrder& Order) { return Order.bCompleted; });
	if (ActiveCommandOrders.Num() >= 8) return false;
	AntagonistCommandResource -= Cost;
	FAntagonistCommandOrder& Order = ActiveCommandOrders.AddDefaulted_GetRef();
	Order.OrderId = NextCommandOrderId++;
	Order.Type = OrderType;
	Order.Faction = Issuer->AntagonistFaction;
	Order.TargetLocation = TargetLocation;
	Order.TargetActor = TargetActor;
	Order.Priority = FMath::Clamp(Priority, 0, 3);
	Order.IssuedAtServerTime = GetServerWorldTimeSeconds();
	OnRep_MatchState();
	ForceNetUpdate();
	return true;
}

bool AVersusGameState::CompleteCommandOrder(int32 OrderId)
{
	if (!HasAuthority()) return false;
	for (FAntagonistCommandOrder& Order : ActiveCommandOrders)
	{
		if (Order.OrderId == OrderId && !Order.bCompleted)
		{
			Order.bCompleted = true;
			OnRep_MatchState();
			ForceNetUpdate();
			return true;
		}
	}
	return false;
}

bool AVersusGameState::GetHighestPriorityOrderForFaction(EAntagonistFaction Faction,
	FAntagonistCommandOrder& OutOrder) const
{
	const FAntagonistCommandOrder* Best = nullptr;
	for (const FAntagonistCommandOrder& Order : ActiveCommandOrders)
	{
		if (!Order.IsActive() || Order.Faction != Faction) continue;
		if (!Best || Order.Priority > Best->Priority
			|| (Order.Priority == Best->Priority && Order.IssuedAtServerTime > Best->IssuedAtServerTime))
		{
			Best = &Order;
		}
	}
	if (!Best) return false;
	OutOrder = *Best;
	return true;
}

void AVersusGameState::SetMatchSettings(const FVersusMatchSettings& NewSettings)
{
	if (!HasAuthority())
	{
		return;
	}
	MatchSettings = NewSettings;
	MatchSettings.Sanitize();
	OnRep_MatchState();
	ForceNetUpdate();
}

void AVersusGameState::SetMatchPhase(EVersusMatchPhase NewPhase)
{
	if (!HasAuthority() || MatchPhase == NewPhase)
	{
		return;
	}
	MatchPhase = NewPhase;
	OnRep_MatchState();
	ForceNetUpdate();
}

void AVersusGameState::OnRep_MatchState()
{
	OnVersusMatchStateChanged.Broadcast();
}
