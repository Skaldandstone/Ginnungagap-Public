#include "Activities/MaintenanceActivityStations.h"
#include "Equipment/EquipmentComponent.h"
#include "Inventory/InventoryComponent.h"
#include "Bloom/PathogenLoadComponent.h"
#include "Progression/ClassSkillComponent.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "Ship/SensorArraySystem.h"
#include "Ship/BulkheadDoor.h"
#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"

void AMaintenanceActivityStation::ConfigurePreset(EPlayerActivityType Type, EActivityMechanic Mechanic, const FText& Name, float Duration, int32 Steps)
{
    Activity.Type = Type;
    Activity.Mechanic = Mechanic;
    Activity.DisplayName = Name;
    Activity.DurationSeconds = Duration;
    Activity.PuzzleSteps = Steps;
    Activity.AllowedMistakes = 3;
    Activity.bBloomSensitive = true;
}

bool AMaintenanceActivityStation::CanStartActivity_Implementation(APawn* Player) const
{
    if (!Super::CanStartActivity_Implementation(Player)) return false;
    if (RequiredItem && RequiredItemCount > 0)
    {
        const UInventoryComponent* Inventory = Player->FindComponentByClass<UInventoryComponent>();
        if (!Inventory || Inventory->GetItemQuantity(RequiredItem) < RequiredItemCount) return false;
    }
    return true;
}

void AMaintenanceActivityStation::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority() || !Player) return;
    UInventoryComponent* Inventory = Player->FindComponentByClass<UInventoryComponent>();
    if (RequiredItem && RequiredItemCount > 0 && (!Inventory || !Inventory->RemoveItem(RequiredItem, RequiredItemCount))) return;

    AActor* Target = TargetActor ? TargetActor.Get() : this;
    UShipDamageComponent* Damage = Target->FindComponentByClass<UShipDamageComponent>();
    UShipPowerNodeComponent* Power = Target->FindComponentByClass<UShipPowerNodeComponent>();

    // Competence is measured in what one pass at a fault actually accomplishes, which is why
    // skills scale the work done rather than a resource price -- there is no repair-cost system
    // for a discount to apply to. Repair and medical work draw on different training, so a station
    // that patches a hull and one that stabilises a casualty read different effects.
    const UClassSkillComponent* Skills = Player->FindComponentByClass<UClassSkillComponent>();
    const float RepairStrength = EffectStrength
        * (1.0f + (Skills ? Skills->GetEffect(SkillEffects::RepairEffectiveness) : 0.0f));
    const float MedicalStrength = EffectStrength
        * (1.0f + (Skills ? Skills->GetEffect(SkillEffects::MedicalEffectiveness) : 0.0f));

    switch (CompletionEffect)
    {
    case EMaintenanceActivityEffect::RepairHull:
        if (Damage) Damage->RepairHull(RepairStrength);
        break;
    case EMaintenanceActivityEffect::SuppressFire:
        if (Damage) Damage->SuppressFire(RepairStrength);
        break;
    case EMaintenanceActivityEffect::SealBreach:
        if (Damage) Damage->SealBreach(RepairStrength);
        break;
    case EMaintenanceActivityEffect::ReplaceComponent:
        if (Damage) Damage->RepairElectricalFault(RepairStrength);
        if (Power) Power->SetDamageFraction(FMath::Max(0.0f, Power->DamageFraction - RepairStrength));
        break;
    case EMaintenanceActivityEffect::FabricateItem:
        if (Inventory && FabricatedItem) Inventory->AddItem(FabricatedItem, FabricatedItemCount);
        if (ConstructedActorClass) GetWorld()->SpawnActor<AActor>(ConstructedActorClass, GetActorTransform());
        break;
    case EMaintenanceActivityEffect::CalibrateSensor:
        // Calibration restores signal-path integrity without silently purchasing a sensor upgrade.
        if (Power) Power->SetDamageFraction(FMath::Max(0.0f, Power->DamageFraction - RepairStrength));
        if (Damage) Damage->RepairElectricalFault(RepairStrength);
        break;
    case EMaintenanceActivityEffect::Decontaminate:
        if (UPathogenLoadComponent* Pathogen = Target->FindComponentByClass<UPathogenLoadComponent>()) Pathogen->PurgeInfection();
        break;
    case EMaintenanceActivityEffect::StabilizePatient:
        if (ACoopSurvivalCharacter* Patient = Cast<ACoopSurvivalCharacter>(TargetActor ? Target : Player))
        {
            Patient->HealthPercent = FMath::Clamp(Patient->HealthPercent + MedicalStrength * 100.0f, 0.0f, 100.0f);
            Patient->OxygenLevelPercent = FMath::Clamp(Patient->OxygenLevelPercent + MedicalStrength * 50.0f, 0.0f, 100.0f);
            Patient->RadiationDoseSv = FMath::Max(0.0f, Patient->RadiationDoseSv - MedicalStrength * 0.25f);
            if (UPlayerStatusEffectComponent* StatusEffects = Patient->GetStatusEffectComponent())
            {
                StatusEffects->TreatMostSevereStatusEffect(MedicalStrength);
            }
        }
        break;
    case EMaintenanceActivityEffect::RerouteBreaker:
        if (Power) { Power->SetNodeOnline(true); Power->SetDamageFraction(FMath::Max(0.0f, Power->DamageFraction - RepairStrength)); }
        break;
    case EMaintenanceActivityEffect::RepairSuit:
        // Repairs the player's worn gear rather than the ship. Equipment protection scales
        // continuously with durability and nothing restored it, so a run was a one-way slide
        // toward no protection at all with no bench to undo it at.
        if (UEquipmentComponent* Equipment = Player->FindComponentByClass<UEquipmentComponent>())
        {
            // Durability is on a 0-100 scale while EffectStrength is a 0-1 fraction, so it is
            // scaled to the item's own range rather than applied raw -- a raw 0.5 would read as
            // half a durability point and look like the station did nothing.
            Equipment->RepairAllEquipment(RepairStrength * 100.0f);
        }
        // And the seal itself. Durability is what the gear can take; integrity is what the vacuum
        // takes, and the walkthrough measured this bench leaving it exactly where it found it
        // (0.80 -> 0.80) a room away from the breach that drains it. Same strength, same scale:
        // the bench's 0.4 takes the default 0.8 suit to a full seal, which the breach room's
        // (1 - integrity) drain then cannot touch.
        if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Player))
        {
            Crew->RepairSuitIntegrity(RepairStrength);
        }
        break;
    case EMaintenanceActivityEffect::ToggleMechanicalOverride:
        if (ABulkheadDoor* Door = Cast<ABulkheadDoor>(Target))
        {
            // An override is the release for a locked door; from here on its own panel works.
            Door->SetLocked(false);
            if (Door->bIsSealed) Door->Unseal(); else Door->Seal();
        }
        break;
    }

    Super::OnActivityCompleted_Implementation(Player);
}

AHullPatchingStation::AHullPatchingStation()
{
    CompletionEffect = EMaintenanceActivityEffect::RepairHull;
    ConfigurePreset(EPlayerActivityType::HullPatching, EActivityMechanic::ToolPath, NSLOCTEXT("Activities", "HullPatch", "Apply hull patch"), 9.0f);
    Activity.ToolPathTolerance = 0.28f;
}

AFireSuppressionStation::AFireSuppressionStation()
{
    CompletionEffect = EMaintenanceActivityEffect::SuppressFire;
    ConfigurePreset(EPlayerActivityType::FireSuppression, EActivityMechanic::ToolPath, NSLOCTEXT("Activities", "FireSuppress", "Sweep fire base"), 6.0f);
    Activity.ToolPathTolerance = 0.38f;
}

APipeSealingStation::APipeSealingStation()
{
    CompletionEffect = EMaintenanceActivityEffect::SealBreach;
    ConfigurePreset(EPlayerActivityType::PipeSealing, EActivityMechanic::Timed, NSLOCTEXT("Activities", "PipeSeal", "Seat pipe clamp"), 5.0f);
}

AComponentReplacementStation::AComponentReplacementStation()
{
    CompletionEffect = EMaintenanceActivityEffect::ReplaceComponent;
    ConfigurePreset(EPlayerActivityType::ComponentReplacement, EActivityMechanic::CableMatching, NSLOCTEXT("Activities", "ReplaceComponent", "Replace damaged component"), 7.0f, 6);
}

AFabricationStation::AFabricationStation()
{
    CompletionEffect = EMaintenanceActivityEffect::FabricateItem;
    ConfigurePreset(EPlayerActivityType::Fabrication, EActivityMechanic::OrderedAssembly, NSLOCTEXT("Activities", "Fabricate", "Assemble fabrication recipe"), 6.0f, 5);
}

ASensorCalibrationStation::ASensorCalibrationStation()
{
    CompletionEffect = EMaintenanceActivityEffect::CalibrateSensor;
    ConfigurePreset(EPlayerActivityType::SensorCalibration, EActivityMechanic::ToolPath, NSLOCTEXT("Activities", "Calibrate", "Align sensor waveform"), 7.0f);
    Activity.ToolPathTolerance = 0.18f;
}

ADecontaminationStation::ADecontaminationStation()
{
    CompletionEffect = EMaintenanceActivityEffect::Decontaminate;
    ConfigurePreset(EPlayerActivityType::Decontamination, EActivityMechanic::Timed, NSLOCTEXT("Activities", "Decontaminate", "Complete decontamination cycle"), 8.0f);
}

AMedicalStabilizationStation::AMedicalStabilizationStation()
{
    CompletionEffect = EMaintenanceActivityEffect::StabilizePatient;
    ConfigurePreset(EPlayerActivityType::MedicalStabilization, EActivityMechanic::DiagnosticSequence, NSLOCTEXT("Activities", "Stabilize", "Stabilize patient"), 7.0f, 6);
    EffectStrength = 0.35f;
}

ABreakerReroutingStation::ABreakerReroutingStation()
{
    CompletionEffect = EMaintenanceActivityEffect::RerouteBreaker;
    ConfigurePreset(EPlayerActivityType::BreakerRerouting, EActivityMechanic::CableMatching, NSLOCTEXT("Activities", "Breaker", "Reroute breaker bus"), 6.0f, 5);
}

AMechanicalOverrideStation::AMechanicalOverrideStation()
{
    CompletionEffect = EMaintenanceActivityEffect::ToggleMechanicalOverride;
    ConfigurePreset(EPlayerActivityType::MechanicalOverride, EActivityMechanic::Timed, NSLOCTEXT("Activities", "MechanicalOverride", "Crank mechanical override"), 5.0f);
}
