#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraShakeBase.h"
#include "GameFramework/Actor.h"
#include "QuickDemoOpeningSequence.generated.h"

class ACameraActor;
class ACoopSurvivalCharacter;
class ACryoPodSystem;
class APlayerController;
class UAudioComponent;
class ULightComponent;
class UPointLightComponent;
class USoundBase;

UENUM(BlueprintType)
enum class EQuickDemoOpeningPhase : uint8
{
    Idle,
    /** Third person on the pod, lid closed, room low. */
    Asleep,
    /** The ship is hit: shake, lights flickering. */
    Strike,
    /** Lights out; the pods' own blue is what is left. */
    Blackout,
    /** The lid opens. */
    Wake,
    /** Out of the pod and on their feet, still third person. */
    ClimbOut,
    /** First person, suit HUD up, controls live. */
    FirstPerson,
    Complete
};

/** One crew member's wake, decided by the server and mirrored to every machine. */
USTRUCT()
struct FQuickDemoCrewWake
{
    GENERATED_BODY()

    UPROPERTY()
    TObjectPtr<ACoopSurvivalCharacter> Crew = nullptr;

    UPROPERTY()
    TObjectPtr<ACryoPodSystem> Pod = nullptr;

    /** Server world time the sleeper's timeline started. */
    UPROPERTY()
    float StartServerTime = -1.0f;

    /** Server world time the sleeper released the pod (pressed the release from inside); -1 until they do. */
    UPROPERTY()
    float ReleasedServerTime = -1.0f;

    UPROPERTY()
    FVector PodSideLocation = FVector::ZeroVector;

    UPROPERTY()
    FVector StandLocation = FVector::ZeroVector;

    UPROPERTY()
    FRotator StandRotation = FRotator::ZeroRotator;

    /** Server-side progress through the authoritative beats; not replicated, not needed elsewhere. */
    EQuickDemoOpeningPhase ServerPhase = EQuickDemoOpeningPhase::Idle;
};

/** The ship being hit. Short and violent, heaviest vertical, gone in a second and a half. */
UCLASS()
class GINNUNGAGAP_API UShipStrikeCameraShake : public UCameraShakeBase
{
    GENERATED_BODY()

public:
    UShipStrikeCameraShake(const FObjectInitializer& ObjectInitializer);
};

/**
 * How the demo opens, in the order James gave it: third person on the sleeper in the cryotube;
 * the ship is hit and the room shakes; the lights go, leaving the blue of the tubes; the sleeper
 * wakes and climbs out, still in third person; then first person, suit HUD, and the tool is
 * somewhere in this room.
 *
 * Scripted natively with timers rather than a Level Sequence, for the same reason the rest of
 * the demo is: it runs from a headless-saved map, it is testable by phase, and every beat is a
 * call into the systems the game already has -- the pod's own lid, the character's own cameras,
 * the HUD's own visibility, a camera shake. Nothing here is cinematic-only state.
 *
 * Presentation is for the local player; pod state is authority. Automation waits on
 * IsComplete() and captures on phase changes. Skip() exists for a session that does not want
 * the eight seconds.
 *
 * Co-op: the server admits every crew member as their pawn appears, host and joiners alike,
 * gives each their own pod (the tagged one first, then the nearest free one to where they
 * spawned) and drives the moves that only authority may make: into the pod, the lid, the climb
 * out, the stand. What it decided is replicated per crew member with the server time it began,
 * and each machine plays the camera, lights and HUD beats for its own player against that clock.
 * A player who joins later wakes on their own timeline; the ones already up see them climb out.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AQuickDemoOpeningSequence : public AActor
{
    GENERATED_BODY()

public:
    AQuickDemoOpeningSequence();

    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening")
    bool bEnabled = true;

    /** The pod the player wakes in. Found by this tag, else the nearest pod to where they spawned. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening")
    FName PlayerPodTag = TEXT("QuickDemoPlayerPod");

    /** The room whose lights go out. Found by this tag on a ModularShipRoom. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening")
    FName RoomTag = TEXT("cryo");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "0.0"))
    float AsleepSeconds = 2.8f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "0.0"))
    float StrikeSeconds = 1.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "0.0"))
    float BlackoutSeconds = 1.8f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "0.0"))
    float WakeSeconds = 1.4f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "0.0"))
    float ClimbOutSeconds = 2.4f;

    /**
     * The pod does not open itself: the sleeper releases it, from inside, with the interact key.
     * If nobody does for this long the ship lets them out anyway, so a player who walked away
     * from the keyboard is not left in a tube for the night.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Timing", meta = (ClampMin = "1.0"))
    float WakeAutoReleaseSeconds = 90.0f;

    /** What the room keeps once the lights have gone: a fraction of what they were. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Light", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float BlackoutRoomLightFraction = 0.10f;

    /** The blue the tubes give off. Cold, low, from inside the glass. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Light")
    FLinearColor CryoGlowColor = FLinearColor(0.20f, 0.48f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening|Light", meta = (ClampMin = "0.0"))
    float CryoGlowIntensity = 380.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening")
    TSubclassOf<UCameraShakeBase> StrikeCameraShake;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Opening")
    TObjectPtr<USoundBase> StrikeSound;

    UFUNCTION(BlueprintPure, Category = "Opening")
    EQuickDemoOpeningPhase GetPhase() const { return Phase; }

    UFUNCTION(BlueprintPure, Category = "Opening")
    bool IsComplete() const { return Phase == EQuickDemoOpeningPhase::Complete; }

    UFUNCTION(BlueprintCallable, Category = "Opening")
    void Skip();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    /** Server: put any crew member who has just arrived into a pod of their own. */
    void ServerAdmitCrew();
    /** Server: the lid, the climb out and the stand for every admitted crew member. */
    void ServerAdvanceCrew();
    /** The wake belonging to this machine's own player, or INDEX_NONE until it has replicated. */
    int32 FindLocalWake() const;
    float ServerNow() const;
    /** Seconds into the local player's timeline that a phase begins. */
    float PhaseStartSeconds(EQuickDemoOpeningPhase Of) const;
    EQuickDemoOpeningPhase PhaseAt(float Elapsed) const;
    /** The phase for a crew member who released the pod this many seconds ago. */
    EQuickDemoOpeningPhase PhaseSinceRelease(float SinceRelease) const;

    void TryArm();
    void EnterPhase(EQuickDemoOpeningPhase NewPhase);
    void SetRoomLights(float Fraction);
    void SetPodGlow(float Fraction);
    void Finish();

    struct FRoomLight
    {
        TWeakObjectPtr<ULightComponent> Light;
        float Intensity = 0.0f;
    };

    UPROPERTY(Replicated)
    TArray<FQuickDemoCrewWake> CrewWakes;

    /** Pods this machine has already turned to face their sleeper's stand. */
    TSet<TWeakObjectPtr<ACryoPodSystem>> TurnedPods;

    EQuickDemoOpeningPhase Phase = EQuickDemoOpeningPhase::Idle;
    float PhaseElapsed = 0.0f;
    float ArmElapsed = 0.0f;
    float LocalStartServerTime = -1.0f;
    /** Skip() was called: crew admitted from now on are simply up, and nobody is put in a pod. */
    bool bSkipped = false;

    TWeakObjectPtr<APlayerController> Player;
    TWeakObjectPtr<ACoopSurvivalCharacter> Crew;
    TWeakObjectPtr<ACryoPodSystem> Pod;
    TWeakObjectPtr<ACameraActor> ShotCamera;
    TArray<FRoomLight> RoomLights;
    TArray<TWeakObjectPtr<UPointLightComponent>> PodGlows;
    FVector PodSideLocation = FVector::ZeroVector;
    FVector StandLocation = FVector::ZeroVector;
    FRotator StandRotation = FRotator::ZeroRotator;
    bool bHudWasVisible = true;
};
