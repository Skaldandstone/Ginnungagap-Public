#include "ShipSection.h"
#include "Components/BoxComponent.h"
#include "BulkheadDoor.h"
#include "ShipNavigationSubsystem.h"
#include "Engine/World.h"
#include "Ship/ShipDamageComponent.h"

bool FShipGameplayHardpoint::IsValid(FString* OutError) const
{
    FString Error;
    if (HardpointId.IsNone())
    {
        Error = TEXT("Ship gameplay hardpoint requires a stable ID.");
    }
    else if (ClearanceRadius < 0.0f)
    {
        Error = FString::Printf(TEXT("Ship gameplay hardpoint %s has negative clearance."), *HardpointId.ToString());
    }

    if (OutError)
    {
        *OutError = Error;
    }
    return Error.IsEmpty();
}

AShipSection::AShipSection()
{
    PrimaryActorTick.bCanEverTick = false;

    SectionBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("SectionBounds"));
    RootComponent = SectionBounds;
    SectionBounds->SetBoxExtent(FVector(500.0f, 500.0f, 300.0f));
    SectionBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    SectionBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    DamageState = CreateDefaultSubobject<UShipDamageComponent>(TEXT("DamageState"));
}

void AShipSection::BeginPlay()
{
    Super::BeginPlay();

    if (bRegisterWithNavigation)
    {
        if (UWorld* World = GetWorld())
        {
            if (UShipNavigationSubsystem* NavSubsystem = World->GetSubsystem<UShipNavigationSubsystem>())
            {
                NavSubsystem->RegisterSection(this);
            }
        }
    }
}

void AShipSection::EndPlay(EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
    {
        if (UShipNavigationSubsystem* NavSubsystem = World->GetSubsystem<UShipNavigationSubsystem>())
        {
            NavSubsystem->UnregisterSection(this);
        }
    }

    Super::EndPlay(EndPlayReason);
}

void AShipSection::AddContamination(float Amount)
{
    Contamination = FMath::Max(0.0f, Contamination + Amount);
}

bool AShipSection::IsContaminated(float Threshold) const
{
    return Contamination > Threshold;
}

bool AShipSection::ContainsPoint(const FVector& Point) const
{
    return SectionBounds ? SectionBounds->Bounds.GetBox().IsInside(Point) : false;
}

bool AShipSection::IsConnectedTo(const AShipSection* Other) const
{
    if (!Other)
    {
        return false;
    }

    for (const FSectionConnection& Connection : Connections)
    {
        if (Connection.Target == Other)
        {
            return true;
        }
    }

    return false;
}

float AShipSection::GetTransferRateTo(const AShipSection* Other) const
{
    for (const FSectionConnection& Connection : Connections)
    {
        if (Connection.Target == Other)
        {
            if (Connection.Door)
            {
                return Connection.TransferCoefficient * Connection.Door->GetTransferMultiplier();
            }
            return Connection.TransferCoefficient;
        }
    }

    return 0.0f;
}

bool AShipSection::IsTraversableTo(const AShipSection* Other, bool bRespectSealedDoors) const
{
    for (const FSectionConnection& Connection : Connections)
    {
        if (Connection.Target == Other)
        {
            if (Connection.Door && bRespectSealedDoors)
            {
                return Connection.Door->IsPassable();
            }
            return true;
        }
    }

    return false;
}

bool AShipSection::AddGameplayHardpoint(const FShipGameplayHardpoint& Hardpoint)
{
    if (!Hardpoint.IsValid() || GameplayHardpoints.ContainsByPredicate([&Hardpoint](const FShipGameplayHardpoint& Existing)
    {
        return Existing.HardpointId == Hardpoint.HardpointId;
    }))
    {
        return false;
    }

    GameplayHardpoints.Add(Hardpoint);
    return true;
}

TArray<FShipGameplayHardpoint> AShipSection::GetGameplayHardpoints(
    EShipGameplayHardpointType HardpointType, bool bOnlyAvailable) const
{
    TArray<FShipGameplayHardpoint> Result;
    for (const FShipGameplayHardpoint& Hardpoint : GameplayHardpoints)
    {
        if (Hardpoint.HardpointType == HardpointType && (!bOnlyAvailable || !Hardpoint.bReserved))
        {
            Result.Add(Hardpoint);
        }
    }
    return Result;
}

bool AShipSection::GetGameplayHardpointWorldTransform(FName HardpointId, FTransform& OutTransform) const
{
    const FShipGameplayHardpoint* Hardpoint = GameplayHardpoints.FindByPredicate([HardpointId](const FShipGameplayHardpoint& Candidate)
    {
        return Candidate.HardpointId == HardpointId;
    });
    if (!Hardpoint)
    {
        return false;
    }

    OutTransform = FTransform(Hardpoint->RelativeRotation, Hardpoint->RelativeLocation) * GetActorTransform();
    return true;
}

bool AShipSection::SetGameplayHardpointReserved(FName HardpointId, bool bReserved)
{
    FShipGameplayHardpoint* Hardpoint = GameplayHardpoints.FindByPredicate([HardpointId](const FShipGameplayHardpoint& Candidate)
    {
        return Candidate.HardpointId == HardpointId;
    });
    if (!Hardpoint)
    {
        return false;
    }

    Hardpoint->bReserved = bReserved;
    return true;
}
