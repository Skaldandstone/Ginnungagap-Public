#include "InteractionComponent.h"
#include "../Interfaces/Interactable.h"
#include "GameFramework/Pawn.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "UI/UiSoundSubsystem.h"

UInteractionComponent::UInteractionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    SetIsReplicatedByDefault(true);
}

void UInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    UpdateFocusedInteractable();
}

void UInteractionComponent::UpdateFocusedInteractable()
{
    // Written as a single assignment at the end rather than early returns, because what the sound
    // below needs is the *transition*, and a function with three exits has nowhere to compare from.
    AActor* Previous = FocusedInteractable;
    AActor* Found = nullptr;

    APawn* OwnerPawn = Cast<APawn>(GetOwner());
    if (OwnerPawn)
    {
        FVector EyeLocation;
        FRotator EyeRotation;
        OwnerPawn->GetActorEyesViewPoint(EyeLocation, EyeRotation);

        // The eye sits at the visor, a step ahead of the capsule, and a bench or console close
        // enough to touch can have its collision around the eye already: a trace that starts
        // inside a body never hits it. Start from behind the eye, inside the capsule (the pawn
        // itself is ignored), so what is right in front still comes up.
        const FVector TraceStart = EyeLocation;
        const FVector TraceEnd = EyeLocation + EyeRotation.Vector() * InteractionRange;

        FHitResult Hit;
        FCollisionQueryParams QueryParams;
        QueryParams.AddIgnoredActor(OwnerPawn);
        // The pawn's own attachments (the MetaHuman body and face are child actors of it) are
        // the pawn too; starting behind the eye, the trace would otherwise find the back of the
        // crew's own head and call that the thing in focus.
        TArray<AActor*> Attached;
        OwnerPawn->GetAttachedActors(Attached, true, true);
        QueryParams.AddIgnoredActors(Attached);

        if (GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, QueryParams))
        {
            if (Hit.GetActor() && Hit.GetActor()->Implements<UInteractable>())
            {
                Found = Hit.GetActor();
            }
        }
    }

    FocusedInteractable = Found;

    // A prompt appearing is the moment Select exists for -- the smallest sound in the palette,
    // because in a ship with thirty-two doors it fires more often than anything else.
    //
    // Three conditions, each earning its place. Found && Found != Previous, so sweeping across the
    // same console for ten seconds is one sound rather than six hundred, and looking *away* is
    // silent -- losing a prompt is not an event, and chiming on it would double every glance.
    // IsLocallyControlled, because this component ticks on the server too: without it a listen-host
    // hears a click every time any remote player looks at a door.
    if (Found && Found != Previous && OwnerPawn && OwnerPawn->IsLocallyControlled())
    {
        if (UWorld* World = GetWorld())
        {
            if (UGameInstance* GameInstance = World->GetGameInstance())
            {
                if (UUiSoundSubsystem* UiSound = GameInstance->GetSubsystem<UUiSoundSubsystem>())
                {
                    UiSound->PlayUiSound(EUiSoundEvent::Select);
                }
            }
        }
    }
}

bool UInteractionComponent::HasFocusedInteractable() const
{
    return FocusedInteractable != nullptr;
}

void UInteractionComponent::TryInteract()
{
    if (!FocusedInteractable)
    {
        return;
    }

    APawn* OwnerPawn = Cast<APawn>(GetOwner());
    if (!IsValidInteractionTarget(FocusedInteractable, OwnerPawn))
    {
        return;
    }

    if (OwnerPawn->HasAuthority())
    {
        IInteractable::Execute_OnInteract(FocusedInteractable, OwnerPawn);
    }
    else
    {
        ServerTryInteract(FocusedInteractable);
    }
}

void UInteractionComponent::ServerTryInteract_Implementation(AActor* Target)
{
    APawn* OwnerPawn = Cast<APawn>(GetOwner());
    if (IsValidInteractionTarget(Target, OwnerPawn))
    {
        IInteractable::Execute_OnInteract(Target, OwnerPawn);
    }
}

bool UInteractionComponent::IsValidInteractionTarget(const AActor* Target, const APawn* OwnerPawn) const
{
    if (!Target || !OwnerPawn || !Target->Implements<UInteractable>())
    {
        return false;
    }

    const float MaxDistance = InteractionRange + OwnerPawn->GetSimpleCollisionRadius();
    return FVector::DistSquared(Target->GetActorLocation(), OwnerPawn->GetActorLocation()) <= FMath::Square(MaxDistance);
}
