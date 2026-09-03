#pragma once

#include "CoreMinimal.h"
#include "Weapons/ShipboardWeapon.h"
#include "CaptiveBoltDriver.generated.h"

/** First playable vertical slice: a low-hull-risk service driver with an unsafe extended bolt. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ACaptiveBoltDriver : public AShipboardWeapon
{
    GENERATED_BODY()

public:
    ACaptiveBoltDriver();
};
