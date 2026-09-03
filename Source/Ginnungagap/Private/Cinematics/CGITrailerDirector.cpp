#include "Cinematics/CGITrailerDirector.h"

#include "Animation/AnimationAsset.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

namespace
{
    TAutoConsoleVariable<int32> CVarCGITrailerStart(
        TEXT("gg.CGITrailer.Start"),
        0,
        TEXT("Set to 1 to start the synchronized in-engine CGI trailer timeline."),
        ECVF_Default);

    float Ease(float Alpha)
    {
        Alpha = FMath::Clamp(Alpha, 0.0f, 1.0f);
        return Alpha * Alpha * (3.0f - 2.0f * Alpha);
    }

    FVector Glide(const FVector& A, const FVector& B, float Alpha)
    {
        return FMath::Lerp(A, B, Ease(Alpha));
    }
}

ACGITrailerDirector::ACGITrailerDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("TrailerRoot"));
}

void ACGITrailerDirector::BeginPlay()
{
    Super::BeginPlay();

    if (!FParse::Param(FCommandLine::Get(), TEXT("CGITrailer")))
    {
        SetActorTickEnabled(false);
        return;
    }

    FParse::Value(FCommandLine::Get(), TEXT("CGITrailerDelay="), StartDelaySeconds);
    FParse::Value(FCommandLine::Get(), TEXT("CGITrailerTimeDilation="), RenderTimeDilation);
    UGameplayStatics::SetGlobalTimeDilation(this, FMath::Clamp(RenderTimeDilation, 0.1f, 1.0f));
    bActivated = true;

    CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    CylinderMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    SphereMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    HullMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Assets/Materials/M_ShipBulkhead_WornSteel.M_ShipBulkhead_WornSteel"));
    DeckMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Assets/Materials/M_ShipDeck_NonSlip.M_ShipDeck_NonSlip"));
    SuitMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Assets/Materials/M_SpaceSuit_Damaged.M_SpaceSuit_Damaged"));
    BloomMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Assets/Materials/M_Bloom_AmethystCorruption.M_Bloom_AmethystCorruption"));

    Camera = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), FVector(5300, -180, 165), FRotator::ZeroRotator);
    if (Camera && Camera->GetCameraComponent())
    {
        UCameraComponent* CameraComponent = Camera->GetCameraComponent();
        CameraComponent->SetFieldOfView(72.0f);
        CameraComponent->PostProcessBlendWeight = 1.0f;
        CameraComponent->PostProcessSettings.bOverride_BloomIntensity = true;
        CameraComponent->PostProcessSettings.BloomIntensity = 2.1f;
        CameraComponent->PostProcessSettings.bOverride_VignetteIntensity = true;
        CameraComponent->PostProcessSettings.VignetteIntensity = 0.58f;
        CameraComponent->PostProcessSettings.bOverride_AutoExposureBias = true;
        CameraComponent->PostProcessSettings.AutoExposureBias = 0.15f;
        CameraComponent->PostProcessSettings.bOverride_MotionBlurAmount = true;
        CameraComponent->PostProcessSettings.MotionBlurAmount = 0.24f;
        CameraComponent->PostProcessSettings.bOverride_ChromaticAberrationStartOffset = true;
        CameraComponent->PostProcessSettings.ChromaticAberrationStartOffset = 0.35f;
        CameraComponent->PostProcessSettings.bOverride_SceneFringeIntensity = true;
        CameraComponent->PostProcessSettings.SceneFringeIntensity = 0.22f;

        UPointLightComponent* CameraFill = NewObject<UPointLightComponent>(Camera);
        CameraFill->SetupAttachment(Camera->GetRootComponent());
        CameraFill->SetRelativeLocation(FVector(35, 0, 5));
        CameraFill->SetLightColor(FColor(150, 178, 235));
        CameraFill->SetIntensity(1850.0f);
        CameraFill->SetAttenuationRadius(920.0f);
        CameraFill->SetCastShadows(false);
        CameraFill->SetVolumetricScatteringIntensity(0.55f);
        CameraFill->RegisterComponent();
    }

    if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
    {
        PC->SetCinematicMode(true, true, true, true, true);
        PC->SetViewTarget(Camera);
        if (APawn* Pawn = PC->GetPawn())
        {
            Pawn->SetActorHiddenInGame(true);
            Pawn->SetActorEnableCollision(false);
        }
    }

    SpawnTrailerCast();
    SpawnCinematicLighting();
    SpawnReactorBloom();

    for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
    {
        It->GetLightComponent()->SetIntensity(0.08f);
    }
    for (TActorIterator<ASkyLight> It(GetWorld()); It; ++It)
    {
        It->GetLightComponent()->SetIntensity(0.12f);
    }

    if (GEngine)
    {
        GEngine->Exec(GetWorld(), TEXT("r.BloomQuality 5"));
        GEngine->Exec(GetWorld(), TEXT("r.MotionBlurQuality 4"));
        GEngine->Exec(GetWorld(), TEXT("r.Tonemapper.Quality 5"));
        GEngine->Exec(GetWorld(), TEXT("r.AmbientOcclusionLevels 3"));
        GEngine->Exec(GetWorld(), TEXT("r.ScreenPercentage 100"));
        GEngine->Exec(GetWorld(), TEXT("r.DepthOfFieldQuality 2"));
    }
}

ASkeletalMeshActor* ACGITrailerDirector::SpawnPerformer(USkeletalMesh* Mesh, UAnimationAsset* Animation,
    UMaterialInterface* Material, const FVector& Location, const FRotator& Rotation,
    const FVector& Scale, bool bLoopAnimation)
{
    if (!GetWorld() || !Mesh)
    {
        return nullptr;
    }

    ASkeletalMeshActor* Performer = GetWorld()->SpawnActor<ASkeletalMeshActor>(ASkeletalMeshActor::StaticClass(), Location, Rotation);
    if (!Performer)
    {
        return nullptr;
    }

    Performer->SetActorScale3D(Scale);
    USkeletalMeshComponent* Component = Performer->GetSkeletalMeshComponent();
    Component->SetSkeletalMeshAsset(Mesh);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Material)
    {
        const int32 MaterialCount = FMath::Max(1, Component->GetNumMaterials());
        for (int32 Slot = 0; Slot < MaterialCount; ++Slot)
        {
            Component->SetMaterial(Slot, Material);
        }
    }
    if (Animation)
    {
        Component->SetAnimationMode(EAnimationMode::AnimationSingleNode);
        Component->PlayAnimation(Animation, bLoopAnimation);
    }
    return Performer;
}

void ACGITrailerDirector::AddRobotPart(AActor* Robot, UStaticMesh* Mesh, const FVector& RelativeLocation,
    const FVector& RelativeScale, const FRotator& RelativeRotation, UMaterialInterface* Material)
{
    if (!Robot || !Mesh)
    {
        return;
    }

    UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(Robot);
    Part->SetStaticMesh(Mesh);
    Part->SetupAttachment(Robot->GetRootComponent());
    Part->SetRelativeLocation(RelativeLocation);
    Part->SetRelativeScale3D(RelativeScale);
    Part->SetRelativeRotation(RelativeRotation);
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (Material)
    {
        Part->SetMaterial(0, Material);
    }
    Part->RegisterComponent();
}

AActor* ACGITrailerDirector::SpawnRobot(const FVector& Location, const FRotator& Rotation, float Scale)
{
    AActor* Robot = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), Location, Rotation);
    if (!Robot)
    {
        return nullptr;
    }

    USceneComponent* RobotRoot = NewObject<USceneComponent>(Robot, TEXT("RobotRoot"));
    RobotRoot->RegisterComponent();
    Robot->SetRootComponent(RobotRoot);
    Robot->SetActorLocationAndRotation(Location, Rotation);
    Robot->SetActorScale3D(FVector(Scale));

    AddRobotPart(Robot, CubeMesh, FVector(0, 0, 135), FVector(0.9f, 0.62f, 0.72f), FRotator::ZeroRotator, HullMaterial);
    AddRobotPart(Robot, SphereMesh, FVector(28, 0, 205), FVector(0.38f, 0.38f, 0.34f), FRotator::ZeroRotator, BloomMaterial);
    AddRobotPart(Robot, SphereMesh, FVector(62, -28, 213), FVector(0.11f), FRotator::ZeroRotator, BloomMaterial);
    AddRobotPart(Robot, CylinderMesh, FVector(0, -55, 95), FVector(0.15f, 0.15f, 1.15f), FRotator(0, 18, 8), HullMaterial);
    AddRobotPart(Robot, CylinderMesh, FVector(0, 55, 95), FVector(0.15f, 0.15f, 1.15f), FRotator(0, -18, -8), HullMaterial);
    AddRobotPart(Robot, CylinderMesh, FVector(-28, -38, -2), FVector(0.19f, 0.19f, 1.45f), FRotator(0, 4, 2), HullMaterial);
    AddRobotPart(Robot, CylinderMesh, FVector(-28, 38, -2), FVector(0.19f, 0.19f, 1.45f), FRotator(0, -4, -2), HullMaterial);
    AddRobotPart(Robot, SphereMesh, FVector(20, 0, 126), FVector(0.48f, 0.28f, 0.62f), FRotator(0, 0, 20), BloomMaterial);

    UPointLightComponent* EyeGlow = NewObject<UPointLightComponent>(Robot);
    EyeGlow->SetupAttachment(RobotRoot);
    EyeGlow->SetRelativeLocation(FVector(70, 0, 205));
    EyeGlow->SetLightColor(FColor(128, 25, 255));
    EyeGlow->SetIntensity(1800.0f);
    EyeGlow->SetAttenuationRadius(270.0f);
    EyeGlow->SetCastShadows(false);
    EyeGlow->RegisterComponent();
    CinematicLights.Add(EyeGlow);
    return Robot;
}

AActor* ACGITrailerDirector::SpawnPropWeapon()
{
    AActor* Weapon = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    if (!Weapon)
    {
        return nullptr;
    }
    USceneComponent* WeaponRoot = NewObject<USceneComponent>(Weapon, TEXT("WeaponRoot"));
    WeaponRoot->RegisterComponent();
    Weapon->SetRootComponent(WeaponRoot);
    Weapon->SetActorLocation(FVector::ZeroVector);
    AddRobotPart(Weapon, CubeMesh, FVector(0, 0, 0), FVector(0.78f, 0.10f, 0.14f), FRotator::ZeroRotator, HullMaterial);
    AddRobotPart(Weapon, CylinderMesh, FVector(75, 0, 0), FVector(0.06f, 0.06f, 0.75f), FRotator(0, 90, 0), DeckMaterial);
    AddRobotPart(Weapon, CubeMesh, FVector(-20, 0, -16), FVector(0.16f, 0.08f, 0.26f), FRotator(0, 0, -15), DeckMaterial);
    return Weapon;
}

void ACGITrailerDirector::SpawnTrailerCast()
{
    USkeletalMesh* Quinn = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"));
    USkeletalMesh* Manny = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
    UAnimationAsset* RifleJog = LoadObject<UAnimationAsset>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Rifle/Jog/MF_Rifle_Jog_Fwd.MF_Rifle_Jog_Fwd"));
    UAnimationAsset* RifleIdle = LoadObject<UAnimationAsset>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS.MF_Rifle_Idle_ADS"));
    CombatAnimation = RifleIdle;
    UAnimationAsset* Attack = LoadObject<UAnimationAsset>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02.MM_Attack_02"));
    UAnimationAsset* Death = LoadObject<UAnimationAsset>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Death/MM_Death_Back_01.MM_Death_Back_01"));

    PlayerPerformer = SpawnPerformer(Quinn, RifleJog ? RifleJog : RifleIdle, SuitMaterial,
        FVector(2150, 0, 20), FRotator(0, 180, 0), FVector(1.0f), true);
    PlayerWeapon = SpawnPropWeapon();

    InfectedPerformers.Add(SpawnPerformer(Manny, Attack, BloomMaterial,
        FVector(-1710, 900, 20), FRotator(0, 180, 0), FVector(1.12f), true));
    InfectedPerformers.Add(SpawnPerformer(Manny, Attack, BloomMaterial,
        FVector(-4050, 40, 20), FRotator(0, 0, 0), FVector(1.18f), true));
    InfectedPerformers.Add(SpawnPerformer(Manny, Attack, BloomMaterial,
        FVector(-4120, -70, 20), FRotator(0, 12, 0), FVector(1.28f), true));
    InfectedPerformers.Add(SpawnPerformer(Manny, Attack, BloomMaterial,
        FVector(-4950, 30, 20), FRotator(0, 0, 0), FVector(1.48f), true));

    CorpsePerformers.Add(SpawnPerformer(Manny, Death, SuitMaterial,
        FVector(150, 1420, 28), FRotator(0, 35, 88), FVector(1.0f), false));
    CorpsePerformers.Add(SpawnPerformer(Quinn, Death, SuitMaterial,
        FVector(-210, 1300, 35), FRotator(0, -65, -82), FVector(0.96f), false));
    CorpsePerformers.Add(SpawnPerformer(Manny, Death, BloomMaterial,
        FVector(-4680, -180, 38), FRotator(0, 100, 84), FVector(1.05f), false));
    CorpsePerformers.Add(SpawnPerformer(Quinn, Death, BloomMaterial,
        FVector(1200, 45, 165), FRotator(28, 80, 68), FVector(0.95f), false));
    CorpsePerformers.Add(SpawnPerformer(Manny, Death, SuitMaterial,
        FVector(900, -55, 225), FRotator(-22, -110, 92), FVector(1.0f), false));

    RobotPerformers.Add(SpawnRobot(FVector(-1750, -900, 30), FRotator(0, 145, 0), 1.0f));
    RobotPerformers.Add(SpawnRobot(FVector(-4090, 105, 30), FRotator(0, -140, 0), 1.12f));
    RobotPerformers.Add(SpawnRobot(FVector(-4720, 230, 30), FRotator(0, -110, 0), 1.25f));
}

void ACGITrailerDirector::SpawnCinematicLighting()
{
    struct FLightDef
    {
        FVector Location;
        FColor Color;
        float Intensity;
        float Radius;
    };

    const FLightDef LightDefs[] =
    {
        { FVector(4700, -180, 225), FColor(45, 105, 255), 2600.0f, 900.0f },
        { FVector(1800, 0, 230), FColor(255, 36, 18), 2100.0f, 850.0f },
        { FVector(1080, 0, 220), FColor(45, 125, 255), 3000.0f, 680.0f },
        { FVector(0, 1250, 220), FColor(38, 170, 210), 1800.0f, 760.0f },
        { FVector(-1600, 880, 220), FColor(115, 20, 255), 2800.0f, 800.0f },
        { FVector(-1650, -900, 220), FColor(255, 64, 20), 2400.0f, 760.0f },
        { FVector(-3150, 0, 220), FColor(255, 24, 12), 3100.0f, 960.0f },
        { FVector(-4050, 0, 205), FColor(185, 18, 255), 3900.0f, 720.0f },
        { FVector(-4780, 0, 210), FColor(125, 18, 255), 6400.0f, 1100.0f },
    };

    for (const FLightDef& Def : LightDefs)
    {
        AActor* LightOwner = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), Def.Location, FRotator::ZeroRotator);
        USceneComponent* LightRoot = NewObject<USceneComponent>(LightOwner);
        LightRoot->RegisterComponent();
        LightOwner->SetRootComponent(LightRoot);
        LightOwner->SetActorLocation(Def.Location);
        UPointLightComponent* Light = NewObject<UPointLightComponent>(LightOwner);
        Light->SetupAttachment(LightRoot);
        Light->SetLightColor(Def.Color);
        Light->SetIntensity(Def.Intensity);
        Light->SetAttenuationRadius(Def.Radius);
        Light->SetCastShadows(true);
        Light->SetVolumetricScatteringIntensity(2.0f);
        Light->RegisterComponent();
        Light->ComponentTags.Add(FName(*FString::SanitizeFloat(Def.Intensity)));
        CinematicLights.Add(Light);
    }
}

void ACGITrailerDirector::SpawnReactorBloom()
{
    if (!SphereMesh || !BloomMaterial)
    {
        return;
    }

    const FVector ReactorCenter(-4800, 0, 125);
    for (int32 Index = 0; Index < 34; ++Index)
    {
        const float Angle = Index * 2.399963f;
        const float Radius = 55.0f + (Index % 7) * 38.0f;
        const FVector Offset(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, (Index % 9) * 34.0f - 120.0f);
        AStaticMeshActor* Spore = GetWorld()->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), ReactorCenter + Offset, FRotator::ZeroRotator);
        if (!Spore)
        {
            continue;
        }
        Spore->GetStaticMeshComponent()->SetStaticMesh(SphereMesh);
        Spore->GetStaticMeshComponent()->SetMaterial(0, BloomMaterial);
        Spore->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Spore->SetActorScale3D(FVector(0.04f + (Index % 4) * 0.018f));
        Spore->Tags.Add(FName(*FString::FromInt(Index)));
        BloomSpores.Add(Spore);
    }

    // Concentric infected machinery around the reactor gives the finale a readable 3D core.
    for (int32 Ring = 0; Ring < 3; ++Ring)
    {
        AActor* Core = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), ReactorCenter + FVector(0, 0, Ring * 75 - 65), FRotator::ZeroRotator);
        USceneComponent* CoreRoot = NewObject<USceneComponent>(Core);
        CoreRoot->RegisterComponent();
        Core->SetRootComponent(CoreRoot);
        Core->SetActorLocation(ReactorCenter + FVector(0, 0, Ring * 75 - 65));
        AddRobotPart(Core, CylinderMesh, FVector::ZeroVector,
            FVector(1.0f + Ring * 0.48f, 1.0f + Ring * 0.48f, 0.18f), FRotator::ZeroRotator,
            Ring == 1 ? BloomMaterial : HullMaterial);
        RobotPerformers.Add(Core);
    }
}

void ACGITrailerDirector::SetCameraPose(const FVector& Location, const FVector& LookAt, float FOV, float Roll)
{
    if (!Camera)
    {
        return;
    }
    FRotator Rotation = (LookAt - Location).Rotation();
    Rotation.Roll += Roll;
    Camera->SetActorLocationAndRotation(Location, Rotation);
    if (UCameraComponent* CameraComponent = Camera->GetCameraComponent())
    {
        CameraComponent->SetFieldOfView(FOV);
    }
}

void ACGITrailerDirector::UpdateCamera(float T)
{
    FVector Location;
    FVector Target;
    float FOV = 68.0f;
    float Roll = 0.0f;

    if (T < 3.5f)
    {
        const float A = T / 3.5f;
        Location = Glide(FVector(2320, -82, 172), FVector(1720, -68, 145), A);
        Target = Glide(FVector(1180, 0, 115), FVector(720, 0, 105), A);
        FOV = FMath::Lerp(76.0f, 64.0f, Ease(A));
    }
    else if (T < 7.0f)
    {
        const float A = (T - 3.5f) / 3.5f;
        Location = Glide(FVector(2500, -105, 145), FVector(900, -82, 130), A);
        Target = PlayerPerformer ? PlayerPerformer->GetActorLocation() + FVector(0, 0, 105) : FVector(1000, 0, 110);
        FOV = 78.0f;
        Roll = FMath::Sin(T * 11.0f) * 0.8f;
    }
    else if (T < 10.5f)
    {
        const float A = (T - 7.0f) / 3.5f;
        Location = Glide(FVector(520, 1120, 170), FVector(-340, 1210, 112), A);
        Target = FVector(-60, 1390, 72);
        FOV = FMath::Lerp(70.0f, 55.0f, Ease(A));
    }
    else if (T < 14.0f)
    {
        const float A = (T - 10.5f) / 3.5f;
        Location = Glide(FVector(-1120, 700, 160), FVector(-1460, 770, 138), A);
        Target = FVector(-1710, 900, 118);
        FOV = FMath::Lerp(64.0f, 48.0f, Ease(A));
        Roll = FMath::Sin(T * 1.8f) * 1.2f;
    }
    else if (T < 17.5f)
    {
        const float A = (T - 14.0f) / 3.5f;
        Location = Glide(FVector(-1750, -475, 160), FVector(-1750, -590, 132), A);
        Target = FVector(-1750, -900, 150);
        FOV = FMath::Lerp(68.0f, 52.0f, Ease(A));
    }
    else if (T < 23.5f)
    {
        const float A = (T - 17.5f) / 6.0f;
        Location = Glide(FVector(-4020, -145, 158), FVector(-4050, -118, 128), A);
        Target = FVector(-4040, 5, 105);
        FOV = 88.0f + FMath::Sin(T * 2.0f) * 2.0f;
        Roll = FMath::Sin(T * 16.0f) * 1.1f;
    }
    else if (T < 27.0f)
    {
        const float A = (T - 23.5f) / 3.5f;
        Location = Glide(FVector(2200, -82, 235), FVector(1550, -65, 210), A);
        Target = FVector(1030, 0, 175);
        FOV = 76.0f;
        Roll = FMath::Lerp(-8.0f, 28.0f, Ease(A));
    }
    else if (T < 32.0f)
    {
        const float A = (T - 27.0f) / 5.0f;
        Location = Glide(FVector(-4800, -445, 175), FVector(-4800, -235, 132), A);
        Target = FVector(-4800, 0, 145);
        FOV = FMath::Lerp(72.0f, 54.0f, Ease(A));
        Roll = FMath::Sin(T * 1.3f) * 1.4f;
    }
    else
    {
        const float A = (T - 32.0f) / 2.0f;
        Location = Glide(FVector(-4950, -285, 142), FVector(-4950, -185, 112), A);
        Target = FVector(-4940, 25, 120);
        FOV = FMath::Lerp(58.0f, 42.0f, Ease(A));
        Roll = FMath::Sin(T * 12.0f) * 1.7f;
    }

    const float Handheld = (T > 3.5f && T < 23.5f) ? 1.0f : 0.35f;
    Location += FVector(0, FMath::Sin(T * 5.7f) * Handheld, FMath::Sin(T * 7.1f) * Handheld * 0.7f);
    SetCameraPose(Location, Target, FOV, Roll);
}

void ACGITrailerDirector::UpdateCast(float T)
{
    if (PlayerPerformer)
    {
        if (T >= 3.25f && T < 7.25f)
        {
            const float A = Ease((T - 3.25f) / 4.0f);
            PlayerPerformer->SetActorHiddenInGame(false);
            PlayerPerformer->SetActorLocation(FMath::Lerp(FVector(2180, 0, 20), FVector(420, 0, 20), A));
            PlayerPerformer->SetActorRotation(FRotator(0, 180, 0));
        }
        else if (T >= 17.25f && T < 23.75f)
        {
            if (!bCombatAnimationSet && CombatAnimation && PlayerPerformer->GetSkeletalMeshComponent())
            {
                PlayerPerformer->GetSkeletalMeshComponent()->PlayAnimation(CombatAnimation, true);
                bCombatAnimationSet = true;
            }
            PlayerPerformer->SetActorHiddenInGame(false);
            PlayerPerformer->SetActorLocation(FVector(-3970 + FMath::Sin(T * 4.0f) * 18.0f, -25, 20));
            PlayerPerformer->SetActorRotation(FRotator(0, 180 + FMath::Sin(T * 2.0f) * 7.0f, 0));
        }
        else
        {
            PlayerPerformer->SetActorHiddenInGame(true);
        }
    }

    if (PlayerWeapon && PlayerPerformer && !PlayerPerformer->IsHidden() && T >= 17.25f)
    {
        const FVector Forward = PlayerPerformer->GetActorForwardVector();
        PlayerWeapon->SetActorHiddenInGame(false);
        PlayerWeapon->SetActorLocation(PlayerPerformer->GetActorLocation() + FVector(0, 0, 112) + Forward * 34.0f);
        PlayerWeapon->SetActorRotation(PlayerPerformer->GetActorRotation() + FRotator(0, 0, -4));
    }
    else if (PlayerWeapon)
    {
        PlayerWeapon->SetActorHiddenInGame(true);
    }

    for (int32 Index = 0; Index < InfectedPerformers.Num(); ++Index)
    {
        ASkeletalMeshActor* Infected = InfectedPerformers[Index];
        if (!Infected)
        {
            continue;
        }
        const FVector Base = Index == 0 ? FVector(-1710, 900, 20)
            : Index == 1 ? FVector(-4050, 40, 20)
            : Index == 2 ? FVector(-4120, -70, 20)
            : FVector(-4950, 30, 20);
        Infected->SetActorLocation(Base + FVector(0, FMath::Sin(T * (2.1f + Index * 0.3f)) * 16.0f, FMath::Sin(T * 3.0f + Index) * 4.0f));
        Infected->SetActorRotation(Infected->GetActorRotation() + FRotator(0, FMath::Sin(T * 2.6f + Index) * 0.18f, 0));
    }

    for (int32 Index = 0; Index < RobotPerformers.Num(); ++Index)
    {
        if (AActor* Robot = RobotPerformers[Index])
        {
            const FRotator BaseRotation = Robot->GetActorRotation();
            Robot->SetActorRotation(FRotator(BaseRotation.Pitch,
                BaseRotation.Yaw + FMath::Sin(T * 2.2f + Index) * 0.22f,
                FMath::Sin(T * 3.1f + Index) * 1.4f));
        }
    }

    for (int32 Index = 0; Index < CorpsePerformers.Num(); ++Index)
    {
        if (Index >= 3 && CorpsePerformers[Index])
        {
            ASkeletalMeshActor* Floating = CorpsePerformers[Index];
            FVector Location = Floating->GetActorLocation();
            Location.Z += FMath::Sin(T * 0.7f + Index) * 0.35f;
            Floating->SetActorLocation(Location);
            Floating->AddActorLocalRotation(FRotator(0.03f, 0.08f, 0.05f));
        }
    }

    for (int32 Index = 0; Index < BloomSpores.Num(); ++Index)
    {
        if (AActor* Spore = BloomSpores[Index])
        {
            FVector Location = Spore->GetActorLocation();
            Location.Z += (0.18f + (Index % 5) * 0.035f);
            if (Location.Z > 430.0f)
            {
                Location.Z = -20.0f;
            }
            Location.X += FMath::Sin(T * 1.6f + Index) * 0.08f;
            Spore->SetActorLocation(Location);
        }
    }
}

void ACGITrailerDirector::UpdateLighting(float T)
{
    for (int32 Index = 0; Index < CinematicLights.Num(); ++Index)
    {
        UPointLightComponent* Light = CinematicLights[Index];
        if (!Light)
        {
            continue;
        }
        const float Pulse = 0.72f + 0.28f * FMath::Sin(T * (3.0f + Index * 0.31f) + Index);
        const float EmergencyStrobe = (Index == 1 || Index == 5) ? (FMath::Frac(T * 1.8f) < 0.12f ? 1.8f : 0.75f) : 1.0f;
        const float BaseIntensity = Index < 3 ? 2300.0f : (Index > 7 ? 1800.0f : 3200.0f);
        Light->SetIntensity(BaseIntensity * Pulse * EmergencyStrobe);
    }
}

void ACGITrailerDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bActivated)
    {
        return;
    }

    ElapsedSeconds += DeltaSeconds;
    if (!bTimelineStarted)
    {
        const FString TriggerPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Demo"), TEXT("StartCGITrailer.trigger"));
        if (CVarCGITrailerStart.GetValueOnGameThread() > 0 || IFileManager::Get().FileExists(*TriggerPath) || ElapsedSeconds >= StartDelaySeconds)
        {
            bTimelineStarted = true;
            ElapsedSeconds = 0.0f;
        }
        else
        {
            UpdateCast(0.0f);
            UpdateLighting(0.0f);
            UpdateCamera(0.0f);
            return;
        }
    }

    const float TrailerTime = ElapsedSeconds;
    UpdateCast(TrailerTime);
    UpdateLighting(TrailerTime);
    UpdateCamera(TrailerTime);

    if (TrailerTime > TrailerDurationSeconds + 1.0f && FParse::Param(FCommandLine::Get(), TEXT("CGITrailerAutoQuit")))
    {
        if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
        {
            PC->ConsoleCommand(TEXT("quit"));
        }
    }
}
