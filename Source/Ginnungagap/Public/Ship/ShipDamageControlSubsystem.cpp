#include "Ship/ShipDamageControlSubsystem.h"
#include "Ship/ShipDamageComponent.h"
#include "Ship/ShipSection.h"

void UShipDamageControlSubsystem::RegisterDamageComponent(UShipDamageComponent* Component)
{
    if (Component) { DamageComponents.AddUnique(Component); }
}

void UShipDamageControlSubsystem::UnregisterDamageComponent(UShipDamageComponent* Component)
{
    DamageComponents.Remove(Component);
}

TArray<AShipSection*> UShipDamageControlSubsystem::GetDamagedSections(float MinimumDangerScore) const
{
    TArray<AShipSection*> Result;
    for (const UShipDamageComponent* Component : DamageComponents)
    {
        AShipSection* Section = Component ? Cast<AShipSection>(Component->GetOwner()) : nullptr;
        if (Section && Component->GetDangerScore() >= MinimumDangerScore) { Result.Add(Section); }
    }
    return Result;
}

AShipSection* UShipDamageControlSubsystem::GetMostCriticalSection() const
{
    AShipSection* MostCritical = nullptr;
    float HighestScore = 0.0f;
    for (const UShipDamageComponent* Component : DamageComponents)
    {
        const float Score = Component ? Component->GetDangerScore() : 0.0f;
        if (Score > HighestScore)
        {
            HighestScore = Score;
            MostCritical = Cast<AShipSection>(Component->GetOwner());
        }
    }
    return MostCritical;
}

