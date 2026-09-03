// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GinnungagapGameMode.generated.h"

/**
 *  Simple GameMode for a third person game
 */
UCLASS()
class AGinnungagapGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:

	/** Constructor */
	AGinnungagapGameMode();

	// When true (default), auto-spawns a single AProceduralShipBuilder at BeginPlay so a playable
	// ship exists with zero manual level placement. Set false (e.g. via a Blueprint override) if
	// you've hand-authored your own level content instead.
	UPROPERTY(EditDefaultsOnly, Category = "Procedural Ship")
	bool bAutoBuildShip = true;

	/** Authored production districts provide their own geometry and gameplay director. */
	UPROPERTY(EditDefaultsOnly, Category = "Procedural Ship")
	bool bSkipAutoBuildForProductionDistricts = true;

protected:
	virtual void BeginPlay() override;
};



