#include "Ship/ShipThrustGravity.h"
#include "Ship/ShipPropulsionSubsystem.h"
#include "Engine/World.h"

AShipThrustGravity::AShipThrustGravity()
{
	PrimaryActorTick.bCanEverTick = false;
	bNetLoadOnClient = true;
}

void AShipThrustGravity::BeginPlay()
{
	Super::BeginPlay();
	if (bEngagedAtStart)
	{
		ApplyThrust();
	}
}

void AShipThrustGravity::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	CutThrust();
	Super::EndPlay(EndPlayReason);
}

void AShipThrustGravity::ApplyThrust()
{
	if (UWorld* World = GetWorld())
	{
		if (UShipPropulsionSubsystem* Propulsion = World->GetSubsystem<UShipPropulsionSubsystem>())
		{
			Propulsion->SetShipThrust(ThrustDirection, Acceleration);
			bEngaged = true;
		}
	}
}

void AShipThrustGravity::CutThrust()
{
	if (UWorld* World = GetWorld())
	{
		if (UShipPropulsionSubsystem* Propulsion = World->GetSubsystem<UShipPropulsionSubsystem>())
		{
			Propulsion->StopShipThrust();
			bEngaged = false;
		}
	}
}
