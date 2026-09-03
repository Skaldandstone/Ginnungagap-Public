#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Progression/PlayerClass.h"
#include "ClassSkillComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnRoleChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSkillsChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActiveSkillTriggered, const FString&, SkillID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActiveSkillExpired, const FString&, SkillID);

/**
 * Live state of one equipped active: how long it stays in force, and when it can be used again.
 *
 * Held in an array rather than a map because TMap cannot replicate, and cooldowns have to survive
 * the trip to the owning client or a co-op player would see a bar that never greys out.
 */
USTRUCT(BlueprintType)
struct FActiveSkillRuntime
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	FString SkillID;

	/** Seconds the effect remains in force. Zero or below means it is not currently contributing. */
	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	float RemainingDuration = 0.0f;

	/** Seconds until it can be triggered again. Runs from activation, not from expiry. */
	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	float RemainingCooldown = 0.0f;

	/** Triggers left this run. Meaningless when the skill's ChargesPerRun is zero. */
	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	int32 ChargesRemaining = 0;
};

/**
 * The player's live skill state during a run: role, unlocked ranks, the payload of equipped
 * actives, and the runtime state of those actives.
 *
 * Effects are queried through GetEffect at the point of use rather than being written into
 * character properties. Stateless means they cannot drift, cannot double-apply when a rank is
 * bought mid-session, and need no matching teardown -- the original design mutated
 * ThrusterAcceleration and OxygenDrainMultiplier in place against an empty RemoveSkillBonuses(),
 * so every purchase compounded the last.
 *
 * Passives contribute whenever they are owned. Actives contribute only while their window is open,
 * which is what lets them carry magnitudes several times larger than any passive.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UClassSkillComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UClassSkillComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	EPressureSuitRole SelectedRole = GinnungagapDefaults::StartingSuitRole;

	/** Owned ranks and the equipped payload. */
	UPROPERTY(BlueprintReadOnly, Category = "Skills")
	FClassSkillsArray OwnedSkills;

	UFUNCTION(BlueprintCallable, Category = "Skills")
	void SelectRole(EPressureSuitRole NewRole);

	UFUNCTION(BlueprintPure, Category = "Skills")
	EPressureSuitRole GetSelectedRole() const { return SelectedRole; }

	/**
	 * Total beneficial fraction for EffectId from everything in force right now: owned passives,
	 * plus equipped actives whose window is still open. Always a non-negative fraction; the caller
	 * decides direction, so a consumer reducing a cost subtracts and one raising a resistance adds.
	 */
	UFUNCTION(BlueprintPure, Category = "Skills")
	float GetEffect(FName EffectId) const;

	/**
	 * Convenience for the common "scale a cost down" case: a multiplier in (0, 1] that never
	 * reaches zero, so no stack of skills makes a drain or cost free.
	 */
	UFUNCTION(BlueprintPure, Category = "Skills")
	float GetCostMultiplier(FName EffectId, float MaxReduction = 0.6f) const;

	// --- Activation -------------------------------------------------------------------------

	/**
	 * Triggers an equipped active. Fails when unequipped, still cooling down, or out of charges.
	 *
	 * Safe to call from the owning client: it starts the window locally so the bar responds without
	 * waiting on a round trip, and asks the server to do the same. The server's copy is what the
	 * hazard maths reads, so a client cannot grant itself an effect by lying here -- the server
	 * re-runs the identical check.
	 */
	UFUNCTION(BlueprintCallable, Category = "Skills|Activation")
	bool ActivateSkill(const FString& SkillID);

	/** Triggers whatever occupies a payload slot, 0-based. What the ability-bar keys call. */
	UFUNCTION(BlueprintCallable, Category = "Skills|Activation")
	bool ActivateSkillSlot(int32 SlotIndex);

	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	bool CanActivateSkill(const FString& SkillID) const;

	/** True while the skill's effect window is open. */
	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	bool IsSkillActive(const FString& SkillID) const;

	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	float GetRemainingDuration(const FString& SkillID) const;

	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	float GetRemainingCooldown(const FString& SkillID) const;

	/** Triggers left this run. Returns -1 for skills limited only by cooldown. */
	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	int32 GetChargesRemaining(const FString& SkillID) const;

	/** SkillID in a payload slot, or empty when the slot is unfilled. */
	UFUNCTION(BlueprintPure, Category = "Skills|Activation")
	FString GetSkillInSlot(int32 SlotIndex) const;

	/** Restores every equipped active to full charges and clears cooldowns. Call when a run starts. */
	UFUNCTION(BlueprintCallable, Category = "Skills|Activation")
	void ResetActivationStateForNewRun();

	// --- Ownership and loadout --------------------------------------------------------------

	UFUNCTION(BlueprintPure, Category = "Skills")
	int32 GetSkillRank(const FString& SkillID) const;

	UFUNCTION(BlueprintPure, Category = "Skills")
	bool HasSkill(const FString& SkillID) const;

	/** Adds a rank locally. Purchase validation and point spending live in RunOutcomeSubsystem. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	void GrantSkillRank(const FString& SkillID);

	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool EquipActiveSkill(const FString& SkillID);

	UFUNCTION(BlueprintCallable, Category = "Skills")
	bool UnequipActiveSkill(const FString& SkillID);

	UFUNCTION(BlueprintPure, Category = "Skills")
	TArray<FString> GetEquippedActiveSkills() const { return OwnedSkills.EquippedActiveSkills; }

	UFUNCTION(BlueprintPure, Category = "Skills")
	int32 GetFreeActiveSlots() const;

	/** Re-reads role, ranks and payload from saved progression. */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	void ReloadFromProgression();

	/**
	 * Supplies the catalogue directly instead of resolving it from the game instance.
	 *
	 * ReloadFromProgression uses this internally; it is public so a caller that already holds the
	 * subsystem -- or one running outside a game instance, such as a test world -- can wire the
	 * component up without a save game standing behind it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Skills")
	void SetSkillTree(UClassSkillTreeSubsystem* InSkillTree);

	UPROPERTY(BlueprintAssignable, Category = "Skills")
	FOnRoleChanged OnRoleChanged;

	UPROPERTY(BlueprintAssignable, Category = "Skills")
	FOnSkillsChanged OnSkillsChanged;

	UPROPERTY(BlueprintAssignable, Category = "Skills|Activation")
	FOnActiveSkillTriggered OnActiveSkillTriggered;

	UPROPERTY(BlueprintAssignable, Category = "Skills|Activation")
	FOnActiveSkillExpired OnActiveSkillExpired;

protected:
	UFUNCTION(Server, Reliable, WithValidation)
	void ServerActivateSkill(const FString& SkillID);

private:
	UPROPERTY()
	class UClassSkillTreeSubsystem* SkillTreeSubsystem;

	/** Replicated to the owner so a client's cooldown readout matches what the server enforces. */
	UPROPERTY(Replicated)
	TArray<FActiveSkillRuntime> ActiveRuntime;

	FActiveSkillRuntime* FindRuntime(const FString& SkillID);
	const FActiveSkillRuntime* FindRuntime(const FString& SkillID) const;

	/** Starts the window and cooldown without re-checking. Callers must gate on CanActivateSkill. */
	void ApplyActivation(const FString& SkillID);

	/**
	 * Drops equipped actives that are no longer legal -- role changed, or the payload outgrew the
	 * slot limit -- so a stale pick cannot keep paying out.
	 */
	void PruneIllegalLoadout();
};
