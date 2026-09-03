#include "Ship/ShipPowerNodeComponent.h"
#include "Ship/ShipPowerGridSubsystem.h"
#include "Net/UnrealNetwork.h"

UShipPowerNodeComponent::UShipPowerNodeComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UShipPowerNodeComponent::BeginPlay()
{
    Super::BeginPlay();
    if (UWorld* World = GetWorld())
    {
        if (UShipPowerGridSubsystem* Grid = World->GetSubsystem<UShipPowerGridSubsystem>())
        {
            Grid->RegisterNode(this);
        }
    }
}

void UShipPowerNodeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UShipPowerGridSubsystem* Grid = World->GetSubsystem<UShipPowerGridSubsystem>())
        {
            Grid->UnregisterNode(this);
        }
    }
    Super::EndPlay(EndPlayReason);
}

void UShipPowerNodeComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UShipPowerNodeComponent, bOnline);
    DOREPLIFETIME(UShipPowerNodeComponent, DamageFraction);
    DOREPLIFETIME(UShipPowerNodeComponent, bPowered);
    DOREPLIFETIME(UShipPowerNodeComponent, AllocatedPowerUnits);
}

void UShipPowerNodeComponent::SetNodeOnline(bool bNewOnline)
{
    if (bOnline != bNewOnline)
    {
        bOnline = bNewOnline;
        NotifyGridDirty();
    }
}

void UShipPowerNodeComponent::SetDamageFraction(float NewDamageFraction)
{
    const float Clamped = FMath::Clamp(NewDamageFraction, 0.0f, 1.0f);
    if (!FMath::IsNearlyEqual(DamageFraction, Clamped))
    {
        DamageFraction = Clamped;
        NotifyGridDirty();
    }
}

float UShipPowerNodeComponent::GetEffectiveGeneration() const
{
    return bOnline && Role == EShipPowerNodeRole::Generator ? GenerationUnits * (1.0f - DamageFraction) : 0.0f;
}

float UShipPowerNodeComponent::GetEffectiveDemand() const
{
    return bOnline && Role == EShipPowerNodeRole::Consumer ? DemandUnits : 0.0f;
}

void UShipPowerNodeComponent::ApplyAllocation(float NewAllocatedPower, bool bNewPowered)
{
    const bool bChanged = bPowered != bNewPowered;
    AllocatedPowerUnits = FMath::Max(0.0f, NewAllocatedPower);
    bPowered = bNewPowered;
    if (bChanged)
    {
        OnPowerStateChanged.Broadcast(bPowered);
    }
}

void UShipPowerNodeComponent::NotifyGridDirty()
{
    if (UWorld* World = GetWorld())
    {
        if (UShipPowerGridSubsystem* Grid = World->GetSubsystem<UShipPowerGridSubsystem>())
        {
            Grid->MarkGridDirty();
        }
    }
}

void UShipPowerNodeComponent::OnRep_PowerState()
{
    OnPowerStateChanged.Broadcast(bPowered);
}

