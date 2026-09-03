#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Stealth/StealthTypes.h"
#include "Templates/PimplPtr.h"
#include "PlayerNoiseEmitterComponent.generated.h"

namespace Audio { class FAudioCaptureSynth; }

/**
 * Turns what the player is physically doing into noise the AI can hear, and optionally lets the
 * player's real microphone do the same.
 *
 * Movement noise is derived on the server from replicated movement state, so it cannot be
 * suppressed by a modified client. Microphone loudness necessarily originates on the owning
 * client, so it is clamped and rate-limited server-side and treated as one input among several
 * rather than as trusted data.
 *
 * MICROPHONE PRIVACY CONTRACT -- this component is built so that opting in cannot leak audio:
 *   - Disabled by default. Nothing opens the device until SetMicrophoneNoiseEnabled(true).
 *   - Capture runs only on the locally controlled pawn, never for remote players.
 *   - Captured samples are reduced to a single RMS number in the same call that reads them and
 *     the buffer is discarded immediately. Audio is never written to disk, never replicated,
 *     never routed to the audio engine, and never held between frames.
 *   - Only the derived 0..1 loudness scalar leaves the machine. Speech content cannot be
 *     reconstructed from it.
 * Any change that stores, forwards, or plays back the captured buffer breaks this contract.
 *
 * The movement-noise audio below does NOT breach it. It plays a designer-authored sound at a
 * volume derived from the same 0..1 loudness scalar the AI reads. No captured sample is ever
 * routed to the audio engine, and nothing the microphone hears is ever played back -- the
 * microphone only contributes a number, and that number only moves a volume slider.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPlayerNoiseEmitterComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPlayerNoiseEmitterComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    /**
     * Opt in or out of microphone-driven noise. Opening the device is deferred to the next tick
     * on the owning client; disabling closes it immediately. Safe to call repeatedly.
     */
    UFUNCTION(BlueprintCallable, Category = "Stealth|Microphone")
    void SetMicrophoneNoiseEnabled(bool bEnabled);

    UFUNCTION(BlueprintPure, Category = "Stealth|Microphone")
    bool IsMicrophoneNoiseEnabled() const { return bMicrophoneNoiseEnabled; }

    /** True once a capture device is actually open and running, not merely requested. */
    UFUNCTION(BlueprintPure, Category = "Stealth|Microphone")
    bool IsMicrophoneCaptureActive() const { return bMicrophoneCaptureActive; }

    /**
     * Most recent noise this player produced, 0..1, across every source. Intended for the
     * player-facing tell (a HUD noise meter) so stealth is legible without exposing AI state.
     */
    UFUNCTION(BlueprintPure, Category = "Stealth")
    float GetCurrentNoiseLevel() const { return CurrentNoiseLevel; }

    /** Report a one-off noise such as a dropped object or a tool. Authority only. */
    UFUNCTION(BlueprintCallable, Category = "Stealth")
    void ReportInstantNoise(float Loudness, ENoiseCategory Category);

    // --- Player-facing tell -------------------------------------------------------------------
    // Without this the stealth loop is one-sided: the AI knows exactly how loud the player is and
    // the player cannot hear themselves, so there is nothing to learn from. Volume is driven by
    // CurrentNoiseLevel rather than recomputed, so what the player hears is by construction what
    // the enemy hears -- a second derivation would drift the moment either side was tuned.

    /** Loop for ordinary movement. Unassigned by default; volume tracks the live noise level. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Audio")
    TObjectPtr<class USoundBase> MovementNoiseLoop;

    /**
     * Loop used while magnetic boots are engaged.
     *
     * A separate asset rather than the same one played louder: the boots are the central traversal
     * trade -- safe footing for a much larger noise signature -- and that needs to read as a
     * different sound, not merely more of the same one.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Audio")
    TObjectPtr<class USoundBase> MagneticBootNoiseLoop;

    /** Scales the tell without touching the loudness the AI hears. Purely a mix control. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Audio", meta = (ClampMin = "0.0"))
    float NoiseAudioVolumeScale = 1.0f;

    /** Noise below this is not worth hearing, and looping a near-silent asset only adds hiss. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Audio", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MinAudibleNoise = 0.05f;

    /**
     * Seconds the tell takes to follow a change in noise.
     *
     * Some smoothing, but little: the point is to feel the consequence of moving, so a slow fade
     * would disconnect the sound from the action that caused it.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Audio", meta = (ClampMin = "0.0"))
    float NoiseAudioSmoothing = 0.12f;

    /** Speed at or below which movement is effectively silent. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "0.0"))
    float SilentSpeedThreshold = 60.0f;

    /** Speed at which movement noise reaches MaxMovementLoudness. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "1.0"))
    float LoudSpeedThreshold = 600.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MaxMovementLoudness = 0.75f;

    /**
     * Magnetic boots clamp audibly to the hull each step. Multiplies movement noise while engaged,
     * making the safe traversal option the loud one.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Movement", meta = (ClampMin = "1.0"))
    float MagneticBootNoiseMultiplier = 1.35f;

    /** Microphone RMS at or below this is treated as room tone and ignored. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Microphone", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MicrophoneNoiseFloor = 0.02f;

    /** Microphone RMS at or above this maps to MaxMicrophoneLoudness. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Microphone", meta = (ClampMin = "0.01", ClampMax = "1.0"))
    float MicrophoneLoudRms = 0.25f;

    /**
     * Ceiling on microphone-driven noise. Deliberately below 1.0: shouting should be a real
     * liability, but never more informative to the AI than firing a weapon.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Microphone", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MaxMicrophoneLoudness = 0.7f;

    /** How often the owning client sends its microphone loudness to the server. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Microphone", meta = (ClampMin = "0.02"))
    float MicrophoneReportInterval = 0.15f;

protected:
    /** Owning client -> server. Unreliable: a dropped update self-corrects on the next interval. */
    UFUNCTION(Server, Unreliable)
    void ServerReportVoiceLoudness(float Loudness);

private:
    /** Derives movement loudness from the owner's current speed and traversal mode. */
    float ComputeMovementLoudness() const;

    /**
     * Reads whatever the capture device has buffered, reduces it to one RMS value, and drops the
     * samples before returning. Returns 0 when capture is inactive or nothing was buffered.
     */
    float ConsumeMicrophoneRms();

    void StartMicrophoneCapture();
    void StopMicrophoneCapture();

    /** True only for the pawn this machine's player actually controls. */
    bool IsLocallyControlledOwner() const;

    /**
     * Keeps the local player's own noise audible to them.
     *
     * Local player only. Another crew member's movement should reach you as world audio from where
     * they actually are, not as a copy of your own tell layered on top.
     */
    void UpdateNoiseAudio(float DeltaTime);

    UPROPERTY(Transient)
    TObjectPtr<class UAudioComponent> NoiseAudio;

    /** Which loop is currently mounted, so the boot swap only restarts the sound when it changes. */
    UPROPERTY(Transient)
    TObjectPtr<class USoundBase> ActiveNoiseLoop;

    float SmoothedNoiseAudioLevel = 0.0f;

    UPROPERTY(EditAnywhere, Category = "Stealth|Microphone")
    bool bMicrophoneNoiseEnabled = false;

    bool bMicrophoneCaptureActive = false;

    UPROPERTY(Replicated)
    float CurrentNoiseLevel = 0.0f;

    /** Latest client-reported microphone loudness, already clamped on arrival. */
    float ReportedVoiceLoudness = 0.0f;

    float TimeSinceMicrophoneReport = 0.0f;

    /**
     * Owned entirely by this component and never handed out. TPimplPtr rather than TUniquePtr:
     * the audio capture headers stay out of this public header, and TPimplPtr captures its
     * deleter where the type is complete, so UHT's generated constructors in the .gen.cpp do not
     * need to see Audio::FAudioCaptureSynth to destroy it.
     */
    TPimplPtr<Audio::FAudioCaptureSynth> CaptureSynth;

    /** Scratch buffer for ConsumeMicrophoneRms. Cleared on every use; never retained across frames. */
    TArray<float> CaptureScratch;
};
