#pragma once

#include "CoreMinimal.h"
#include "Bloom/BloomEnemyArchetypes.h"
#include "Mission/MissionTypes.h"
#include "BloomDormantHulk.generated.h"

class UAudioComponent;
class UCameraShakeBase;
class USoundBase;

/**
 * The mechanized host from the production reference, grown into the ship and asleep in it.
 *
 * The trailer beat sheet has the power come back and, somewhere else in the ship, something very
 * large wake up and roar. Until this class nothing in the engine could do that: the Bloom hosts
 * hunt from the first frame, and there was no dormant state, no wake, no roar, no way for a
 * mission event to reach a creature. This is that foundation, built on the implemented
 * ABloomMechanizedEnemy the reference packet names as the runtime authority rather than on new
 * art -- the packet is explicit that the JACK prototype stays until a measured replacement passes.
 *
 * Dormant, it is slumped, dim, rooted, and cannot attack. When its objective completes it rises
 * over WakeRiseSeconds while its infection presentation ramps to Overgrown, roars once (sound,
 * camera shake on every local player, one line on the HUD), and stays where it is: anchored is
 * the default, because a hulk that wakes and immediately walks out of the breach room to find the
 * player is a chase, and the beat is a threat, not a chase. Clear bStayAnchoredAfterWake to let it
 * hunt.
 *
 * Wired to the mission subsystem directly rather than through the demo director, so the director
 * does not need to know a monster exists and any level can place one against any objective.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ABloomDormantHulk : public ABloomMechanizedEnemy
{
    GENERATED_BODY()

public:
    ABloomDormantHulk();

    virtual void Tick(float DeltaTime) override;
    virtual void PossessedBy(AController* NewController) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    /** Completing this objective wakes it. None leaves it asleep until Wake() is called. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk")
    FName WakeObjectiveId = TEXT("QD_RestorePower");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk")
    bool bStayAnchoredAfterWake = true;

    /** Slump to standing. Also the infection ramp from DormantInfectionProgress to full. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk", meta = (ClampMin = "0.1"))
    float WakeRiseSeconds = 1.8f;

    /** After the wake begins. The roar lands mid-rise, when the silhouette is already changing. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk", meta = (ClampMin = "0.0"))
    float RoarDelaySeconds = 0.9f;

    /**
     * Where the infection sits while dormant. 0.45 shows the core growth and the first of the arm
     * growth at a dim glow; waking runs it to 1.0 so the crown reveals as it rises.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float DormantInfectionProgress = 0.45f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk")
    TObjectPtr<USoundBase> RoarSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk")
    TSubclassOf<UCameraShakeBase> RoarCameraShake;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk")
    FText AlertLine;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom|Hulk", meta = (ClampMin = "0.0"))
    float AlertLineSeconds = 7.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Hulk")
    TObjectPtr<UAudioComponent> RoarAudio;

    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "Bloom|Hulk")
    void Wake();

    UFUNCTION(BlueprintPure, Category = "Bloom|Hulk")
    bool IsDormant() const { return !bAwake; }

    UFUNCTION(BlueprintPure, Category = "Bloom|Hulk")
    bool HasRoared() const { return bRoared; }

    /** 0 asleep, 1 fully risen; eased. */
    UFUNCTION(BlueprintPure, Category = "Bloom|Hulk")
    float GetWakeAlpha() const;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void ApplyProgressiveVisualsAndTuning(float Progress) override;
    virtual void ApplyNativeAttackPose(float PoseAlpha) override;

    UPROPERTY(ReplicatedUsing = OnRep_Awake, VisibleAnywhere, BlueprintReadOnly, Category = "Bloom|Hulk")
    bool bAwake = false;

    UFUNCTION()
    void OnRep_Awake();

    UFUNCTION()
    void HandleObjectiveChanged(FName ObjectiveId, EMissionObjectiveState NewState);

    UFUNCTION(NetMulticast, Reliable)
    void MulticastRoar();

private:
    void ApplyAnchoring();

    float WakeElapsed = 0.0f;
    bool bRoared = false;
    /** Set when the objective was already done as the level came up (a restored checkpoint): rise and roar are skipped. */
    bool bWakeSilently = false;
    double BeginPlaySeconds = 0.0;
};
