#include "BioScannerComponent.h"
#include "../Ship/ShipSection.h"
#include "../Ship/ShipNavigationSubsystem.h"
#include "Engine/World.h"
#include "CoopSurvivalCharacter.h"
#include "Progression/ClassSkillComponent.h"
#include "Progression/PlayerClass.h"

UBioScannerComponent::UBioScannerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UBioScannerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    UpdateReadings();
}

void UBioScannerComponent::UpdateReadings()
{
    AdjacentReadings.Reset();
    LocalReading = FSectionScanReading();

    AActor* Owner = GetOwner();
    UWorld* World = GetWorld();
    if (!Owner || !World)
    {
        return;
    }

    UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>();
    if (!Navigation)
    {
        return;
    }

    AShipSection* CurrentSection = Navigation->GetSectionContainingLocation(Owner->GetActorLocation());
    if (!CurrentSection)
    {
        return;
    }

    const float Floor = GetEffectiveDetectionFloor();

    LocalReading.SectionID = CurrentSection->SectionID;
    LocalReading.Concentration = FMath::Max(CurrentSection->Contamination, Floor);
    LocalReading.bSealedFromHere = false;
    LocalReading.bIsAdjacent = false;

    // Breadth-first out to the trained range rather than a single pass over direct connections.
    // Untrained this visits exactly the neighbours it always did, so the baseline reading is
    // unchanged; training is what pushes the frontier further out.
    const int32 MaxHops = GetEffectiveScanHops();

    TSet<int32> Seen;
    Seen.Add(CurrentSection->SectionID);

    TArray<AShipSection*> Frontier;
    Frontier.Add(CurrentSection);

    for (int32 Hop = 1; Hop <= MaxHops && Frontier.Num() > 0; ++Hop)
    {
        TArray<AShipSection*> Next;
        for (AShipSection* Section : Frontier)
        {
            for (const FSectionConnection& Connection : Section->Connections)
            {
                AShipSection* Target = Connection.Target;
                if (!Target || Seen.Contains(Target->SectionID))
                {
                    continue;
                }
                Seen.Add(Target->SectionID);

                FSectionScanReading Reading;
                Reading.SectionID = Target->SectionID;
                Reading.Concentration = FMath::Max(Target->Contamination, Floor);
                // Sealed is reported relative to the compartment the reading was reached through,
                // not to where the player is standing: what matters is whether the growth can move,
                // and past the first hop the player's own position no longer answers that.
                Reading.bSealedFromHere = !Section->IsTraversableTo(Target);
                Reading.bIsAdjacent = (Hop == 1);

                AdjacentReadings.Add(Reading);
                Next.Add(Target);
            }
        }
        Frontier = MoveTemp(Next);
    }
}
float UBioScannerComponent::GetEffectiveDetectionFloor() const
{
    // Sensitivity shrinks the floor rather than raising the reading, so a trained scientist sees a
    // faint trace where an untrained one sees the same flat "nothing" the clamp produces. It never
    // reaches zero: a scanner with no noise floor at all would report every compartment as dirty.
    const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(GetOwner());
    const UClassSkillComponent* Skills = Character ? Character->GetSkillComponent() : nullptr;
    if (!Skills)
    {
        return DetectionFloor;
    }

    const float Sensitivity = Skills->GetEffect(SkillEffects::ScanSensitivity);
    const float Scale = FMath::Clamp(1.0f - Sensitivity, MinDetectionFloorFraction, 1.0f);
    return DetectionFloor * Scale;
}

int32 UBioScannerComponent::GetEffectiveScanHops() const
{
    const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(GetOwner());
    const UClassSkillComponent* Skills = Character ? Character->GetSkillComponent() : nullptr;
    if (!Skills)
    {
        return BaseScanHops;
    }

    // Whole compartments, so the fractional part of a part-ranked skill buys nothing until it
    // completes. A reading either reaches the next bulkhead or it does not.
    const int32 Extra = FMath::FloorToInt(Skills->GetEffect(SkillEffects::ScanRange));
    return FMath::Clamp(BaseScanHops + Extra, BaseScanHops, MaxScanHops);
}

bool UBioScannerComponent::IsLocalSectionContaminated() const
{
    return LocalReading.Concentration > GetEffectiveDetectionFloor();
}

FPatientScanReading UBioScannerComponent::ScanPatient(const ACoopSurvivalCharacter* Patient) const
{
    FPatientScanReading Reading;
    if (!Patient)
    {
        return Reading;
    }
    Reading.bValidPatient = true;
    Reading.HealthPercent = Patient->HealthPercent;
    Reading.OxygenPercent = Patient->OxygenLevelPercent;
    Reading.RadiationDoseSv = Patient->RadiationDoseSv;
    if (const UPlayerStatusEffectComponent* StatusEffects = Patient->GetStatusEffectComponent())
    {
        Reading.Conditions = StatusEffects->GetActiveStatusEffects();
        Reading.MostUrgentCondition = StatusEffects->GetMostUrgentStatusEffect(Reading.bHasUrgentCondition);
        if (Reading.bHasUrgentCondition)
        {
            Reading.RecommendedAction = UPlayerStatusEffectComponent::GetRecommendedTreatment(Reading.MostUrgentCondition);
        }
        for (const FPlayerStatusEffectState& Condition : Reading.Conditions)
        {
            if (StatusEffects->GetClinicalSeverity(Condition.Type) == EPlayerStatusSeverity::Critical)
            {
                ++Reading.CriticalConditionCount;
            }
        }
    }
    return Reading;
}

FPatientScanReading UBioScannerComponent::GetOwnerPatientReading() const
{
    return ScanPatient(Cast<ACoopSurvivalCharacter>(GetOwner()));
}
