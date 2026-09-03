#include "Versus/VersusPlayerState.h"

#include "Net/UnrealNetwork.h"
#include "Versus/AntagonistSkillTreeSubsystem.h"
#include "Versus/VersusGameState.h"

AVersusPlayerState::AVersusPlayerState()
{
	bReplicates = true;
}

void AVersusPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AVersusPlayerState, VersusTeam);
	DOREPLIFETIME(AVersusPlayerState, AntagonistFaction);
	DOREPLIFETIME(AVersusPlayerState, AntagonistTeamRole);
	DOREPLIFETIME(AVersusPlayerState, AntagonistSkillPoints);
	DOREPLIFETIME(AVersusPlayerState, UnlockedAntagonistSkillIds);
}

void AVersusPlayerState::SetVersusIdentity(EVersusTeam NewTeam, EAntagonistFaction NewFaction)
{
	if (!HasAuthority())
	{
		return;
	}
	VersusTeam = NewTeam;
	AntagonistFaction = NewTeam == EVersusTeam::Antagonist ? NewFaction : EAntagonistFaction::None;
	AntagonistTeamRole = EAntagonistTeamRole::Operative;
	if (NewTeam != EVersusTeam::Antagonist)
	{
		AntagonistSkillPoints = 0;
		UnlockedAntagonistSkillIds.Reset();
	}
	OnRep_VersusIdentity();
	ForceNetUpdate();
}

void AVersusPlayerState::SetAntagonistTeamRole(EAntagonistTeamRole NewRole)
{
	if (!HasAuthority() || VersusTeam != EVersusTeam::Antagonist) return;
	AntagonistTeamRole = NewRole;
	OnRep_VersusIdentity();
	ForceNetUpdate();
}

void AVersusPlayerState::ServerRequestCommanderRole_Implementation(bool bBecomeCommander)
{
	if (AVersusGameState* State = GetWorld() ? GetWorld()->GetGameState<AVersusGameState>() : nullptr)
	{
		if (bBecomeCommander) State->TryClaimCommander(this);
		else State->ReleaseCommander(this);
	}
}

void AVersusPlayerState::ServerIssueCommandOrder_Implementation(EAntagonistOrderType OrderType,
	FVector_NetQuantize TargetLocation, AActor* TargetActor, int32 Priority)
{
	if (AVersusGameState* State = GetWorld() ? GetWorld()->GetGameState<AVersusGameState>() : nullptr)
	{
		State->TryIssueCommandOrder(this, OrderType, TargetLocation, TargetActor, Priority);
	}
}

void AVersusPlayerState::GrantAntagonistSkillPoints(int32 Points)
{
	if (!HasAuthority() || VersusTeam != EVersusTeam::Antagonist || Points <= 0)
	{
		return;
	}
	AntagonistSkillPoints = FMath::Max(0, AntagonistSkillPoints + Points);
	OnRep_AntagonistProgression();
	ForceNetUpdate();
}

void AVersusPlayerState::ServerUnlockAntagonistSkill_Implementation(FName SkillId)
{
	if (VersusTeam != EVersusTeam::Antagonist || !GetGameInstance())
	{
		return;
	}
	const UAntagonistSkillTreeSubsystem* SkillTree =
		GetGameInstance()->GetSubsystem<UAntagonistSkillTreeSubsystem>();
	if (!SkillTree || !SkillTree->CanUnlockSkill(SkillId, AntagonistFaction,
		UnlockedAntagonistSkillIds, AntagonistSkillPoints))
	{
		return;
	}

	const FAntagonistSkill Skill = SkillTree->GetSkill(SkillId);
	AntagonistSkillPoints -= Skill.PointCost;
	UnlockedAntagonistSkillIds.Add(SkillId);
	OnRep_AntagonistProgression();
	ForceNetUpdate();
}

void AVersusPlayerState::OnRep_VersusIdentity()
{
	OnVersusIdentityChanged.Broadcast();
}

void AVersusPlayerState::OnRep_AntagonistProgression()
{
	OnAntagonistProgressionChanged.Broadcast();
}
