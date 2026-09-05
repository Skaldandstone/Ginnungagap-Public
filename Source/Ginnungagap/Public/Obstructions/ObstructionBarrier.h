#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Activities/PlayerActivitySource.h"
#include "Interfaces/Interactable.h"
#include "Obstructions/ObstructionTypes.h"
#include "ObstructionBarrier.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnObstructionCleared,
	AObstructionBarrier*, Barrier, EObstructionVerb, Verb);

/**
 * Something in the way, with more than one way past it.
 *
 * The demo ship has thirty-two door cranks and no obstructions -- every blockage in it is a thing
 * you interact with until it opens. This is the other kind: a collapse, a welded panel, a jammed
 * hatch, where the interesting question is not whether you get through but what it costs you.
 *
 * ## Why the verbs are asymmetric
 *
 * Breach is fast, loud, and damages ship systems standing near it. Cut is slower, spends the
 * condition of the gear you will need later, and can burn you if that gear is already poor. Squeeze
 * costs no equipment at all and can leave you most of the way through and stuck, which raises acute
 * stress. Three costs in three different currencies, so the choice depends on what the player is
 * short of rather than on which number is smallest.
 *
 * ## bBypassable
 *
 * Marks whether there is another way round. James asked for this explicitly -- "in most cases" the
 * player can redirect, with "some cases where they do have to go through it".
 *
 * It is a flag on the obstruction rather than a fact about the map because nothing can currently
 * check the real answer: every deck is a single corridor with rooms hanging off it (TRO-239), so
 * there is no second route to find. Declaring it here means the levels can be authored with the
 * intent recorded, and a later pass can assert the flag against the actual graph. It affects no
 * behaviour yet, which is stated rather than hidden.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AObstructionBarrier : public AActor,
	public IInteractable, public IPlayerActivitySource
{
	GENERATED_BODY()

public:
	AObstructionBarrier();

	/** Blocks movement until cleared. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Obstruction")
	TObjectPtr<UBoxComponent> Blocker;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Obstruction")
	TObjectPtr<UStaticMeshComponent> VisualMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction")
	FText DisplayName;

	/**
	 * What this obstruction permits, and at what cost. A verb absent from the map is not allowed.
	 *
	 * Left empty by default rather than filled with all three. An obstruction that permits
	 * everything is not a decision, and a default that quietly permits everything would make every
	 * unconfigured blockage in the ship a shrug.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction")
	TMap<EObstructionVerb, FObstructionVerbOption> Options;

	/** Whether there is another way round. See the class comment: recorded, not yet enforced. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction")
	bool bBypassable = true;

	/**
	 * Where the visual ends up once it has been cut: a barrier does not vanish, it is dropped
	 * beside the way through. Relative to its authored pose. A squeeze leaves it exactly as it was.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction|Cleared")
	FVector CutVisualOffset = FVector(0.0f, 70.0f, -105.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Obstruction|Cleared")
	FRotator CutVisualRotation = FRotator(0.0f, 0.0f, 62.0f);

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Obstruction")
	bool bCleared = false;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Obstruction")
	EObstructionVerb ClearedWith = EObstructionVerb::Breach;

	UPROPERTY(BlueprintAssignable, Category="Obstruction")
	FOnObstructionCleared OnObstructionCleared;

	/** Whether the pawn could pass this way now, and if not, why not. */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	EObstructionRefusal GetRefusal(EObstructionVerb Verb, const APawn* Player) const;

	UFUNCTION(BlueprintPure, Category="Obstruction")
	bool CanResolveWith(EObstructionVerb Verb, const APawn* Player) const;

	/** Every verb this pawn could use right now. Empty is a legitimate answer. */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	TArray<EObstructionVerb> GetAvailableVerbs(const APawn* Player) const;

	/**
	 * Passes the obstruction, applies what it costs, and clears the blocker.
	 *
	 * Returns false and does nothing if the verb is refused, so a caller cannot half-apply a
	 * resolution the obstruction never permitted.
	 */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	bool ResolveWith(EObstructionVerb Verb, APawn* Player);

	/** How much of a nearby system this verb would ruin at that distance, 0..1. */
	UFUNCTION(BlueprintPure, Category="Obstruction")
	float GetCollateralAtDistance(EObstructionVerb Verb, float Distance) const;

	/** Convenience for authoring: the three shapes these come in. */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	void ApplyAuthoringPreset(FName PresetName);

	// --- choosing a verb ----------------------------------------------------------------------
	//
	// The barrier holds the choice rather than the player, because it is a property of this
	// obstruction and not of the person standing at it: walk away mid-cut and come back, and you
	// are still cutting. It also means a prompt only has to ask the barrier what it is set to.

	/** The verb the next interaction will attempt. */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Obstruction")
	EObstructionVerb SelectedVerb = EObstructionVerb::Breach;

	/** Chooses a verb. Refuses one this obstruction does not permit, rather than arming a failure. */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	bool SelectVerb(EObstructionVerb Verb, const APawn* Player);

	/**
	 * Moves to the next verb this pawn could actually use.
	 *
	 * What a prompt key binds to. Cycles only through available verbs, so a player pressing it at
	 * a welded bulkhead never lands on "squeeze" and wonders why nothing happened.
	 */
	UFUNCTION(BlueprintCallable, Category="Obstruction")
	EObstructionVerb CycleVerb(const APawn* Player);

	// --- IInteractable ------------------------------------------------------------------------
	virtual void OnInteract_Implementation(APawn* InteractingPawn) override;
	virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const override;

	/** "Squeeze through", "Cut through", "Set charges" -- what a verb is called to a player. */
	UFUNCTION(BlueprintPure, Category="Obstruction")
	static FText GetVerbName(EObstructionVerb Verb);

	// --- IPlayerActivitySource ----------------------------------------------------------------
	//
	// Routed through the activity system rather than resolved on a keypress, so the three verbs
	// are things the player *does* for a length of time in a corridor that is not safe. Cutting in
	// particular becomes a real welding activity, which means it can be failed -- and a failed weld
	// is already wired to spend gear condition and roll for a burn.
	virtual FPlayerActivityDefinition GetActivityDefinition_Implementation(APawn* Player) const override;
	virtual bool CanStartActivity_Implementation(APawn* Player) const override;
	virtual void OnActivityCompleted_Implementation(APawn* Player) override;

protected:
	/** Damages ship systems standing near a breach. */
	void ApplyCollateral(const FObstructionVerbOption& Option);

	/** Tells the noise subsystem, so this is a thing that can be heard rather than a private event. */
	void ReportNoise(const FObstructionVerbOption& Option, EObstructionVerb Verb, AActor* NoiseSource);

	/** Spends equipment condition and rolls for a welding burn. */
	void ApplyCutCost(const FObstructionVerbOption& Option, APawn* Player);

	/** Rolls for the near miss, and raises stress if it happens. */
	void ApplySqueezeCost(const FObstructionVerbOption& Option, APawn* Player);
};
