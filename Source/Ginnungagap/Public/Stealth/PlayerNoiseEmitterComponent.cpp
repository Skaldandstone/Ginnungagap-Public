#include "Stealth/PlayerNoiseEmitterComponent.h"

#include "AudioCaptureCore.h"
#include "Components/AudioComponent.h"
#include "Sound/SoundBase.h"
#include "CoopSurvivalCharacter.h"
#include "Progression/ClassSkillComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"
#include "Stealth/NoisePerceptionSubsystem.h"

UPlayerNoiseEmitterComponent::UPlayerNoiseEmitterComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(true);
}


void UPlayerNoiseEmitterComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UPlayerNoiseEmitterComponent, CurrentNoiseLevel);
}

void UPlayerNoiseEmitterComponent::BeginPlay()
{
    Super::BeginPlay();

    if (bMicrophoneNoiseEnabled && IsLocallyControlledOwner())
    {
        StartMicrophoneCapture();
    }
}

void UPlayerNoiseEmitterComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // Release the capture device promptly on travel, disconnect, or PIE stop rather than waiting
    // for garbage collection to run the destructor.
    StopMicrophoneCapture();
    Super::EndPlay(EndPlayReason);
}

void UPlayerNoiseEmitterComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }

    // Microphone runs on the owning client only; the server never touches a capture device.
    if (IsLocallyControlledOwner())
    {
        if (bMicrophoneNoiseEnabled && !bMicrophoneCaptureActive)
        {
            StartMicrophoneCapture();
        }
        else if (!bMicrophoneNoiseEnabled && bMicrophoneCaptureActive)
        {
            StopMicrophoneCapture();
        }

        if (bMicrophoneCaptureActive)
        {
            const float Rms = ConsumeMicrophoneRms();
            const float Normalized = FMath::GetMappedRangeValueClamped(
                FVector2D(MicrophoneNoiseFloor, MicrophoneLoudRms),
                FVector2D(0.0f, MaxMicrophoneLoudness),
                Rms);

            TimeSinceMicrophoneReport += DeltaTime;
            if (TimeSinceMicrophoneReport >= MicrophoneReportInterval)
            {
                TimeSinceMicrophoneReport = 0.0f;
                if (Owner->HasAuthority())
                {
                    ReportedVoiceLoudness = Normalized;
                }
                else
                {
                    ServerReportVoiceLoudness(Normalized);
                }
            }
        }
    }

    // The player's own tell, updated before the authority guard below. A remote client never
    // reaches the authoritative section, so driving the audio from there would leave everyone
    // except the listen-server host unable to hear themselves -- which is the exact one-sidedness
    // this is meant to fix. It reads the replicated CurrentNoiseLevel, so a client is still
    // hearing the server's figure rather than a local guess.
    UpdateNoiseAudio(DeltaTime);

    // Everything below is the authoritative noise decision. Clients derive nothing.
    if (!Owner->HasAuthority())
    {
        return;
    }

    if (const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Owner))
    {
        if (Character->bIsDead)
        {
            CurrentNoiseLevel = 0.0f;
            return;
        }
    }

    const float MovementLoudness = ComputeMovementLoudness();

    // Voice decays on the server between client updates so a client that stops sending (crash,
    // packet loss, or a deliberately silenced client) fades out instead of staying loud forever.
    ReportedVoiceLoudness = FMath::FInterpConstantTo(ReportedVoiceLoudness, 0.0f, DeltaTime, 1.0f);

    UWorld* World = GetWorld();
    UNoisePerceptionSubsystem* Perception = World ? World->GetSubsystem<UNoisePerceptionSubsystem>() : nullptr;
    if (!Perception)
    {
        return;
    }

    const FVector Location = Owner->GetActorLocation();
    if (MovementLoudness > 0.0f)
    {
        Perception->ReportNoise(Location, MovementLoudness, ENoiseCategory::Movement, Owner);
    }
    if (ReportedVoiceLoudness > 0.0f)
    {
        Perception->ReportNoise(Location, ReportedVoiceLoudness, ENoiseCategory::Voice, Owner);
    }

    // The player-facing meter shows the loudest thing they are currently doing, which is what
    // actually determines whether they are heard.
    CurrentNoiseLevel = FMath::Max(MovementLoudness, ReportedVoiceLoudness);
}

void UPlayerNoiseEmitterComponent::UpdateNoiseAudio(float DeltaTime)
{
    // Only the player whose pawn this is. Another crew member's noise should arrive as world audio
    // from where they are standing, not as a duplicate of this player's own tell.
    if (!IsLocallyControlledOwner())
    {
        return;
    }

    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }

    // CurrentNoiseLevel is replicated, so the client is reading the server's figure rather than a
    // local guess. That is the whole point: the tell has to agree with what the AI acted on, or it
    // teaches the player something untrue.
    const float Target = CurrentNoiseLevel;
    SmoothedNoiseAudioLevel = NoiseAudioSmoothing > 0.0f
        ? FMath::FInterpTo(SmoothedNoiseAudioLevel, Target, DeltaTime, 1.0f / NoiseAudioSmoothing)
        : Target;

    const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Owner);
    const bool bBoots = Character && Character->AreMagneticBootsEnabled();
    USoundBase* DesiredLoop = bBoots && MagneticBootNoiseLoop ? MagneticBootNoiseLoop : MovementNoiseLoop;

    // Nothing assigned yet is the normal state until audio is sourced, and it must stay silent
    // rather than warn every frame.
    if (!DesiredLoop || SmoothedNoiseAudioLevel < MinAudibleNoise)
    {
        if (NoiseAudio && NoiseAudio->IsPlaying())
        {
            NoiseAudio->Stop();
            ActiveNoiseLoop = nullptr;
        }
        return;
    }

    if (!NoiseAudio)
    {
        NoiseAudio = NewObject<UAudioComponent>(Owner);
        NoiseAudio->bAutoActivate = false;
        // Attached rather than fire-and-forget so it follows the player and can be retuned live.
        NoiseAudio->SetupAttachment(Owner->GetRootComponent());
        NoiseAudio->RegisterComponent();
    }

    // Swap only when the loop actually changes; reassigning every frame would restart the sound
    // continuously and produce a stutter rather than a tone.
    if (ActiveNoiseLoop != DesiredLoop)
    {
        NoiseAudio->SetSound(DesiredLoop);
        ActiveNoiseLoop = DesiredLoop;
        NoiseAudio->Play();
    }
    else if (!NoiseAudio->IsPlaying())
    {
        NoiseAudio->Play();
    }

    NoiseAudio->SetVolumeMultiplier(
        FMath::Clamp(SmoothedNoiseAudioLevel, 0.0f, 1.0f) * FMath::Max(0.0f, NoiseAudioVolumeScale));
}

void UPlayerNoiseEmitterComponent::ServerReportVoiceLoudness_Implementation(float Loudness)
{
    // Never trust the reported value: a modified client could send anything. Clamping to the
    // designed ceiling means the worst a client can do is make itself louder than it really is.
    ReportedVoiceLoudness = FMath::Clamp(Loudness, 0.0f, MaxMicrophoneLoudness);
}

void UPlayerNoiseEmitterComponent::ReportInstantNoise(float Loudness, ENoiseCategory Category)
{
    AActor* Owner = GetOwner();
    if (!Owner || !Owner->HasAuthority())
    {
        return;
    }

    if (UWorld* World = GetWorld())
    {
        if (UNoisePerceptionSubsystem* Perception = World->GetSubsystem<UNoisePerceptionSubsystem>())
        {
            Perception->ReportNoise(Owner->GetActorLocation(), FMath::Clamp(Loudness, 0.0f, 1.0f), Category, Owner);
        }
    }
}

float UPlayerNoiseEmitterComponent::ComputeMovementLoudness() const
{
    const AActor* Owner = GetOwner();
    if (!Owner)
    {
        return 0.0f;
    }

    const float Speed = Owner->GetVelocity().Size();
    if (Speed <= SilentSpeedThreshold)
    {
        return 0.0f;
    }

    float Loudness = FMath::GetMappedRangeValueClamped(
        FVector2D(SilentSpeedThreshold, LoudSpeedThreshold),
        FVector2D(0.0f, MaxMovementLoudness),
        Speed);

    if (const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(Owner))
    {
        if (Character->AreMagneticBootsEnabled())
        {
            Loudness *= MagneticBootNoiseMultiplier;
        }

        // Damping applies after the boot penalty so quiet soles offset loud boots rather than
        // being multiplied away by them.
        if (const UClassSkillComponent* Skills = Character->GetSkillComponent())
        {
            Loudness *= Skills->GetCostMultiplier(SkillEffects::MovementNoise);
        }
    }

    return FMath::Clamp(Loudness, 0.0f, 1.0f);
}

void UPlayerNoiseEmitterComponent::StartMicrophoneCapture()
{
    if (bMicrophoneCaptureActive || !IsLocallyControlledOwner())
    {
        return;
    }

    if (!CaptureSynth.IsValid())
    {
        CaptureSynth = MakePimpl<Audio::FAudioCaptureSynth>();
    }

    // A missing or busy microphone is an ordinary situation, not an error: the player simply
    // produces no voice noise and the rest of the stealth system is unaffected.
    if (!CaptureSynth->OpenDefaultStream())
    {
        UE_LOG(LogTemp, Log, TEXT("PlayerNoiseEmitter: no usable capture device; microphone noise stays off."));
        CaptureSynth.Reset();
        return;
    }

    if (!CaptureSynth->StartCapturing())
    {
        UE_LOG(LogTemp, Log, TEXT("PlayerNoiseEmitter: capture device would not start; microphone noise stays off."));
        CaptureSynth.Reset();
        return;
    }

    bMicrophoneCaptureActive = true;
}

void UPlayerNoiseEmitterComponent::StopMicrophoneCapture()
{
    if (CaptureSynth.IsValid())
    {
        if (CaptureSynth->IsCapturing())
        {
            CaptureSynth->StopCapturing();
        }
        CaptureSynth.Reset();
    }

    CaptureScratch.Reset();
    bMicrophoneCaptureActive = false;
    ReportedVoiceLoudness = 0.0f;
}

float UPlayerNoiseEmitterComponent::ConsumeMicrophoneRms()
{
    if (!CaptureSynth.IsValid() || !CaptureSynth->IsCapturing())
    {
        return 0.0f;
    }

    CaptureScratch.Reset();
    if (!CaptureSynth->GetAudioData(CaptureScratch) || CaptureScratch.Num() == 0)
    {
        return 0.0f;
    }

    double SumSquares = 0.0;
    for (const float Sample : CaptureScratch)
    {
        SumSquares += static_cast<double>(Sample) * static_cast<double>(Sample);
    }
    const float Rms = static_cast<float>(FMath::Sqrt(SumSquares / static_cast<double>(CaptureScratch.Num())));

    // Privacy contract: the samples are gone before this function returns. Only Rms survives.
    CaptureScratch.Reset();

    return Rms;
}

void UPlayerNoiseEmitterComponent::SetMicrophoneNoiseEnabled(bool bEnabled)
{
    if (bMicrophoneNoiseEnabled == bEnabled)
    {
        return;
    }

    bMicrophoneNoiseEnabled = bEnabled;

    if (!bEnabled)
    {
        // Close the device immediately on opt-out rather than waiting for the next tick.
        StopMicrophoneCapture();
    }
}

bool UPlayerNoiseEmitterComponent::IsLocallyControlledOwner() const
{
    const APawn* OwningPawn = Cast<APawn>(GetOwner());
    return OwningPawn && OwningPawn->IsLocallyControlled();
}
