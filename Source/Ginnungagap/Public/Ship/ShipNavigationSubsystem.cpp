#include "ShipNavigationSubsystem.h"
#include "ShipSection.h"
#include "BulkheadDoor.h"
#include "../../Ginnungagap.h"
#include "TimerManager.h"
#include "Engine/World.h"

void UShipNavigationSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);

    InWorld.GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UShipNavigationSubsystem::ValidateSectionConnections));
}

void UShipNavigationSubsystem::ValidateSectionConnections() const
{
    for (const AShipSection* Section : AllSections)
    {
        if (!Section)
        {
            continue;
        }

        for (const FSectionConnection& Connection : Section->Connections)
        {
            const AShipSection* Target = Connection.Target;
            if (!Target)
            {
                continue;
            }

            const FSectionConnection* Reciprocal = nullptr;
            for (const FSectionConnection& Candidate : Target->Connections)
            {
                if (Candidate.Target == Section)
                {
                    Reciprocal = &Candidate;
                    break;
                }
            }

            if (!Reciprocal)
            {
                UE_LOG(LogGinnungagap, Warning,
                    TEXT("ShipSection connection %s -> %s is one-way: %s has no connection entry pointing back to %s."),
                    *Section->GetName(), *Target->GetName(), *Target->GetName(), *Section->GetName());
                continue;
            }

            if (Connection.Door != Reciprocal->Door)
            {
                UE_LOG(LogGinnungagap, Warning,
                    TEXT("ShipSection connection %s <-> %s references different doors (%s vs %s): sealing will not be symmetric."),
                    *Section->GetName(), *Target->GetName(),
                    Connection.Door ? *Connection.Door->GetName() : TEXT("None"),
                    Reciprocal->Door ? *Reciprocal->Door->GetName() : TEXT("None"));
            }
        }
    }
}

void UShipNavigationSubsystem::RegisterSection(AShipSection* Section)
{
    if (Section)
    {
        AllSections.AddUnique(Section);
    }
}

void UShipNavigationSubsystem::UnregisterSection(AShipSection* Section)
{
    AllSections.Remove(Section);
}

AShipSection* UShipNavigationSubsystem::GetSectionContainingLocation(const FVector& Location) const
{
    for (AShipSection* Section : AllSections)
    {
        if (Section && Section->ContainsPoint(Location))
        {
            return Section;
        }
    }
    return nullptr;
}

bool UShipNavigationSubsystem::FindSectionPath(AShipSection* Start, AShipSection* End, TArray<AShipSection*>& OutPath, bool bRespectSealedDoors) const
{
    OutPath.Reset();

    if (!Start || !End)
    {
        return false;
    }

    if (Start == End)
    {
        OutPath.Add(Start);
        return true;
    }

    TMap<AShipSection*, AShipSection*> CameFrom;
    TArray<AShipSection*> Queue;
    Queue.Add(Start);
    CameFrom.Add(Start, nullptr);

    bool bFound = false;
    int32 QueueIndex = 0;
    while (QueueIndex < Queue.Num())
    {
        AShipSection* Current = Queue[QueueIndex++];
        if (Current == End)
        {
            bFound = true;
            break;
        }

        for (const FSectionConnection& Connection : Current->Connections)
        {
            AShipSection* Neighbor = Connection.Target;
            if (!Neighbor || CameFrom.Contains(Neighbor))
            {
                continue;
            }

            if (!Current->IsTraversableTo(Neighbor, bRespectSealedDoors))
            {
                continue;
            }

            CameFrom.Add(Neighbor, Current);
            Queue.Add(Neighbor);
        }
    }

    if (!bFound)
    {
        return false;
    }

    AShipSection* Step = End;
    while (Step)
    {
        OutPath.Insert(Step, 0);
        Step = CameFrom.FindRef(Step);
    }

    return true;
}
