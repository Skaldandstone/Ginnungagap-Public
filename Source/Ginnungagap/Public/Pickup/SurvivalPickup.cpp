// Copyright Epic Games, Inc. All Rights Reserved.

#include "SurvivalPickup.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "CoopSurvivalCharacter.h"

ASurvivalPickup::ASurvivalPickup()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;

    CollisionSphere = CreateDefaultSubobject<USphereComponent>(TEXT("CollisionSphere"));
    RootComponent = CollisionSphere;
    CollisionSphere->InitSphereRadius(50.0f);
    CollisionSphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    CollisionSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
    CollisionSphere->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    CollisionSphere->OnComponentBeginOverlap.AddDynamic(this, &ASurvivalPickup::OnOverlap);
    VisualMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("VisualMesh"));
    VisualMesh->SetupAttachment(CollisionSphere);
    VisualMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void ASurvivalPickup::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (VisualMesh && !VisualMesh->GetStaticMesh())
    {
        const TCHAR* Path = PickupType == EPickupType::Oxygen
            ? TEXT("/Game/Assets/Models/Pickups/SM_Pickup_OxygenCanister.SM_Pickup_OxygenCanister")
            : TEXT("/Game/Assets/Models/Pickups/SM_Pickup_MedicalInjector.SM_Pickup_MedicalInjector");
        VisualMesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Path));
    }
}

void ASurvivalPickup::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(ASurvivalPickup, PickupType);
    DOREPLIFETIME(ASurvivalPickup, Amount);
}

void ASurvivalPickup::BeginPlay()
{
    Super::BeginPlay();
}

void ASurvivalPickup::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}
UFUNCTION()
void ASurvivalPickup::OnOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    ACoopSurvivalCharacter* PlayerCharacter = Cast<ACoopSurvivalCharacter>(OtherActor);
    if (!PlayerCharacter)
    {
        return;
    }

    if (PickupType == EPickupType::Oxygen)
    {
        PlayerCharacter->OxygenLevelPercent = FMath::Clamp(PlayerCharacter->OxygenLevelPercent + Amount, 0.0f, 100.0f);
    }
    else if (PickupType == EPickupType::Health)
    {
        PlayerCharacter->HealthPercent = FMath::Clamp(PlayerCharacter->HealthPercent + Amount, 0.0f, 100.0f);
    }

    Destroy();
}
