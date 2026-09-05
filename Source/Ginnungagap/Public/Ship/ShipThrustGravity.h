#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ShipThrustGravity.generated.h"

/**
 * Puts the ship under drive thrust from BeginPlay, so a thrust-gravity deck stack (decks stacked
 * along the drive axis, engines below) has "down" toward the engines. The propulsion subsystem
 * publishes the pseudo-gravity and every character's zero-g component turns it into walking
 * gravity; without this actor the ship coasts and the crew float.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipThrustGravity : public AActor
{
	GENERATED_BODY()

public:
	AShipThrustGravity();

	/** Direction the drive pushes the ship (world space). Gravity points the other way. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	FVector ThrustDirection = FVector::UpVector;

	/** Drive acceleration in cm/s^2: 980 is one g at the zero-g component's default scale. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	float Acceleration = 9800.0f;

	/**
	 * Whether the drive is already burning when the map starts. Off on the corvette: the ship is
	 * dead when the crew wake, they float out of cryo, and the deck becomes "down" only when the
	 * main bus is restored (the power station calls ApplyThrust).
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ship")
	bool bEngagedAtStart = true;

	UFUNCTION(BlueprintPure, Category = "Ship")
	bool IsEngaged() const { return bEngaged; }

	UFUNCTION(BlueprintCallable, Category = "Ship")
	void ApplyThrust();

	UFUNCTION(BlueprintCallable, Category = "Ship")
	void CutThrust();

protected:
	virtual void BeginPlay() override;
	bool bEngaged = false;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
};
