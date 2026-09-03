#include "Bloom/BloomDormantHulk.h"

#include "AI/PatrollingEnemyController.h"
#include "Bloom/BloomRoarCameraShake.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Mission/MissionObjectiveSubsystem.h"
#include "Net/UnrealNetwork.h"
#include "Player/SurvivalPlayerController.h"
#include "Sound/SoundBase.h"
#include "UI/SurvivalHUDWidget.h"

namespace
{
    // The assembled silhouette sits this far below the capsule centre so the scaled-up legs meet
    // the bottom of the taller capsule instead of hanging above the deck.
    constexpr float VisualBaseZ = -30.0f;
    constexpr float VisualScale = 1.3f;
}

ABloomDormantHulk::ABloomDormantHulk()
{
    // Its own progression. The global Bloom stage would pull it to Latent (0.0) on BeginPlay and
    // erase the dormant state before anyone saw it.
    bTrackGlobalBloomStage = false;
    InfectionProgress = DormantInfectionProgress;

    // Massive: the reference calls it a heavy bruiser and the hero concept fills a corridor.
    AttackPoseRoot->SetRelativeScale3D(FVector(VisualScale));
    GetCapsuleComponent()->InitCapsuleSize(88.0f, 188.0f);

    RoarAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RoarAudio"));
    RoarAudio->SetupAttachment(AttackPoseRoot);
    RoarAudio->bAutoActivate = false;
    // Heard across the deck. A roar that stops at the room wall is a growl.
    RoarAudio->bOverrideAttenuation = true;
    RoarAudio->AttenuationOverrides.bSpatialize = true;
    RoarAudio->AttenuationOverrides.AttenuationShape = EAttenuationShape::Sphere;
    RoarAudio->AttenuationOverrides.AttenuationShapeExtents = FVector(1400.0f);
    RoarAudio->AttenuationOverrides.FalloffDistance = 9000.0f;

    // Project-authored, synthesised by tools/build_bloom_hulk_reveal_assets.py. Soft: the class
    // must construct before the asset exists.
    RoarSound = LoadObject<USoundBase>(nullptr,
        TEXT("/Game/Assets/Ships/Production/Audio/S_Bloom_Hulk_Roar.S_Bloom_Hulk_Roar"));
    if (RoarSound)
    {
        RoarAudio->SetSound(RoarSound);
    }

    RoarCameraShake = UBloomRoarCameraShake::StaticClass();
    AlertLine = NSLOCTEXT("QuickDemo", "HulkAlertLine", "UNKNOWN BIOMASS SIGNATURE  //  DECK 3 AFT");
}

void ABloomDormantHulk::BeginPlay()
{
    Super::BeginPlay();
    BeginPlaySeconds = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;

    if (HasAuthority() && !WakeObjectiveId.IsNone())
    {
        if (UGameInstance* GameInstance = GetGameInstance())
        {
            if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
            {
                Missions->OnObjectiveChanged.AddDynamic(this, &ABloomDormantHulk::HandleObjectiveChanged);
            }
        }
    }
    ApplyAnchoring();
}

void ABloomDormantHulk::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UMissionObjectiveSubsystem* Missions = GameInstance->GetSubsystem<UMissionObjectiveSubsystem>())
        {
            Missions->OnObjectiveChanged.RemoveDynamic(this, &ABloomDormantHulk::HandleObjectiveChanged);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void ABloomDormantHulk::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(ABloomDormantHulk, bAwake);
}

void ABloomDormantHulk::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    ApplyAnchoring();
}

void ABloomDormantHulk::ApplyAnchoring()
{
    if (APatrollingEnemyController* Patrol = Cast<APatrollingEnemyController>(GetController()))
    {
        Patrol->bAnchored = !bAwake || bStayAnchoredAfterWake;
    }
}

float ABloomDormantHulk::GetWakeAlpha() const
{
    if (!bAwake)
    {
        return 0.0f;
    }
    if (bWakeSilently || WakeRiseSeconds <= KINDA_SMALL_NUMBER)
    {
        return 1.0f;
    }
    return FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(WakeElapsed / WakeRiseSeconds, 0.0f, 1.0f));
}

void ABloomDormantHulk::HandleObjectiveChanged(FName ObjectiveId, EMissionObjectiveState NewState)
{
    if (!HasAuthority() || bAwake || NewState != EMissionObjectiveState::Completed || ObjectiveId != WakeObjectiveId)
    {
        return;
    }
    // An objective completing within a second of the level coming up is a checkpoint being
    // restored, not a player finishing it: the hulk should already be awake, not wake on camera.
    const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
    bWakeSilently = (Now - BeginPlaySeconds) < 1.0;
    Wake();
}

void ABloomDormantHulk::Wake()
{
    if (!HasAuthority() || bAwake)
    {
        return;
    }
    bAwake = true;
    WakeElapsed = 0.0f;
    if (bWakeSilently)
    {
        WakeElapsed = WakeRiseSeconds;
        bRoared = true;
        SetInfectionProgress(1.0f);
    }
    ApplyAnchoring();
    ForceNetUpdate();
}

void ABloomDormantHulk::OnRep_Awake()
{
    ApplyAnchoring();
}

void ABloomDormantHulk::Tick(const float DeltaTime)
{
    Super::Tick(DeltaTime);
    if (!bAwake || bWakeSilently)
    {
        return;
    }

    WakeElapsed += DeltaTime;

    if (HasAuthority())
    {
        // The rise is also the infection running to Overgrown: glow up, growth out, crown revealed.
        // Driven through the existing progression so every client sees the same thing.
        const float Progress = FMath::Lerp(DormantInfectionProgress, 1.0f, GetWakeAlpha());
        if (Progress > InfectionProgress + KINDA_SMALL_NUMBER)
        {
            SetInfectionProgress(Progress);
        }
        if (!bRoared && WakeElapsed >= RoarDelaySeconds)
        {
            MulticastRoar();
        }
    }
}

void ABloomDormantHulk::MulticastRoar_Implementation()
{
    bRoared = true;

    if (RoarAudio && RoarAudio->Sound)
    {
        RoarAudio->Play();
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }
    for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
    {
        APlayerController* PC = It->Get();
        if (!PC || !PC->IsLocalController())
        {
            continue;
        }
        if (PC->PlayerCameraManager && RoarCameraShake)
        {
            PC->PlayerCameraManager->StartCameraShake(RoarCameraShake, 1.0f);
        }
        if (ASurvivalPlayerController* Survival = Cast<ASurvivalPlayerController>(PC))
        {
            if (USurvivalHUDWidget* HUD = Survival->GetHUDWidget())
            {
                HUD->ShowAlertLine(AlertLine, AlertLineSeconds);
            }
        }
    }
}

void ABloomDormantHulk::ApplyProgressiveVisualsAndTuning(const float Progress)
{
    Super::ApplyProgressiveVisualsAndTuning(Progress);
    if (!bAwake)
    {
        // Asleep means asleep: nothing in reach, nowhere to go.
        AttackRange = 0.0f;
        if (UCharacterMovementComponent* Movement = GetCharacterMovement())
        {
            Movement->MaxWalkSpeed = 0.0f;
        }
    }
}

void ABloomDormantHulk::ApplyNativeAttackPose(const float PoseAlpha)
{
    // Owns the whole pose rather than layering on the base: the base writes AttackPoseRoot's
    // location every tick, which would erase the slump.
    const float Slump = 1.0f - GetWakeAlpha();
    const float Time = GetWorld() ? static_cast<float>(GetWorld()->GetTimeSeconds()) : 0.0f;
    // A slow heave once it is up: something that size breathes, and a set piece that holds one
    // frame reads as a statue.
    const float Breath = (1.0f - Slump) * 3.0f * FMath::Sin(Time * 0.9f);

    AttackPoseRoot->SetRelativeLocation(FVector(12.0f * PoseAlpha, 0.0f, VisualBaseZ - 70.0f * Slump + Breath));
    AttackPoseRoot->SetRelativeRotation(FRotator(-3.0f * PoseAlpha - 24.0f * Slump, 0.0f, 0.0f));
    RightArm->SetRelativeRotation(FRotator(-68.0f * PoseAlpha + 34.0f * Slump, 180.0f, 8.0f));
    LeftArm->SetRelativeRotation(FRotator(34.0f * Slump, 0.0f, -8.0f));
    RobotHead->SetRelativeRotation(FRotator(-35.0f * Slump, 0.0f, 0.0f));
}
