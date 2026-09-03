#pragma once

#include "CoreMinimal.h"
#include "ShipSystemActor.h"
#include "../Interfaces/Interactable.h"
#include "../StarSystem/StarSystemTypes.h"
#include "JumpConsoleSystem.generated.h"

UCLASS()
class GINNUNGAGAP_API AJumpConsoleSystem : public AShipSystemActor, public IInteractable
{
    GENERATED_BODY()

public:
    AJumpConsoleSystem();

    virtual void OnInteract_Implementation(APawn* InteractingPawn) override;

    UFUNCTION(BlueprintCallable, Category = "Jump Console")
    bool ConfirmJumpSelection(int32 CandidateIndex);

    /** Demo fallback used when no Blueprint destination picker is attached. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump Console")
    bool bAutoSelectFirstCandidate = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Jump Console")
    TSubclassOf<class UJumpDestinationWidget> DestinationWidgetClass;

    UFUNCTION(BlueprintCallable, Category = "Jump Console")
    void CloseDestinationPicker();

    UFUNCTION(BlueprintImplementableEvent, Category = "Jump Console")
    void OnJumpConsoleOpened(const TArray<FJumpCandidate>& Candidates);

protected:
    virtual void ApplyCorruptionEffects() override;
    virtual void RemoveCorruptionEffects() override;

private:
    UPROPERTY()
    TObjectPtr<UJumpDestinationWidget> DestinationWidget;
};
