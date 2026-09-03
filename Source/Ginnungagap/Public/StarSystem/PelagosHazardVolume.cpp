#include "StarSystem/PelagosHazardVolume.h"

#include "Components/BoxComponent.h"
#include "Kismet/GameplayStatics.h"

APelagosHazardVolume::APelagosHazardVolume()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.1f;
    bReplicates = true;
    SetReplicateMovement(false);

    HazardBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("HazardBounds"));
    RootComponent = HazardBounds;
    HazardBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    HazardBounds->SetCollisionResponseToAllChannels(ECR_Overlap);
}

void APelagosHazardVolume::BeginPlay()
{
    Super::BeginPlay();
    HazardBounds->SetBoxExtent(Definition.Extent);
    HazardBounds->OnComponentBeginOverlap.AddDynamic(this, &APelagosHazardVolume::HandleBeginOverlap);
    HazardBounds->OnComponentEndOverlap.AddDynamic(this, &APelagosHazardVolume::HandleEndOverlap);
}

void APelagosHazardVolume::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!HasAuthority() || Definition.DamagePerSecond <= 0.0f)
    {
        return;
    }

    DamageAccumulator += DeltaSeconds;
    if (DamageAccumulator < DamageInterval)
    {
        return;
    }

    const float AppliedDamage = Definition.DamagePerSecond * DamageAccumulator;
    DamageAccumulator = 0.0f;
    for (auto It = OverlappingActors.CreateIterator(); It; ++It)
    {
        if (AActor* Actor = It->Get())
        {
            UGameplayStatics::ApplyDamage(Actor, AppliedDamage, nullptr, this, nullptr);
        }
        else
        {
            It.RemoveCurrent();
        }
    }
}

void APelagosHazardVolume::HandleBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (OtherActor && OtherActor != this)
    {
        OverlappingActors.Add(OtherActor);
        OnHazardEntered.Broadcast(Definition.HazardId, OtherActor);
    }
}

void APelagosHazardVolume::HandleEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex)
{
    if (OtherActor)
    {
        OverlappingActors.Remove(OtherActor);
        OnHazardExited.Broadcast(Definition.HazardId, OtherActor);
    }
}
