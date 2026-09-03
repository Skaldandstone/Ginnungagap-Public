// Copyright Epic Games, Inc. All Rights Reserved.

#include "Progression/ClassSkillComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Progression/ClassSkillTreeSubsystem.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "Engine/GameInstance.h"
#include "Net/UnrealNetwork.h"

UClassSkillComponent::UClassSkillComponent()
{
	// Ticks only to advance activation windows and cooldowns. Effects themselves are pulled by
	// their consumers rather than pushed from here.
	PrimaryComponentTick.bCanEverTick = true;
	SetIsReplicatedByDefault(true);
}

void UClassSkillComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	// Owner-only: no other client needs to know how long until this player's kit is ready again.
	DOREPLIFETIME_CONDITION(UClassSkillComponent, ActiveRuntime, COND_OwnerOnly);
}

void UClassSkillComponent::BeginPlay()
{
	Super::BeginPlay();
	ReloadFromProgression();
}

void UClassSkillComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	for (FActiveSkillRuntime& Runtime : ActiveRuntime)
	{
		if (Runtime.RemainingDuration > 0.0f)
		{
			Runtime.RemainingDuration -= DeltaTime;
			if (Runtime.RemainingDuration <= 0.0f)
			{
				// Clamped rather than left negative so GetRemainingDuration never reports nonsense.
				Runtime.RemainingDuration = 0.0f;
				OnActiveSkillExpired.Broadcast(Runtime.SkillID);
			}
		}

		if (Runtime.RemainingCooldown > 0.0f)
		{
			Runtime.RemainingCooldown = FMath::Max(0.0f, Runtime.RemainingCooldown - DeltaTime);
		}
	}
}

void UClassSkillComponent::ReloadFromProgression()
{
	UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr;
	if (!GameInstance)
	{
		return;
	}

	SetSkillTree(GameInstance->GetSubsystem<UClassSkillTreeSubsystem>());

	if (URunOutcomeSubsystem* RunOutcome = GameInstance->GetSubsystem<URunOutcomeSubsystem>())
	{
		SelectedRole = RunOutcome->GetPlayerRole();
		OwnedSkills = RunOutcome->GetRoleSkills(SelectedRole);
	}

	PruneIllegalLoadout();
	ResetActivationStateForNewRun();
	OnSkillsChanged.Broadcast();
}

void UClassSkillComponent::SetSkillTree(UClassSkillTreeSubsystem* InSkillTree)
{
	SkillTreeSubsystem = InSkillTree;
}

void UClassSkillComponent::SelectRole(EPressureSuitRole NewRole)
{
	if (SelectedRole == NewRole)
	{
		return;
	}

	SelectedRole = NewRole;

	// Progression is per-role, so switching swaps the whole owned set rather than carrying the
	// previous role's ranks across.
	if (UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr)
	{
		if (URunOutcomeSubsystem* RunOutcome = GameInstance->GetSubsystem<URunOutcomeSubsystem>())
		{
			OwnedSkills = RunOutcome->GetRoleSkills(SelectedRole);
		}
	}

	PruneIllegalLoadout();
	ResetActivationStateForNewRun();
	OnRoleChanged.Broadcast();
	OnSkillsChanged.Broadcast();
}

void UClassSkillComponent::ResetActivationStateForNewRun()
{
	ActiveRuntime.Empty();
	if (!SkillTreeSubsystem)
	{
		return;
	}

	for (const FString& SkillID : OwnedSkills.EquippedActiveSkills)
	{
		const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);

		FActiveSkillRuntime Runtime;
		Runtime.SkillID = SkillID;
		Runtime.ChargesRemaining = Skill.ChargesPerRun;
		ActiveRuntime.Add(Runtime);
	}
}

FActiveSkillRuntime* UClassSkillComponent::FindRuntime(const FString& SkillID)
{
	return ActiveRuntime.FindByPredicate(
		[&SkillID](const FActiveSkillRuntime& Runtime) { return Runtime.SkillID == SkillID; });
}

const FActiveSkillRuntime* UClassSkillComponent::FindRuntime(const FString& SkillID) const
{
	return ActiveRuntime.FindByPredicate(
		[&SkillID](const FActiveSkillRuntime& Runtime) { return Runtime.SkillID == SkillID; });
}

bool UClassSkillComponent::CanActivateSkill(const FString& SkillID) const
{
	if (!SkillTreeSubsystem || !OwnedSkills.EquippedActiveSkills.Contains(SkillID))
	{
		return false;
	}

	const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
	if (Skill.Activation != ESkillActivation::Active || GetSkillRank(SkillID) <= 0)
	{
		return false;
	}

	const FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	if (!Runtime || Runtime->RemainingCooldown > 0.0f)
	{
		return false;
	}

	// Re-triggering while still in force would silently waste a charge, so it is refused rather
	// than allowed to refresh the window.
	if (Runtime->RemainingDuration > 0.0f)
	{
		return false;
	}

	// ChargesPerRun of zero means limited by cooldown alone.
	return Skill.ChargesPerRun <= 0 || Runtime->ChargesRemaining > 0;
}

void UClassSkillComponent::ApplyActivation(const FString& SkillID)
{
	const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
	FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	if (!Runtime)
	{
		return;
	}

	Runtime->RemainingDuration = Skill.DurationSeconds;

	// Cooldown runs from activation rather than expiry, so the number a player reads is the whole
	// cycle instead of a gap that only begins once the effect lapses.
	Runtime->RemainingCooldown = Skill.CooldownSeconds;

	if (Skill.ChargesPerRun > 0)
	{
		Runtime->ChargesRemaining = FMath::Max(0, Runtime->ChargesRemaining - 1);
	}

	OnActiveSkillTriggered.Broadcast(SkillID);
}

bool UClassSkillComponent::ActivateSkill(const FString& SkillID)
{
	if (!CanActivateSkill(SkillID))
	{
		return false;
	}

	ApplyActivation(SkillID);

	// The server's copy is what the hazard maths reads. Running it locally too keeps the bar
	// responsive without waiting on the round trip; the server re-checks, so a client that lies
	// here changes nothing but its own display.
	const AActor* Owner = GetOwner();
	if (Owner && Owner->GetLocalRole() < ROLE_Authority)
	{
		ServerActivateSkill(SkillID);
	}

	return true;
}

bool UClassSkillComponent::ServerActivateSkill_Validate(const FString& SkillID)
{
	// Length guard only. Legality is decided by CanActivateSkill, which knows the loadout.
	return SkillID.Len() <= 64;
}

void UClassSkillComponent::ServerActivateSkill_Implementation(const FString& SkillID)
{
	if (!CanActivateSkill(SkillID))
	{
		return;
	}

	ApplyActivation(SkillID);
}

bool UClassSkillComponent::ActivateSkillSlot(int32 SlotIndex)
{
	const FString SkillID = GetSkillInSlot(SlotIndex);
	return !SkillID.IsEmpty() && ActivateSkill(SkillID);
}

FString UClassSkillComponent::GetSkillInSlot(int32 SlotIndex) const
{
	return OwnedSkills.EquippedActiveSkills.IsValidIndex(SlotIndex)
		? OwnedSkills.EquippedActiveSkills[SlotIndex]
		: FString();
}

bool UClassSkillComponent::IsSkillActive(const FString& SkillID) const
{
	const FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	return Runtime && Runtime->RemainingDuration > 0.0f;
}

float UClassSkillComponent::GetRemainingDuration(const FString& SkillID) const
{
	const FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	return Runtime ? FMath::Max(0.0f, Runtime->RemainingDuration) : 0.0f;
}

float UClassSkillComponent::GetRemainingCooldown(const FString& SkillID) const
{
	const FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	return Runtime ? FMath::Max(0.0f, Runtime->RemainingCooldown) : 0.0f;
}

int32 UClassSkillComponent::GetChargesRemaining(const FString& SkillID) const
{
	if (!SkillTreeSubsystem)
	{
		return -1;
	}

	// -1 rather than a large number, so a HUD can distinguish "unlimited" from "plenty left"
	// without having to know the catalogue.
	const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
	if (Skill.ChargesPerRun <= 0)
	{
		return -1;
	}

	const FActiveSkillRuntime* Runtime = FindRuntime(SkillID);
	return Runtime ? Runtime->ChargesRemaining : 0;
}

int32 UClassSkillComponent::GetSkillRank(const FString& SkillID) const
{
	const int32* Rank = OwnedSkills.SkillRanks.Find(SkillID);
	return Rank ? FMath::Max(0, *Rank) : 0;
}

bool UClassSkillComponent::HasSkill(const FString& SkillID) const
{
	return GetSkillRank(SkillID) > 0;
}

void UClassSkillComponent::GrantSkillRank(const FString& SkillID)
{
	if (!SkillTreeSubsystem || !SkillTreeSubsystem->DoesSkillExist(SkillID))
	{
		return;
	}

	const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
	int32& Rank = OwnedSkills.SkillRanks.FindOrAdd(SkillID);
	Rank = FMath::Clamp(Rank + 1, 0, Skill.MaxRank);

	OnSkillsChanged.Broadcast();
}

bool UClassSkillComponent::EquipActiveSkill(const FString& SkillID)
{
	if (!SkillTreeSubsystem
		|| !SkillTreeSubsystem->CanEquipActiveSkill(SelectedRole, SkillID, OwnedSkills))
	{
		return false;
	}

	OwnedSkills.EquippedActiveSkills.Add(SkillID);

	// A newly equipped active arrives ready, with full charges.
	const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
	FActiveSkillRuntime Runtime;
	Runtime.SkillID = SkillID;
	Runtime.ChargesRemaining = Skill.ChargesPerRun;
	ActiveRuntime.Add(Runtime);

	OnSkillsChanged.Broadcast();
	return true;
}

bool UClassSkillComponent::UnequipActiveSkill(const FString& SkillID)
{
	if (OwnedSkills.EquippedActiveSkills.Remove(SkillID) <= 0)
	{
		return false;
	}

	// Runtime state goes with it, so an active cannot keep contributing after leaving the payload,
	// and cannot be re-equipped to dodge its own cooldown.
	ActiveRuntime.RemoveAll(
		[&SkillID](const FActiveSkillRuntime& Runtime) { return Runtime.SkillID == SkillID; });

	OnSkillsChanged.Broadcast();
	return true;
}

int32 UClassSkillComponent::GetFreeActiveSlots() const
{
	return FMath::Max(0,
		FClassProgression::MaxEquippedActiveSkills - OwnedSkills.EquippedActiveSkills.Num());
}

void UClassSkillComponent::PruneIllegalLoadout()
{
	if (!SkillTreeSubsystem)
	{
		return;
	}

	OwnedSkills.EquippedActiveSkills.RemoveAll([this](const FString& SkillID)
	{
		const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
		const bool bStillOwned = GetSkillRank(SkillID) > 0;
		const bool bStillLegal = Skill.Activation == ESkillActivation::Active
			&& SkillTreeSubsystem->IsSkillVisibleToRole(Skill, SelectedRole);
		return !bStillOwned || !bStillLegal;
	});

	// Trim rather than reject if saved data predates a smaller slot count. Keeping the earliest
	// picks is arbitrary but deterministic, which matters more than which three survive.
	if (OwnedSkills.EquippedActiveSkills.Num() > FClassProgression::MaxEquippedActiveSkills)
	{
		OwnedSkills.EquippedActiveSkills.SetNum(FClassProgression::MaxEquippedActiveSkills);
	}
}

float UClassSkillComponent::GetEffect(FName EffectId) const
{
	if (!SkillTreeSubsystem)
	{
		return 0.0f;
	}

	// Passives are simply true of the character whenever owned.
	float Total = SkillTreeSubsystem->GetPassiveEffectMagnitude(EffectId, OwnedSkills);

	// Actives contribute only while their window is open. Equipping one grants the right to
	// trigger it, never the effect itself -- which is what allows their magnitudes to be several
	// times larger than any passive without unbalancing a run.
	for (const FString& SkillID : OwnedSkills.EquippedActiveSkills)
	{
		if (!IsSkillActive(SkillID))
		{
			continue;
		}

		const FClassSkill Skill = SkillTreeSubsystem->GetSkillByID(SkillID);
		if (Skill.EffectId != EffectId)
		{
			continue;
		}

		Total += SkillTreeSubsystem->GetSkillEffectMagnitude(SkillID, GetSkillRank(SkillID));
	}

	return Total;
}

float UClassSkillComponent::GetCostMultiplier(FName EffectId, float MaxReduction) const
{
	// Clamped short of 1.0 so no combination of skills makes a drain or cost disappear outright.
	// Skill should shift the odds, never remove the constraint the game is built on.
	const float Reduction = FMath::Clamp(GetEffect(EffectId), 0.0f, FMath::Clamp(MaxReduction, 0.0f, 0.95f));
	return 1.0f - Reduction;
}
