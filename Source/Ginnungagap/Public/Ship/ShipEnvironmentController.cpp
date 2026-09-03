#include "Ship/ShipEnvironmentController.h"

#include "Bloom/BloomDirector.h"
#include "Components/AudioComponent.h"
#include "Components/DecalComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Sound/SoundBase.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipSection.h"
#include "EngineUtils.h"

AShipEnvironmentController::AShipEnvironmentController()
{
    PrimaryActorTick.bCanEverTick = false;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    AtmosphereFog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("AtmosphereFog"));
    AtmosphereFog->SetupAttachment(SceneRoot);

    PostProcess = CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcess"));
    PostProcess->SetupAttachment(SceneRoot);
    PostProcess->bUnbound = true;

    AmbientAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("AmbientAudio"));
    AmbientAudio->SetupAttachment(SceneRoot);
    AmbientAudio->bAutoActivate = false;
    AmbientAudio->bOverrideAttenuation = true;
    AmbientAudio->AttenuationOverrides.bSpatialize = true;
    AmbientAudio->AttenuationOverrides.AttenuationShape = EAttenuationShape::Sphere;
    AmbientAudio->AttenuationOverrides.AttenuationShapeExtents = FVector(6500.0f);
    AmbientAudio->AttenuationOverrides.FalloffDistance = 2500.0f;

    for (int32 Index = 0; Index < 6; ++Index)
    {
        UStaticMeshComponent* Growth = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("BloomGrowth_%02d"), Index));
        Growth->SetupAttachment(SceneRoot);
        const float Angle = Index * 137.5f;
        Growth->SetRelativeLocation(FVector(FMath::Cos(FMath::DegreesToRadians(Angle)) * (300.0f + Index * 95.0f),
            FMath::Sin(FMath::DegreesToRadians(Angle)) * (260.0f + Index * 70.0f), 35.0f + Index * 65.0f));
        Growth->SetRelativeRotation(FRotator(Index * 17.0f, Angle, Index * 29.0f));
        Growth->SetRelativeScale3D(FVector(0.7f + Index * 0.18f));
        Growth->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        BloomGrowths.Add(Growth);
    }

    for (int32 Index = 0; Index < 3; ++Index)
    {
        UPointLightComponent* Light = CreateDefaultSubobject<UPointLightComponent>(
            *FString::Printf(TEXT("StateLight_%02d"), Index));
        Light->SetupAttachment(SceneRoot);
        Light->SetRelativeLocation(FVector((Index - 1) * 750.0f, 0.0f, 320.0f));
        Light->SetAttenuationRadius(1300.0f);
        Light->SetIntensity(2200.0f);
        Light->SetCastShadows(Index == 1);
        StateLights.Add(Light);
    }

    for (int32 Index = 0; Index < 4; ++Index)
    {
        UDecalComponent* Decal = CreateDefaultSubobject<UDecalComponent>(
            *FString::Printf(TEXT("DamageDecal_%02d"), Index));
        Decal->SetupAttachment(SceneRoot);
        Decal->SetRelativeLocation(FVector((Index - 1.5f) * 420.0f, Index % 2 == 0 ? -480.0f : 480.0f, 75.0f));
        Decal->SetRelativeRotation(FRotator(-90.0f, Index * 43.0f, 0.0f));
        Decal->DecalSize = FVector(120.0f, 260.0f, 260.0f);
        DamageDecals.Add(Decal);
    }
}

void AShipEnvironmentController::BeginPlay()
{
    Super::BeginPlay();
    BindRuntimeState();
    RefreshEnvironment();
    if (AmbientAudio->Sound)
    {
        AmbientAudio->Play();
    }
}

void AShipEnvironmentController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (BoundBloomDirector)
    {
        BoundBloomDirector->OnBloomStageChanged.RemoveDynamic(this, &AShipEnvironmentController::HandleBloomStageChanged);
    }
    if (BoundDamageState)
    {
        BoundDamageState->OnDamageStateChanged.RemoveDynamic(this, &AShipEnvironmentController::HandleDamageStateChanged);
    }
    Super::EndPlay(EndPlayReason);
}

void AShipEnvironmentController::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    RefreshEnvironment();
}

void AShipEnvironmentController::ApplyEnvironmentState(EBloomStage BloomStage, bool bInAlert, bool bInDamage)
{
    PreviewBloomStage = BloomStage;
    bAlertActive = bInAlert;
    bDamageActive = bInDamage;
    RefreshEnvironment();
}

void AShipEnvironmentController::ApplyGameplaySignals(EBloomStage BloomStage, float DamageDangerScore)
{
    const float Danger = FMath::Clamp(DamageDangerScore, 0.0f, 1.0f);
    PreviewBloomStage = BloomStage;
    bDamageActive = Danger > 0.05f;
    bAlertActive = BloomStage != EBloomStage::Latent || Danger > 0.2f;
    RefreshEnvironment();
}

void AShipEnvironmentController::BindRuntimeState()
{
    if (bFollowLiveBloomState && GetGameInstance())
    {
        BoundBloomDirector = GetGameInstance()->GetSubsystem<UBloomDirector>();
        if (BoundBloomDirector)
        {
            BoundBloomDirector->OnBloomStageChanged.AddUniqueDynamic(this, &AShipEnvironmentController::HandleBloomStageChanged);
            PreviewBloomStage = BoundBloomDirector->GetCurrentStage();
        }
    }

    if (bFollowShipDamageState)
    {
        if (!MonitoredSection)
        {
            for (TActorIterator<AShipSection> It(GetWorld()); It; ++It)
            {
                if (It->ContainsPoint(GetActorLocation()))
                {
                    MonitoredSection = *It;
                    break;
                }
            }
        }
        if (MonitoredSection)
        {
            BoundDamageState = MonitoredSection->DamageState;
            if (BoundDamageState)
            {
                BoundDamageState->OnDamageStateChanged.AddUniqueDynamic(this, &AShipEnvironmentController::HandleDamageStateChanged);
            }
        }
    }

    if (bFollowLiveBloomState || bFollowShipDamageState)
    {
        ApplyGameplaySignals(PreviewBloomStage, BoundDamageState ? BoundDamageState->GetDangerScore() : 0.0f);
    }
}

void AShipEnvironmentController::HandleBloomStageChanged(EBloomStage NewStage)
{
    ApplyGameplaySignals(NewStage, BoundDamageState ? BoundDamageState->GetDangerScore() : (bDamageActive ? 1.0f : 0.0f));
}

void AShipEnvironmentController::HandleDamageStateChanged()
{
    ApplyGameplaySignals(PreviewBloomStage, BoundDamageState ? BoundDamageState->GetDangerScore() : 0.0f);
}

void AShipEnvironmentController::RefreshEnvironment()
{
    const int32 Stage = static_cast<int32>(PreviewBloomStage);
    const bool bBloomPresent = Stage > static_cast<int32>(EBloomStage::Latent);
    const int32 VisibleGrowths = FMath::Clamp(Stage, 0, BloomGrowths.Num());

    for (int32 Index = 0; Index < BloomGrowths.Num(); ++Index)
    {
        UStaticMeshComponent* Growth = BloomGrowths[Index];
        Growth->SetStaticMesh(Index < 2 ? BloomNoduleMesh : (Index < 4 ? BloomTendrilMesh : BloomRibMesh));
        Growth->SetMaterial(0, Stage >= static_cast<int32>(EBloomStage::Puppeteer)
            ? BloomAdvancedMaterial : BloomColonyMaterial);
        Growth->SetVisibility(Index < VisibleGrowths, true);
    }

    for (UDecalComponent* Decal : DamageDecals)
    {
        Decal->SetDecalMaterial(DamageDecalMaterial);
        Decal->SetVisibility(bDamageActive, true);
    }

    const FLinearColor LightColor = bBloomPresent
        ? FLinearColor(0.22f, 0.015f, 0.5f)
        : (bAlertActive ? FLinearColor(0.75f, 0.015f, 0.005f) : FLinearColor(0.55f, 0.72f, 1.0f));
    for (int32 Index = 0; Index < StateLights.Num(); ++Index)
    {
        StateLights[Index]->SetLightColor(LightColor);
        StateLights[Index]->SetIntensity(bDamageActive && Index != 1 ? 350.0f : (bBloomPresent ? 1500.0f : 2200.0f));
    }

    AtmosphereFog->SetFogDensity(bBloomPresent ? 0.018f + Stage * 0.008f : (bDamageActive ? 0.015f : 0.004f));
    AtmosphereFog->SetFogInscatteringColor(bBloomPresent
        ? FLinearColor(0.09f, 0.008f, 0.16f) : FLinearColor(0.08f, 0.11f, 0.14f));
    AtmosphereFog->SetFogHeightFalloff(0.45f);

    PostProcess->Settings.bOverride_VignetteIntensity = true;
    PostProcess->Settings.VignetteIntensity = bBloomPresent ? 0.45f + Stage * 0.05f : (bDamageActive ? 0.35f : 0.18f);
    PostProcess->Settings.bOverride_FilmGrainIntensity = true;
    PostProcess->Settings.FilmGrainIntensity = bDamageActive || bBloomPresent ? 0.32f : 0.08f;
    PostProcess->Settings.bOverride_BloomIntensity = true;
    PostProcess->Settings.BloomIntensity = bBloomPresent ? 1.8f : 0.65f;

    USoundBase* DesiredSound = bBloomPresent ? BloomSound : (bAlertActive ? AlarmSound : ShipHumSound);
    if (AmbientAudio->Sound != DesiredSound)
    {
        AmbientAudio->SetSound(DesiredSound);
    }
}
