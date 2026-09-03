#include "LifeSupportSystem.h"
#include "CryoPodSystem.h"
#include "../CoopSurvivalCharacter.h"
#include "../Bloom/BloomDirector.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"

ALifeSupportSystem::ALifeSupportSystem()
{
    SystemType = EShipSystemType::LifeSupport;
    PrimaryActorTick.bCanEverTick = true;
}

void ALifeSupportSystem::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (!bIsCorrupted)
    {
        TimeSinceFailureStarted = 0.0f;
        return;
    }

    TimeSinceFailureStarted += DeltaTime;
    const float RampFraction = DrainRampUpSeconds > 0.0f ? FMath::Clamp(TimeSinceFailureStarted / DrainRampUpSeconds, 0.0f, 1.0f) : 1.0f;
    const float CurrentMultiplier = FMath::Lerp(1.0f, OxygenDrainMultiplierWhenFailed, RampFraction);

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
    {
        ACoopSurvivalCharacter* Character = *It;
        if (Character && !IsCharacterProtectedByCryo(Character))
        {
            Character->OxygenDrainMultiplier = CurrentMultiplier;
            if (RampFraction >= CarbonDioxideStatusStartsAtRamp)
            {
                if (UPlayerStatusEffectComponent* StatusEffects = Character->GetStatusEffectComponent())
                {
                    const float Severity = FMath::GetMappedRangeValueClamped(
                        FVector2D(CarbonDioxideStatusStartsAtRamp, 1.0f), FVector2D(0.15f, 1.0f), RampFraction);
                    StatusEffects->ApplyStatusEffect(EPlayerStatusEffect::CarbonDioxideToxicity, Severity, 6.0f,
                        EPlayerStatusSource::Atmosphere);
                }
            }
        }
    }
}

bool ALifeSupportSystem::IsCharacterProtectedByCryo(const ACoopSurvivalCharacter* Character) const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    for (TActorIterator<ACryoPodSystem> It(World); It; ++It)
    {
        ACryoPodSystem* Pod = *It;
        if (Pod && Pod->IsFunctioning() && Pod->bIsOccupied && Pod->OccupyingCharacter.Get() == Character)
        {
            return true;
        }
    }

    return false;
}

void ALifeSupportSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (!bIsCorrupted || bIsRepairing)
    {
        return;
    }

    bIsRepairing = true;
    GetWorldTimerManager().SetTimer(RepairTimerHandle, this, &ALifeSupportSystem::FinishRepair, RepairDuration, false);
}

void ALifeSupportSystem::FinishRepair()
{
    bIsRepairing = false;

    if (!bIsCorrupted)
    {
        return;
    }

    Execute_OnBloomPurged(this);

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UBloomDirector* Director = GI->GetSubsystem<UBloomDirector>())
        {
            Director->NotifySystemPurged(this);
        }
    }
}

void ALifeSupportSystem::ApplyCorruptionEffects()
{
    TimeSinceFailureStarted = 0.0f;
}

void ALifeSupportSystem::RemoveCorruptionEffects()
{
    TimeSinceFailureStarted = 0.0f;

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
    {
        if (ACoopSurvivalCharacter* Character = *It)
        {
            Character->OxygenDrainMultiplier = 1.0f;
        }
    }
}
