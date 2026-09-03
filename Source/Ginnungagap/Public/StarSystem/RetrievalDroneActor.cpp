#include "RetrievalDroneActor.h"
#include "ResourceNodeActor.h"
#include "ShipResourceInventorySubsystem.h"
#include "../Bloom/BloomDirector.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"

ARetrievalDroneActor::ARetrievalDroneActor()
{
    PrimaryActorTick.bCanEverTick = false;
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    RootComponent = VisualMesh;
    VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/Assets/Models/Drones/SM_Drone_Retrieval.SM_Drone_Retrieval")));
    VisualMesh->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/Assets/Materials/Production/Instances/MI_Surface_Drone.MI_Surface_Drone")));
}

bool ARetrievalDroneActor::DispatchTo(AResourceNodeActor* TargetNode, float HazardSeverity)
{
    if ((CurrentState != EDroneState::Docked && CurrentState != EDroneState::Returned) || !TargetNode || !TargetNode->bShipOnStation)
    {
        return false;
    }

    AssignedTargetNode = TargetNode;

    const float LossChance = FMath::Clamp(BaseLossChance + LossChancePerSeverity * HazardSeverity, 0.0f, 1.0f);
    bWillBeLost = FMath::FRand() < LossChance;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            Director->RegisterPlayerAction(EBloomPlayerActionType::DispatchedDrone);
        }
    }

    SetDroneState(EDroneState::OutboundTravel);
    GetWorldTimerManager().SetTimer(StateTimerHandle, this, &ARetrievalDroneActor::BeginCollecting, OutboundTravelDuration, false);
    return true;
}

void ARetrievalDroneActor::BeginCollecting()
{
    SetDroneState(EDroneState::Collecting);
    GetWorldTimerManager().SetTimer(StateTimerHandle, this, &ARetrievalDroneActor::BeginReturnTravel, CollectingDuration, false);
}

void ARetrievalDroneActor::BeginReturnTravel()
{
    SetDroneState(EDroneState::ReturnTravel);
    GetWorldTimerManager().SetTimer(StateTimerHandle, this, &ARetrievalDroneActor::FinishReturn, ReturnTravelDuration, false);
}

void ARetrievalDroneActor::FinishReturn()
{
    if (bWillBeLost)
    {
        SetDroneState(EDroneState::Lost);
        AssignedTargetNode.Reset();
        return;
    }

    if (AResourceNodeActor* Node = AssignedTargetNode.Get())
    {
        if (UGameInstance* GI = GetGameInstance())
        {
            if (UShipResourceInventorySubsystem* Inventory = GI->GetSubsystem<UShipResourceInventorySubsystem>())
            {
                Inventory->AddResource(Node->ResourceType, Node->Quantity);
            }
        }
        Node->DepleteResourceNode();
    }

    AssignedTargetNode.Reset();
    SetDroneState(EDroneState::Returned);
}

void ARetrievalDroneActor::SetDroneState(EDroneState NewState)
{
    if (CurrentState == NewState)
    {
        return;
    }
    CurrentState = NewState;
    OnDroneStateChanged.Broadcast(CurrentState);
}

float ARetrievalDroneActor::GetStateProgress() const
{
    float Duration = 0.0f;
    switch (CurrentState)
    {
    case EDroneState::OutboundTravel: Duration = OutboundTravelDuration; break;
    case EDroneState::Collecting: Duration = CollectingDuration; break;
    case EDroneState::ReturnTravel: Duration = ReturnTravelDuration; break;
    case EDroneState::Returned: return 1.0f;
    default: return 0.0f;
    }
    const float Remaining = GetWorldTimerManager().GetTimerRemaining(StateTimerHandle);
    return Duration > 0.0f ? FMath::Clamp(1.0f - Remaining / Duration, 0.0f, 1.0f) : 0.0f;
}

void ARetrievalDroneActor::RepairAndRecall()
{
    if (!HasAuthority()) return;
    GetWorldTimerManager().ClearTimer(StateTimerHandle);
    AssignedTargetNode.Reset();
    bWillBeLost = false;
    SetDroneState(EDroneState::Docked);
}
