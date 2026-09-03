#include "Activities/OperationsActivityStations.h"
#include "Bloom/BloomCorruptible.h"
#include "Bloom/BloomDirector.h"
#include "CoopSurvivalCharacter.h"
#include "Ship/BulkheadDoor.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "StarSystem/RetrievalDroneActor.h"
#include "Net/UnrealNetwork.h"

void AOperationsActivityStation::ConfigurePreset(EPlayerActivityType Type, EActivityMechanic Mechanic, const FText& Name, float Duration, int32 Steps)
{
    Activity.Type = Type;
    Activity.Mechanic = Mechanic;
    Activity.DisplayName = Name;
    Activity.DurationSeconds = Duration;
    Activity.PuzzleSteps = Steps;
    Activity.AllowedMistakes = 3;
    Activity.bBloomSensitive = true;
}

void AOperationsActivityStation::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority() || !Player) return;
    AActor* Target = TargetActor ? TargetActor.Get() : this;
    UShipPowerNodeComponent* Power = Target->FindComponentByClass<UShipPowerNodeComponent>();
    UShipDamageComponent* Damage = Target->FindComponentByClass<UShipDamageComponent>();

    switch (CompletionEffect)
    {
    case EOperationsActivityEffect::RepressurizeAirlock:
        if (ABulkheadDoor* Door = Cast<ABulkheadDoor>(Target)) Door->Seal();
        if (Damage) Damage->SealBreach(EffectStrength);
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::ServiceScrubber:
        if (Target->Implements<UBloomCorruptible>()) IBloomCorruptible::Execute_OnBloomPurged(Target);
        if (Power) { Power->SetNodeOnline(true); Power->SetDamageFraction(0.0f); }
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::BalanceCoolant:
        if (Power) Power->SetDamageFraction(FMath::Max(0.0f, Power->DamageFraction - EffectStrength));
        OperationalValue = FMath::Clamp(OperationalValue + EffectStrength, 0.0f, 1.0f);
        break;
    case EOperationsActivityEffect::RecoverBattery:
        if (Power)
        {
            Power->SetNodeOnline(true);
            Power->StoredPowerUnits = FMath::Clamp(Power->StoredPowerUnits + Power->StorageCapacityUnits * EffectStrength, 0.0f, Power->StorageCapacityUnits);
            Power->NotifyGridDirty();
            OperationalValue = Power->StorageCapacityUnits > 0.0f ? Power->StoredPowerUnits / Power->StorageCapacityUnits : 1.0f;
        }
        break;
    case EOperationsActivityEffect::StartReactor:
        if (Power) { Power->SetDamageFraction(0.0f); Power->SetNodeOnline(true); }
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::RepairDrone:
        if (ARetrievalDroneActor* Drone = Cast<ARetrievalDroneActor>(Target)) Drone->RepairAndRecall();
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::ServiceTurret:
        if (Power) { Power->SetDamageFraction(0.0f); Power->SetNodeOnline(true); }
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::PatchSuit:
        if (ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(TargetActor ? Target : Player))
            Character->SuitIntegrity = FMath::Clamp(Character->SuitIntegrity + EffectStrength, 0.0f, 1.0f);
        OperationalValue = 1.0f;
        break;
    case EOperationsActivityEffect::ContainSample:
        OperationalValue = 1.0f;
        bOperationSecured = true;
        break;
    case EOperationsActivityEffect::PurgeBloom:
        if (Target->Implements<UBloomCorruptible>())
        {
            IBloomCorruptible::Execute_OnBloomPurged(Target);
            if (UGameInstance* GI = GetGameInstance())
                if (UBloomDirector* Bloom = GI->GetSubsystem<UBloomDirector>()) Bloom->NotifySystemPurged(Target);
        }
        OperationalValue = 1.0f;
        bOperationSecured = true;
        break;
    }
    OnOperationStateChanged(OperationalValue, bOperationSecured);
    Super::OnActivityCompleted_Implementation(Player);
}

void AOperationsActivityStation::OnRep_OperationState() { OnOperationStateChanged(OperationalValue, bOperationSecured); }
void AOperationsActivityStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AOperationsActivityStation, OperationalValue);
    DOREPLIFETIME(AOperationsActivityStation, bOperationSecured);
}

AAirlockRepressurizationStation::AAirlockRepressurizationStation()
{ CompletionEffect = EOperationsActivityEffect::RepressurizeAirlock; ConfigurePreset(EPlayerActivityType::AirlockRepressurization, EActivityMechanic::CableMatching, NSLOCTEXT("Activities", "Repressurize", "Sequence airlock repressurization"), 7.0f, 5); }
AOxygenScrubberServiceStation::AOxygenScrubberServiceStation()
{ CompletionEffect = EOperationsActivityEffect::ServiceScrubber; ConfigurePreset(EPlayerActivityType::ScrubberService, EActivityMechanic::OrderedAssembly, NSLOCTEXT("Activities", "Scrubber", "Replace scrubber media"), 7.0f, 6); }
ACoolantBalancingStation::ACoolantBalancingStation()
{ CompletionEffect = EOperationsActivityEffect::BalanceCoolant; ConfigurePreset(EPlayerActivityType::CoolantBalancing, EActivityMechanic::ToolPath, NSLOCTEXT("Activities", "Coolant", "Balance coolant flow"), 8.0f); Activity.ToolPathTolerance = 0.2f; }
ABatteryRecoveryStation::ABatteryRecoveryStation()
{ CompletionEffect = EOperationsActivityEffect::RecoverBattery; ConfigurePreset(EPlayerActivityType::BatteryRecovery, EActivityMechanic::CableMatching, NSLOCTEXT("Activities", "Battery", "Recover battery bank"), 7.0f, 6); }
AReactorStartupStation::AReactorStartupStation()
{ CompletionEffect = EOperationsActivityEffect::StartReactor; ConfigurePreset(EPlayerActivityType::ReactorStartup, EActivityMechanic::OrderedAssembly, NSLOCTEXT("Activities", "Reactor", "Sequence reactor startup"), 10.0f, 8); Activity.AllowedMistakes = 2; }
ADroneRepairStation::ADroneRepairStation()
{ CompletionEffect = EOperationsActivityEffect::RepairDrone; ConfigurePreset(EPlayerActivityType::DroneRepair, EActivityMechanic::CableMatching, NSLOCTEXT("Activities", "DroneRepair", "Repair retrieval drone"), 7.0f, 6); }
ATurretServiceStation::ATurretServiceStation()
{ CompletionEffect = EOperationsActivityEffect::ServiceTurret; ConfigurePreset(EPlayerActivityType::TurretService, EActivityMechanic::OrderedAssembly, NSLOCTEXT("Activities", "Turret", "Service turret feed"), 8.0f, 6); }
ASuitPatchingStation::ASuitPatchingStation()
{ CompletionEffect = EOperationsActivityEffect::PatchSuit; ConfigurePreset(EPlayerActivityType::SuitPatching, EActivityMechanic::ToolPath, NSLOCTEXT("Activities", "SuitPatch", "Patch pressure suit"), 6.0f); Activity.ToolPathTolerance = 0.26f; EffectStrength = 0.3f; }
ASampleContainmentStation::ASampleContainmentStation()
{ CompletionEffect = EOperationsActivityEffect::ContainSample; ConfigurePreset(EPlayerActivityType::SampleContainment, EActivityMechanic::DiagnosticSequence, NSLOCTEXT("Activities", "ContainSample", "Seal biological sample"), 7.0f, 6); }
ABloomPurgingStation::ABloomPurgingStation()
{ CompletionEffect = EOperationsActivityEffect::PurgeBloom; ConfigurePreset(EPlayerActivityType::BloomPurging, EActivityMechanic::GenomeSequence, NSLOCTEXT("Activities", "PurgeBloom", "Isolate Bloom signature"), 9.0f, 8); Activity.AllowedMistakes = 2; Activity.BloomInterferenceScale = 1.5f; }
