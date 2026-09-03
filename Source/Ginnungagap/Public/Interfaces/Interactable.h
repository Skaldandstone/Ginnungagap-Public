#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "Interactable.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UInteractable : public UInterface
{
    GENERATED_BODY()
};

class IInteractable
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    void OnInteract(APawn* Instigator);

    /**
     * What the HUD should say while this is being looked at. Empty means say nothing.
     *
     * The HUD has had an interaction prompt panel since it was written and **nothing has ever
     * called SetInteractionPrompt**. Every interactable object in the ship -- thirty-two door
     * cranks, both benches, four CIC stations, five obstructions -- has been silent, so the only
     * way to learn that a thing can be used is to walk into it and press the key.
     *
     * Defaulted to empty rather than to "Use" on purpose: an object that has not been given
     * something specific to say should say nothing, not fill the panel with a word that means
     * nothing. A prompt that is always there stops being read.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Interaction")
    FText GetInteractionPrompt(APawn* Viewer) const;
    virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const { return FText::GetEmpty(); }
};
