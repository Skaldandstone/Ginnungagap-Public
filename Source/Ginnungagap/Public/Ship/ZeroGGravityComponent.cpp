#include "ZeroGGravityComponent.h"
#include "ShipPropulsionSubsystem.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"

UZeroGGravityComponent::UZeroGGravityComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UZeroGGravityComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    ACharacter* OwnerCharacter = Cast<ACharacter>(GetOwner());
    if (!OwnerCharacter)
    {
        return;
    }

    UCharacterMovementComponent* MovementComponent = OwnerCharacter->GetCharacterMovement();
    if (!MovementComponent)
    {
        return;
    }

    UWorld* World = GetWorld();
    UShipPropulsionSubsystem* Propulsion = World ? World->GetSubsystem<UShipPropulsionSubsystem>() : nullptr;
    if (!Propulsion)
    {
        return;
    }

    if (Propulsion->IsShipThrusting())
    {
        const FVector PseudoGravity = Propulsion->GetPseudoGravity();
        MovementComponent->SetGravityDirection(PseudoGravity.GetSafeNormal());
        MovementComponent->GravityScale = PseudoGravity.Size() * GravityScalePerAcceleration;

        if (!bUnderPseudoGravity)
        {
            MovementComponent->SetMovementMode(MOVE_Walking);
            bUnderPseudoGravity = true;
        }
    }
    else if (bUnderPseudoGravity)
    {
        MovementComponent->GravityScale = 0.0f;
        MovementComponent->SetMovementMode(MOVE_Flying);
        bUnderPseudoGravity = false;
    }
}
