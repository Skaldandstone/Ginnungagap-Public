#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "JumpDestinationRowWidget.generated.h"

class UJumpDestinationWidget;

UCLASS()
class GINNUNGAGAP_API UJumpDestinationRowWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void Configure(UJumpDestinationWidget* InOwner, int32 InIndex, const FText& Label, const FLinearColor& Color);

private:
    UFUNCTION()
    void HandleClicked();

    UPROPERTY()
    TObjectPtr<UJumpDestinationWidget> Owner;

    int32 CandidateIndex = INDEX_NONE;
};
