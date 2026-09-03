#include "Activities/SpecialistActivityCatalog.h"

namespace
{
constexpr int32 SpecialistPresetCount = 100;
constexpr int32 SpecialistVariantCount = 5;
constexpr int32 SpecialistImplementationCount = SpecialistPresetCount * SpecialistVariantCount;

EActivityMechanic MechanicForIndex(int32 Index)
{
    static const EActivityMechanic Rotation[] =
    {
        EActivityMechanic::ToolPath,
        EActivityMechanic::OrderedAssembly,
        EActivityMechanic::DiagnosticSequence,
        EActivityMechanic::CableMatching,
        EActivityMechanic::Timed
    };
    return Rotation[Index % UE_ARRAY_COUNT(Rotation)];
}

EFieldActivityOutcome OutcomeForIndex(int32 Index)
{
    const int32 Discipline = Index / 10;
    const bool bAlternate = (Index % 2) != 0;
    switch (Discipline)
    {
    case 0: return bAlternate ? EFieldActivityOutcome::RestorePower : EFieldActivityOutcome::ImproveOperationalState;
    case 1: return bAlternate ? EFieldActivityOutcome::SealBreach : EFieldActivityOutcome::RepairHull;
    case 2: return bAlternate ? EFieldActivityOutcome::Decontaminate : EFieldActivityOutcome::RestoreOxygen;
    case 3: return bAlternate ? EFieldActivityOutcome::RestoreOxygen : EFieldActivityOutcome::RestoreHealth;
    case 4: return bAlternate ? EFieldActivityOutcome::SecureTarget : EFieldActivityOutcome::RecordInspection;
    case 5: return bAlternate ? EFieldActivityOutcome::RestorePower : EFieldActivityOutcome::SecureTarget;
    case 6: return bAlternate ? EFieldActivityOutcome::RecordInspection : EFieldActivityOutcome::SecureTarget;
    case 7: return bAlternate ? EFieldActivityOutcome::SecureTarget : EFieldActivityOutcome::ImproveOperationalState;
    case 8: return bAlternate ? EFieldActivityOutcome::RestorePower : EFieldActivityOutcome::RecordInspection;
    default: return bAlternate ? EFieldActivityOutcome::Decontaminate : EFieldActivityOutcome::PurgeBloom;
    }
}
}

ASpecialistActivityStation::ASpecialistActivityStation()
{
    bUsePresetDefaults = false;
    ApplySpecialistPreset();
}

void ASpecialistActivityStation::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplySpecialistPreset();
}

void ASpecialistActivityStation::ApplySpecialistPreset()
{
    const int32 Index = static_cast<int32>(SpecialistPreset);
    check(Index >= 0 && Index < SpecialistPresetCount);
    Activity.Type = EPlayerActivityType::FieldProcedure;
    Activity.DisplayName = StaticEnum<ESpecialistActivityPreset>()->GetDisplayNameTextByValue(Index);
    Activity.Mechanic = MechanicForIndex(Index);
    Activity.DurationSeconds = 5.0f + static_cast<float>(Index % 5);
    Activity.PuzzleSteps = 4 + Index % 5;
    Activity.InputSequence.Reset();
    Activity.AllowedMistakes = Index % 10 >= 7 ? 2 : 3;
    Activity.ToolPathTolerance = 0.14f + static_cast<float>(Index % 5) * 0.035f;
    Activity.bBloomSensitive = Index >= 90 || (Index % 3) != 0;
    Activity.BloomInterferenceScale = Index >= 90 ? 1.5f : 1.0f;
    Activity.MinimumBloomInterference = 0.0f;
    Activity.MaxRange = 300.0f;
    Activity.bLockMovement = true;
    Activity.bCancelWhenOutOfRange = true;
    Outcome = OutcomeForIndex(Index);
    EffectStrength = 0.2f + static_cast<float>(Index % 3) * 0.1f;

    const FString ProcedureName = Activity.DisplayName.ToString();
    switch (ProcedureVariant)
    {
    case ESpecialistProcedureVariant::Training:
        Activity.DisplayName = FText::FromString(FString::Printf(TEXT("TRAINING // %s"), *ProcedureName));
        Activity.DurationSeconds *= 1.2f;
        Activity.PuzzleSteps = FMath::Max(2, Activity.PuzzleSteps - 2);
        Activity.AllowedMistakes = 5;
        Activity.ToolPathTolerance = FMath::Min(0.5f, Activity.ToolPathTolerance * 1.4f);
        Activity.bBloomSensitive = false;
        Activity.BloomInterferenceScale = 0.0f;
        Activity.MinimumBloomInterference = 0.0f;
        EffectStrength *= 0.5f;
        break;
    case ESpecialistProcedureVariant::Nominal:
        break;
    case ESpecialistProcedureVariant::Emergency:
        Activity.DisplayName = FText::FromString(FString::Printf(TEXT("EMERGENCY // %s"), *ProcedureName));
        Activity.DurationSeconds *= 0.85f;
        Activity.PuzzleSteps += 1;
        Activity.AllowedMistakes = FMath::Min(Activity.AllowedMistakes, 2);
        Activity.ToolPathTolerance *= 0.85f;
        Activity.BloomInterferenceScale *= 1.2f;
        EffectStrength = FMath::Min(1.0f, EffectStrength * 1.25f);
        break;
    case ESpecialistProcedureVariant::EVA:
        Activity.DisplayName = FText::FromString(FString::Printf(TEXT("EVA // %s"), *ProcedureName));
        Activity.DurationSeconds *= 1.3f;
        Activity.PuzzleSteps += 1;
        Activity.AllowedMistakes = FMath::Min(Activity.AllowedMistakes, 2);
        Activity.ToolPathTolerance *= 0.8f;
        Activity.MaxRange = 180.0f;
        Activity.bLockMovement = true;
        EffectStrength = FMath::Min(1.0f, EffectStrength * 1.1f);
        break;
    case ESpecialistProcedureVariant::BloomCompromised:
        Activity.DisplayName = FText::FromString(FString::Printf(TEXT("BLOOM INTERFERENCE // %s"), *ProcedureName));
        Activity.DurationSeconds *= 1.15f;
        Activity.PuzzleSteps += 2;
        Activity.AllowedMistakes = 1;
        Activity.ToolPathTolerance *= 0.7f;
        Activity.bBloomSensitive = true;
        Activity.BloomInterferenceScale = FMath::Max(1.8f, Activity.BloomInterferenceScale * 1.5f);
        Activity.MinimumBloomInterference = 0.65f;
        EffectStrength = FMath::Min(1.0f, EffectStrength * 1.2f);
        break;
    }
}

int32 ASpecialistActivityStation::GetImplementationId() const
{
    return static_cast<int32>(SpecialistPreset) * SpecialistVariantCount + static_cast<int32>(ProcedureVariant);
}

FSpecialistImplementationDescriptor ASpecialistActivityStation::GetImplementationDescriptor() const
{
    FSpecialistImplementationDescriptor Descriptor;
    Descriptor.ImplementationId = GetImplementationId();
    Descriptor.Procedure = SpecialistPreset;
    Descriptor.Variant = ProcedureVariant;
    Descriptor.DisplayName = Activity.DisplayName;
    Descriptor.DurationSeconds = Activity.DurationSeconds;
    Descriptor.PuzzleSteps = Activity.PuzzleSteps;
    Descriptor.AllowedMistakes = Activity.AllowedMistakes;
    Descriptor.ToolPathTolerance = Activity.ToolPathTolerance;
    Descriptor.BloomInterferenceScale = Activity.BloomInterferenceScale;
    Descriptor.MinimumBloomInterference = Activity.MinimumBloomInterference;
    return Descriptor;
}

void ASpecialistActivityStation::OnActivityCompleted_Implementation(APawn* Player)
{
    AActor* AffectedTarget = TargetActor ? TargetActor.Get() : this;
    Super::OnActivityCompleted_Implementation(Player);
    if (HasAuthority()) OnSpecialistProcedureCompleted(SpecialistPreset, AffectedTarget, Player);
}

static_assert(static_cast<int32>(ESpecialistActivityPreset::ManifestationAnchorPurge) + 1 == SpecialistPresetCount,
    "Specialist activity catalog must contain exactly one hundred presets");
static_assert(static_cast<int32>(ESpecialistProcedureVariant::BloomCompromised) + 1 == SpecialistVariantCount,
    "Specialist activity catalog must contain exactly five variants");
static_assert(SpecialistImplementationCount == 500,
    "Specialist procedure matrix must contain exactly five hundred implementations");
