#include "Ship/ProductionBulkheadDoor.h"
#include "Sound/SoundBase.h"
#include "Kismet/GameplayStatics.h"

#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

namespace
{
    const TCHAR* KitFrame = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_01_OUTSIDE.SM_DOOR_FRAME_01_OUTSIDE");
    const TCHAR* KitLeftLeaf = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_LEFT.SM_DOOR_01_LEFT");
    const TCHAR* KitRightLeaf = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_RIGHT.SM_DOOR_01_RIGHT");
    const TCHAR* KitLintel = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_02_UP.SM_DOOR_FRAME_02_UP");

    UStaticMeshComponent* MakePart(AActor* Owner, const TCHAR* Name, USceneComponent* Parent, bool bBlocks)
    {
        UStaticMeshComponent* Part = Owner->CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Part->SetupAttachment(Parent);
        Part->SetCollisionProfileName(bBlocks ? TEXT("BlockAll") : TEXT("NoCollision"));
        Part->SetCollisionEnabled(bBlocks ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
        // Nothing on a door cuts the navmesh: a sealed leaf is opened by whoever walks up to it,
        // so paths run through doorways and the walkers (and the route tests) deal with the leaf.
        Part->SetCanEverAffectNavigation(false);
        return Part;
    }
}

AProductionBulkheadDoor::AProductionBulkheadDoor()
{
    PrimaryActorTick.bCanEverTick = true;

    USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    // Frame and lintel never block: the wall either side of the gap already does, and a frame
    // whose collision is its bounding box would close the very opening it decorates.
    FrameMesh = MakePart(this, TEXT("FrameMesh"), SceneRoot, false);
    LintelMesh = MakePart(this, TEXT("LintelMesh"), SceneRoot, false);
    LeftPanel = MakePart(this, TEXT("LeftPanel"), SceneRoot, true);
    RightPanel = MakePart(this, TEXT("RightPanel"), SceneRoot, true);

    SealIndicator = CreateDefaultSubobject<UPointLightComponent>(TEXT("SealIndicator"));
    SealIndicator->SetupAttachment(SceneRoot);
    SealIndicator->SetAttenuationRadius(220.0f);
    SealIndicator->SetIntensity(350.0f);
    SealIndicator->SetCastShadows(false);

    FrameMeshAsset = LoadObject<UStaticMesh>(nullptr, KitFrame);
    LeftLeafMeshAsset = LoadObject<UStaticMesh>(nullptr, KitLeftLeaf);
    RightLeafMeshAsset = LoadObject<UStaticMesh>(nullptr, KitRightLeaf);
    LintelMeshAsset = LoadObject<UStaticMesh>(nullptr, KitLintel);
}

void AProductionBulkheadDoor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);

    if (FrameMeshAsset)
    {
        FrameMesh->SetStaticMesh(FrameMeshAsset);
    }
    if (LintelMeshAsset)
    {
        LintelMesh->SetStaticMesh(LintelMeshAsset);
    }
    UStaticMesh* LeftAsset = LeftLeafMeshAsset ? LeftLeafMeshAsset.Get() : PanelMeshAsset.Get();
    UStaticMesh* RightAsset = RightLeafMeshAsset ? RightLeafMeshAsset.Get() : PanelMeshAsset.Get();
    if (LeftAsset)
    {
        LeftPanel->SetStaticMesh(LeftAsset);
    }
    if (RightAsset)
    {
        RightPanel->SetStaticMesh(RightAsset);
    }
    if (bApplyDoorMaterial && DoorMaterial)
    {
        for (UStaticMeshComponent* Part : {FrameMesh.Get(), LintelMesh.Get(), LeftPanel.Get(), RightPanel.Get()})
        {
            Part->SetMaterial(0, DoorMaterial);
        }
    }

    ApplyGeometry();
    SnapLeavesToState();
}

void AProductionBulkheadDoor::ApplyGeometry()
{
    const float FloorZ = FloorOffset;

    // Frame: scaled so its opening is the doorway, standing on the floor.
    float FrameTop = FloorZ + DoorwayHeight;
    float FrameWidth = DoorwayWidth;
    if (UStaticMesh* Frame = FrameMesh->GetStaticMesh())
    {
        const FBox Bounds = Frame->GetBoundingBox();
        const float ScaleX = DoorwayWidth / FrameNativeOpeningWidth;
        const float ScaleZ = DoorwayHeight / FrameNativeOpeningHeight;
        FrameMesh->SetRelativeScale3D(FVector(ScaleX, 1.0f, ScaleZ));
        FrameMesh->SetRelativeLocation(FVector(0.0f, 0.0f, FloorZ - Bounds.Min.Z * ScaleZ));
        FrameTop = FloorZ + Bounds.GetSize().Z * ScaleZ;
        FrameWidth = Bounds.GetSize().X * ScaleX;
    }

    // Lintel: from the frame top to the ceiling, as wide as the frame.
    const float CeilingZ = FloorZ + CeilingHeight;
    if (UStaticMesh* Lintel = LintelMesh->GetStaticMesh())
    {
        const FBox Bounds = Lintel->GetBoundingBox();
        const float Span = CeilingZ - FrameTop;
        const float Height = FMath::Max(1.0f, Bounds.GetSize().Z);
        const float Width = FMath::Max(1.0f, Bounds.GetSize().X);
        if (Span > 2.0f)
        {
            const float ScaleZ = Span / Height;
            LintelMesh->SetVisibility(true);
            LintelMesh->SetRelativeScale3D(FVector(FrameWidth / Width, 1.0f, ScaleZ));
            LintelMesh->SetRelativeLocation(FVector(0.0f, 0.0f, CeilingZ - Bounds.Max.Z * ScaleZ));
        }
        else
        {
            LintelMesh->SetVisibility(false);
        }
    }

    // Leaves: each covers half the opening plus a centimetre so the meeting line has no daylight,
    // with its outer edge on the jamb. Travel is its own width plus the margin.
    const float HalfSpan = DoorwayWidth * 0.5f + 1.0f;
    LeafOpenTravel = HalfSpan + LeafSlideMargin;
    auto Fit = [&](UStaticMeshComponent* Leaf, bool bLeft, float& OutClosedX)
    {
        UStaticMesh* Mesh = Leaf->GetStaticMesh();
        if (!Mesh)
        {
            return;
        }
        const FBox Bounds = Mesh->GetBoundingBox();
        const float Width = FMath::Max(1.0f, Bounds.GetSize().X);
        const float Height = FMath::Max(1.0f, Bounds.GetSize().Z);
        const float ScaleX = HalfSpan / Width;
        const float ScaleZ = DoorwayHeight / Height;
        Leaf->SetRelativeScale3D(FVector(ScaleX, 1.0f, ScaleZ));
        OutClosedX = bLeft
            ? -DoorwayWidth * 0.5f - Bounds.Min.X * ScaleX
            : DoorwayWidth * 0.5f - Bounds.Max.X * ScaleX;
        LeafZ = FloorZ - Bounds.Min.Z * ScaleZ;
    };
    Fit(LeftPanel, true, LeftClosedX);
    Fit(RightPanel, false, RightClosedX);

    SealIndicator->SetRelativeLocation(FVector(0.0f, 40.0f, FrameTop + 30.0f));
}

FVector AProductionBulkheadDoor::LeafTarget(bool bLeft) const
{
    const float Travel = IsPassable() ? LeafOpenTravel : 0.0f;
    return bLeft
        ? FVector(LeftClosedX - Travel, 0.0f, LeafZ)
        : FVector(RightClosedX + Travel, 0.0f, LeafZ);
}

void AProductionBulkheadDoor::SnapLeavesToState()
{
    LeftPanel->SetRelativeLocation(LeafTarget(true));
    RightPanel->SetRelativeLocation(LeafTarget(false));
    const ECollisionEnabled::Type Collision = IsPassable() ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics;
    LeftPanel->SetCollisionEnabled(Collision);
    RightPanel->SetCollisionEnabled(Collision);
}

void AProductionBulkheadDoor::BeginPlay()
{
    Super::BeginPlay();
    // The leaf layout (closed X, travel, Z) is derived in construction and never saved, so a door
    // loaded from a level would otherwise snap its leaves to Z 0: half under the deck, where
    // nothing in front of the doorway could be looked at or blocked. Derive it again from the
    // saved settings before taking the state.
    ApplyGeometry();
    // A door begins in its state, not sliding into it.
    SnapLeavesToState();
}

float AProductionBulkheadDoor::GetLeafOpenFraction() const
{
    if (LeafOpenTravel <= KINDA_SMALL_NUMBER)
    {
        return IsPassable() ? 1.0f : 0.0f;
    }
    return FMath::Clamp(FMath::Abs(LeftPanel->GetRelativeLocation().X - LeftClosedX) / LeafOpenTravel, 0.0f, 1.0f);
}

namespace
{
    // The door's own voice: a servo close and open from the SciFiWorld pack, played where the door
    // is, only when the state actually changes (a restore that re-applies the same state is silent).
    void PlayDoorSound(const AActor* Door, bool bClosing)
    {
        if (!Door || !Door->GetWorld() || !Door->GetWorld()->IsGameWorld()) return;
        USoundBase* Sound = LoadObject<USoundBase>(nullptr, bClosing
            ? TEXT("/Game/SciFiWorld/Audio/S_SciFiDoorClose01_Cue.S_SciFiDoorClose01_Cue")
            : TEXT("/Game/SciFiWorld/Audio/S_SciFiDoorOpen01_Cue.S_SciFiDoorOpen01_Cue"));
        if (Sound)
        {
            UGameplayStatics::PlaySoundAtLocation(Door, Sound, Door->GetActorLocation() + FVector(0.0f, 0.0f, 120.0f), 0.8f);
        }
    }
}

void AProductionBulkheadDoor::Seal()
{
    const bool bWasSealed = bIsSealed;
    Super::Seal();
    if (!bWasSealed && bIsSealed && HasActorBegunPlay()) PlayDoorSound(this, true);
    SetActorTickEnabled(true);
}

void AProductionBulkheadDoor::Unseal()
{
    const bool bWasSealed = bIsSealed;
    Super::Unseal();
    if (bWasSealed && !bIsSealed && HasActorBegunPlay()) PlayDoorSound(this, false);
    SetActorTickEnabled(true);
}

void AProductionBulkheadDoor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    // Interpolate until the leaves are home, then snap and stop ticking. VInterpTo only ever
    // approaches its target, and a leaf that is still "moving" by a hundredth of a centimetre is a
    // navigation-relevant component dirtying its tile every frame -- across 96 doors that was a
    // navmesh rebuild storm that starved the game thread and hung the walkthrough test. Seal and
    // Unseal turn ticking back on; the leaves move for their two seconds and the door goes quiet.
    const FVector LeftGoal = LeafTarget(true);
    const FVector RightGoal = LeafTarget(false);
    const FVector LeftNow = FMath::VInterpTo(LeftPanel->GetRelativeLocation(), LeftGoal, DeltaSeconds, VisualMoveSpeed);
    const FVector RightNow = FMath::VInterpTo(RightPanel->GetRelativeLocation(), RightGoal, DeltaSeconds, VisualMoveSpeed);
    const bool bSettled = FVector::DistSquared(LeftNow, LeftGoal) < 0.25f && FVector::DistSquared(RightNow, RightGoal) < 0.25f;
    LeftPanel->SetRelativeLocation(bSettled ? LeftGoal : LeftNow);
    RightPanel->SetRelativeLocation(bSettled ? RightGoal : RightNow);
    if (bSettled)
    {
        SetActorTickEnabled(false);
    }

    // The leaves stop being a wall the moment the door starts to open, and become one again the
    // moment it starts to close: a player sliding through a half-open door is the door working.
    const ECollisionEnabled::Type Collision = IsPassable() ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics;
    if (LeftPanel->GetCollisionEnabled() != Collision)
    {
        LeftPanel->SetCollisionEnabled(Collision);
        RightPanel->SetCollisionEnabled(Collision);
    }

    SealIndicator->SetLightColor(bIsCorrupted ? FLinearColor(0.4f, 0.02f, 0.7f)
        : (bIsSealed ? FLinearColor(0.8f, 0.02f, 0.01f) : FLinearColor(0.02f, 0.65f, 0.12f)));
}
