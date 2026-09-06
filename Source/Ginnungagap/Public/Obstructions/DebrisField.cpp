#include "Obstructions/DebrisField.h"
#include "Components/BoxComponent.h"
#include "CoopSurvivalCharacter.h"

ADebrisField::ADebrisField()
{
    PrimaryActorTick.bCanEverTick = false;
    Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
    SetRootComponent(Volume);
    Volume->SetBoxExtent(FVector(250.0f, 200.0f, 150.0f));
    Volume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
    Volume->SetCanEverAffectNavigation(false);
    Volume->OnComponentBeginOverlap.AddDynamic(this, &ADebrisField::OnVolumeBeginOverlap);
    Volume->OnComponentEndOverlap.AddDynamic(this, &ADebrisField::OnVolumeEndOverlap);
    Tags.Add(TEXT("CorvetteDebrisField"));
}

void ADebrisField::GetEnds(FVector& OutA, FVector& OutB) const
{
    const FVector Along = GetActorForwardVector() * (Volume ? Volume->GetScaledBoxExtent().X + 120.0f : 370.0f);
    OutA = GetActorLocation() - Along;
    OutB = GetActorLocation() + Along;
}

FVector ADebrisField::FarEnd(const FVector& From) const
{
    FVector A, B;
    GetEnds(A, B);
    return FVector::DistSquared(From, A) > FVector::DistSquared(From, B) ? A : B;
}

void ADebrisField::OnVolumeBeginOverlap(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(OtherActor)) { Crew->SetInDebrisField(true); }
}

void ADebrisField::OnVolumeEndOverlap(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, int32)
{
    if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(OtherActor)) { Crew->SetInDebrisField(false); }
}
