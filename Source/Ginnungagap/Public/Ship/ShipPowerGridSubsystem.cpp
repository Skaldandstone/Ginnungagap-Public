#include "Ship/ShipPowerGridSubsystem.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "Stats/Stats.h"

void UShipPowerGridSubsystem::Tick(float DeltaTime)
{
    RecalculateGrid(DeltaTime);
}

TStatId UShipPowerGridSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UShipPowerGridSubsystem, STATGROUP_Tickables);
}

void UShipPowerGridSubsystem::RegisterNode(UShipPowerNodeComponent* Node)
{
    if (Node) { Nodes.AddUnique(Node); bGridDirty = true; }
}

void UShipPowerGridSubsystem::UnregisterNode(UShipPowerNodeComponent* Node)
{
    Nodes.Remove(Node);
    bGridDirty = true;
}

void UShipPowerGridSubsystem::RecalculateGrid(float DeltaTime)
{
    Nodes.RemoveAll([](const TObjectPtr<UShipPowerNodeComponent>& Node) { return !IsValid(Node); });
    if (!bGridDirty && DeltaTime <= 0.0f) { return; }

    BusSnapshots.Reset();
    TMap<FName, TArray<UShipPowerNodeComponent*>> NodesByBus;
    for (UShipPowerNodeComponent* Node : Nodes)
    {
        if (Node) { NodesByBus.FindOrAdd(Node->BusId).Add(Node); }
    }

    for (TPair<FName, TArray<UShipPowerNodeComponent*>>& BusPair : NodesByBus)
    {
        FShipPowerBusSnapshot Snapshot;
        Snapshot.BusId = BusPair.Key;
        TArray<UShipPowerNodeComponent*> Consumers;
        TArray<UShipPowerNodeComponent*> Storage;

        for (UShipPowerNodeComponent* Node : BusPair.Value)
        {
            if (Node->Role == EShipPowerNodeRole::Generator)
            {
                Snapshot.Generation += Node->GetEffectiveGeneration();
                Node->ApplyAllocation(0.0f, Node->bOnline);
            }
            else if (Node->Role == EShipPowerNodeRole::Storage)
            {
                Storage.Add(Node);
                Snapshot.StoredPower += Node->StoredPowerUnits;
            }
            else
            {
                Consumers.Add(Node);
                Snapshot.Demand += Node->GetEffectiveDemand();
            }
        }

        Consumers.Sort([](const UShipPowerNodeComponent& A, const UShipPowerNodeComponent& B) { return A.Priority < B.Priority; });
        float Available = Snapshot.Generation;
        if (Available < Snapshot.Demand && DeltaTime > 0.0f)
        {
            float Deficit = Snapshot.Demand - Available;
            for (UShipPowerNodeComponent* Battery : Storage)
            {
                if (!Battery->bOnline || Deficit <= 0.0f) { continue; }
                const float Discharged = FMath::Min3(Battery->StoredPowerUnits, Battery->MaxDischargeRate * DeltaTime, Deficit);
                Battery->StoredPowerUnits -= Discharged;
                Available += Discharged;
                Deficit -= Discharged;
            }
        }

        for (UShipPowerNodeComponent* Consumer : Consumers)
        {
            const float Demand = Consumer->GetEffectiveDemand();
            const float Allocated = FMath::Min(Available, Demand);
            const bool bPowered = Demand <= KINDA_SMALL_NUMBER || Allocated + KINDA_SMALL_NUMBER >= Demand * Consumer->MinimumPowerFraction;
            Consumer->ApplyAllocation(Allocated, bPowered);
            Available -= Allocated;
            Snapshot.ServedDemand += Allocated;
            if (!bPowered) { ++Snapshot.UnpoweredConsumers; }
        }

        if (Available > 0.0f && DeltaTime > 0.0f)
        {
            for (UShipPowerNodeComponent* Battery : Storage)
            {
                if (!Battery->bOnline || Available <= 0.0f) { continue; }
                const float CapacityRemaining = FMath::Max(0.0f, Battery->StorageCapacityUnits - Battery->StoredPowerUnits);
                const float Charged = FMath::Min3(CapacityRemaining, Battery->MaxChargeRate * DeltaTime, Available);
                Battery->StoredPowerUnits += Charged;
                Available -= Charged;
            }
        }

        Snapshot.StoredPower = 0.0f;
        for (UShipPowerNodeComponent* Battery : Storage)
        {
            Snapshot.StoredPower += Battery->StoredPowerUnits;
            Battery->ApplyAllocation(0.0f, Battery->bOnline && Battery->StoredPowerUnits > KINDA_SMALL_NUMBER);
        }
        BusSnapshots.Add(BusPair.Key, Snapshot);
    }
    bGridDirty = false;
}

FShipPowerBusSnapshot UShipPowerGridSubsystem::GetBusSnapshot(FName BusId) const
{
    if (const FShipPowerBusSnapshot* Snapshot = BusSnapshots.Find(BusId)) { return *Snapshot; }
    FShipPowerBusSnapshot Empty; Empty.BusId = BusId; return Empty;
}

TArray<FShipPowerBusSnapshot> UShipPowerGridSubsystem::GetAllBusSnapshots() const
{
    TArray<FShipPowerBusSnapshot> Result;
    BusSnapshots.GenerateValueArray(Result);
    return Result;
}

