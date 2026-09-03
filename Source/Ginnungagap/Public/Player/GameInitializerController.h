#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "GameInitializerController.generated.h"

class UMenuManagerSubsystem;

/**
 * A simple player controller that runs on the main menu level to initialize the game flow.
 */
UCLASS()
class GINNUNGAGAP_API AGameInitializerController : public APlayerController
{
	GENERATED_BODY()

public:
	AGameInitializerController();

	/**
	 * Skip the boot/title sequence and drop straight into the three-step expedition setup.
	 *
	 * Defaults to false so the main-menu world opens on the boot splash and start screen, which is
	 * the actual front end: Start Game, Continue, and Settings all live there, and jumping past it
	 * left Continue and Settings unreachable. Set true to shortcut the front end when iterating on
	 * mode select, map customization, or loadout.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Menu|Startup")
	bool bLaunchIntoPreGameWorkflow = false;

protected:
	virtual void BeginPlay() override;

	UPROPERTY()
	UMenuManagerSubsystem* MenuManager;
};
