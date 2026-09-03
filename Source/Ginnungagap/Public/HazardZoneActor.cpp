// Copyright Epic Games, Inc. All Rights Reserved.

#include "HazardZoneActor.h"
#include "Components/BoxComponent.h"
#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "AI/HorrorEnemy.h"
#include "Ship/ShipSection.h"
#include "Ship/ShipNavigationSubsystem.h"
#include "Bloom/BloomDirector.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

AHazardZoneActor::AHazardZoneActor()
{
    PrimaryActorTick.bCanEverTick = true;

    ZoneBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("ZoneBounds"));
    RootComponent = ZoneBounds;
    ZoneBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ZoneBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    ZoneBounds->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    ZoneBounds->OnComponentBeginOverlap.AddDynamic(this, &AHazardZoneActor::OnZoneBeginOverlap);
    ZoneBounds->OnComponentEndOverlap.AddDynamic(this, &AHazardZoneActor::OnZoneEndOverlap);
}

void AHazardZoneActor::BeginPlay()
{
    Super::BeginPlay();

    if (UWorld* World = GetWorld())
    {
        if (UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>())
        {
            CachedSection = Navigation->GetSectionContainingLocation(GetActorLocation());
        }
    }
}

void AHazardZoneActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    for (ACoopSurvivalCharacter* Survivor : OverlappingSurvivors)
    {
        if (!Survivor)
        {
            continue;
        }

        float Distance = FVector::Dist(Survivor->GetActorLocation(), GetActorLocation());
        float Intensity = CalculateIntensityAtDistance(Distance);

        FPhysicsEnvironmentState ScaledState = EnvironmentState;
        ScaledState.SolarRadiationFlux *= Intensity;
        ScaledState.DustDensity *= Intensity;
        // TemperatureC is deliberately not scaled with the others. Flux and dust are quantities that
        // genuinely thin out with distance; temperature is an absolute, and scaling the default 20 C
        // by a 0.5 falloff would claim the edge of a fire is colder than the room around it.

        Survivor->UpdateSurvival(DeltaTime, ScaledState, Survivor->SuitIntegrity, Survivor->Stability);

        ApplyThermalExposure(Survivor, Intensity, DeltaTime);
    }

    for (AHorrorEnemy* Manifestation : OverlappingManifestations)
    {
        if (!Manifestation)
        {
            continue;
        }

        float Distance = FVector::Dist(Manifestation->GetActorLocation(), GetActorLocation());
        float Intensity = CalculateIntensityAtDistance(Distance);

        if (EnvironmentState.bSolarStormActive || EnvironmentState.SolarRadiationFlux > 0.0f)
        {
            Manifestation->ReceiveHazardExposure(EBloomHazardType::Radiation, EnvironmentState.SolarRadiationFlux * Intensity * DeltaTime);
        }
        if (EnvironmentState.bVacuumZone)
        {
            Manifestation->ReceiveHazardExposure(EBloomHazardType::Vacuum, Intensity * DeltaTime);
        }
        if (EnvironmentState.bMicrogravityZone)
        {
            Manifestation->ReceiveHazardExposure(EBloomHazardType::Microgravity, Intensity * DeltaTime);
        }
        if (EnvironmentState.DustDensity > 0.0f)
        {
            Manifestation->ReceiveHazardExposure(EBloomHazardType::Dust, EnvironmentState.DustDensity * Intensity * DeltaTime);
        }
    }

    DecayHazardContamination(DeltaTime);
}

float AHazardZoneActor::GetNormalizedHeat() const
{
    const float Range = BurnSaturationC - BurnThresholdC;
    if (Range <= KINDA_SMALL_NUMBER)
    {
        // A designer who sets saturation at or below the threshold has described a zone with no
        // gradient. Reading that as "never burns" rather than dividing by zero, because the other
        // reading -- instantly maximal above the threshold -- is a cliff nobody asked for.
        return 0.0f;
    }

    return FMath::Clamp((EnvironmentState.TemperatureC - BurnThresholdC) / Range, 0.0f, 1.0f);
}

void AHazardZoneActor::ApplyThermalExposure(ACoopSurvivalCharacter* Survivor, float Intensity, float DeltaTime)
{
    // A hot zone burned the Bloom's contamination away and did nothing at all to the person standing
    // in it: TemperatureC fed DecayHazardContamination and nothing else, while the status component
    // carried an ApplyHeatSourceExposure written for exactly this and never called. This is the wire
    // between them.
    if (!Survivor || DeltaTime <= 0.0f)
    {
        return;
    }

    // How hot, and then how close. Both are needed: a furnace across the room should not burn you,
    // and neither should standing inside a zone that happens to be room temperature.
    const float Heat = GetNormalizedHeat();
    if (Heat <= KINDA_SMALL_NUMBER)
    {
        return;
    }

    if (UPlayerStatusEffectComponent* Status = Survivor->GetStatusEffectComponent())
    {
        Status->ApplyHeatSourceExposure(Heat * Intensity, DeltaTime);
    }
}

void AHazardZoneActor::DecayHazardContamination(float DeltaTime)
{
    if (!CachedSection)
    {
        return;
    }

    UWorld* World = GetWorld();
    if (!World || !World->GetGameInstance())
    {
        return;
    }

    UBloomDirector* Director = World->GetGameInstance()->GetSubsystem<UBloomDirector>();
    if (!Director)
    {
        return;
    }

    float DecayAmount = 0.0f;

    if (EnvironmentState.bSolarStormActive || EnvironmentState.SolarRadiationFlux > 0.0f)
    {
        DecayAmount += EnvironmentState.SolarRadiationFlux * Director->GetHazardEffectiveness(EBloomHazardType::Radiation);
    }
    if (EnvironmentState.TemperatureC > 0.0f)
    {
        DecayAmount += EnvironmentState.TemperatureC * 0.01f * Director->GetHazardEffectiveness(EBloomHazardType::Thermal);
    }
    if (EnvironmentState.bVacuumZone)
    {
        DecayAmount += Director->GetHazardEffectiveness(EBloomHazardType::Vacuum);
    }
    if (EnvironmentState.bMicrogravityZone)
    {
        DecayAmount += Director->GetHazardEffectiveness(EBloomHazardType::Microgravity);
    }
    if (EnvironmentState.DustDensity > 0.0f)
    {
        DecayAmount += EnvironmentState.DustDensity * Director->GetHazardEffectiveness(EBloomHazardType::Dust);
    }

    if (DecayAmount > 0.0f)
    {
        CachedSection->AddContamination(-DecayAmount * DeltaTime);
    }
}

float AHazardZoneActor::CalculateIntensityAtDistance(float Distance) const
{
    if (!bUseDistanceFalloff)
    {
        return 1.0f;
    }

    float NormalizedDistance = FMath::Clamp(Distance / MaxFalloffDistance, 0.0f, 1.0f);

    if (IntensityCurve)
    {
        return IntensityCurve->GetFloatValue(NormalizedDistance);
    }

    // Default linear falloff if no curve is assigned.
    return 1.0f - NormalizedDistance;
}

void AHazardZoneActor::OnZoneBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (ACoopSurvivalCharacter* Survivor = Cast<ACoopSurvivalCharacter>(OtherActor))
    {
        OverlappingSurvivors.AddUnique(Survivor);
    }
    else if (AHorrorEnemy* Manifestation = Cast<AHorrorEnemy>(OtherActor))
    {
        OverlappingManifestations.AddUnique(Manifestation);
    }
}

void AHazardZoneActor::OnZoneEndOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
    if (ACoopSurvivalCharacter* Survivor = Cast<ACoopSurvivalCharacter>(OtherActor))
    {
        OverlappingSurvivors.Remove(Survivor);
    }
    else if (AHorrorEnemy* Manifestation = Cast<AHorrorEnemy>(OtherActor))
    {
        OverlappingManifestations.Remove(Manifestation);
    }
}