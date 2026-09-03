#include "LevelSetup/QuickDemoOpeningSequence.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Player/SurvivalPlayerController.h"
#include "Shakes/PerlinNoiseCameraShakePattern.h"
#include "Ship/CryoPodSystem.h"
#include "Ship/ModularShipRoom.h"
#include "Sound/SoundBase.h"
#include "UI/SurvivalHUDWidget.h"
#include "Weapons/WeaponMountComponent.h"

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

void AQuickDemoOpeningSequence::TryArm()
{
    // The pawn is possessed a tick or two after BeginPlay; keep asking for a few seconds.
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    ACoopSurvivalCharacter* Character = PC ? Cast<ACoopSurvivalCharacter>(PC->GetPawn()) : nullptr;
    if (!PC || !Character)
    {
        if (ArmElapsed > 5.0f)
        {
            Finish();
        }
        return;
    }
    Player = PC;
    Crew = Character;

    // Nobody wakes from cryo holding a bolt driver. The mount auto-arms every pawn at BeginPlay;
    // the demo's crew find their tool at the workshop bench, which grants it, so empty their hands
    // here. Server side, like the mount itself.
    if (HasAuthority())
    {
        if (UWeaponMountComponent* Mount = Character->FindComponentByClass<UWeaponMountComponent>())
        {
            Mount->ReleaseWeapon();
        }
    }

    // The pod. Tagged by the placement script; otherwise the nearest one to where they spawned.
    ACryoPodSystem* Chosen = nullptr;
    float BestDistance = TNumericLimits<float>::Max();
    for (TActorIterator<ACryoPodSystem> It(GetWorld()); It; ++It)
    {
        if (!PlayerPodTag.IsNone() && It->ActorHasTag(PlayerPodTag))
        {
            Chosen = *It;
            break;
        }
        const float Distance = FVector::Dist(It->GetActorLocation(), Character->GetActorLocation());
        if (Distance < BestDistance)
        {
            BestDistance = Distance;
            Chosen = *It;
        }
    }
    if (!Chosen)
    {
        Finish();
        return;
    }
    Pod = Chosen;

    // Where they end up: where they spawned, facing back at the pod. Where they start: inside it.
    StandLocation = Character->GetActorLocation();
    const FVector PodLocation = Chosen->GetActorLocation();
    const FVector Out = (StandLocation - PodLocation).GetSafeNormal2D();
    StandRotation = (-Out).Rotation();
    PodSideLocation = FVector(PodLocation.X, PodLocation.Y, StandLocation.Z) + Out * 120.0f;

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

    // The sleeper: in the pod, hidden inside it, with no say in anything yet.
    if (HasAuthority())
    {
        Chosen->TryEnterPod(Character);
    }
    Character->SetActorEnableCollision(false);
    Character->SetActorLocation(PodLocation + FVector(0.0f, 0.0f, 40.0f), false, nullptr, ETeleportType::TeleportPhysics);
    Character->SetActorHiddenInGame(true);
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
    const FVector CameraLocation = PodLocation + Out * 300.0f + FVector(0.0f, 0.0f, 330.0f);
    const FRotator CameraRotation = (PodLocation + FVector(0.0f, 0.0f, 75.0f) - CameraLocation).Rotation();
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
        if (ThePod && HasAuthority())
        {
            ThePod->ExitPod();   // opens the lid
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
        SetActorTickEnabled(false);
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
                Character->SetActorLocation(StandLocation, false, nullptr, ETeleportType::TeleportPhysics);
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
    if (ACryoPodSystem* ThePod = Pod.Get(); ThePod && HasAuthority() && ThePod->bIsOccupied)
    {
        ThePod->ExitPod();
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
    if (Phase != EQuickDemoOpeningPhase::Complete)
    {
        SetRoomLights(BlackoutRoomLightFraction);
        SetPodGlow(1.0f);
        Finish();
    }
}

void AQuickDemoOpeningSequence::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PhaseElapsed += DeltaSeconds;

    switch (Phase)
    {
    case EQuickDemoOpeningPhase::Idle:
        ArmElapsed += DeltaSeconds;
        TryArm();
        break;

    case EQuickDemoOpeningPhase::Asleep:
        if (PhaseElapsed >= AsleepSeconds)
        {
            EnterPhase(EQuickDemoOpeningPhase::Strike);
        }
        break;

    case EQuickDemoOpeningPhase::Strike:
    {
        // Lights failing: hard flicker that decays into the blackout.
        const float T = PhaseElapsed / FMath::Max(StrikeSeconds, KINDA_SMALL_NUMBER);
        const float Flicker = (FMath::Sin(PhaseElapsed * 47.0f) > 0.2f ? 1.0f : 0.15f) * (1.0f - 0.8f * T);
        SetRoomLights(FMath::Max(BlackoutRoomLightFraction, 0.35f * Flicker));
        SetPodGlow(0.35f * T);
        if (PhaseElapsed >= StrikeSeconds)
        {
            EnterPhase(EQuickDemoOpeningPhase::Blackout);
        }
        break;
    }

    case EQuickDemoOpeningPhase::Blackout:
    {
        const float T = FMath::Clamp(PhaseElapsed / FMath::Max(BlackoutSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f);
        SetPodGlow(FMath::Lerp(0.35f, 1.0f, FMath::SmoothStep(0.0f, 1.0f, T)));
        if (PhaseElapsed >= BlackoutSeconds)
        {
            EnterPhase(EQuickDemoOpeningPhase::Wake);
        }
        break;
    }

    case EQuickDemoOpeningPhase::Wake:
        if (PhaseElapsed >= WakeSeconds)
        {
            EnterPhase(EQuickDemoOpeningPhase::ClimbOut);
        }
        break;

    case EQuickDemoOpeningPhase::ClimbOut:
    {
        // A step away from the tube over the phase, in the same shot.
        if (ACoopSurvivalCharacter* Character = Crew.Get())
        {
            const float T = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(PhaseElapsed / FMath::Max(ClimbOutSeconds, KINDA_SMALL_NUMBER), 0.0f, 1.0f));
            Character->SetActorLocation(FMath::Lerp(PodSideLocation, StandLocation, T), false, nullptr, ETeleportType::TeleportPhysics);
        }
        if (PhaseElapsed >= ClimbOutSeconds)
        {
            EnterPhase(EQuickDemoOpeningPhase::FirstPerson);
        }
        break;
    }

    case EQuickDemoOpeningPhase::FirstPerson:
        if (PhaseElapsed >= 0.25f)
        {
            EnterPhase(EQuickDemoOpeningPhase::Complete);
        }
        break;

    default:
        break;
    }
}
