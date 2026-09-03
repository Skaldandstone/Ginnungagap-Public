#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "Stealth/StealthTypes.h"
#include "PatrollingEnemyController.generated.h"

class AHorrorEnemy;
class AShipSection;

UCLASS()
class GINNUNGAGAP_API APatrollingEnemyController : public AAIController
{
    GENERATED_BODY()

public:
    APatrollingEnemyController();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    UBehaviorTree* BehaviorTree;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    float DetectionRange = 1500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    float LoseInterestTime = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    float PatrolSpeed = 300.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    float ChaseSpeed = 500.0f;

    // Used when driving movement natively (no BehaviorTree assigned) in place of the BT task's own AcceptanceRadius.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    float PatrolAcceptanceRadius = 50.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    TArray<FVector> PatrolPoints;

    UPROPERTY(BlueprintReadOnly, Category = "AI")
    int32 CurrentPatrolIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Section Patrol")
    TArray<AShipSection*> PatrolSections;

    UPROPERTY(BlueprintReadOnly, Category = "AI|Section Patrol")
    int32 CurrentSectionTargetIndex = 0;

    UPROPERTY(BlueprintReadOnly, Category = "AI|Section Patrol")
    TArray<AShipSection*> CurrentPath;

    UPROPERTY(BlueprintReadOnly, Category = "AI|Section Patrol")
    int32 CurrentPathStepIndex = 0;

    UFUNCTION(BlueprintCallable, Category = "AI|Section Patrol")
    bool ComputePathToNextSection();

    UFUNCTION(BlueprintCallable, Category = "AI|Section Patrol")
    AShipSection* GetCurrentPatrolTarget() const;

    UFUNCTION(BlueprintCallable, Category = "AI|Section Patrol")
    void AdvancePatrolStep();

    void InitializePatrolPoints();
    void UpdatePlayerDetection(float DeltaTime);

    /**
     * Scales this listener's hearing range against the perception subsystem's base propagation
     * distance. Larger creatures or Bloom-adapted hosts can hear further without changing the
     * shared noise rules.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.0"))
    float HearingRangeScale = 1.0f;

    /** How long the AI keeps searching a noise location before giving up and resuming patrol. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.0"))
    float InvestigateDurationSeconds = 6.0f;

    /** Movement speed while investigating: deliberately between patrol and chase. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.0"))
    float InvestigateSpeed = 380.0f;

    /**
     * Half-angle of the vision cone in degrees. Previously detection was effectively 360 degrees,
     * so approaching from behind gave the player nothing. 75 gives roughly human forward vision.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "1.0", ClampMax = "180.0"))
    float VisionConeHalfAngleDegrees = 75.0f;

    /**
     * How fast certainty accumulates against a fully-exposed target at point-blank range, in
     * units per second. Detection is gradual rather than instant so darkness, stillness, and
     * breaking line of sight can actually be used to escape a partial sighting.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.01"))
    float DetectionBuildRate = 1.6f;

    /** How fast certainty drains once nothing is visible. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.01"))
    float DetectionDecayRate = 0.5f;

    /** Certainty at or above which a target is considered confirmed and the AI goes Alert. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.05", ClampMax = "1.0"))
    float ConfirmedDetectionThreshold = 1.0f;

    /**
     * Certainty at or above which a partial sighting is enough to investigate. Between this and
     * ConfirmedDetectionThreshold the AI knows something is there without having identified it.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float SuspicionDetectionThreshold = 0.35f;

    /**
     * Perception multiplier at full Bloom maturity (Manifestation). Applied to sight range,
     * hearing range, and how fast certainty builds, so a late-run Bloom host is genuinely harder
     * to evade than an early one. Only ever applied to Bloom-aligned hosts: pirates, rebels, and
     * aliens are not part of the organism and do not inherit its adaptation.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception|Bloom", meta = (ClampMin = "1.0"))
    float MaxBloomPerceptionScale = 1.6f;

    /** Set false to opt a specific Bloom-aligned host out of stage adaptation. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception|Bloom")
    bool bAdaptsWithBloomStage = true;

    /**
     * 1.0 for anything that is not an adapting Bloom host, rising toward MaxBloomPerceptionScale
     * as the Bloom matures. Exposed so the same curve can drive presentation without duplicating
     * the mapping.
     */
    UFUNCTION(BlueprintPure, Category = "AI|Perception|Bloom")
    float GetBloomPerceptionScale() const;

    /**
     * Multiplier applied to perception by the encounter pacing.
     *
     * Kept separate from the Bloom scale rather than folded into it, because the two answer
     * different questions and want to be tuned apart. The Bloom scale is about what this creature
     * has become; the pacing scale is about whether the run needs pressure right now. Multiplying
     * them is intentional -- an advanced Bloom during Pressure should be the worst moment in a run.
     */
    UFUNCTION(BlueprintPure, Category = "AI|Perception|Pacing")
    float GetPacingPerceptionScale() const;

    /**
     * Whether this enemy answers to the encounter pacing at all.
     *
     * On by default and worth being able to switch off: a scripted beat -- something waiting in a
     * specific room for a specific objective -- should not have its senses dulled because the run
     * happens to be in Relief.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI|Perception|Pacing")
    bool bObeysEncounterPacing = true;

    /**
     * Rooted where it stands. Perception and attacks still run; the native movement below does
     * not. For a set piece -- something grown into a wall that wakes and roars and does not come
     * for you, yet -- rather than for a hunter. Cleared, the controller resumes whatever it would
     * have done.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    bool bAnchored = false;

    /** True only for hosts that are part of the Bloom, which gates both adaptation and learning. */
    UFUNCTION(BlueprintPure, Category = "AI|Perception|Bloom")
    bool IsBloomAligned() const;

    /** Current awareness. Read-only for gameplay/UI; drives the movement decision in Tick. */
    UFUNCTION(BlueprintPure, Category = "AI|Perception")
    EEnemyAwareness GetAwareness() const { return Awareness; }

    /**
     * Current certainty about the best visible candidate, 0..1. Intended as the player-facing
     * tell (a rising detection indicator), which is why it is exposed while raw AI internals
     * such as the candidate itself are not.
     */
    UFUNCTION(BlueprintPure, Category = "AI|Perception")
    float GetDetectionProgress() const { return DetectionProgress; }

    /** Where this AI currently believes something happened. Only meaningful while Suspicious. */
    UFUNCTION(BlueprintPure, Category = "AI|Perception")
    FVector GetInvestigationLocation() const { return InvestigationLocation; }

protected:
    /** Polls the noise subsystem and promotes to Suspicious when something is audible. */
    void UpdateHearing(float DeltaTime);

    UPROPERTY()
    AHorrorEnemy* OwnerEnemy;

    UPROPERTY()
    TObjectPtr<AActor> DetectedTarget;

    float TimeSinceLostPlayer = 0.0f;

    /** Rising/falling certainty about the current best visible candidate. */
    float DetectionProgress = 0.0f;

    /**
     * Best candidate this frame before the certainty threshold is met. Distinct from
     * DetectedTarget, which only becomes set once detection is actually confirmed.
     */
    UPROPERTY()
    TObjectPtr<AActor> PendingVisualTarget;

    UPROPERTY(BlueprintReadOnly, Category = "AI|Perception", meta = (AllowPrivateAccess = "true"))
    EEnemyAwareness Awareness = EEnemyAwareness::Unaware;

    FVector InvestigationLocation = FVector::ZeroVector;

    float InvestigateTimeRemaining = 0.0f;

    /** Set when an investigation move has been issued, so it is not re-issued every tick. */
    bool bInvestigateMoveIssued = false;

    /**
     * Whoever this enemy was last actually chasing, held until it gives up on them.
     *
     * Distinct from DetectedTarget, which is cleared the instant the target is out of sight. The
     * moment worth crediting the player for is not losing sight of them -- that happens constantly
     * behind cover -- but giving up on them entirely, which is LoseInterestTime later and by then
     * DetectedTarget has long since gone. Weak, because the pursued actor can be destroyed mid-chase
     * and a raw pointer would outlive it.
     */
    TWeakObjectPtr<AActor> PursuedTarget;

private:
    void OnPossess(APawn* InPawn) override;

    // Tracks whether a native (BT-less) patrol move is currently underway, so Tick() knows to
    // advance to the next target only once the previous one has actually been reached.
    bool bPatrolMoveInProgress = false;
};
