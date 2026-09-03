#include "Ship/ShipInteractiveFixture.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"

AShipInteractiveFixture::AShipInteractiveFixture()
{
    PrimaryActorTick.bCanEverTick = false;

    FixtureMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FixtureMesh"));
    SetRootComponent(FixtureMesh);
    FixtureMesh->SetCollisionProfileName(TEXT("BlockAllDynamic"));

    StatusLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("StatusLight"));
    StatusLight->SetupAttachment(FixtureMesh);
    StatusLight->SetRelativeLocation(FVector(0.0f, -35.0f, 120.0f));
    StatusLight->SetAttenuationRadius(250.0f);
    StatusLight->SetIntensity(450.0f);
    StatusLight->SetCastShadows(false);
}

void AShipInteractiveFixture::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (FixtureMeshAsset)
    {
        FixtureMesh->SetStaticMesh(FixtureMeshAsset);
    }
    RefreshVisualState();
}

void AShipInteractiveFixture::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!CanInteractWithFixture())
    {
        return;
    }

    OnActivated.Broadcast(this);
    if (bToggleOnInteract)
    {
        SetFixtureEnabled(!bEnabled);
    }
}

void AShipInteractiveFixture::SetFixtureEnabled(bool bNewEnabled)
{
    if (bEnabled == bNewEnabled || bIsCorrupted)
    {
        return;
    }

    bEnabled = bNewEnabled;
    RefreshVisualState();
    OnStateChanged.Broadcast(this, bEnabled);
}

bool AShipInteractiveFixture::CanInteractWithFixture() const
{
    return !bLocked && !bIsCorrupted && IsOperational();
}

void AShipInteractiveFixture::ApplyCorruptionEffects()
{
    bEnabled = false;
    RefreshVisualState();
    OnStateChanged.Broadcast(this, false);
}

void AShipInteractiveFixture::RemoveCorruptionEffects()
{
    RefreshVisualState();
}

void AShipInteractiveFixture::RefreshVisualState()
{
    UMaterialInterface* DesiredMaterial = bIsCorrupted ? CorruptedMaterial : (bEnabled ? ActiveMaterial : NormalMaterial);
    if (FixtureMesh && DesiredMaterial)
    {
        FixtureMesh->SetMaterial(0, DesiredMaterial);
    }

    if (StatusLight)
    {
        const FLinearColor Color = bIsCorrupted
            ? FLinearColor(0.35f, 0.02f, 0.65f)
            : (bEnabled ? FLinearColor(0.05f, 0.55f, 1.0f) : FLinearColor(0.7f, 0.03f, 0.01f));
        StatusLight->SetLightColor(Color);
        StatusLight->SetIntensity(bEnabled || bIsCorrupted ? 450.0f : 90.0f);
    }
}
