#include "BloomDirector.h"
#include "Meta/RunSeedSubsystem.h"
#include "BloomHost.h"
#include "BloomCorruptible.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "TimerManager.h"

void UBloomDirector::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    for (uint8 i = 0; i <= static_cast<uint8>(EBloomHazardType::Dust); ++i)
    {
        HazardResistance.Add(static_cast<EBloomHazardType>(i), 0.0f);
    }

    if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
    {
        World->GetTimerManager().SetTimer(PassiveProgressTimerHandle, this, &UBloomDirector::TickPassiveProgress, TickInterval, true);
    }
}

void UBloomDirector::Deinitialize()
{
    if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
    {
        World->GetTimerManager().ClearTimer(PassiveProgressTimerHandle);
    }

    Super::Deinitialize();
}

void UBloomDirector::TickPassiveProgress()
{
    EvolutionProgress += PassiveProgressPerTick;
    if (EvolutionProgress >= EvolutionProgressPerStage)
    {
        EvolutionProgress -= EvolutionProgressPerStage;
        AdvanceStage();
    }
}

void UBloomDirector::RegisterHazardExposure(EBloomHazardType HazardType, float Amount)
{
    float& Resistance = HazardResistance.FindOrAdd(HazardType);
    Resistance = FMath::Clamp(Resistance + ResistanceGainPerExposure * Amount, 0.0f, MaxHazardResistance);

    EvolutionProgress += Amount * 0.1f;
    if (EvolutionProgress >= EvolutionProgressPerStage)
    {
        EvolutionProgress -= EvolutionProgressPerStage;
        AdvanceStage();
    }

    float& ExposureEntry = CurrentVisitCriteria.ExposureByType.FindOrAdd(HazardType);
    ExposureEntry += Amount;
    CurrentVisitCriteria.TotalHazardExposure += Amount;
}

void UBloomDirector::RegisterPlayerAction(EBloomPlayerActionType ActionType, float Weight)
{
    switch (ActionType)
    {
    case EBloomPlayerActionType::ReactivatedShipSystem:
        CurrentVisitCriteria.ShipSystemsReactivated += 1;
        CurrentVisitCriteria.WeightedActionScore += Weight;
        break;
    case EBloomPlayerActionType::PerformedEVA:
        CurrentVisitCriteria.EVAExcursions += 1;
        CurrentVisitCriteria.WeightedActionScore += Weight;
        break;
    case EBloomPlayerActionType::DispatchedDrone:
        CurrentVisitCriteria.DronesDispatched += 1;
        CurrentVisitCriteria.WeightedActionScore += Weight;
        break;
    case EBloomPlayerActionType::PurgedCorruption:
        CurrentVisitCriteria.CorruptionPurges += 1;
        break;
    }
}

bool UBloomDirector::RollForJumpSabotage(AActor* System)
{
    if (static_cast<uint8>(CurrentStage) < static_cast<uint8>(MinStageForJumpSabotage))
    {
        return false;
    }

    const int32 StagesBeyondMin = static_cast<uint8>(CurrentStage) - static_cast<uint8>(MinStageForJumpSabotage);
    const float SabotageChance = FMath::Clamp(BaseSabotageChance + SabotageChancePerStageBeyondMin * StagesBeyondMin, 0.0f, 1.0f);

    // Drawn from the seeded channel so a sabotage that ruined a run can be replayed exactly.
    URunSeedSubsystem* Seeds = GetGameInstance() ? GetGameInstance()->GetSubsystem<URunSeedSubsystem>() : nullptr;
    if (!Seeds || !Seeds->RollChance(RunSeedChannels::BloomRolls, SabotageChance))
    {
        return false;
    }

    return TryCorruptSystem(System);
}

bool UBloomDirector::RollForSelfDestructCounter()
{
    if (static_cast<uint8>(CurrentStage) < static_cast<uint8>(MinStageForSelfDestructCounter))
    {
        return false;
    }

    const int32 StagesBeyondMin = static_cast<uint8>(CurrentStage) - static_cast<uint8>(MinStageForSelfDestructCounter);
    const float CounterChance = FMath::Clamp(BaseSelfDestructCounterChance + SelfDestructCounterChancePerStageBeyondMin * StagesBeyondMin, 0.0f, 1.0f);

    URunSeedSubsystem* Seeds = GetGameInstance() ? GetGameInstance()->GetSubsystem<URunSeedSubsystem>() : nullptr;
    if (!Seeds || !Seeds->RollChance(RunSeedChannels::BloomRolls, CounterChance))
    {
        return false;
    }

    AdvanceStage();
    return true;
}

void UBloomDirector::ForceResetBloom()
{
    const bool bStageChanged = CurrentStage != EBloomStage::Latent;
    CurrentStage = EBloomStage::Latent;
    EvolutionProgress = 0.0f;
    InfectedHosts.Reset();
    CorruptedSystems.Reset();
    if (bStageChanged)
    {
        OnBloomStageChanged.Broadcast(CurrentStage);
    }
}

void UBloomDirector::NotifySystemPurged(AActor* System)
{
    CorruptedSystems.RemoveAll([System](const TWeakObjectPtr<AActor>& Weak)
    {
        return !Weak.IsValid() || Weak.Get() == System;
    });
}

float UBloomDirector::GetHazardEffectiveness(EBloomHazardType HazardType) const
{
    const float* Resistance = HazardResistance.Find(HazardType);
    return 1.0f - (Resistance ? *Resistance : 0.0f);
}

void UBloomDirector::RegisterStealthTacticUse(EBloomStealthTactic Tactic, float Weight)
{
    if (Weight <= 0.0f)
    {
        return;
    }

    // Accumulate only. Effectiveness deliberately does not move mid-run: the Bloom adapts during
    // jumps, and the crew is meant to discover what changed after arrival rather than watch a
    // tactic visibly decay while they are relying on it.
    PendingStealthTacticUse.FindOrAdd(Tactic) += Weight;
}

float UBloomDirector::GetStealthTacticEffectiveness(EBloomStealthTactic Tactic) const
{
    const float* Counter = StealthTacticCounter.Find(Tactic);
    const float Adaptation = Counter ? *Counter : 0.0f;
    return FMath::Clamp(1.0f - Adaptation, MinStealthTacticEffectiveness, 1.0f);
}

void UBloomDirector::AdvanceStage()
{
    if (CurrentStage != EBloomStage::Manifestation)
    {
        CurrentStage = static_cast<EBloomStage>(static_cast<uint8>(CurrentStage) + 1);
        OnBloomStageChanged.Broadcast(CurrentStage);
    }
}

void UBloomDirector::RestoreStage(EBloomStage RestoredStage)
{
    const EBloomStage PreviousStage = CurrentStage;
    CurrentStage = RestoredStage;
    EvolutionProgress = 0.0f;
    if (PreviousStage != CurrentStage)
    {
        OnBloomStageChanged.Broadcast(CurrentStage);
    }
}

void UBloomDirector::OnSystemJump()
{
    const float ExposureContribution = CurrentVisitCriteria.TotalHazardExposure * JumpEvolutionPerExposurePoint;
    const float ActionContribution = CurrentVisitCriteria.WeightedActionScore * JumpEvolutionPerPlayerAction;
    const float PurgeMitigation = CurrentVisitCriteria.CorruptionPurges * JumpEvolutionPerPlayerAction;

    const float JumpEvolutionAmount = FMath::Max(0.0f, JumpEvolutionBaseAmount + ExposureContribution + ActionContribution - PurgeMitigation);

    EvolutionProgress += JumpEvolutionAmount;
    while (EvolutionProgress >= EvolutionProgressPerStage)
    {
        EvolutionProgress -= EvolutionProgressPerStage;
        AdvanceStage();
    }

    // Convert this visit's evasion behaviour into counter-adaptation. Decay first so a tactic the
    // crew stopped leaning on recovers, then apply what they actually used this visit -- otherwise
    // the Bloom would only ever harden and switching approach could never win ground back.
    for (TPair<EBloomStealthTactic, float>& Entry : StealthTacticCounter)
    {
        Entry.Value *= (1.0f - FMath::Clamp(StealthCounterDecayPerJump, 0.0f, 1.0f));
    }

    for (const TPair<EBloomStealthTactic, float>& Use : PendingStealthTacticUse)
    {
        const float MaxCounter = 1.0f - MinStealthTacticEffectiveness;
        float& Counter = StealthTacticCounter.FindOrAdd(Use.Key);
        Counter = FMath::Clamp(Counter + Use.Value * StealthCounterGainPerUse, 0.0f, MaxCounter);
    }
    PendingStealthTacticUse.Reset();

    CurrentVisitCriteria = FSystemVisitCriteria();
}

bool UBloomDirector::TryInfectHost(AActor* Host)
{
    if (!Host || !Host->Implements<UBloomHost>())
    {
        return false;
    }

    if (!IBloomHost::Execute_CanBeBloomPossessed(Host))
    {
        return false;
    }

    IBloomHost::Execute_OnBloomPossession(Host);
    InfectedHosts.AddUnique(Host);
    return true;
}

bool UBloomDirector::TryCorruptSystem(AActor* System)
{
    if (!System || !System->Implements<UBloomCorruptible>())
    {
        return false;
    }

    if (!IBloomCorruptible::Execute_CanBeBloomCorrupted(System))
    {
        return false;
    }

    IBloomCorruptible::Execute_OnBloomCorruption(System);
    CorruptedSystems.AddUnique(System);
    return true;
}
