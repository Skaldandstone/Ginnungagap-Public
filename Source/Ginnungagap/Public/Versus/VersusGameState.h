#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "Versus/VersusTypes.h"
#include "VersusGameState.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnVersusMatchStateChanged);

UCLASS()
class GINNUNGAGAP_API AVersusGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(ReplicatedUsing=OnRep_MatchState, BlueprintReadOnly, Category="Versus")
	FVersusMatchSettings MatchSettings;

	UPROPERTY(ReplicatedUsing=OnRep_MatchState, BlueprintReadOnly, Category="Versus")
	EVersusMatchPhase MatchPhase = EVersusMatchPhase::WaitingForPlayers;

	UPROPERTY(BlueprintAssignable, Category="Versus")
	FOnVersusMatchStateChanged OnVersusMatchStateChanged;

	UPROPERTY(ReplicatedUsing=OnRep_MatchState, BlueprintReadOnly, Category="Versus|Commander")
	TObjectPtr<class AVersusPlayerState> AntagonistCommander;

	UPROPERTY(ReplicatedUsing=OnRep_MatchState, BlueprintReadOnly, Category="Versus|Commander")
	int32 AntagonistCommandResource = 30;

	UPROPERTY(ReplicatedUsing=OnRep_MatchState, BlueprintReadOnly, Category="Versus|Commander")
	TArray<FAntagonistCommandOrder> ActiveCommandOrders;

	UFUNCTION(BlueprintPure, Category="Versus")
	int32 GetTeamPlayerCount(EVersusTeam Team) const;

	UFUNCTION(BlueprintPure, Category="Versus")
	bool HasMinimumPlayers() const;

	UFUNCTION(BlueprintPure, Category="Versus|Commander")
	static int32 GetOrderResourceCost(EAntagonistOrderType OrderType);

	UFUNCTION(BlueprintPure, Category="Versus|Commander")
	static bool CanFactionIssueOrder(EAntagonistFaction Faction, EAntagonistOrderType OrderType);

	UFUNCTION(BlueprintPure, Category="Versus|Commander")
	bool HasCommander() const;

	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Versus|Commander")
	void AddCommandResource(EAntagonistFaction Faction, int32 Amount);

	bool TryClaimCommander(class AVersusPlayerState* Candidate);
	void ReleaseCommander(class AVersusPlayerState* Candidate);
	bool TryIssueCommandOrder(class AVersusPlayerState* Issuer, EAntagonistOrderType OrderType,
		const FVector& TargetLocation, AActor* TargetActor, int32 Priority);
	bool CompleteCommandOrder(int32 OrderId);

	UFUNCTION(BlueprintPure, Category="Versus|Commander")
	bool GetHighestPriorityOrderForFaction(EAntagonistFaction Faction,
		FAntagonistCommandOrder& OutOrder) const;

	void SetMatchSettings(const FVersusMatchSettings& NewSettings);
	void SetMatchPhase(EVersusMatchPhase NewPhase);

private:
	int32 NextCommandOrderId = 1;

protected:
	UFUNCTION()
	void OnRep_MatchState();
};
