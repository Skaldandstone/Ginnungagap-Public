#include "StatusEffects/PlayerHallucinationActor.h"

#include "Components/StaticMeshComponent.h"

APlayerHallucinationActor::APlayerHallucinationActor()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = false;
    SetActorEnableCollision(false);
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HallucinationVisual"));
    RootComponent = VisualMesh;
    VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    VisualMesh->SetGenerateOverlapEvents(false);
    VisualMesh->SetCastShadow(false);
}

void APlayerHallucinationActor::Configure(EPlayerHallucinationType Type, float Severity, float LifetimeSeconds)
{
    HallucinationSeverity = FMath::Clamp(Severity, 0.0f, 1.0f);
    TotalLifetimeSeconds = FMath::Max(0.25f, LifetimeSeconds);
    const TCHAR* MeshPath = Type == EPlayerHallucinationType::BloomGrowth
        ? TEXT("/Game/Assets/Models/Bloom/Expansion/SM_Bloom_FloorGrowth.SM_Bloom_FloorGrowth")
        : (Type == EPlayerHallucinationType::PhantomMovement
            ? TEXT("/Game/Assets/Models/Bloom/SM_Bloom_Crawler_Proxy.SM_Bloom_Crawler_Proxy")
            : TEXT("/Game/Assets/Models/Bloom/SM_Bloom_Puppeteer_Proxy.SM_Bloom_Puppeteer_Proxy"));
    VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, MeshPath));
    const float Scale = FMath::Lerp(0.65f, 1.15f, HallucinationSeverity);
    SetActorScale3D(FVector(Scale));
    SetLifeSpan(TotalLifetimeSeconds);
}

void APlayerHallucinationActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    AgeSeconds += DeltaTime;
    const float LifeAlpha = FMath::Clamp(AgeSeconds / TotalLifetimeSeconds, 0.0f, 1.0f);
    const bool bVisible = LifeAlpha < 0.72f || FMath::Sin(AgeSeconds * 31.0f) > FMath::Lerp(0.8f, -0.15f, HallucinationSeverity);
    VisualMesh->SetVisibility(bVisible);
    AddActorWorldOffset(GetActorForwardVector() * DeltaTime * FMath::Lerp(0.0f, 85.0f, HallucinationSeverity), false);
}
