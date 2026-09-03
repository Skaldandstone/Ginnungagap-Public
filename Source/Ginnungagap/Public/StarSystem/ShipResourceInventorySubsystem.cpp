#include "ShipResourceInventorySubsystem.h"
#include "../Ship/ShipHelmSystem.h"

void UShipResourceInventorySubsystem::AddResource(EStarSystemResourceType ResourceType, int32 Amount)
{
    int32& Current = ResourceAmounts.FindOrAdd(ResourceType);
    const int32 Previous = Current;
    Current = FMath::Max(0, Current + Amount);
    OnResourceChanged.Broadcast(ResourceType, Current, Current - Previous);
}

bool UShipResourceInventorySubsystem::TrySpendResource(EStarSystemResourceType ResourceType, int32 Amount)
{
    int32* Current = ResourceAmounts.Find(ResourceType);
    if (!Current || *Current < Amount)
    {
        return false;
    }

    *Current -= Amount;
    OnResourceChanged.Broadcast(ResourceType, *Current, -Amount);
    return true;
}

int32 UShipResourceInventorySubsystem::GetResourceAmount(EStarSystemResourceType ResourceType) const
{
    const int32* Current = ResourceAmounts.Find(ResourceType);
    return Current ? *Current : 0;
}

bool UShipResourceInventorySubsystem::TrySpendForHeadingCorrection(AShipHelmSystem* Helm, float ReductionFraction, int32 FuelCost)
{
    if (!Helm)
    {
        return false;
    }

    if (!TrySpendResource(EStarSystemResourceType::NavigationFuel, FuelCost))
    {
        return false;
    }

    Helm->ConsumeHeadingOffset(ReductionFraction);
    return true;
}
