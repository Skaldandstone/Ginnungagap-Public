#include "LevelSetup/QuickDemoOpeningSequence.h"
#include "Net/UnrealNetwork.h"
#include "GameFramework/CharacterMovementComponent.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Engine/World.h"
#include "GameFramework/GameStateBase.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Player/SurvivalPlayerController.h"
#include "Shakes/PerlinNoiseCameraShakePattern.h"
#include "Ship/CryoPodSystem.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/ModularShipRoom.h"
#include "Sound/SoundBase.h"
#include "UI/SurvivalHUDWidget.h"
#include "Weapons/WeaponMountComponent.h"
#include "Weapons/ShipboardWeapon.h"

UShipStrikeCameraShake::UShipStrikeCameraShake(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    bSingleInstance = true;
    UPerlinNoiseCameraShakePattern* Pattern =
        ObjectInitializer.CreateDefaultSubobject<UPerlinNoiseCameraShakePattern>(this, TEXT("StrikePattern"));
    Pattern->Duration = 1.5f;
    Pattern->BlendInTime = 0.03f;
    Pattern->BlendOutTime = 1.1f;
    Pattern->X.Amplitude = 6.0f;  Pattern->X.Frequency = 14.0f;
    Pattern->Y.Amplitude = 5.0f;  Pattern->Y.Frequency = 12.0f;
    Pattern->Z.Amplitude = 9.0f;  Pattern->Z.Frequency = 16.0f;
    Pattern->Pitch.Amplitude = 2.6f; Pattern->Pitch.Frequency = 11.0f;
    Pattern->Yaw.Amplitude = 1.4f;   Pattern->Yaw.Frequency = 9.0f;
    Pattern->Roll.Amplitude = 2.0f;  Pattern->Roll.Frequency = 8.0f;
    SetRootShakePattern(Pattern);
}

AQuickDemoOpeningSequence::AQuickDemoOpeningSequence()
{
    PrimaryActorTick.bCanEverTick = true;
    // The wakes it hands out are everyone's business, wherever they stand.
    bReplicates = true;
    bAlwaysRelevant = true;
    StrikeCameraShake = UShipStrikeCameraShake::StaticClass();
    StrikeSound = LoadObject<USoundBase>(nullptr,
        TEXT("/Game/Assets/Ships/Production/Audio/S_Ship_HullStrike.S_Ship_HullStrike"));
}

void AQuickDemoOpeningSequence::BeginPlay()
{
    Super::BeginPlay();
    if (!bEnabled)
    {
        Phase = EQuickDemoOpeningPhase::Complete;
        SetActorTickEnabled(false);
    }
}

void AQuickDemoOpeningSequence::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (ShotCamera.IsValid())
    {
        ShotCamera->Destroy();
    }
    Super::EndPlay(EndPlayReason);
}

void AQuickDemoOpeningSequence::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AQuickDemoOpeningSequence, CrewWakes);
}

float AQuickDemoOpeningSequence::ServerNow() const
{
    const UWorld* World = GetWorld();
    if (const AGameStateBase* GameState = World ? World->GetGameState() : nullptr)
    {
        return GameState->GetServerWorldTimeSeconds();
    }
    return World ? World->GetTimeSeconds() : 0.0f;
}

float AQuickDemoOpeningSequence::PhaseStartSeconds(EQuickDemoOpeningPhase Of) const
{
    float Start = 0.0f;
    if (Of == EQuickDemoOpeningPhase::Asleep) return Start;
    Start += AsleepSeconds;
    if (Of == EQuickDemoOpeningPhase::Strike) return Start;
    Start += StrikeSeconds;
    if (Of == EQuickDemoOpeningPhase::Blackout) return Start;
    Start += BlackoutSeconds;
    if (Of == EQuickDemoOpeningPhase::Wake) return Start;
    Start += WakeSeconds;
    if (Of == EQuickDemoOpeningPhase::ClimbOut) return Start;
    Start += ClimbOutSeconds;
    if (Of == EQuickDemoOpeningPhase::FirstPerson) return Start;
    return Start + 0.25f;   // Complete
}

EQuickDemoOpeningPhase AQuickDemoOpeningSequence::PhaseSinceRelease(float SinceRelease) const
{
    if (SinceRelease < 0.0f) return EQuickDemoOpeningPhase::Wake;
    if (SinceRelease < ClimbOutSeconds) return EQuickDemoOpeningPhase::ClimbOut;
    if (SinceRelease < ClimbOutSeconds + 0.25f) return EQuickDemoOpeningPhase::FirstPerson;
    return EQuickDemoOpeningPhase::Complete;
}

EQuickDemoOpeningPhase AQuickDemoOpeningSequence::PhaseAt(float Elapsed) const
{
    // The clock runs the ship's part: the strike, the blackout, the tube coming awake. What
    // follows waits on the sleeper releasing the pod (PhaseSinceRelease).
    static const EQuickDemoOpeningPhase Order[] = {
        EQuickDemoOpeningPhase::Asleep, EQuickDemoOpeningPhase::Strike, EQuickDemoOpeningPhase::Blackout,
        EQuickDemoOpeningPhase::Wake };
    EQuickDemoOpeningPhase Result = EQuickDemoOpeningPhase::Asleep;
    for (EQuickDemoOpeningPhase Candidate : Order)
    {
        if (Elapsed >= PhaseStartSeconds(Candidate))
        {
            Result = Candidate;
        }
    }
    return Result;
}

int32 AQuickDemoOpeningSequence::FindLocalWake() const
{
    const APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    const APawn* LocalPawn = PC ? PC->GetPawn() : nullptr;
    if (!LocalPawn)
    {
        return INDEX_NONE;
    }
    return CrewWakes.IndexOfByPredicate([LocalPawn](const FQuickDemoCrewWake& Wake) { return static_cast<const APawn*>(Wake.Crew.Get()) == LocalPawn; });
}

void AQuickDemoOpeningSequence::ServerAdmitCrew()
{
    UWorld* World = GetWorld();
    for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
    {
        APlayerController* PC = It->Get();
        ACoopSurvivalCharacter* Character = PC ? Cast<ACoopSurvivalCharacter>(PC->GetPawn()) : nullptr;
        if (!Character || CrewWakes.ContainsByPredicate([Character](const FQuickDemoCrewWake& Wake) { return Wake.Crew == Character; }))
        {
            continue;
        }

        // Nobody wakes from cryo holding a bolt driver. The mount auto-arms every pawn at
        // BeginPlay; the demo's crew find their tool at the workshop bench, which grants it, so
        // empty their hands here.
        if (UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>())
        {
            // Gone, not dropped: a released tool lay on the deck at the spawn point where the
            // survey walk tripped over it. The bench hands one over later.
            if (AShipboardWeapon* Starter = Mount->ReleaseWeapon(false))
            {
                Starter->Destroy();
            }
        }

        // Their pod: the tagged one while it is still free, otherwise the nearest one to where
        // they spawned that nobody else was given.
        ACryoPodSystem* Chosen = nullptr;
        float BestDistance = TNumericLimits<float>::Max();
        for (TActorIterator<ACryoPodSystem> PodIt(World); PodIt; ++PodIt)
        {
            ACryoPodSystem* Candidate = *PodIt;
            const bool bTaken = Candidate->bIsOccupied
                || CrewWakes.ContainsByPredicate([Candidate](const FQuickDemoCrewWake& Wake) { return Wake.Pod == Candidate; });
            if (bTaken)
            {
                continue;
            }
            if (!PlayerPodTag.IsNone() && Candidate->ActorHasTag(PlayerPodTag))
            {
                Chosen = Candidate;
                break;
            }
            const float Distance = FVector::Dist(Candidate->GetActorLocation(), Character->GetActorLocation());
            if (Distance < BestDistance)
            {
                BestDistance = Distance;
                Chosen = Candidate;
            }
        }

        FQuickDemoCrewWake Wake;
        Wake.Crew = Character;
        Wake.Pod = Chosen;
        Wake.StartServerTime = ServerNow();
        Wake.StandLocation = Character->GetActorLocation();
        if (!Chosen || bSkipped)
        {
            // Nowhere to sleep, or the opening was skipped before they arrived (a test, a session
            // that does not want the eight seconds): they are simply up, and the pod is nobody's.
            Wake.Pod = nullptr;
            // Nowhere to sleep: they are simply up. The local side finishes at once on a null pod.
            Wake.ServerPhase = EQuickDemoOpeningPhase::Complete;
            CrewWakes.Add(Wake);
            continue;
        }

        // Where they end up: where they spawned, facing the bay's bulkhead door (the way out, and
        // the first thing to read). Where they start: inside the pod.
        const FVector PodLocation = Chosen->GetActorLocation();
        const FVector Out = (Wake.StandLocation - PodLocation).GetSafeNormal2D();
        Wake.StandRotation = (-Out).Rotation();
        {
            ABulkheadDoor* NearestDoor = nullptr;
            float NearestDistance = TNumericLimits<float>::Max();
            for (TActorIterator<ABulkheadDoor> DoorIt(World); DoorIt; ++DoorIt)
            {
                const float Distance = FVector::Dist2D(DoorIt->GetActorLocation(), Wake.StandLocation);
                if (Distance < NearestDistance) { NearestDistance = Distance; NearestDoor = *DoorIt; }
            }
            if (NearestDoor)
            {
                Wake.StandRotation = FRotator(0.0f, (NearestDoor->GetActorLocation() - Wake.StandLocation).GetSafeNormal2D().Rotation().Yaw, 0.0f);
            }
        }
        const bool bVertical = Chosen->UsesVerticalPod();
        if (bVertical)
        {
            Chosen->SetActorRotation(FRotator(0.0f, Out.Rotation().Yaw, 0.0f));
            TurnedPods.Add(Chosen);
        }
        Wake.PodSideLocation = bVertical
            ? FVector(PodLocation.X, PodLocation.Y, Wake.StandLocation.Z) - Out * 8.0f
            : FVector(PodLocation.X, PodLocation.Y, Wake.StandLocation.Z) + Out * 120.0f;

        // Nobody sleeps in a pressure suit: whatever the pawn class defaults to, the crew wake in
        // the cryo bodysuit and draw a suit at the rack.
        if (Character->bPressureOversuitEquipped)
        {
            Character->SetPressureOversuitEquipped(false);
        }
        // The sleeper: in the pod, with no say in anything yet.
        Chosen->TryEnterPod(Character);
        Character->SetActorEnableCollision(false);
        if (bVertical)
        {
            Character->SetActorLocation(Wake.PodSideLocation, false, nullptr, ETeleportType::TeleportPhysics);
            Character->SetActorRotation(FRotator(0.0f, Out.Rotation().Yaw, 0.0f));
        }
        else
        {
            Character->SetActorLocation(PodLocation + FVector(0.0f, 0.0f, 40.0f), false, nullptr, ETeleportType::TeleportPhysics);
            Character->SetActorHiddenInGame(true);
        }
        Wake.ServerPhase = EQuickDemoOpeningPhase::Asleep;
        UE_LOG(LogTemp, Display, TEXT("Opening %s: %s sleeps in %s (occupied=%d by %s), placed at %s, hidden=%d, first person=%d, vertical=%d"),
            *GetName(), *Character->GetName(), *Chosen->GetName(), Chosen->bIsOccupied ? 1 : 0,
            Chosen->OccupyingCharacter.IsValid() ? *Chosen->OccupyingCharacter->GetName() : TEXT("nobody"),
            *Character->GetActorLocation().ToCompactString(), Character->IsHidden() ? 1 : 0, Character->IsFirstPersonView() ? 1 : 0, bVertical ? 1 : 0);
        CrewWakes.Add(Wake);
        ForceNetUpdate();
        UE_LOG(LogTemp, Display, TEXT("Opening %s admitted %s into %s (skipped=%d, %d wakes)"), *GetName(), *Character->GetName(), *Chosen->GetName(), bSkipped ? 1 : 0, CrewWakes.Num());
    }
}

void AQuickDemoOpeningSequence::ServerAdvanceCrew()
{
    const float Now = ServerNow();
    for (FQuickDemoCrewWake& Wake : CrewWakes)
    {
        ACoopSurvivalCharacter* Character = Wake.Crew;
        if (Wake.ServerPhase == EQuickDemoOpeningPhase::Complete)
        {
            continue;
        }
        if (!Character)
        {
            Wake.ServerPhase = EQuickDemoOpeningPhase::Complete;
            continue;
        }
        const float Elapsed = Now - Wake.StartServerTime;
        EQuickDemoOpeningPhase Target = PhaseAt(Elapsed);

        if (Wake.ServerPhase < EQuickDemoOpeningPhase::Wake && Target >= EQuickDemoOpeningPhase::Wake)
        {
            // The tube is awake; it does not open. The sleeper releases it from inside.
            Wake.ServerPhase = EQuickDemoOpeningPhase::Wake;
        }
        if (Wake.ServerPhase == EQuickDemoOpeningPhase::Wake && Wake.ReleasedServerTime < 0.0f)
        {
            if (Wake.Pod && FMath::Fmod(Elapsed, 5.0f) < 0.05f)
            {
                UE_LOG(LogTemp, Display, TEXT("Opening %s: %s awake in %s, waiting for the release (occupied=%d by %s, pawn at %s)"), *GetName(),
                    *Character->GetName(), *Wake.Pod->GetName(), Wake.Pod->bIsOccupied ? 1 : 0,
                    Wake.Pod->OccupyingCharacter.IsValid() ? *Wake.Pod->OccupyingCharacter->GetName() : TEXT("nobody"), *Character->GetActorLocation().ToCompactString());
            }
            const bool bReleased = !Wake.Pod || !Wake.Pod->bIsOccupied;
            const bool bOverdue = Elapsed - PhaseStartSeconds(EQuickDemoOpeningPhase::Wake) > WakeAutoReleaseSeconds;
            if (bReleased || bOverdue)
            {
                if (Wake.Pod && Wake.Pod->bIsOccupied)
                {
                    Wake.Pod->ExitPod();
                }
                Wake.ReleasedServerTime = Now;
                ForceNetUpdate();
            }
        }
        if (Wake.ReleasedServerTime >= 0.0f)
        {
            Target = PhaseSinceRelease(Now - Wake.ReleasedServerTime);
        }
        if (Wake.ServerPhase < EQuickDemoOpeningPhase::ClimbOut && Target >= EQuickDemoOpeningPhase::ClimbOut)
        {
            Character->SetActorLocation(Wake.PodSideLocation, false, nullptr, ETeleportType::TeleportPhysics);
            Character->SetActorRotation(Wake.StandRotation);
            Character->SetActorHiddenInGame(false);
            Character->SetActorEnableCollision(true);
            Wake.ServerPhase = EQuickDemoOpeningPhase::ClimbOut;
        }
        if (Wake.ServerPhase == EQuickDemoOpeningPhase::ClimbOut && Target == EQuickDemoOpeningPhase::ClimbOut)
        {
            // A step away from the tube over the phase.
            const float T = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((Now - Wake.ReleasedServerTime) / FMath::Max(ClimbOutSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f));
            UE_LOG(LogTemp, Verbose, TEXT("Opening climb-out lerp %s T=%.2f"), *Character->GetName(), T);
            Character->SetActorLocation(FMath::Lerp(Wake.PodSideLocation, Wake.StandLocation, T), false, nullptr, ETeleportType::TeleportPhysics);
        }
        if (Wake.ServerPhase < EQuickDemoOpeningPhase::FirstPerson && Target >= EQuickDemoOpeningPhase::FirstPerson)
        {
            // Off the pod first: leaving a moving base (the lid, the sleeper's platform) imparts
            // its velocity, and under drive gravity that launched the crew across the casualty
            // station on wake.
            Character->SetBase(static_cast<UPrimitiveComponent*>(nullptr), NAME_None);
            Character->SetActorLocation(Wake.StandLocation, false, nullptr, ETeleportType::TeleportPhysics);
            Character->SetActorRotation(Wake.StandRotation);
            if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
            {
                Move->StopMovementImmediately();
            }
            Character->SetActorHiddenInGame(false);
            Character->SetActorEnableCollision(true);
            if (Wake.Pod && Wake.Pod->bIsOccupied)
            {
                Wake.Pod->ExitPod();
            }
            Wake.ServerPhase = EQuickDemoOpeningPhase::Complete;
        }
    }
}

void AQuickDemoOpeningSequence::TryArm()
{
    // The pawn is possessed a tick or two after BeginPlay, and its wake reaches a client a little
    // after that; keep asking for a few seconds.
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    const int32 Index = FindLocalWake();
    ACoopSurvivalCharacter* Character = Index != INDEX_NONE ? CrewWakes[Index].Crew.Get() : nullptr;
    if (!PC || !Character)
    {
        if (ArmElapsed > 8.0f || bSkipped)
        {
            Finish();
        }
        return;
    }
    if (bSkipped)
    {
        Finish();
        return;
    }
    const FQuickDemoCrewWake& Wake = CrewWakes[Index];
    Player = PC;
    Crew = Character;
    Pod = Wake.Pod;
    LocalStartServerTime = Wake.StartServerTime;
    PodSideLocation = Wake.PodSideLocation;
    StandLocation = Wake.StandLocation;
    StandRotation = Wake.StandRotation;

    ACryoPodSystem* Chosen = Wake.Pod;
    if (!Chosen)
    {
        Finish();
        return;
    }
    const FVector PodLocation = Chosen->GetActorLocation();
    const FVector Out = (StandLocation - PodLocation).GetSafeNormal2D();
    const bool bVertical = Chosen->UsesVerticalPod();

    // The room's lights, so they can go out. Any light inside the tagged room's footprint.
    for (TActorIterator<AModularShipRoom> It(GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(RoomTag))
        {
            continue;
        }
        const FBox Room = FBox::BuildAABB(It->GetActorLocation(), It->ModuleSize * 0.5f + FVector(60.0f));
        for (TActorIterator<AActor> ActorIt(GetWorld()); ActorIt; ++ActorIt)
        {
            // The tubes' own glow is on the pods' circuit, not the room's: it does not die with
            // the ship, and it is what lights the bay until the crew suit up.
            if (ActorIt->IsA<ACryoPodSystem>())
            {
                continue;
            }
            if (!Room.IsInside(ActorIt->GetActorLocation()))
            {
                continue;
            }
            for (ULightComponent* Light : TInlineComponentArray<ULightComponent*>(*ActorIt))
            {
                if (Light && Light->GetVisibleFlag() && Light->Intensity > 0.0f)
                {
                    RoomLights.Add({Light, Light->Intensity});
                }
            }
        }
        break;
    }

    // Each pod gets its own blue, off until the blackout.
    for (TActorIterator<ACryoPodSystem> It(GetWorld()); It; ++It)
    {
        UPointLightComponent* Glow = NewObject<UPointLightComponent>(*It, TEXT("OpeningCryoGlow"));
        Glow->SetupAttachment(It->GetRootComponent());
        Glow->SetRelativeLocation(FVector(0.0f, 0.0f, 70.0f));
        Glow->SetLightColor(CryoGlowColor);
        Glow->SetIntensity(0.0f);
        Glow->SetAttenuationRadius(520.0f);
        Glow->SetCastShadows(false);
        Glow->RegisterComponent();
        PodGlows.Add(Glow);
    }

    // Arriving to a wake that is already over (a very slow load): the room as the others left
    // it, and straight to the controls.
    if (Wake.ReleasedServerTime >= 0.0f && PhaseSinceRelease(ServerNow() - Wake.ReleasedServerTime) == EQuickDemoOpeningPhase::Complete)
    {
        Skip();
        return;
    }

    // The sleeper, as this machine shows them: inside the pod, watched from outside until the
    // hand-over. In first person the crew's own head sections are switched off, which from the
    // shot camera is a body with no helmet. The server has already placed them; the same values
    // here keep the local pawn from arguing with it.
    Character->SetActorEnableCollision(false);
    Character->SetFirstPersonView(false);
    if (bVertical)
    {
        Character->SetActorLocation(PodSideLocation, false, nullptr, ETeleportType::TeleportPhysics);
        Character->SetActorRotation(FRotator(0.0f, Out.Rotation().Yaw, 0.0f));
    }
    else
    {
        Character->SetActorLocation(PodLocation + FVector(0.0f, 0.0f, 40.0f), false, nullptr, ETeleportType::TeleportPhysics);
        Character->SetActorHiddenInGame(true);
    }
    PC->DisableInput(PC);
    if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
    {
        if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
        {
            bHudWasVisible = HUD->IsVisible();
            HUD->SetVisibility(ESlateVisibility::Collapsed);
        }
    }

    // The shot: high and close over the foot of the pod, looking down its length at the lid, so
    // the sleeper's pod fills the frame and the neighbouring pods stay out of the foreground. A
    // low, distant camera between the rows saw only the nearest lid's underside.
    const FVector CameraLocation = bVertical
        ? PodLocation + Out * 340.0f + FVector(0.0f, 0.0f, 165.0f)   // front of the glass, chest height
        : PodLocation + Out * 300.0f + FVector(0.0f, 0.0f, 330.0f);
    const FRotator CameraRotation = ((bVertical ? PodLocation + FVector(0.0f, 0.0f, 120.0f) : PodLocation + FVector(0.0f, 0.0f, 75.0f)) - CameraLocation).Rotation();
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACameraActor* Camera = GetWorld()->SpawnActor<ACameraActor>(CameraLocation, CameraRotation, Params);
    if (Camera)
    {
        Camera->GetCameraComponent()->SetFieldOfView(62.0f);
        ShotCamera = Camera;
        PC->SetViewTargetWithBlend(Camera, 0.0f);
    }

    SetRoomLights(0.35f);
    EnterPhase(EQuickDemoOpeningPhase::Asleep);
}

void AQuickDemoOpeningSequence::SetRoomLights(float Fraction)
{
    for (const FRoomLight& Entry : RoomLights)
    {
        if (ULightComponent* Light = Entry.Light.Get())
        {
            Light->SetIntensity(Entry.Intensity * Fraction);
        }
    }
}

void AQuickDemoOpeningSequence::SetPodGlow(float Fraction)
{
    for (const TWeakObjectPtr<UPointLightComponent>& Glow : PodGlows)
    {
        if (UPointLightComponent* Light = Glow.Get())
        {
            Light->SetIntensity(CryoGlowIntensity * Fraction);
        }
    }
}

void AQuickDemoOpeningSequence::EnterPhase(EQuickDemoOpeningPhase NewPhase)
{
    Phase = NewPhase;
    PhaseElapsed = 0.0f;
    APlayerController* PC = Player.Get();
    ACoopSurvivalCharacter* Character = Crew.Get();
    ACryoPodSystem* ThePod = Pod.Get();

    switch (Phase)
    {
    case EQuickDemoOpeningPhase::Strike:
        if (PC && PC->PlayerCameraManager && StrikeCameraShake)
        {
            PC->PlayerCameraManager->StartCameraShake(StrikeCameraShake, 1.0f);
        }
        if (StrikeSound && ThePod)
        {
            UGameplayStatics::PlaySoundAtLocation(this, StrikeSound, ThePod->GetActorLocation() + FVector(0.0f, 0.0f, 300.0f));
        }
        break;

    case EQuickDemoOpeningPhase::Blackout:
        SetRoomLights(BlackoutRoomLightFraction);
        break;

    case EQuickDemoOpeningPhase::Wake:
        // Awake, in the tube, and it is theirs to open: the keys come back and the visor comes
        // up so the release prompt can be read. The lid itself is the server's, on the release.
        if (PC)
        {
            PC->EnableInput(PC);
            if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
            {
                if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
                {
                    HUD->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
                }
            }
        }
        break;

    case EQuickDemoOpeningPhase::ClimbOut:
        // Out of the tube, on their feet beside it, in the same shot.
        if (Character)
        {
            Character->SetActorLocation(PodSideLocation, false, nullptr, ETeleportType::TeleportPhysics);
            Character->SetActorRotation(StandRotation);
            Character->SetActorHiddenInGame(false);
            Character->SetActorEnableCollision(true);
        }
        break;

    case EQuickDemoOpeningPhase::FirstPerson:
        if (PC)
        {
            if (Character)
            {
                Character->SetActorLocation(StandLocation, false, nullptr, ETeleportType::TeleportPhysics);
                Character->SetActorRotation(StandRotation);
                PC->SetControlRotation(StandRotation);
                Character->SetFirstPersonView(true);
            }
            PC->SetViewTargetWithBlend(Character ? static_cast<AActor*>(Character) : PC->GetPawn(), 0.0f);
            PC->EnableInput(PC);
            if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
            {
                if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
                {
                    HUD->SetVisibility(bHudWasVisible ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
                }
            }
        }
        if (ShotCamera.IsValid())
        {
            ShotCamera->Destroy();
            ShotCamera = nullptr;
        }
        break;

    case EQuickDemoOpeningPhase::Complete:
        // The server keeps ticking for crew who arrive later; a client has nothing more to do.
        if (!HasAuthority())
        {
            SetActorTickEnabled(false);
        }
        break;

    default:
        break;
    }
}

void AQuickDemoOpeningSequence::Finish()
{
    // Undo anything half-done, then stand down.
    if (APlayerController* PC = Player.Get())
    {
        if (ACoopSurvivalCharacter* Character = Crew.Get())
        {
            Character->SetActorHiddenInGame(false);
            Character->SetActorEnableCollision(true);
            if (!StandLocation.IsZero())
            {
                Character->SetBase(static_cast<UPrimitiveComponent*>(nullptr), NAME_None);
                Character->SetActorLocation(StandLocation, false, nullptr, ETeleportType::TeleportPhysics);
                if (UCharacterMovementComponent* Move = Character->GetCharacterMovement())
                {
                    Move->StopMovementImmediately();
                }
            }
            Character->SetFirstPersonView(true);
            PC->SetViewTargetWithBlend(Character, 0.0f);
        }
        PC->EnableInput(PC);
        if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
        {
            if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
            {
                HUD->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
            }
        }
    }
    if (HasAuthority())
    {
        // Every wake still running is over now, whatever the clock says: a skipped opening
        // stands the whole crew up, and nobody is left in a tube to be stood up later, on top of
        // wherever a test or a player has since put them.
        bool bAnyAdvanced = false;
        for (FQuickDemoCrewWake& Wake : CrewWakes)
        {
            if (Wake.ServerPhase == EQuickDemoOpeningPhase::Complete) continue;
            Wake.StartServerTime = ServerNow() - PhaseStartSeconds(EQuickDemoOpeningPhase::Wake) - 1.0f;
            Wake.ReleasedServerTime = ServerNow() - ClimbOutSeconds - 1.0f;
            bAnyAdvanced = true;
        }
        if (bAnyAdvanced) ServerAdvanceCrew();
        if (ACryoPodSystem* ThePod = Pod.Get(); ThePod && ThePod->bIsOccupied)
        {
            ThePod->ExitPod();
        }
    }
    if (ShotCamera.IsValid())
    {
        ShotCamera->Destroy();
        ShotCamera = nullptr;
    }
    EnterPhase(EQuickDemoOpeningPhase::Complete);
}

void AQuickDemoOpeningSequence::Skip()
{
    UE_LOG(LogTemp, Display, TEXT("Opening %s skipped (phase %d, local wake %d, %d wakes)"), *GetName(), static_cast<int32>(Phase), FindLocalWake(), CrewWakes.Num());
    bSkipped = true;
    if (Phase != EQuickDemoOpeningPhase::Complete)
    {
        SetRoomLights(BlackoutRoomLightFraction);
        SetPodGlow(1.0f);
        Finish();
    }
    // Skipped means no opening this session, for anyone: the actor stops ticking, so nothing it
    // does later (an admission, a climb-out) can move a crew member a test or a player has placed.
    SetActorTickEnabled(false);
}

void AQuickDemoOpeningSequence::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (HasAuthority() && bEnabled)
    {
        ServerAdmitCrew();
        ServerAdvanceCrew();
    }

    // Any pod given to a sleeper turns to face where they will stand, on every machine.
    for (const FQuickDemoCrewWake& Wake : CrewWakes)
    {
        if (Wake.Pod && Wake.Pod->UsesVerticalPod() && !TurnedPods.Contains(Wake.Pod.Get()))
        {
            const FVector Out = (Wake.StandLocation - Wake.Pod->GetActorLocation()).GetSafeNormal2D();
            Wake.Pod->SetActorRotation(FRotator(0.0f, Out.Rotation().Yaw, 0.0f));
            TurnedPods.Add(Wake.Pod.Get());
        }
    }

    if (Phase == EQuickDemoOpeningPhase::Idle)
    {
        ArmElapsed += DeltaSeconds;
        TryArm();
        return;
    }
    if (Phase == EQuickDemoOpeningPhase::Complete)
    {
        return;
    }

    // The local timeline runs on the server's clock, so a client's beats land where the server's
    // moves do. Phases are entered in order, one per tick at most, so nothing is skipped. The
    // clock carries the beats to Wake; the rest follow the sleeper's own release.
    const float Elapsed = ServerNow() - LocalStartServerTime;
    EQuickDemoOpeningPhase Target = PhaseAt(Elapsed);
    const int32 LocalIndex = FindLocalWake();
    const float Released = LocalIndex != INDEX_NONE ? CrewWakes[LocalIndex].ReleasedServerTime : -1.0f;
    if (Released >= 0.0f)
    {
        Target = PhaseSinceRelease(ServerNow() - Released);
    }
    else if (Phase == EQuickDemoOpeningPhase::Wake)
    {
        // Awake in the tube, waiting on the release: the visor says what to press.
        if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(Player.Get()))
        {
            if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
            {
                HUD->ShowSystemPrompt(TEXT("[ E ] RELEASE THE POD"));
            }
        }
    }
    if (Target > Phase)
    {
        EnterPhase(static_cast<EQuickDemoOpeningPhase>(static_cast<uint8>(Phase) + 1));
        if (Phase == EQuickDemoOpeningPhase::Complete)
        {
            return;
        }
    }
    PhaseElapsed = Released >= 0.0f && Phase >= EQuickDemoOpeningPhase::ClimbOut
        ? ServerNow() - Released - (Phase == EQuickDemoOpeningPhase::FirstPerson ? ClimbOutSeconds : 0.0f)
        : Elapsed - PhaseStartSeconds(Phase);

    switch (Phase)
    {
    case EQuickDemoOpeningPhase::Strike:
    {
        // Lights failing: hard flicker that decays into the blackout.
        const float T = PhaseElapsed / FMath::Max(StrikeSeconds, KINDA_SMALL_NUMBER);
        const float Flicker = (FMath::Sin(PhaseElapsed * 47.0f) > 0.2f ? 1.0f : 0.15f) * (1.0f - 0.8f * T);
        SetRoomLights(FMath::Max(BlackoutRoomLightFraction, 0.35f * Flicker));
        SetPodGlow(0.35f * T);
        break;
    }

    case EQuickDemoOpeningPhase::Blackout:
    {
        const float T = FMath::Clamp(PhaseElapsed / FMath::Max(BlackoutSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f);
        SetPodGlow(FMath::Lerp(0.35f, 1.0f, FMath::SmoothStep(0.0f, 1.0f, T)));
        break;
    }

    case EQuickDemoOpeningPhase::ClimbOut:
    {
        // A step away from the tube over the phase, in the same shot.
        if (ACoopSurvivalCharacter* Character = Crew.Get())
        {
            const float T = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(PhaseElapsed / FMath::Max(ClimbOutSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f));
            Character->SetActorLocation(FMath::Lerp(PodSideLocation, StandLocation, T), false, nullptr, ETeleportType::TeleportPhysics);
        }
        break;
    }

    default:
        break;
    }
}
