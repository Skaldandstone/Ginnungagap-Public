#include "PathogenLoadComponent.h"
#include "BloomDirector.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Net/UnrealNetwork.h"

UPathogenLoadComponent::UPathogenLoadComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(true);
}

void UPathogenLoadComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UPathogenLoadComponent, InfectionState);
    DOREPLIFETIME(UPathogenLoadComponent, PathogenLoad);
}

void UPathogenLoadComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    TickInfectionProgress(DeltaTime);
}

void UPathogenLoadComponent::ApplyExposure(float Concentration, float DeltaTime)
{
    if (InfectionState == EInfectionState::Symptomatic)
    {
        return;
    }

    const float EffectiveConcentration = Concentration * (1.0f - Resistance);
    if (EffectiveConcentration <= 0.0f)
    {
        return;
    }

    AccumulatedDose += EffectiveConcentration * DeltaTime;

    if (InfectionState == EInfectionState::Clean && AccumulatedDose > 0.0f)
    {
        InfectionState = EInfectionState::Exposed;
    }

    if (InfectionState == EInfectionState::Exposed && AccumulatedDose >= InfectiousDoseThreshold)
    {
        InfectionState = EInfectionState::Incubating;
        PathogenLoad = FMath::Max(PathogenLoad, 1.0f);
    }
}

void UPathogenLoadComponent::TickInfectionProgress(float DeltaTime)
{
    if (InfectionState != EInfectionState::Incubating && InfectionState != EInfectionState::Symptomatic)
    {
        return;
    }

    if (SubstrateQuality > 0.0f)
    {
        PathogenLoad += ReplicationRate * PathogenLoad * (1.0f - PathogenLoad / SubstrateQuality) * DeltaTime;
        PathogenLoad = FMath::Clamp(PathogenLoad, 0.0f, SubstrateQuality);
    }

    if (InfectionState == EInfectionState::Incubating && PathogenLoad >= SymptomaticThreshold)
    {
        InfectionState = EInfectionState::Symptomatic;
        OnBecameSymptomatic.Broadcast();

        AActor* Owner = GetOwner();
        UWorld* World = GetWorld();
        if (Owner && World && World->GetGameInstance())
        {
            if (UBloomDirector* Director = World->GetGameInstance()->GetSubsystem<UBloomDirector>())
            {
                if (Director->GetCurrentStage() >= EBloomStage::Puppeteer)
                {
                    Director->TryInfectHost(Owner);
                }
            }
        }
    }
}

float UPathogenLoadComponent::ConsumeSheddingOutput(float DeltaTime)
{
    if (InfectionState != EInfectionState::Incubating && InfectionState != EInfectionState::Symptomatic)
    {
        return 0.0f;
    }

    return PathogenLoad * SheddingRate * DeltaTime;
}

void UPathogenLoadComponent::PurgeInfection()
{
    InfectionState = EInfectionState::Clean;
    AccumulatedDose = 0.0f;
    PathogenLoad = 0.0f;
}
