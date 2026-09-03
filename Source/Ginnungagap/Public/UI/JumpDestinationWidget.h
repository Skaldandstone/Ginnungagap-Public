#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "StarSystem/StarSystemTypes.h"
#include "JumpDestinationWidget.generated.h"

class AJumpConsoleSystem;
class UVerticalBox;

/** Native destination picker used by C++ jump consoles and replaceable by a Blueprint subclass. */
UCLASS()
class GINNUNGAGAP_API UJumpDestinationWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;

    void Configure(AJumpConsoleSystem* InConsole, const TArray<FJumpCandidate>& InCandidates);

    void SelectCandidate(int32 Index);

private:
    void BuildRows();

    UPROPERTY()
    TObjectPtr<AJumpConsoleSystem> Console;

    UPROPERTY()
    TObjectPtr<UVerticalBox> CandidateList;

    TArray<FJumpCandidate> Candidates;
};
