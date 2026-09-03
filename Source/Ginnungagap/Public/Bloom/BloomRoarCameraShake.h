#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraShakeBase.h"
#include "BloomRoarCameraShake.generated.h"

/**
 * The ship shaking when something very large in it makes a noise.
 *
 * Perlin noise rather than a sinusoid: a roar is not a machine. Short blend-in, long blend-out,
 * heaviest on the vertical, so it reads as a structure flexing and settling rather than a
 * camera being wobbled.
 */
UCLASS()
class GINNUNGAGAP_API UBloomRoarCameraShake : public UCameraShakeBase
{
    GENERATED_BODY()

public:
    UBloomRoarCameraShake(const FObjectInitializer& ObjectInitializer);
};
