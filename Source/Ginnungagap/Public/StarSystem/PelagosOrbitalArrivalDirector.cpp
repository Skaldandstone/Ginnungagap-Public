#include "StarSystem/PelagosOrbitalArrivalDirector.h"

#include "Net/UnrealNetwork.h"

APelagosOrbitalArrivalDirector::APelagosOrbitalArrivalDirector()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(false);
}

void APelagosOrbitalArrivalDirector::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority())
    {
        DockStates.Init(EPelagosDockState::Available, ArrivalDefinition ? ArrivalDefinition->Docks.Num() : 0);
        if (ArrivalDefinition)
        {
            for (int32 Index = 0; Index < ArrivalDefinition->Docks.Num(); ++Index)
            {
                if (ArrivalDefinition->Docks[Index].bEmergencyDock)
                {
                    DockStates[Index] = EPelagosDockState::EmergencyOnly;
                }
            }
        }
    }
}

void APelagosOrbitalArrivalDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(APelagosOrbitalArrivalDirector, ArrivalState);
    DOREPLIFETIME(APelagosOrbitalArrivalDirector, ReservedDockId);
    DOREPLIFETIME(APelagosOrbitalArrivalDirector, ActiveRouteId);
    DOREPLIFETIME(APelagosOrbitalArrivalDirector, DockStates);
}

void APelagosOrbitalArrivalDirector::NotifyJumpArrival(const FStarSystemData& SystemData)
{
    if (!HasAuthority() || !ArrivalDefinition || !ArrivalDefinition->bAutoStartOnJumpArrival)
    {
        return;
    }

    if (!ArrivalDefinition->DestinationId.IsNone()
        && !SystemData.DisplayName.IsEmpty()
        && !SystemData.DisplayName.Contains(ArrivalDefinition->DestinationId.ToString(), ESearchCase::IgnoreCase))
    {
        return;
    }

    if (ArrivalState != EPelagosArrivalState::Inactive && ArrivalState != EPelagosArrivalState::Departure)
    {
        return;
    }

    SetArrivalState(EPelagosArrivalState::JumpExit);
}

bool APelagosOrbitalArrivalDirector::AdvanceArrivalState()
{
    if (!HasAuthority())
    {
        return false;
    }

    const EPelagosArrivalState NextState = ArrivalState == EPelagosArrivalState::Departure
        ? EPelagosArrivalState::JumpExit
        : static_cast<EPelagosArrivalState>(static_cast<uint8>(ArrivalState) + 1);
    if (!IsValidStateTransition(ArrivalState, NextState))
    {
        return false;
    }

    SetArrivalState(NextState);
    return true;
}

bool APelagosOrbitalArrivalDirector::RequestDock(FName RequestedDockId, bool bLargeShip, bool bEmergency)
{
    if (!HasAuthority() || !ArrivalDefinition || !ReservedDockId.IsNone())
    {
        return false;
    }

    auto CanUseDock = [&](int32 Index)
    {
        if (!DockStates.IsValidIndex(Index) || !ArrivalDefinition->Docks.IsValidIndex(Index))
        {
            return false;
        }
        const FPelagosDockDefinition& Dock = ArrivalDefinition->Docks[Index];
        const EPelagosDockState State = DockStates[Index];
        const bool bStateAllowsUse = State == EPelagosDockState::Available || (bEmergency && State == EPelagosDockState::EmergencyOnly);
        return bStateAllowsUse && (!bLargeShip || Dock.bSupportsLargeShips) && (!Dock.bEmergencyDock || bEmergency);
    };

    int32 DockIndex = RequestedDockId.IsNone() ? INDEX_NONE : FindDockIndex(RequestedDockId);
    if (DockIndex == INDEX_NONE)
    {
        for (int32 Index = 0; Index < ArrivalDefinition->Docks.Num(); ++Index)
        {
            if (CanUseDock(Index))
            {
                DockIndex = Index;
                break;
            }
        }
    }

    if (!CanUseDock(DockIndex))
    {
        return false;
    }

    ReservedDockId = ArrivalDefinition->Docks[DockIndex].DockId;
    ActiveRouteId = NAME_None;
    DockStates[DockIndex] = EPelagosDockState::Reserved;
    OnDockStateChanged.Broadcast(ReservedDockId, EPelagosDockState::Reserved);
    if (ArrivalState == EPelagosArrivalState::DockRequest)
    {
        SetArrivalState(EPelagosArrivalState::DockAssignment);
    }
    return true;
}

bool APelagosOrbitalArrivalDirector::BeginFinalApproach(FName RouteId)
{
    if (!HasAuthority() || ReservedDockId.IsNone() || ArrivalState != EPelagosArrivalState::DockAssignment)
    {
        return false;
    }

    const int32 RouteIndex = FindRouteIndex(RouteId);
    if (!ArrivalDefinition || !ArrivalDefinition->Routes.IsValidIndex(RouteIndex))
    {
        return false;
    }

    ActiveRouteId = ArrivalDefinition->Routes[RouteIndex].RouteId;
    SetArrivalState(EPelagosArrivalState::FinalApproach);
    return true;
}

bool APelagosOrbitalArrivalDirector::ConfirmSoftCapture(FName DockId)
{
    const int32 Index = FindDockIndex(DockId);
    if (!HasAuthority() || DockId != ReservedDockId || ArrivalState != EPelagosArrivalState::FinalApproach
        || !DockStates.IsValidIndex(Index) || DockStates[Index] != EPelagosDockState::Reserved)
    {
        return false;
    }

    SetArrivalState(EPelagosArrivalState::SoftCapture);
    return true;
}

bool APelagosOrbitalArrivalDirector::ConfirmHardDock(FName DockId)
{
    const int32 Index = FindDockIndex(DockId);
    if (!HasAuthority() || DockId != ReservedDockId || ArrivalState != EPelagosArrivalState::SoftCapture
        || !DockStates.IsValidIndex(Index) || DockStates[Index] != EPelagosDockState::Reserved)
    {
        return false;
    }
    DockStates[Index] = EPelagosDockState::Occupied;
    OnDockStateChanged.Broadcast(DockId, EPelagosDockState::Occupied);
    SetArrivalState(EPelagosArrivalState::HardDock);
    return true;
}

bool APelagosOrbitalArrivalDirector::ReleaseDock(FName DockId)
{
    const int32 Index = FindDockIndex(DockId);
    if (!HasAuthority() || !ArrivalDefinition || DockId != ReservedDockId
        || !DockStates.IsValidIndex(Index) || !ArrivalDefinition->Docks.IsValidIndex(Index))
    {
        return false;
    }
    DockStates[Index] = ArrivalDefinition->Docks[Index].bEmergencyDock ? EPelagosDockState::EmergencyOnly : EPelagosDockState::Available;
    ReservedDockId = NAME_None;
    ActiveRouteId = NAME_None;
    OnDockStateChanged.Broadcast(DockId, DockStates[Index]);
    SetArrivalState(EPelagosArrivalState::Departure);
    return true;
}

EPelagosDockState APelagosOrbitalArrivalDirector::GetDockState(FName DockId) const
{
    const int32 Index = FindDockIndex(DockId);
    return DockStates.IsValidIndex(Index) ? DockStates[Index] : EPelagosDockState::Faulted;
}

bool APelagosOrbitalArrivalDirector::GetDockDefinition(FName DockId, FPelagosDockDefinition& OutDock) const
{
    const int32 Index = FindDockIndex(DockId);
    if (!ArrivalDefinition || !ArrivalDefinition->Docks.IsValidIndex(Index))
    {
        return false;
    }
    OutDock = ArrivalDefinition->Docks[Index];
    return true;
}

bool APelagosOrbitalArrivalDirector::GetRouteDefinition(FName RouteId, FPelagosArrivalRouteDefinition& OutRoute) const
{
    const int32 Index = FindRouteIndex(RouteId);
    if (!ArrivalDefinition || !ArrivalDefinition->Routes.IsValidIndex(Index))
    {
        return false;
    }
    OutRoute = ArrivalDefinition->Routes[Index];
    return true;
}

bool APelagosOrbitalArrivalDirector::SetDockOperationalState(FName DockId, EPelagosDockState NewState)
{
    const int32 Index = FindDockIndex(DockId);
    if (!HasAuthority() || !DockStates.IsValidIndex(Index)
        || NewState == EPelagosDockState::Reserved || NewState == EPelagosDockState::Occupied
        || DockId == ReservedDockId)
    {
        return false;
    }
    DockStates[Index] = NewState;
    OnDockStateChanged.Broadcast(DockId, NewState);
    ForceNetUpdate();
    return true;
}

bool APelagosOrbitalArrivalDirector::IsValidStateTransition(EPelagosArrivalState From, EPelagosArrivalState To)
{
    if (From == EPelagosArrivalState::Departure && To == EPelagosArrivalState::JumpExit)
    {
        return true;
    }
    return static_cast<uint8>(To) == static_cast<uint8>(From) + 1;
}

void APelagosOrbitalArrivalDirector::OnRep_ArrivalState(EPelagosArrivalState PreviousState)
{
    OnArrivalStateChanged.Broadcast(PreviousState, ArrivalState);
}

void APelagosOrbitalArrivalDirector::SetArrivalState(EPelagosArrivalState NewState)
{
    if (ArrivalState == NewState)
    {
        return;
    }
    const EPelagosArrivalState PreviousState = ArrivalState;
    ArrivalState = NewState;
    OnArrivalStateChanged.Broadcast(PreviousState, NewState);
    ForceNetUpdate();
}

int32 APelagosOrbitalArrivalDirector::FindDockIndex(FName DockId) const
{
    if (!ArrivalDefinition)
    {
        return INDEX_NONE;
    }
    return ArrivalDefinition->Docks.IndexOfByPredicate([DockId](const FPelagosDockDefinition& Dock)
    {
        return Dock.DockId == DockId;
    });
}

int32 APelagosOrbitalArrivalDirector::FindRouteIndex(FName RouteId) const
{
    if (!ArrivalDefinition)
    {
        return INDEX_NONE;
    }
    return ArrivalDefinition->Routes.IndexOfByPredicate([RouteId](const FPelagosArrivalRouteDefinition& Route)
    {
        return Route.RouteId == RouteId;
    });
}
