#include "Bloom/BloomRoarCameraShake.h"

#include "Shakes/PerlinNoiseCameraShakePattern.h"

UBloomRoarCameraShake::UBloomRoarCameraShake(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    bSingleInstance = true;

    UPerlinNoiseCameraShakePattern* Pattern =
        ObjectInitializer.CreateDefaultSubobject<UPerlinNoiseCameraShakePattern>(this, TEXT("RoarPattern"));
    Pattern->Duration = 2.6f;
    Pattern->BlendInTime = 0.12f;
    Pattern->BlendOutTime = 1.5f;

    Pattern->X.Amplitude = 2.2f;  Pattern->X.Frequency = 9.0f;
    Pattern->Y.Amplitude = 1.8f;  Pattern->Y.Frequency = 7.0f;
    Pattern->Z.Amplitude = 3.6f;  Pattern->Z.Frequency = 11.0f;

    Pattern->Pitch.Amplitude = 0.9f; Pattern->Pitch.Frequency = 8.0f;
    Pattern->Yaw.Amplitude = 0.6f;   Pattern->Yaw.Frequency = 6.0f;
    Pattern->Roll.Amplitude = 0.7f;  Pattern->Roll.Frequency = 5.0f;

    Pattern->FOV.Amplitude = 0.8f;   Pattern->FOV.Frequency = 4.0f;

    SetRootShakePattern(Pattern);
}
