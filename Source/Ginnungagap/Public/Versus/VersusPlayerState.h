#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "Versus/VersusTypes.h"
#include "VersusPlayerState.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnVersusIdentityChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAntagonistProgressionChanged);

UCLASS()
class GINNUNGAGAP_API AVersusPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	AVersusPlayerState();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(ReplicatedUsing=OnRep_VersusIdentity, BlueprintReadOnly, Category="Versus")
	EVersusTeam VersusTeam = EVersusTeam::Spectator;

	UPROPERTY(ReplicatedUsing=OnRep_VersusIdentity, BlueprintReadOnly, Category="Versus")
	EAntagonistFaction AntagonistFaction = EAntagonistFaction::None;

	UPROPERTY(ReplicatedUsing=OnRep_VersusIdentity, BlueprintReadOnly, Category="Versus|Commander")
	EAntagonistTeamRole AntagonistTeamRole = EAntagonistTeamRole::Operative;

	UPROPERTY(ReplicatedUsing=OnRep_AntagonistProgression, BlueprintReadOnly, Category="Versus|Progression")
	int32 AntagonistSkillPoints = 0;

	UPROPERTY(ReplicatedUsing=OnRep_AntagonistProgression, BlueprintReadOnly, Category="Versus|Progression")
	TArray<FName> UnlockedAntagonistSkillIds;

	UPROPERTY(BlueprintAssignable, Category="Versus")
	FOnVersusIdentityChanged OnVersusIdentityChanged;

	UPROPERTY(BlueprintAssignable, Category="Versus|Progression")
	FOnAntagonistProgressionChanged OnAntagonistProgressionChanged;

	UFUNCTION(BlueprintPure, Category="Versus")
	bool IsAntagonist() const { return VersusTeam == EVersusTeam::Antagonist; }

	UFUNCTION(BlueprintCallable, Server, Reliable, Category="Versus|Progression")
	void ServerUnlockAntagonistSkill(FName SkillId);

	UFUNCTION(BlueprintCallable, Server, Reliable, Category="Versus|Commander")
	void ServerRequestCommanderRole(bool bBecomeCommander);

	UFUNCTION(BlueprintCallable, Server, Reliable, Category="Versus|Commander")
	void ServerIssueCommandOrder(EAntagonistOrderType OrderType, FVector_NetQuantize TargetLocation,
		AActor* TargetActor, int32 Priority);

	/** Server-only reward hook for match events and faction objectives. */
	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Versus|Progression")
	void GrantAntagonistSkillPoints(int32 Points);

	void SetVersusIdentity(EVersusTeam NewTeam, EAntagonistFaction NewFaction);
	void SetAntagonistTeamRole(EAntagonistTeamRole NewRole);

protected:
	UFUNCTION()
	void OnRep_VersusIdentity();

	UFUNCTION()
	void OnRep_AntagonistProgression();
};
