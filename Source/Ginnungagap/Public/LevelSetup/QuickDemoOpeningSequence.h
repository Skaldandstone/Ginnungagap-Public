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

private:
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

    EQuickDemoOpeningPhase Phase = EQuickDemoOpeningPhase::Idle;
    float PhaseElapsed = 0.0f;
    float ArmElapsed = 0.0f;

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
