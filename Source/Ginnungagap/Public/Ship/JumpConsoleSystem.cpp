#include "JumpConsoleSystem.h"
#include "../StarSystem/JumpSequenceSubsystem.h"
#include "Engine/GameInstance.h"
#include "UI/JumpDestinationWidget.h"
#include "GameFramework/PlayerController.h"

AJumpConsoleSystem::AJumpConsoleSystem()
{
    SystemType = EShipSystemType::JumpDrive;
    DestinationWidgetClass = UJumpDestinationWidget::StaticClass();
}

void AJumpConsoleSystem::OnInteract_Implementation(APawn* InteractingPawn)
{
    if (bIsCorrupted)
    {
        return;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UJumpSequenceSubsystem* JumpSequence = GI->GetSubsystem<UJumpSequenceSubsystem>())
        {
            if (JumpSequence->CurrentPhase != EJumpPhase::Cruising)
            {
                return;
            }

            if (JumpSequence->CurrentCandidates.Num() == 0)
            {
                JumpSequence->GenerateJumpCandidates();
            }

            OnJumpConsoleOpened(JumpSequence->CurrentCandidates);
            APlayerController* PC = InteractingPawn ? Cast<APlayerController>(InteractingPawn->GetController()) : nullptr;
            if (PC && DestinationWidgetClass)
            {
                if (!DestinationWidget)
                {
                    DestinationWidget = CreateWidget<UJumpDestinationWidget>(PC, DestinationWidgetClass);
                }
                if (DestinationWidget)
                {
                    DestinationWidget->Configure(this, JumpSequence->CurrentCandidates);
                    DestinationWidget->AddToViewport(50);
                    PC->SetInputMode(FInputModeGameAndUI().SetWidgetToFocus(DestinationWidget->TakeWidget()));
                    PC->SetShowMouseCursor(true);
                    return;
                }
            }
            if (bAutoSelectFirstCandidate && !JumpSequence->CurrentCandidates.IsEmpty())
            {
                ConfirmJumpSelection(0);
            }
        }
    }
}

void AJumpConsoleSystem::CloseDestinationPicker()
{
    if (!DestinationWidget)
    {
        return;
    }
    if (APlayerController* PC = DestinationWidget->GetOwningPlayer())
    {
        PC->SetInputMode(FInputModeGameOnly());
        PC->SetShowMouseCursor(false);
    }
    DestinationWidget->RemoveFromParent();
}

bool AJumpConsoleSystem::ConfirmJumpSelection(int32 CandidateIndex)
{
    if (bIsCorrupted)
    {
        return false;
    }

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UJumpSequenceSubsystem* JumpSequence = GI->GetSubsystem<UJumpSequenceSubsystem>())
        {
            return JumpSequence->SelectJumpCandidate(CandidateIndex) && JumpSequence->BeginJumpWarningCountdown();
        }
    }

    return false;
}

void AJumpConsoleSystem::ApplyCorruptionEffects()
{
    // Corrupted consoles simply refuse interaction (see OnInteract_Implementation); no additional state to unwind.
}

void AJumpConsoleSystem::RemoveCorruptionEffects()
{
}
