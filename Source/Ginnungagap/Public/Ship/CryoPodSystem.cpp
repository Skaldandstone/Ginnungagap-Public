#include "CryoPodSystem.h"
#include "../CoopSurvivalCharacter.h"
#include "../Bloom/BloomDirector.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "StatusEffects/PlayerPsychosisComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Curves/CurveFloat.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

ACryoPodSystem::ACryoPodSystem()
{
    // Full-body pod envelope is authored in centimeters to match Unreal character scale.
    PrimaryActorTick.bCanEverTick = true;
    SystemType = EShipSystemType::Cryo;
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;

    USceneComponent* NeutralRoot = CreateDefaultSubobject<USceneComponent>(TEXT("NeutralRoot"));
    SetRootComponent(NeutralRoot);
    PodRakePivot = CreateDefaultSubobject<USceneComponent>(TEXT("PodRakePivot"));
    PodRakePivot->SetupAttachment(NeutralRoot);
    VisualMesh->SetupAttachment(PodRakePivot);

    LidPivot = CreateDefaultSubobject<USceneComponent>(TEXT("LidPivot"));
    LidPivot->SetupAttachment(PodRakePivot);
    // Matches the baked-in canted hinge center from the generated base assets.
    LidPivot->SetRelativeLocation(FVector(0.0f, -125.0f, 164.0f));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedBaseFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Base.SM_CryoPod_GS_Base"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedBedFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Bed.SM_CryoPod_GS_Bed"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedDetailsFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Details.SM_CryoPod_GS_Details"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedHingeFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_HingeFinal.SM_CryoPod_GS_HingeFinal"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedRestraintsFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Restraints.SM_CryoPod_GS_Restraints"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedStatusLightsFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_StatusLights.SM_CryoPod_GS_StatusLights"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedFrameFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidFrame.SM_CryoPod_GS_LidFrame"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> GeneratedGlassFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidGlass.SM_CryoPod_GS_LidGlass"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> FrameMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_WornGunmetal.M_Cryo_WornGunmetal"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GlassMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_CrackedFrostGlass.M_Cryo_CrackedFrostGlass"));

    // Eleven cryo materials were authored for this pod and two of them were being used -- the lid
    // frame and the lid glass. The other six components had no material assigned at all, so they
    // rendered in the engine default and the pod read as flat plastic in every shot of the room
    // the demo opens on.
    //
    // The names map onto the components almost exactly, which is the giveaway that they were made
    // for this and then never wired: OiledBlackHull for the shell, RestraintCushion for the berth
    // and the straps, WornGunmetal for the trim and the hinge, and three status colours for a
    // panel that had none.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> HullMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_OiledBlackHull.M_Cryo_OiledBlackHull"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> CushionMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_RestraintCushion.M_Cryo_RestraintCushion"));

    // The three status colours. Held on the class rather than looked up each refresh: constructor
    // finders are the only sanctioned way to load in a constructor, and RefreshStatusLights runs
    // whenever the pod changes state.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ThawMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_ThawCyan.M_Cryo_ThawCyan"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> IdleMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_AmberPractical.M_Cryo_AmberPractical"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> FaultMaterialFinder(
        TEXT("/Game/Assets/ShipRooms/Cryo/M_Cryo_FaultRed.M_Cryo_FaultRed"));

    StatusOccupiedMaterial = ThawMaterialFinder.Succeeded() ? ThawMaterialFinder.Object : nullptr;
    StatusIdleMaterial = IdleMaterialFinder.Succeeded() ? IdleMaterialFinder.Object : nullptr;
    StatusFaultMaterial = FaultMaterialFinder.Succeeded() ? FaultMaterialFinder.Object : nullptr;

    if (GeneratedBaseFinder.Succeeded())
    {
        VisualMesh->SetStaticMesh(GeneratedBaseFinder.Object);
    if (HullMaterialFinder.Succeeded()) VisualMesh->SetMaterial(0, HullMaterialFinder.Object);
        VisualMesh->SetCollisionProfileName(TEXT("BlockAll"));
    }

    BedInsert = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BedInsert"));
    BedInsert->SetupAttachment(PodRakePivot);
    BedInsert->SetStaticMesh(GeneratedBedFinder.Succeeded() ? GeneratedBedFinder.Object : CubeFinder.Object);
    if (CushionMaterialFinder.Succeeded()) BedInsert->SetMaterial(0, CushionMaterialFinder.Object);
    BedInsert->SetCollisionProfileName(TEXT("BlockAll"));

    DetailTrim = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DetailTrim"));
    DetailTrim->SetupAttachment(PodRakePivot);
    DetailTrim->SetStaticMesh(GeneratedDetailsFinder.Succeeded() ? GeneratedDetailsFinder.Object : CubeFinder.Object);
    if (FrameMaterialFinder.Succeeded()) DetailTrim->SetMaterial(0, FrameMaterialFinder.Object);
    DetailTrim->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    HingeAssembly = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HingeAssembly"));
    HingeAssembly->SetupAttachment(PodRakePivot);
    HingeAssembly->SetStaticMesh(GeneratedHingeFinder.Succeeded() ? GeneratedHingeFinder.Object : CubeFinder.Object);
    if (FrameMaterialFinder.Succeeded()) HingeAssembly->SetMaterial(0, FrameMaterialFinder.Object);
    HingeAssembly->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    Restraints = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Restraints"));
    Restraints->SetupAttachment(PodRakePivot);
    Restraints->SetStaticMesh(GeneratedRestraintsFinder.Succeeded() ? GeneratedRestraintsFinder.Object : CubeFinder.Object);
    if (CushionMaterialFinder.Succeeded()) Restraints->SetMaterial(0, CushionMaterialFinder.Object);
    Restraints->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    StatusLights = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StatusLights"));
    StatusLights->SetupAttachment(PodRakePivot);
    StatusLights->SetStaticMesh(GeneratedStatusLightsFinder.Succeeded() ? GeneratedStatusLightsFinder.Object : CubeFinder.Object);
    StatusLights->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // Set here as well as on every state change, so a pod that is never interacted with still
    // shows the right colour rather than the engine default.
    RefreshStatusLights();

    LidFrame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LidFrame"));
    LidFrame->SetupAttachment(LidPivot);
    LidFrame->SetStaticMesh(GeneratedFrameFinder.Succeeded() ? GeneratedFrameFinder.Object : CubeFinder.Object);
    LidFrame->SetRelativeLocation(FVector::ZeroVector);
    LidFrame->SetRelativeScale3D(GeneratedFrameFinder.Succeeded() ? FVector::OneVector : FVector(1.82f, 0.18f, 3.05f));
    LidFrame->SetCollisionProfileName(TEXT("BlockAll"));
    if (FrameMaterialFinder.Succeeded()) LidFrame->SetMaterial(0, FrameMaterialFinder.Object);

    LidGlass = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LidGlass"));
    LidGlass->SetupAttachment(LidPivot);
    LidGlass->SetStaticMesh(GeneratedGlassFinder.Succeeded() ? GeneratedGlassFinder.Object : CubeFinder.Object);
    LidGlass->SetRelativeLocation(FVector::ZeroVector);
    LidGlass->SetRelativeScale3D(GeneratedGlassFinder.Succeeded() ? FVector::OneVector : FVector(1.48f, 0.035f, 2.65f));
    LidGlass->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    if (GlassMaterialFinder.Succeeded()) LidGlass->SetMaterial(0, GlassMaterialFinder.Object);

    // The Fab stasis pod, if it has been imported (tools/import_fab_cryo_stasis_pod.py). Its mesh
    // is centred, 200 cm tall, door on its -Y; stood on the actor origin and turned so the door
    // faces +X. It replaces every generated part of the pod's look.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> VerticalPodFinder(
        TEXT("/Game/Fab_CryoStasisPod/Meshes/SM_CryoStasisPod.SM_CryoStasisPod"));
    VerticalPod = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VerticalPod"));
    VerticalPod->SetupAttachment(RootComponent);
    VerticalPod->SetRelativeLocation(FVector(0.0f, 0.0f, 100.0f));
    VerticalPod->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    VerticalPod->SetCollisionProfileName(TEXT("BlockAll"));
    if (VerticalPodFinder.Succeeded())
    {
        VerticalPod->SetStaticMesh(VerticalPodFinder.Object);
        for (UStaticMeshComponent* Generated : { VisualMesh.Get(), BedInsert.Get(), DetailTrim.Get(), HingeAssembly.Get(),
            Restraints.Get(), StatusLights.Get(), LidFrame.Get(), LidGlass.Get() })
        {
            if (Generated)
            {
                Generated->SetVisibility(false, true);
                Generated->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    else
    {
        VerticalPod->SetVisibility(false);
        VerticalPod->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }

    PodRakePivot->SetRelativeLocation(FVector(0.0f, 0.0f, PodRakeLift));
    PodRakePivot->SetRelativeRotation(FRotator(0.0f, 0.0f, PodRakeAngle));
    // Shut by default. A bay where every lid stands open reads as already evacuated -- an open pod
    // means somebody got out of it, and four open pods claim four people did.
    //
    // It is also most of the room's art problem: an open lid presents a large oval of
    // M_Cryo_CrackedFrostGlass to the camera, and with four of them the glass was the brightest,
    // bluest thing in frame by a wide margin. No light colour could out-vote it.
    //
    // bLidOpen is EditAnywhere, so a level opens the pods its story needs opened. TryEnterPod still
    // closes and ExitPod still opens, so the mechanism is unchanged -- only the resting state is.
    bLidOpen = false;
    LidAnimationAlpha = 0.0f;
    ApplyLidPose();
}

bool ACryoPodSystem::UsesVerticalPod() const
{
    return VerticalPod && VerticalPod->GetStaticMesh() != nullptr;
}

void ACryoPodSystem::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    PodRakePivot->SetRelativeLocation(FVector(0.0f, 0.0f, PodRakeLift));
    PodRakePivot->SetRelativeRotation(FRotator(0.0f, 0.0f, PodRakeAngle));
    ApplyLidPose();
}

void ACryoPodSystem::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float TargetAlpha = bLidOpen ? 1.0f : 0.0f;
    const float AnimationRate = 1.0f / FMath::Max(LidAnimationDuration, KINDA_SMALL_NUMBER);
    LidAnimationAlpha = FMath::FInterpConstantTo(
        LidAnimationAlpha, TargetAlpha, DeltaSeconds, AnimationRate);
    ApplyLidPose();
    OnLidMotionProgress.Broadcast(LidAnimationAlpha, bLidOpen);

    if (FMath::IsNearlyEqual(LidAnimationAlpha, TargetAlpha, KINDA_SMALL_NUMBER))
    {
        LidAnimationAlpha = TargetAlpha;
        ApplyLidPose();
        SetActorTickEnabled(false);
        OnLidMotionFinished.Broadcast(bLidOpen);
    }
}

void ACryoPodSystem::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(ACryoPodSystem, bLidOpen);
}

bool ACryoPodSystem::TryEnterPod(ACoopSurvivalCharacter* Character)
{
    if (!Character || bIsOccupied || !IsFunctioning())
    {
        return false;
    }

    bIsOccupied = true;
    RefreshStatusLights();
    OccupyingCharacter = Character;
    SetLidOpen(false);
    Character->OxygenLevelPercent = FMath::Max(Character->OxygenLevelPercent, 50.0f);
    if (UPlayerStatusEffectComponent* StatusEffects = Character->GetStatusEffectComponent())
    {
        StatusEffects->RemoveStatusEffect(EPlayerStatusEffect::Hypoxia);
        StatusEffects->TreatStatusEffect(EPlayerStatusEffect::SpaceMotionSickness, 0.5f);
        StatusEffects->TreatStatusEffect(EPlayerStatusEffect::JumpPsychosis, 0.25f);
    }
    Character->ClientApplyPsychosisGrounding(30.0f, 0.1f);
    return true;
}

void ACryoPodSystem::ExitPod()
{
    bIsOccupied = false;
    RefreshStatusLights();
    OccupyingCharacter = nullptr;
    SetLidOpen(true);
}

void ACryoPodSystem::SetLidOpen(bool bOpen)
{
    if (bLidOpen == bOpen && FMath::IsNearlyEqual(LidAnimationAlpha, bOpen ? 1.0f : 0.0f))
    {
        return;
    }

    bLidOpen = bOpen;
    if (LidAnimationDuration <= KINDA_SMALL_NUMBER)
    {
        OnLidMotionStarted.Broadcast(bLidOpen);
        LidAnimationAlpha = bLidOpen ? 1.0f : 0.0f;
        ApplyLidPose();
        OnLidMotionProgress.Broadcast(LidAnimationAlpha, bLidOpen);
        OnLidMotionFinished.Broadcast(bLidOpen);
        SetActorTickEnabled(false);
        return;
    }

    BeginLidMotion();
    ForceNetUpdate();
}

void ACryoPodSystem::OnRep_LidOpen()
{
    BeginLidMotion();
}

void ACryoPodSystem::BeginLidMotion()
{
    SetActorTickEnabled(true);
    OnLidMotionStarted.Broadcast(bLidOpen);
}

void ACryoPodSystem::ApplyLidPose()
{
    if (!LidPivot)
    {
        return;
    }

    // The optional artist curve overrides the SmoothStep fallback while the
    // generated lid keeps its hinge-local authored pivot.
    const float EasedAlpha = LidAnimationCurve
        ? FMath::Clamp(LidAnimationCurve->GetFloatValue(LidAnimationAlpha), 0.0f, 1.0f)
        : FMath::SmoothStep(0.0f, 1.0f, LidAnimationAlpha);
    const float LidAngle = FMath::Lerp(-90.0f, LidOpenAngle, EasedAlpha);
    LidPivot->SetRelativeRotation(FRotator(0.0f, 0.0f, LidAngle));
}

void ACryoPodSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (bIsCorrupted)
    {
        if (!bIsRepairing)
        {
            bIsRepairing = true;
            GetWorldTimerManager().SetTimer(RepairTimerHandle, this, &ACryoPodSystem::FinishRepair, RepairDuration, false);
        }
        return;
    }

    ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(InteractingPawn);
    if (!Character)
    {
        return;
    }

    if (bIsOccupied && OccupyingCharacter.Get() == Character)
    {
        ExitPod();
    }
    else
    {
        TryEnterPod(Character);
    }
}

FText ACryoPodSystem::GetInteractionPrompt_Implementation(APawn* Viewer) const
{
    // What the pod offers, in words: the HUD otherwise falls back to the actor's label, and
    // "CVT_CRYOPOD_01" is a placement name, not a thing a crew member reads off a tube.
    if (bIsCorrupted)
    {
        return bIsRepairing ? NSLOCTEXT("CryoPod", "Repairing", "Repairing cryo pod...")
                            : NSLOCTEXT("CryoPod", "Repair", "Repair cryo pod");
    }
    if (bIsOccupied)
    {
        return OccupyingCharacter.Get() == Viewer ? NSLOCTEXT("CryoPod", "Leave", "Leave cryo pod")
                                                  : NSLOCTEXT("CryoPod", "Occupied", "Cryo pod (occupied)");
    }
    return NSLOCTEXT("CryoPod", "Enter", "Enter cryo pod");
}

void ACryoPodSystem::FinishRepair()
{
    bIsRepairing = false;

    if (!bIsCorrupted)
    {
        return;
    }

    Execute_OnBloomPurged(this);

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            Director->NotifySystemPurged(this);
        }
    }
}

void ACryoPodSystem::RefreshStatusLights()
{
    if (!StatusLights)
    {
        return;
    }

    // Corruption outranks occupancy: a pod that has failed reads as failed whether or not somebody
    // is still in it, which is the more urgent thing for a player crossing the bay to notice.
    UMaterialInterface* Wanted = bIsCorrupted
        ? StatusFaultMaterial
        : (bIsOccupied ? StatusOccupiedMaterial : StatusIdleMaterial);

    if (Wanted)
    {
        StatusLights->SetMaterial(0, Wanted);
    }
}

void ACryoPodSystem::ApplyCorruptionEffects()
{
    // Occupant fate is resolved by UJumpSequenceSubsystem at jump time, not here.
    RefreshStatusLights();
}

void ACryoPodSystem::RemoveCorruptionEffects()
{
    RefreshStatusLights();
}
