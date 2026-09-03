#include "LevelSetup/ShipCheckpointVolume.h"

#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"

AShipCheckpointVolume::AShipCheckpointVolume()
{
    PrimaryActorTick.bCanEverTick = false;
    Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
    SetRootComponent(Trigger);
    Trigger->SetBoxExtent(FVector(220.0f, 420.0f, 240.0f));
    Trigger->SetCollisionProfileName(TEXT("Trigger"));
    Trigger->OnComponentBeginOverlap.AddDynamic(this, &AShipCheckpointVolume::HandleOverlap);
}

void AShipCheckpointVolume::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep,
    const FHitResult& SweepResult)
{
    APawn* Pawn = Cast<APawn>(OtherActor);
    if (!Pawn || !Pawn->IsPlayerControlled() || bActivated)
    {
        return;
    }
    bActivated = true;
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UShipCheckpointSubsystem* Checkpoints = GameInstance->GetSubsystem<UShipCheckpointSubsystem>())
        {
            FTransform RespawnTransform = GetActorTransform();
            RespawnTransform.SetLocation(GetActorLocation() + GetActorRotation().RotateVector(RespawnOffset));
            Checkpoints->RecordCheckpoint(GetWorld(), CheckpointId, RespawnTransform);
        }
    }
    OnCheckpointReached.Broadcast(this, Pawn);
}
