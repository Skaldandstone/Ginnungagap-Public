#include "Activities/FieldActivityCatalog.h"
#include "Progression/ClassSkillComponent.h"
#include "Bloom/BloomCorruptible.h"
#include "Bloom/BloomDirector.h"
#include "Bloom/PathogenLoadComponent.h"
#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipPowerNodeComponent.h"
#include "Engine/GameInstance.h"
#include "Net/UnrealNetwork.h"

namespace
{
struct FFieldPresetConfig
{
    const TCHAR* Name;
    EActivityMechanic Mechanic;
    EFieldActivityOutcome Outcome;
    float Duration;
    int32 Steps;
    float Tolerance;
    bool bBloomSensitive;
};

// Ordered exactly like EFieldActivityPreset. These are compressed physical procedures, not arbitrary QTEs.
static const FFieldPresetConfig Presets[] =
{
    {TEXT("Install tether anchor"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Inspect hull plating"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 7, 0, .30f, true},
    {TEXT("Patch micrometeor puncture"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RepairHull, 8, 0, .20f, true},
    {TEXT("Deploy antenna array"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Clean solar panel"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RestorePower, 7, 0, .32f, false},
    {TEXT("Deploy radiator"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Cut obstructing debris"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SecureTarget, 6, 0, .24f, true},
    {TEXT("Secure cargo latch"), EActivityMechanic::Timed, EFieldActivityOutcome::SecureTarget, 4, 0, .25f, false},
    {TEXT("Pressure-test airlock seal"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SealBreach, 7, 5, .25f, true},
    {TEXT("Service maneuvering thruster"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 8, 6, .25f, true},
    {TEXT("Replace fuse"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 5, 4, .25f, true},
    {TEXT("Prime fluid pump"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 5, 0, .25f, true},
    {TEXT("Align isolation valves"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Lubricate bearing"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 5, 0, .34f, false},
    {TEXT("Backflush filter"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Brace damaged conduit"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Tune vibration damper"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .18f, true},
    {TEXT("Flush heat exchanger"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Pressure-test pipework"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, true},
    {TEXT("Synchronize generator phase"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RestorePower, 8, 0, .16f, true},
    {TEXT("Diagnose distribution bus"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, true},
    {TEXT("Isolate ground fault"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 7, 6, .25f, true},
    {TEXT("Tune communications carrier"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .18f, true},
    {TEXT("Align navigation beacon"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .16f, true},
    {TEXT("Recover data core"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Replace control relay"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 6, 5, .25f, true},
    {TEXT("Restore lighting circuit"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 6, 5, .25f, true},
    {TEXT("Deploy sensor mast"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Configure transponder"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Activate emergency beacon"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::RestorePower, 5, 4, .25f, true},
    {TEXT("Collect sterile sample swab"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SecureTarget, 5, 0, .28f, true},
    {TEXT("Focus microscopy stage"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 7, 0, .14f, true},
    {TEXT("Isolate culture specimen"), EActivityMechanic::GenomeSequence, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Run radiation assay"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, true},
    {TEXT("Collect atmosphere sample"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Analyze mineral sample"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, false},
    {TEXT("Map contamination boundary"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 8, 0, .22f, true},
    {TEXT("Establish quarantine barrier"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Run sterilizer cycle"), EActivityMechanic::Timed, EFieldActivityOutcome::Decontaminate, 8, 0, .25f, true},
    {TEXT("Excise Bloom growth"), EActivityMechanic::ToolPath, EFieldActivityOutcome::PurgeBloom, 9, 0, .16f, true},
    {TEXT("Control hemorrhage"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RestoreHealth, 6, 0, .24f, true},
    {TEXT("Splint fracture"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::RestoreHealth, 7, 6, .25f, false},
    {TEXT("Fit oxygen mask"), EActivityMechanic::Timed, EFieldActivityOutcome::RestoreOxygen, 4, 0, .25f, false},
    {TEXT("Compound antidote"), EActivityMechanic::GenomeSequence, EFieldActivityOutcome::Decontaminate, 8, 7, .25f, true},
    {TEXT("Charge defibrillator"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RestoreHealth, 6, 5, .25f, true},
    {TEXT("Refill suit oxygen"), EActivityMechanic::Timed, EFieldActivityOutcome::RestoreOxygen, 5, 0, .25f, false},
    {TEXT("Prepare emergency ration"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 5, 4, .25f, false},
    {TEXT("Verify cargo inventory"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, true},
    {TEXT("Disassemble salvage"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Attach rescue tether"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 5, .25f, true},
    {TEXT("Calibrate star tracker"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .14f, true},
    {TEXT("Align inertial gyroscope"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 8, 0, .15f, true},
    {TEXT("Purge RCS thruster"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Bleed propulsion fuel line"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .25f, true},
    {TEXT("Synchronize docking clamps"), EActivityMechanic::CableMatching, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Inspect landing gear"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, false},
    {TEXT("Reboot flight computer"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RestorePower, 7, 6, .25f, true},
    {TEXT("Verify plotted course"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, true},
    {TEXT("Track radar dish"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .16f, true},
    {TEXT("Inspect jump coil"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 9, 7, .25f, true},
    {TEXT("Service water recycler"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Clear waste compactor"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 5, 0, .25f, false},
    {TEXT("Mix hydroponic nutrients"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Repair grow-light circuit"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 6, 5, .25f, true},
    {TEXT("Service galley heater"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 6, 5, .25f, false},
    {TEXT("Repair bunk restraint"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 4, .25f, false},
    {TEXT("Clear hygiene drain"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 5, 0, .25f, true},
    {TEXT("Test carbon-dioxide monitor"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, true},
    {TEXT("Patch thermal insulation"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RepairHull, 7, 0, .27f, false},
    {TEXT("Survey habitat leak"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SealBreach, 8, 0, .20f, true},
    {TEXT("Pry sealed salvage crate"), EActivityMechanic::Timed, EFieldActivityOutcome::SecureTarget, 5, 0, .25f, true},
    {TEXT("Strip reusable hull panel"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .22f, true},
    {TEXT("Harvest cable harness"), EActivityMechanic::CableMatching, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Siphon residual fuel"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .25f, true},
    {TEXT("Extract data module"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Shield reactor material"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Assemble artifact cradle"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Tag wreck with beacon"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 4, .25f, false},
    {TEXT("Balance cargo mass"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Plan salvage cut"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 7, 0, .18f, true},
    {TEXT("Bypass mechanical lock"), EActivityMechanic::CableMatching, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Restore security camera"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 6, 5, .25f, true},
    {TEXT("Configure turret IFF"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Audit armory inventory"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, true},
    {TEXT("Clear ammunition feed"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, false},
    {TEXT("Brace security barricade"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Deploy motion sensor"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 6, 5, .25f, true},
    {TEXT("Bag forensic evidence"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 4, .25f, true},
    {TEXT("Apply rescue restraint"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 4, .25f, false},
    {TEXT("Decrypt security log"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 9, 8, .25f, true},
    {TEXT("Triage casualty"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RestoreHealth, 6, 5, .25f, true},
    {TEXT("Secure patient to stretcher"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 5, 5, .25f, false},
    {TEXT("Deploy emergency lighting"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 5, 4, .25f, true},
    {TEXT("Restore alarm circuit"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 6, 5, .25f, true},
    {TEXT("Provision escape pod"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Transmit distress packet"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Apply firebreak foam"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SecureTarget, 7, 0, .24f, true},
    {TEXT("Prepare radiation shelter"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Mark evacuation route"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SecureTarget, 6, 0, .30f, true},
    {TEXT("Recover flight recorder"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 9, 8, .25f, true},
    {TEXT("Scan mineral prospect"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 7, 0, .18f, true},
    {TEXT("Set drill anchor"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Replace drill bit"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, false},
    {TEXT("Assay ore grade"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, true},
    {TEXT("Map rock fractures"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 8, 0, .19f, true},
    {TEXT("Place controlled mining charge"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true},
    {TEXT("Install dust suppression"), EActivityMechanic::CableMatching, EFieldActivityOutcome::ImproveOperationalState, 6, 5, .25f, true},
    {TEXT("Clear ore conveyor"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .25f, true},
    {TEXT("Calibrate ore hopper scale"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .17f, false},
    {TEXT("Extract geological core"), EActivityMechanic::ToolPath, EFieldActivityOutcome::SecureTarget, 8, 0, .21f, true},
    {TEXT("Zero CNC tooling"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .14f, true},
    {TEXT("Level additive print bed"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .16f, false},
    {TEXT("Load fabrication feedstock"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 5, 4, .25f, false},
    {TEXT("Charge induction furnace"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Prepare casting mold"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, false},
    {TEXT("Lay composite reinforcement"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RepairHull, 8, 0, .20f, false},
    {TEXT("Control adhesive cure"), EActivityMechanic::Timed, EFieldActivityOutcome::SecureTarget, 7, 0, .25f, true},
    {TEXT("Audit fastener torque"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 6, 5, .25f, false},
    {TEXT("Inspect component dimensions"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, true},
    {TEXT("Sterilize precision tools"), EActivityMechanic::Timed, EFieldActivityOutcome::Decontaminate, 7, 0, .25f, true},
    {TEXT("Calibrate robotic actuator"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .17f, true},
    {TEXT("Replace servo module"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RepairElectrical, 7, 6, .25f, true},
    {TEXT("Align lidar emitter"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .15f, true},
    {TEXT("Teach manipulator path"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 8, 0, .18f, true},
    {TEXT("Swap robot battery"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::RestorePower, 6, 5, .25f, false},
    {TEXT("Verify control firmware"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 7, 6, .25f, true},
    {TEXT("Set track tension"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .22f, false},
    {TEXT("Balance drone propellers"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 7, 0, .16f, true},
    {TEXT("Calibrate camera gimbal"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .15f, true},
    {TEXT("Reset autonomy controller"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RestorePower, 8, 7, .25f, true},
    {TEXT("Balance habitat humidity"), EActivityMechanic::ToolPath, EFieldActivityOutcome::ImproveOperationalState, 6, 0, .20f, true},
    {TEXT("Calibrate temperature sensor"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 6, 0, .16f, false},
    {TEXT("Service pressure regulator"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SealBreach, 7, 6, .25f, true},
    {TEXT("Balance oxygen manifold"), EActivityMechanic::CableMatching, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Purge line with nitrogen"), EActivityMechanic::Timed, EFieldActivityOutcome::Decontaminate, 7, 0, .25f, true},
    {TEXT("Clear condensate drain"), EActivityMechanic::Timed, EFieldActivityOutcome::ImproveOperationalState, 5, 0, .25f, true},
    {TEXT("Replace microbial filter"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::Decontaminate, 7, 6, .25f, true},
    {TEXT("Locate acoustic leak"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 8, 0, .18f, true},
    {TEXT("Test radiation shutters"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Configure emergency ventilation"), EActivityMechanic::CableMatching, EFieldActivityOutcome::RestorePower, 7, 6, .25f, true},
    {TEXT("Upload mission data"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Verify shift handover"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 5, 4, .25f, true},
    {TEXT("Confirm command checklist"), EActivityMechanic::OrderedAssembly, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Enroll crew identity"), EActivityMechanic::GenomeSequence, EFieldActivityOutcome::SecureTarget, 7, 6, .25f, true},
    {TEXT("Revoke access credential"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Annotate tactical map"), EActivityMechanic::ToolPath, EFieldActivityOutcome::RecordInspection, 6, 0, .26f, true},
    {TEXT("Confirm hazard briefing"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::RecordInspection, 5, 4, .25f, true},
    {TEXT("Review resource allocation"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::ImproveOperationalState, 7, 6, .25f, true},
    {TEXT("Verify evacuation roster"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 6, 5, .25f, true},
    {TEXT("Recover incident report"), EActivityMechanic::DiagnosticSequence, EFieldActivityOutcome::SecureTarget, 8, 7, .25f, true}
};
static_assert(UE_ARRAY_COUNT(Presets) == 150, "Field activity catalog must contain exactly one hundred and fifty presets");
}

AFieldActivityStation::AFieldActivityStation() { ApplyPresetDefaults(); }

void AFieldActivityStation::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (bUsePresetDefaults) ApplyPresetDefaults();
}

void AFieldActivityStation::ApplyPresetDefaults()
{
    const FFieldPresetConfig& Config = Presets[static_cast<uint8>(Preset)];
    Activity.Type = EPlayerActivityType::FieldProcedure;
    Activity.Mechanic = Config.Mechanic;
    Activity.DisplayName = FText::FromString(FString(Config.Name));
    Activity.DurationSeconds = Config.Duration;
    Activity.PuzzleSteps = Config.Steps;
    Activity.ToolPathTolerance = Config.Tolerance;
    Activity.AllowedMistakes = Config.Duration >= 8.0f ? 2 : 3;
    Activity.bBloomSensitive = Config.bBloomSensitive;
    Activity.BloomInterferenceScale = Preset == EFieldActivityPreset::BloomGrowthExcision ? 1.5f : 1.0f;
    Outcome = Config.Outcome;
}

void AFieldActivityStation::OnActivityCompleted_Implementation(APawn* Player)
{
    if (!HasAuthority() || !Player) return;
    AActor* Target = TargetActor ? TargetActor.Get() : this;
    UShipDamageComponent* Damage = Target->FindComponentByClass<UShipDamageComponent>();
    UShipPowerNodeComponent* Power = Target->FindComponentByClass<UShipPowerNodeComponent>();
    ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(TargetActor ? Target : Player);

    switch (Outcome)
    {
    case EFieldActivityOutcome::RecordInspection: OperationalValue = 1.0f; break;
    case EFieldActivityOutcome::ImproveOperationalState: OperationalValue = FMath::Clamp(OperationalValue + EffectStrength, 0.0f, 1.0f); break;
    case EFieldActivityOutcome::RepairHull: if (Damage) Damage->RepairHull(EffectStrength); break;
    case EFieldActivityOutcome::SealBreach: if (Damage) Damage->SealBreach(EffectStrength); break;
    case EFieldActivityOutcome::RepairElectrical: if (Damage) Damage->RepairElectricalFault(EffectStrength); if (Power) Power->SetDamageFraction(FMath::Max(0.0f, Power->DamageFraction - EffectStrength)); break;
    case EFieldActivityOutcome::RestorePower: if (Power) { Power->SetDamageFraction(0.0f); Power->SetNodeOnline(true); } OperationalValue = 1.0f; break;
    case EFieldActivityOutcome::RestoreSuit: if (Character) Character->SuitIntegrity = FMath::Clamp(Character->SuitIntegrity + EffectStrength, 0.0f, 1.0f); break;
    case EFieldActivityOutcome::RestoreHealth: if (Character) Character->HealthPercent = FMath::Clamp(Character->HealthPercent + EffectStrength * 100.0f, 0.0f, 100.0f); break;
    case EFieldActivityOutcome::RestoreOxygen: if (Character) Character->OxygenLevelPercent = FMath::Clamp(Character->OxygenLevelPercent + EffectStrength * 100.0f, 0.0f, 100.0f); break;
    case EFieldActivityOutcome::Decontaminate: if (UPathogenLoadComponent* Pathogen = Target->FindComponentByClass<UPathogenLoadComponent>()) Pathogen->PurgeInfection(); break;
    case EFieldActivityOutcome::PurgeBloom:
        if (Target->Implements<UBloomCorruptible>())
        {
            IBloomCorruptible::Execute_OnBloomPurged(Target);
            if (UGameInstance* GI = GetGameInstance()) if (UBloomDirector* Bloom = GI->GetSubsystem<UBloomDirector>()) Bloom->NotifySystemPurged(Target);
        }
        break;
    case EFieldActivityOutcome::SecureTarget: bTargetSecured = true; OperationalValue = 1.0f; break;
    }
    if (Character)
    {
        if (UPlayerStatusEffectComponent* StatusEffects = Character->GetStatusEffectComponent())
        {
            // Medical training raises what each intervention achieves. It is read from whoever is
            // performing the procedure, not the patient, so treating a casualty benefits from the
            // medic's skill rather than the casualty's.
            const UClassSkillComponent* Skills = Player ? Player->FindComponentByClass<UClassSkillComponent>() : nullptr;
            const float Treatment = EffectStrength
                * (1.0f + (Skills ? Skills->GetEffect(SkillEffects::MedicalEffectiveness) : 0.0f));

            switch (Preset)
            {
            case EFieldActivityPreset::HemorrhageControl:
                StatusEffects->TreatStatusEffect(EPlayerStatusEffect::Hemorrhage, Treatment * 1.5f);
                break;
            case EFieldActivityPreset::FractureSplinting:
                StatusEffects->TreatStatusEffect(EPlayerStatusEffect::Fracture, Treatment * 1.25f);
                break;
            case EFieldActivityPreset::OxygenMaskFitting:
            case EFieldActivityPreset::SuitOxygenRefill:
                StatusEffects->TreatStatusEffect(EPlayerStatusEffect::Hypoxia, Treatment * 2.0f);
                StatusEffects->TreatStatusEffect(EPlayerStatusEffect::CarbonDioxideToxicity, Treatment);
                break;
            case EFieldActivityPreset::CasualtyTriage:
                StatusEffects->TreatMostSevereStatusEffect(Treatment * 0.75f);
                break;
            default: break;
            }
        }
    }
    OnFieldProcedureCompleted(Preset, Target, Player);
    OnFieldStateChanged(OperationalValue, bTargetSecured);
    Super::OnActivityCompleted_Implementation(Player);
}

void AFieldActivityStation::OnRep_FieldState() { OnFieldStateChanged(OperationalValue, bTargetSecured); }
void AFieldActivityStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AFieldActivityStation, OperationalValue);
    DOREPLIFETIME(AFieldActivityStation, bTargetSecured);
}
