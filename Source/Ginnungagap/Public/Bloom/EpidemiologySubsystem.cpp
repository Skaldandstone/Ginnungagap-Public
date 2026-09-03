#include "EpidemiologySubsystem.h"
#include "../Ship/ShipSection.h"
#include "../Ship/ShipNavigationSubsystem.h"
#include "PathogenLoadComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "UObject/UObjectIterator.h"

void UEpidemiologySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    if (UWorld* World = GetWorld())
    {
        World->GetTimerManager().SetTimer(StepTimerHandle, this, &UEpidemiologySubsystem::StepSimulation, StepInterval, true);
    }
}

void UEpidemiologySubsystem::Deinitialize()
{
    if (UWorld* World = GetWorld())
    {
        World->GetTimerManager().ClearTimer(StepTimerHandle);
    }

    Super::Deinitialize();
}

void UEpidemiologySubsystem::StepSimulation()
{
    StepExposure(StepInterval);
    StepShedding(StepInterval);
    StepDiffusionAndDecay(StepInterval);
}

void UEpidemiologySubsystem::StepExposure(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>();
    if (!Navigation)
    {
        return;
    }

    for (TObjectIterator<UPathogenLoadComponent> It; It; ++It)
    {
        UPathogenLoadComponent* Component = *It;
        if (!IsValid(Component) || Component->GetWorld() != World)
        {
            continue;
        }

        AActor* Owner = Component->GetOwner();
        if (!Owner)
        {
            continue;
        }

        if (AShipSection* Section = Navigation->GetSectionContainingLocation(Owner->GetActorLocation()))
        {
            Component->ApplyExposure(Section->Contamination, DeltaTime);
        }
    }
}

void UEpidemiologySubsystem::StepShedding(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>();
    if (!Navigation)
    {
        return;
    }

    for (TObjectIterator<UPathogenLoadComponent> It; It; ++It)
    {
        UPathogenLoadComponent* Component = *It;
        if (!IsValid(Component) || Component->GetWorld() != World)
        {
            continue;
        }

        AActor* Owner = Component->GetOwner();
        if (!Owner)
        {
            continue;
        }

        const float SheddingOutput = Component->ConsumeSheddingOutput(DeltaTime);
        if (SheddingOutput <= 0.0f)
        {
            continue;
        }

        if (AShipSection* Section = Navigation->GetSectionContainingLocation(Owner->GetActorLocation()))
        {
            Section->AddContamination(SheddingOutput);
        }
    }
}

void UEpidemiologySubsystem::StepDiffusionAndDecay(float DeltaTime)
{
    TMap<AShipSection*, float> ContaminationDeltas;

    for (TObjectIterator<AShipSection> It; It; ++It)
    {
        AShipSection* Section = *It;
        if (!IsValid(Section) || Section->GetWorld() != GetWorld())
        {
            continue;
        }

        for (const FSectionConnection& Connection : Section->Connections)
        {
            if (!Connection.Target)
            {
                continue;
            }

            const float TransferRate = Section->GetTransferRateTo(Connection.Target);
            const float TransferAmount = Section->Contamination * TransferRate * Section->DiffusionRate * DeltaTime;

            if (TransferAmount <= 0.0f)
            {
                continue;
            }

            ContaminationDeltas.FindOrAdd(Section) -= TransferAmount;
            ContaminationDeltas.FindOrAdd(Connection.Target) += TransferAmount;
        }
    }

    for (const TPair<AShipSection*, float>& Delta : ContaminationDeltas)
    {
        if (Delta.Key)
        {
            Delta.Key->AddContamination(Delta.Value);
        }
    }

    for (TObjectIterator<AShipSection> It; It; ++It)
    {
        AShipSection* Section = *It;
        if (!IsValid(Section) || Section->GetWorld() != GetWorld())
        {
            continue;
        }

        Section->AddContamination(-Section->Contamination * Section->NaturalDecayRate * DeltaTime);
    }
}

void UEpidemiologySubsystem::SeedOutbreak(AShipSection* Section, float Amount)
{
    if (Section)
    {
        Section->AddContamination(Amount);
    }
}
