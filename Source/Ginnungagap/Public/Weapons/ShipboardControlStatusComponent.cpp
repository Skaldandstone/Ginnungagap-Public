#include "Weapons/ShipboardControlStatusComponent.h"

#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"

UShipboardControlStatusComponent::UShipboardControlStatusComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    SetIsReplicatedByDefault(true);
}

UShipboardControlStatusComponent* UShipboardControlStatusComponent::FindOrCreate(AActor* TargetActor)
{
    if (!TargetActor)
    {
        return nullptr;
    }
    if (UShipboardControlStatusComponent* Existing =
        TargetActor->FindComponentByClass<UShipboardControlStatusComponent>())
    {
        return Existing;
    }
    if (!TargetActor->HasAuthority())
    {
        return nullptr;
    }

    UShipboardControlStatusComponent* Created =
        NewObject<UShipboardControlStatusComponent>(TargetActor, UShipboardControlStatusComponent::StaticClass());
    if (!Created)
    {
        return nullptr;
    }
    Created->SetIsReplicated(true);
    TargetActor->AddInstanceComponent(Created);
    Created->RegisterComponent();
    return Created;
}

void UShipboardControlStatusComponent::BeginPlay()
{
    Super::BeginPlay();
    if (IsControlEffectActive())
    {
        if (ActiveEffect != EWeaponControlEffect::Mark)
        {
            CaptureMovementBaseline();
            SetComponentTickEnabled(true);
            EnforceMovementState();
        }
    }
}

void UShipboardControlStatusComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RestoreMovementState();
    Super::EndPlay(EndPlayReason);
}

void UShipboardControlStatusComponent::ApplyControlEffect(EWeaponControlEffect Effect,
    float DurationSeconds, float MovementMultiplier)
{
    AActor* OwnerActor = GetOwner();
    if (!OwnerActor || !OwnerActor->HasAuthority() || Effect == EWeaponControlEffect::None
        || DurationSeconds <= 0.0f)
    {
        return;
    }

    if (IsControlEffectActive() && ActiveEffect != EWeaponControlEffect::Mark)
    {
        RestoreMovementState();
    }
    if (Effect != EWeaponControlEffect::Mark)
    {
        CaptureMovementBaseline();
    }
    ActiveEffect = Effect;
    ActiveMovementMultiplier = FMath::Clamp(MovementMultiplier, 0.0f, 1.0f);
    EffectEndTimeSeconds = GetWorld()->GetTimeSeconds() + DurationSeconds;
    GetWorld()->GetTimerManager().SetTimer(
        ExpirationTimer, this, &UShipboardControlStatusComponent::ClearControlEffect,
        DurationSeconds, false);
    SetComponentTickEnabled(Effect != EWeaponControlEffect::Mark);
    EnforceMovementState();
    OnControlEffectChanged.Broadcast(ActiveEffect);
    OwnerActor->ForceNetUpdate();
}

float UShipboardControlStatusComponent::GetRemainingDurationSeconds() const
{
    return GetWorld() && IsControlEffectActive()
        ? FMath::Max(0.0f, EffectEndTimeSeconds - GetWorld()->GetTimeSeconds())
        : 0.0f;
}

void UShipboardControlStatusComponent::ClearControlEffect()
{
    if (AActor* OwnerActor = GetOwner(); OwnerActor && !OwnerActor->HasAuthority())
    {
        return;
    }
    ActiveEffect = EWeaponControlEffect::None;
    ActiveMovementMultiplier = 1.0f;
    EffectEndTimeSeconds = 0.0f;
    RestoreMovementState();
    SetComponentTickEnabled(false);
    OnControlEffectChanged.Broadcast(ActiveEffect);
    if (AActor* OwnerActor = GetOwner())
    {
        OwnerActor->ForceNetUpdate();
    }
}

void UShipboardControlStatusComponent::OnRep_ControlState()
{
    if (IsControlEffectActive())
    {
        if (ActiveEffect == EWeaponControlEffect::Mark)
        {
            RestoreMovementState();
            SetComponentTickEnabled(false);
        }
        else
        {
            CaptureMovementBaseline();
            SetComponentTickEnabled(true);
            EnforceMovementState();
        }
    }
    else
    {
        RestoreMovementState();
        SetComponentTickEnabled(false);
    }
    OnControlEffectChanged.Broadcast(ActiveEffect);
}

void UShipboardControlStatusComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (IsControlEffectActive())
    {
        EnforceMovementState();
    }
}

void UShipboardControlStatusComponent::CaptureMovementBaseline()
{
    if (!bMovementBaselineCaptured)
    {
        if (const UCharacterMovementComponent* Movement = FindCharacterMovement())
        {
            BaselineMaxWalkSpeed = Movement->MaxWalkSpeed;
            bMovementBaselineCaptured = true;
        }
    }
}

void UShipboardControlStatusComponent::EnforceMovementState()
{
    if (ActiveEffect == EWeaponControlEffect::Mark)
    {
        return;
    }
    CaptureMovementBaseline();
    if (UCharacterMovementComponent* Movement = FindCharacterMovement();
        Movement && bMovementBaselineCaptured)
    {
        Movement->MaxWalkSpeed = BaselineMaxWalkSpeed * ActiveMovementMultiplier;
        if (ActiveMovementMultiplier <= KINDA_SMALL_NUMBER)
        {
            Movement->StopMovementImmediately();
        }
    }
}

void UShipboardControlStatusComponent::RestoreMovementState()
{
    if (UCharacterMovementComponent* Movement = FindCharacterMovement();
        Movement && bMovementBaselineCaptured)
    {
        Movement->MaxWalkSpeed = BaselineMaxWalkSpeed;
    }
    bMovementBaselineCaptured = false;
    BaselineMaxWalkSpeed = 0.0f;
}

UCharacterMovementComponent* UShipboardControlStatusComponent::FindCharacterMovement() const
{
    if (const ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        return Character->GetCharacterMovement();
    }
    return nullptr;
}

void UShipboardControlStatusComponent::GetLifetimeReplicatedProps(
    TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UShipboardControlStatusComponent, ActiveEffect);
    DOREPLIFETIME(UShipboardControlStatusComponent, EffectEndTimeSeconds);
    DOREPLIFETIME(UShipboardControlStatusComponent, ActiveMovementMultiplier);
}
