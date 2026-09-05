#include "Activities/WeldableBulkheadDoor.h"
#include "Activities/PlayerActivityComponent.h"
#include "Net/UnrealNetwork.h"
#include "Activities/PlayerActivityComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AWeldableBulkheadDoor::AWeldableBulkheadDoor()
{
    PrimaryActorTick.bCanEverTick = true;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    WeldSeam = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeldSeam"));
    WeldSeam->SetupAttachment(RootComponent);
    WeldSeam->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WeldSeam->SetCanEverAffectNavigation(false);
    WeldSeam->SetCastShadow(false);
    WeldSeam->SetHiddenInGame(true);
    WeldArc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WeldArc"));
    WeldArc->SetupAttachment(RootComponent);
    WeldArc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WeldArc->SetCanEverAffectNavigation(false);
    WeldArc->SetCastShadow(false);
    WeldArc->SetHiddenInGame(true);
    if (Cube.Succeeded())
    {
        WeldSeam->SetStaticMesh(Cube.Object);
        WeldArc->SetStaticMesh(Cube.Object);
    }
    WeldArcLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("WeldArcLight"));
    WeldArcLight->SetupAttachment(RootComponent);
    WeldArcLight->SetIntensity(0.0f);
    WeldArcLight->SetLightColor(FLinearColor(1.0f, 0.62f, 0.28f));
    WeldArcLight->SetAttenuationRadius(520.0f);
    WeldArcLight->SetCastShadows(false);
    WeldArcLight->SetVisibility(false);

    WeldingActivity.Type = EPlayerActivityType::Welding;
    WeldingActivity.Mechanic = EActivityMechanic::ToolPath;
    WeldingActivity.DisplayName = NSLOCTEXT("Activities", "WeldDoorSeam", "Emergency seam weld");
    WeldingActivity.DurationSeconds = 8.0f;
    WeldingActivity.ToolPathTolerance = 0.22f;
    WeldingActivity.MaxRange = 220.0f;
    WeldingActivity.bBloomSensitive = true;

    // A door welded shut in an earlier emergency is not a wall: the same tool path, run the other
    // way, cuts the seam and the door is a door again.
    CuttingActivity.Type = EPlayerActivityType::Welding;
    CuttingActivity.Mechanic = EActivityMechanic::ToolPath;
    CuttingActivity.DisplayName = NSLOCTEXT("Activities", "CutDoorSeam", "Cut emergency weld");
    CuttingActivity.DurationSeconds = 10.0f;
    CuttingActivity.ToolPathTolerance = 0.22f;
    CuttingActivity.MaxRange = 220.0f;
    CuttingActivity.bBloomSensitive = true;
}

void AWeldableBulkheadDoor::BeginPlay()
{
    Super::BeginPlay();
    if (UMaterialInterface* Parent = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Assets/Ships/Production/Materials/Fx/M_WeldSeam.M_WeldSeam")))
    {
        SeamMaterial = UMaterialInstanceDynamic::Create(Parent, this);
        ArcMaterial = UMaterialInstanceDynamic::Create(Parent, this);
        if (WeldSeam) WeldSeam->SetMaterial(0, SeamMaterial);
        if (WeldArc) WeldArc->SetMaterial(0, ArcMaterial);
        if (ArcMaterial) ArcMaterial->SetScalarParameterValue(TEXT("Heat"), 1.0f);
    }
    // On a timer rather than Tick: the production door switches its own tick off between cycles.
    LastLookSeconds = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    GetWorldTimerManager().SetTimer(WeldLookTimer, this, &AWeldableBulkheadDoor::UpdateWeldLook, 0.05f, true);
    UpdateWeldLook();
}

void AWeldableBulkheadDoor::UpdateWeldLook()
{
    if (!WeldSeam || !WeldArc || !WeldArcLight || !GetWorld()) return;
    const float NowSeconds = GetWorld()->GetTimeSeconds();
    const float DeltaSeconds = FMath::Clamp(NowSeconds - LastLookSeconds, 0.0f, 0.5f);
    LastLookSeconds = NowSeconds;

    // Whoever is at work on this door, on any machine: their activity snapshot replicates.
    const FPlayerActivitySnapshot* Work = nullptr;
    for (TActorIterator<APawn> It(GetWorld()); It; ++It)
    {
        const UPlayerActivityComponent* Activity = It->FindComponentByClass<UPlayerActivityComponent>();
        if (Activity && Activity->IsActivityActive() && Activity->GetActivitySource() == this)
        {
            Work = &Activity->GetSnapshot();
            break;
        }
    }

    // The bead runs across the leaves at chest height, along the door's own width.
    const float Width = FMath::Max(DoorwayWidth - 20.0f, 60.0f);
    const float SeamZ = FloorOffset + DoorwayHeight * 0.48f;
    const bool bWelding = Work && !bWeldedShut;
    const bool bCutting = Work && bWeldedShut;
    // Welding lays the bead down as progress climbs; a welded door shows the whole bead; cutting
    // takes it away behind the torch.
    float BeadFraction = bWeldedShut ? 1.0f : 0.0f;
    if (bWelding) BeadFraction = Work->Progress;
    if (bCutting) BeadFraction = 1.0f - Work->Progress;
    const bool bShowBead = BeadFraction > 0.02f;
    WeldSeam->SetHiddenInGame(!bShowBead);
    if (bShowBead)
    {
        const float Length = Width * BeadFraction;
        // Welding grows from the hinge side; cutting shortens from the same side, so the arc is at
        // the bead's far end in both cases.
        const float StartX = -Width * 0.5f;
        WeldSeam->SetRelativeLocation(FVector(StartX + Length * 0.5f, 0.0f, SeamZ));
        WeldSeam->SetRelativeScale3D(FVector(Length / 100.0f, 0.07f, 0.05f));
    }

    if (Work)
    {
        SeamHeat = FMath::Min(1.0f, SeamHeat + DeltaSeconds * 0.8f);
        const float TipX = -Width * 0.5f + Width * (bCutting ? 1.0f - Work->Progress : Work->Progress);
        // The seam the torch is chasing wanders; the arc sits where the torch actually is.
        const float TorchZ = SeamZ + Work->ToolOffset.Y * 22.0f;
        WeldArc->SetHiddenInGame(false);
        WeldArc->SetRelativeLocation(FVector(TipX, 0.0f, TorchZ));
        WeldArc->SetRelativeScale3D(FVector(0.09f, 0.11f, 0.09f));
        const bool bOnSeam = Work->ToolAccuracy > 0.0f;
        const float Flicker = bOnSeam ? FMath::FRandRange(2600.0f, 6500.0f) * (0.5f + 0.5f * Work->ToolAccuracy) : 500.0f;
        WeldArcLight->SetVisibility(true);
        WeldArcLight->SetIntensity(Flicker);
        WeldArcLight->SetRelativeLocation(FVector(TipX, 45.0f, TorchZ));
        if (ArcMaterial) ArcMaterial->SetScalarParameterValue(TEXT("Heat"), bOnSeam ? 1.0f : 0.35f);
    }
    else
    {
        SeamHeat = FMath::Max(0.0f, SeamHeat - DeltaSeconds * 0.06f);
        WeldArc->SetHiddenInGame(true);
        WeldArcLight->SetIntensity(0.0f);
        WeldArcLight->SetVisibility(false);
    }
    if (SeamMaterial) SeamMaterial->SetScalarParameterValue(TEXT("Heat"), SeamHeat * 0.7f);
}

void AWeldableBulkheadDoor::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!InteractingPawn) return;
    if (bWeldedShut)
    {
        if (UPlayerActivityComponent* Activity = InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
            Activity->StartActivity(this, CuttingActivity);
        return;
    }
    // Close first: welding an open or moving door cannot produce a pressure seal.
    if (!bIsSealed)
    {
        if (CanBeSealed()) Seal();
        else return;
    }
    if (UPlayerActivityComponent* Activity = InteractingPawn->FindComponentByClass<UPlayerActivityComponent>())
        Activity->StartActivity(this, IPlayerActivitySource::Execute_GetActivityDefinition(this, InteractingPawn));
}

FPlayerActivityDefinition AWeldableBulkheadDoor::GetActivityDefinition_Implementation(APawn* Player) const
{
    return bWeldedShut ? CuttingActivity : WeldingActivity;
}

bool AWeldableBulkheadDoor::CanStartActivity_Implementation(APawn* Player) const
{
    if (!Player || bIsCorrupted) return false;
    return bWeldedShut || bIsSealed;
}

void AWeldableBulkheadDoor::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority()) return;
    if (bWeldedShut)
    {
        // Cut free, and open: nobody cuts a seam to leave the door shut.
        CutEmergencyWeld();
        Super::Unseal();
        return;
    }
    bWeldedShut = true;
    Seal();
    OnWeldStateChanged(true);
}

void AWeldableBulkheadDoor::CutEmergencyWeld()
{
    if (!HasAuthority() || !bWeldedShut) return;
    bWeldedShut = false;
    OnWeldStateChanged(false);
}

void AWeldableBulkheadDoor::Unseal()
{
    if (!bWeldedShut) Super::Unseal();
}

bool AWeldableBulkheadDoor::IsPassable() const { return !bWeldedShut && Super::IsPassable(); }

void AWeldableBulkheadDoor::OnRep_WeldedShut() { OnWeldStateChanged(bWeldedShut); }

void AWeldableBulkheadDoor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AWeldableBulkheadDoor, bWeldedShut);
}
