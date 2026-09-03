#include "StarSystem/PelagosArrivalGateVolume.h"

#include "Components/BoxComponent.h"
#include "EngineUtils.h"
#include "StarSystem/PelagosOrbitalArrivalDirector.h"

APelagosArrivalGateVolume::APelagosArrivalGateVolume()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(false);

    TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
    RootComponent = TriggerVolume;
    TriggerVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TriggerVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    TriggerVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    TriggerVolume->SetCollisionResponseToChannel(ECC_Vehicle, ECR_Overlap);
    TriggerVolume->SetGenerateOverlapEvents(true);
}

void APelagosArrivalGateVolume::BeginPlay()
{
    Super::BeginPlay();
    TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &APelagosArrivalGateVolume::HandleBeginOverlap);
}

void APelagosArrivalGateVolume::SetGateEnabled(bool bEnabled)
{
    TriggerVolume->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
}

void APelagosArrivalGateVolume::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!HasAuthority() || !OtherActor || (!RequiredActorTag.IsNone() && !OtherActor->ActorHasTag(RequiredActorTag)))
    {
        return;
    }

    APelagosOrbitalArrivalDirector* Director = ResolveDirector();
    if (!Director || Director->ArrivalState != RequiredState)
    {
        return;
    }

    bool bSucceeded = false;
    switch (Action)
    {
    case EPelagosGateAction::AdvanceState:
        bSucceeded = Director->AdvanceArrivalState();
        break;
    case EPelagosGateAction::RequestDock:
        bSucceeded = Director->RequestDock(DockId, false, false);
        break;
    case EPelagosGateAction::BeginFinalApproach:
        bSucceeded = Director->BeginFinalApproach(RouteId);
        break;
    case EPelagosGateAction::ConfirmSoftCapture:
        bSucceeded = Director->ConfirmSoftCapture(DockId);
        break;
    case EPelagosGateAction::ConfirmHardDock:
        bSucceeded = Director->ConfirmHardDock(DockId);
        break;
    case EPelagosGateAction::ReleaseDock:
        bSucceeded = Director->ReleaseDock(DockId);
        break;
    }

    if (bSucceeded)
    {
        OnGateTriggered.Broadcast(GateId, OtherActor);
        if (bDisableAfterSuccess)
        {
            SetGateEnabled(false);
        }
    }
}

APelagosOrbitalArrivalDirector* APelagosArrivalGateVolume::ResolveDirector() const
{
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<APelagosOrbitalArrivalDirector> It(World); It; ++It)
        {
            return *It;
        }
    }
    return nullptr;
}
