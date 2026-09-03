#pragma once

#include "CoreMinimal.h"
#include "VersusTypes.generated.h"

UENUM(BlueprintType)
enum class EVersusTeam : uint8
{
	Protagonist,
	Antagonist,
	IndependentAI,
	Spectator
};

UENUM(BlueprintType)
enum class EAntagonistFaction : uint8
{
	None,
	Bloom,
	Pirates,
	Rebels,
	Alien
};

UENUM(BlueprintType)
enum class EVersusMatchPhase : uint8
{
	WaitingForPlayers,
	Warmup,
	InProgress,
	ProtagonistsWon,
	AntagonistsWon,
	Aborted
};

UENUM(BlueprintType)
enum class EAntagonistTeamRole : uint8
{
	Operative,
	Commander
};

UENUM(BlueprintType)
enum class EAntagonistOrderType : uint8
{
	Attack,
	Defend,
	Scout,
	Sabotage,
	Harvest,
	Infest,
	Rally
};

USTRUCT(BlueprintType)
struct FAntagonistCommandOrder
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	int32 OrderId = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	EAntagonistOrderType Type = EAntagonistOrderType::Attack;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	EAntagonistFaction Faction = EAntagonistFaction::None;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	FVector_NetQuantize TargetLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	TObjectPtr<AActor> TargetActor;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander", meta=(ClampMin="0", ClampMax="3"))
	int32 Priority = 1;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	float IssuedAtServerTime = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Versus|Commander")
	bool bCompleted = false;

	bool IsActive() const { return OrderId != INDEX_NONE && !bCompleted; }
};

USTRUCT(BlueprintType)
struct FVersusMatchSettings
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus", meta=(ClampMin="1", ClampMax="8"))
	int32 ProtagonistSlots = 4;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus", meta=(ClampMin="1", ClampMax="4"))
	int32 AntagonistSlots = 1;

	/** Faction used for player-controlled antagonists in this match. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus")
	EAntagonistFaction PlayerAntagonistFaction = EAntagonistFaction::Bloom;

	/** Independently controlled factions. They are hostile to both player teams unless they share a faction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus")
	TArray<EAntagonistFaction> IndependentAIFactions;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus")
	bool bAllowJoinInProgress = false;

	void Sanitize()
	{
		ProtagonistSlots = FMath::Clamp(ProtagonistSlots, 1, 8);
		AntagonistSlots = FMath::Clamp(AntagonistSlots, 1, 4);
		if (PlayerAntagonistFaction == EAntagonistFaction::None)
		{
			PlayerAntagonistFaction = EAntagonistFaction::Bloom;
		}
		IndependentAIFactions.Remove(EAntagonistFaction::None);
		IndependentAIFactions.Remove(PlayerAntagonistFaction);
		for (int32 Index = IndependentAIFactions.Num() - 1; Index >= 0; --Index)
		{
			if (IndependentAIFactions.Find(IndependentAIFactions[Index]) != Index)
			{
				IndependentAIFactions.RemoveAt(Index);
			}
		}
	}

	bool IsValid() const
	{
		return ProtagonistSlots >= 1 && ProtagonistSlots <= 8
			&& AntagonistSlots >= 1 && AntagonistSlots <= 4
			&& PlayerAntagonistFaction != EAntagonistFaction::None;
	}

	int32 GetMaxPlayers() const { return ProtagonistSlots + AntagonistSlots; }
};

USTRUCT(BlueprintType)
struct FAntagonistSkill
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	FName SkillId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	EAntagonistFaction Faction = EAntagonistFaction::Bloom;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill", meta=(ClampMin="1", ClampMax="5"))
	int32 Tier = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill", meta=(ClampMin="0"))
	int32 PointCost = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	TArray<FName> PrerequisiteSkillIds;

	/** Gameplay tag-like identifier interpreted by the antagonist pawn or faction director. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	FName EffectId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Antagonist Skill")
	float EffectMagnitude = 0.0f;

	bool IsDefined() const { return !SkillId.IsNone() && Faction != EAntagonistFaction::None; }
};
