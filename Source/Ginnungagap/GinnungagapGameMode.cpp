// Copyright Epic Games, Inc. All Rights Reserved.

#include "GinnungagapGameMode.h"
#include "CoopSurvivalCharacter.h"
#include "Player/SurvivalPlayerController.h"
#include "LevelSetup/ProceduralShipBuilder.h"
#include "Cinematics/CGITrailerDirector.h"
#include "Ship/ModularShipRoom.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

AGinnungagapGameMode::AGinnungagapGameMode()
{
    static ConstructorHelpers::FClassFinder<APawn> SuitedPlayerClass(
        TEXT("/Game/Characters/Player/Blueprints/BP_Player_Suit_Crew"));
    DefaultPawnClass = ACoopSurvivalCharacter::StaticClass();
    if (SuitedPlayerClass.Succeeded())
    {
        DefaultPawnClass = SuitedPlayerClass.Class;
    }
	PlayerControllerClass = ASurvivalPlayerController::StaticClass();
}

void AGinnungagapGameMode::BeginPlay()
{
	Super::BeginPlay();

	if (!bAutoBuildShip)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const FString MapName = World->GetMapName();
	const bool bIsProductionDistrict = MapName.Contains(TEXT("Companionway_Showcase"))
		|| MapName.Contains(TEXT("ExpressSpine_Showcase"))
		|| MapName.Contains(TEXT("CarrierConcourse_Showcase"));
	if (bSkipAutoBuildForProductionDistricts && bIsProductionDistrict)
	{
		UE_LOG(LogTemp, Display, TEXT("Using authored production district '%s'; procedural ship generation disabled."), *MapName);
		return;
	}

	// Authored ship maps (including the four-deck quick demo) already contain their
	// room graph. Spawning the procedural builder here would layer a second ship on
	// top of the playable level when PIE begins.
	for (TActorIterator<AModularShipRoom> It(World); It; ++It)
	{
		UE_LOG(LogTemp, Display, TEXT("Using authored modular ship '%s'; procedural ship generation disabled."), *MapName);
		return;
	}

	for (TActorIterator<AProceduralShipBuilder> It(World); It; ++It)
	{
		return;
	}

	World->SpawnActor<AProceduralShipBuilder>();

	if (FParse::Param(FCommandLine::Get(), TEXT("CGITrailer")))
	{
		World->SpawnActor<ACGITrailerDirector>();
	}
}
