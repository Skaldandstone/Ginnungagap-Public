// Copyright Epic Games, Inc. All Rights Reserved.

#include "Ship/CryoPodSystem.h"
#include "Ship/BulkheadDoor.h"
#include "Activities/WeldableBulkheadDoor.h"
#include "EngineUtils.h"
#include "SurvivalPlayerController.h"
#include "Components/InputComponent.h"
#include "CoopSurvivalCharacter.h"
#include "Interaction/InteractionComponent.h"
#include "Obstructions/ObstructionBarrier.h"
#include "Activities/PlayerActivityComponent.h"
#include "Meta/RunSeedSubsystem.h"
#include "UI/SurvivalHUDWidget.h"
#include "UI/ProgressionMenuWidget.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"
#include "StatusEffects/PlayerPsychosisComponent.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "GameFramework/Character.h"
#include "Versus/AntagonistActivityComponent.h"
#include "Versus/AntagonistPlayerCharacter.h"
#include "UI/AntagonistActivityWidget.h"
#include "UI/MenuWidgetResolution.h"

ASurvivalPlayerController::ASurvivalPlayerController()
{
    HUDWidgetClass = USurvivalHUDWidget::StaticClass();
    ProgressionMenuClass = UProgressionMenuWidget::StaticClass();
    AntagonistActivityWidgetClass = UAntagonistActivityWidget::StaticClass();
}

void ASurvivalPlayerController::BeginPlay()
{
    Super::BeginPlay();

    if (IsLocalController() && HUDWidgetClass)
    {
        HUDWidget = CreateWidget<USurvivalHUDWidget>(this, HUDWidgetClass);
        if (HUDWidget)
        {
            HUDWidget->AddToViewport();

            if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
            {
                HUDWidget->SetCharacterReference(SurvivalCharacter);
            }
        }
    }

    // Upgrade to the authored Blueprint here rather than in the constructor: constructors run
    // during CDO creation at module load, where loading an asset is unsafe. Only replace the
    // native default, so an explicit override on a Blueprint subclass is left alone.
    if (ProgressionMenuClass == UProgressionMenuWidget::StaticClass())
    {
        ProgressionMenuClass = GinnungagapMenuWidgets::ResolveClass<UProgressionMenuWidget>(
            GINNUNGAGAP_MENU_WBP("ProgressionMenu"));
    }

    if (IsLocalController() && ProgressionMenuClass)
    {
        ProgressionMenu = CreateWidget<UProgressionMenuWidget>(this, ProgressionMenuClass);
        if (ProgressionMenu)
        {
            ProgressionMenu->AddToViewport();
        }
    }

    SetupAntagonistActivityWidget(GetPawn());
}

void ASurvivalPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);

    if (HUDWidget)
    {
        HUDWidget->SetCharacterReference(Cast<ACoopSurvivalCharacter>(InPawn));
    }

    SetupAntagonistActivityWidget(InPawn);
}

void ASurvivalPlayerController::SetupAntagonistActivityWidget(APawn* InPawn)
{
    if (!IsLocalController()) return;
    AAntagonistPlayerCharacter* Antagonist = Cast<AAntagonistPlayerCharacter>(InPawn);
    if (!Antagonist)
    {
        if (AntagonistActivityWidget) AntagonistActivityWidget->SetVisibility(ESlateVisibility::Collapsed);
        return;
    }
    if (!AntagonistActivityWidget && AntagonistActivityWidgetClass)
    {
        AntagonistActivityWidget = CreateWidget<UAntagonistActivityWidget>(this, AntagonistActivityWidgetClass);
        if (AntagonistActivityWidget) AntagonistActivityWidget->AddToViewport(30);
    }
    if (AntagonistActivityWidget)
    {
        AntagonistActivityWidget->SetActivityComponent(Antagonist->GetAntagonistActivityComponent());
    }
}

void ASurvivalPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();

    if (!InputComponent)
    {
        return;
    }

    InputComponent->BindAxis(TEXT("MoveForward"), this, &ASurvivalPlayerController::OnMove_Forward);
    InputComponent->BindAxis(TEXT("MoveRight"), this, &ASurvivalPlayerController::OnMove_Right);
    InputComponent->BindAxis(TEXT("LookUp"), this, &ASurvivalPlayerController::OnLook_Up);
    InputComponent->BindAxis(TEXT("Turn"), this, &ASurvivalPlayerController::OnLook_Right);

    InputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ASurvivalPlayerController::OnJumpPressed);
    InputComponent->BindAction(TEXT("Jump"), IE_Released, this, &ASurvivalPlayerController::OnJumpReleased);
    InputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &ASurvivalPlayerController::OnInteract);
    InputComponent->BindAction(TEXT("CycleApproach"), IE_Pressed, this, &ASurvivalPlayerController::OnCycleApproach);
    InputComponent->BindAction(TEXT("ActivitySecondary"), IE_Pressed, this, &ASurvivalPlayerController::OnActivitySecondary);
    InputComponent->BindAction(TEXT("ActivityTertiary"), IE_Pressed, this, &ASurvivalPlayerController::OnActivityTertiary);
    InputComponent->BindAction(TEXT("ActivityQuaternary"), IE_Pressed, this, &ASurvivalPlayerController::OnActivityQuaternary);
    InputComponent->BindAction(TEXT("ActivityCancel"), IE_Pressed, this, &ASurvivalPlayerController::OnActivityCancel);

    // Progression menu toggle (ESC key)
    FInputActionBinding& ProgressionBinding = InputComponent->BindAction(TEXT("Progression"), IE_Pressed, this, &ASurvivalPlayerController::OnToggleProgressionMenu);
    ProgressionBinding.bExecuteWhenPaused = true;
    InputComponent->BindAction(TEXT("RestartDemo"), IE_Pressed, this, &ASurvivalPlayerController::OnRestartDemo);
    InputComponent->BindAction(TEXT("ToggleView"), IE_Pressed, this, &ASurvivalPlayerController::OnToggleView);
    InputComponent->BindAction(TEXT("UseSupply"), IE_Pressed, this, &ASurvivalPlayerController::OnUseSupply);
}

void ASurvivalPlayerController::OnMove_Forward(float Value)
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        SurvivalCharacter->TryAddTraversalMovementInput(GetControlRotation().Vector(), Value);
        return;
    }
    if (APawn* ControlledPawn = GetPawn())
    {
        ControlledPawn->AddMovementInput(GetControlRotation().Vector(), Value);
    }
}

void ASurvivalPlayerController::OnMove_Right(float Value)
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        const FRotationMatrix ControlRotationMatrix(GetControlRotation());
        SurvivalCharacter->TryAddTraversalMovementInput(ControlRotationMatrix.GetUnitAxis(EAxis::Y), Value);
        return;
    }
    if (APawn* ControlledPawn = GetPawn())
    {
        const FRotationMatrix ControlRotationMatrix(GetControlRotation());
        ControlledPawn->AddMovementInput(ControlRotationMatrix.GetUnitAxis(EAxis::Y), Value);
    }
}

void ASurvivalPlayerController::OnLook_Up(float Value)
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent(); Activity && Activity->UsesToolPath())
        { Activity->SubmitToolDelta(FVector2D(0.0f, Value)); return; }
    AddPitchInput(Value);
}

void ASurvivalPlayerController::OnLook_Right(float Value)
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent(); Activity && Activity->UsesToolPath())
        { Activity->SubmitToolDelta(FVector2D(Value, 0.0f)); return; }
    AddYawInput(Value);
}

void ASurvivalPlayerController::OnJumpPressed()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        SurvivalCharacter->PushOffSurface();
        return;
    }
    if (ACharacter* ControlledCharacter = Cast<ACharacter>(GetPawn()))
    {
        ControlledCharacter->Jump();
    }
}

void ASurvivalPlayerController::OnJumpReleased()
{
    if (ACharacter* ControlledCharacter = Cast<ACharacter>(GetPawn()))
    {
        ControlledCharacter->StopJumping();
    }
}

void ASurvivalPlayerController::OnCycleApproach()
{
    // Changes how the player intends to get past whatever they are looking at.
    //
    // Shares the F key with ActivitySecondary, which is safe because the two can never both apply:
    // ActivitySecondary is only meaningful while an activity is running, and this only does
    // anything while looking at an obstruction that has not been started. Rather than add a
    // fourteenth binding to a scheme James has already asked to keep close to WASD.
    ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn());
    if (!SurvivalCharacter)
    {
        return;
    }

    UInteractionComponent* Interaction = SurvivalCharacter->GetInteractionComponent();
    AActor* Focused = Interaction ? Interaction->GetFocusedInteractable() : nullptr;

    if (AObstructionBarrier* Barrier = Cast<AObstructionBarrier>(Focused))
    {
        Barrier->CycleVerb(SurvivalCharacter);
    }
}

void ASurvivalPlayerController::OnInteract()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent(); Activity && Activity->IsActivityActive())
        {
            Activity->SubmitInput(EActivityInput::Primary);
            return;
        }
        if (UInteractionComponent* Interaction = SurvivalCharacter->GetInteractionComponent())
        {
            // Inside a cryo pod E releases the tube they are in, whatever the eye-line trace has
            // found through the glass (the console on the wall behind it, as often as not).
            for (TActorIterator<ACryoPodSystem> It(GetWorld()); It; ++It)
            {
                if (It->bIsOccupied && It->OccupyingCharacter.Get() == SurvivalCharacter)
                {
                    UE_LOG(LogTemp, Display, TEXT("Interact: %s releases %s (pawn at %s, pod at %s)"), *SurvivalCharacter->GetName(), *It->GetName(),
                        *SurvivalCharacter->GetActorLocation().ToCompactString(), *It->GetActorLocation().ToCompactString());
                    Interaction->ServerTryInteract(*It);
                    return;
                }
            }
            // A bulkhead is pushed at, not clicked: the body leans into it as the leaves cycle.
            // Only a door that will cycle: a welded or locked one starts an activity (or refuses),
            // and the push's root motion would carry the crew out of the activity's range.
            ABulkheadDoor* Door = Cast<ABulkheadDoor>(Interaction->GetFocusedInteractable());
            AWeldableBulkheadDoor* Welded = Cast<AWeldableBulkheadDoor>(Door);
            if (Door && !(Welded && Welded->bWeldedShut) && !(Door->bLocked && Door->bIsSealed))
            {
                SurvivalCharacter->PlayGesture(TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_Push.RT_A_Push"), 1.3f);
            }
            Interaction->TryInteract();
        }
		return;
	}
	if (APawn* ControlledPawn = GetPawn())
	{
		if (UAntagonistActivityComponent* Activity =
			ControlledPawn->FindComponentByClass<UAntagonistActivityComponent>(); Activity && Activity->IsActivityActive())
		{
			Activity->SubmitInput(EActivityInput::Primary);
			return;
		}
		if (UInteractionComponent* Interaction = ControlledPawn->FindComponentByClass<UInteractionComponent>())
		{
			Interaction->TryInteract();
		}
    }
}

void ASurvivalPlayerController::OnToggleProgressionMenu()
{
    if (ProgressionMenu)
    {
        ProgressionMenu->ToggleMenu();
    }
}

void ASurvivalPlayerController::OnActivitySecondary()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent()) Activity->SubmitInput(EActivityInput::Secondary);
	if (APawn* ControlledPawn = GetPawn())
		if (UAntagonistActivityComponent* Activity = ControlledPawn->FindComponentByClass<UAntagonistActivityComponent>()) Activity->SubmitInput(EActivityInput::Secondary);
}

void ASurvivalPlayerController::OnActivityTertiary()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent()) Activity->SubmitInput(EActivityInput::Tertiary);
	if (APawn* ControlledPawn = GetPawn())
		if (UAntagonistActivityComponent* Activity = ControlledPawn->FindComponentByClass<UAntagonistActivityComponent>()) Activity->SubmitInput(EActivityInput::Tertiary);
}

void ASurvivalPlayerController::OnActivityQuaternary()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent()) Activity->SubmitInput(EActivityInput::Quaternary);
	if (APawn* ControlledPawn = GetPawn())
		if (UAntagonistActivityComponent* Activity = ControlledPawn->FindComponentByClass<UAntagonistActivityComponent>()) Activity->SubmitInput(EActivityInput::Quaternary);
}

void ASurvivalPlayerController::OnActivityCancel()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
        if (UPlayerActivityComponent* Activity = SurvivalCharacter->GetPlayerActivityComponent()) Activity->CancelActivity();
	if (APawn* ControlledPawn = GetPawn())
		if (UAntagonistActivityComponent* Activity = ControlledPawn->FindComponentByClass<UAntagonistActivityComponent>()) Activity->CancelActivity();
}

void ASurvivalPlayerController::OnUseSupply()
{
    if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        Crew->UseBestSupply();
    }
}

void ASurvivalPlayerController::OnToggleView()
{
    // First or third person, on a key: the way the ship is played and recorded.
    if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        Crew->SetFirstPersonView(!Crew->IsFirstPersonView());
    }
}

void ASurvivalPlayerController::OnRestartDemo()
{
    if (UWorld* World = GetWorld())
    {
        UGameplayStatics::OpenLevel(this, FName(*World->GetMapName().Replace(TEXT("UEDPIE_0_"), TEXT(""))));
    }
}

void ASurvivalPlayerController::SeedRun(int32 Seed)
{
    UGameInstance* GameInstance = GetGameInstance();
    URunSeedSubsystem* Seeds = GameInstance ? GameInstance->GetSubsystem<URunSeedSubsystem>() : nullptr;
    if (!Seeds)
    {
        UE_LOG(LogTemp, Warning, TEXT("SeedRun: no run seed subsystem available"));
        return;
    }

    // SeedRun logs the chosen value itself, including the line needed to reproduce it, so there is
    // nothing to print here that would not be a duplicate.
    Seeds->SeedRun(Seed);
}

void ASurvivalPlayerController::ShowRunSeed()
{
    UGameInstance* GameInstance = GetGameInstance();
    URunSeedSubsystem* Seeds = GameInstance ? GameInstance->GetSubsystem<URunSeedSubsystem>() : nullptr;
    if (!Seeds)
    {
        UE_LOG(LogTemp, Warning, TEXT("ShowRunSeed: no run seed subsystem available"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("Run seed %d. Reproduce with: SeedRun %d"),
        Seeds->GetRunSeed(), Seeds->GetRunSeed());
}

void ASurvivalPlayerController::TestPsychosisEpisode()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        if (UPlayerPsychosisComponent* Psychosis = SurvivalCharacter->GetPsychosisComponent())
        {
            constexpr int32 EpisodeTypeCount = 5;
            Psychosis->TriggerEpisodeForTesting(
                static_cast<EPlayerHallucinationType>(PsychosisTestEpisodeIndex % EpisodeTypeCount), 0.85f);
            ++PsychosisTestEpisodeIndex;
        }
    }
}

void ASurvivalPlayerController::EnablePsychosisTestMode()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        if (UPlayerStatusEffectComponent* StatusEffects = SurvivalCharacter->GetStatusEffectComponent();
            StatusEffects && SurvivalCharacter->HasAuthority())
        {
            StatusEffects->ApplyStatusEffect(EPlayerStatusEffect::JumpPsychosis, 0.85f, 300.0f,
                EPlayerStatusSource::JumpExposure);
        }
    }
}

void ASurvivalPlayerController::PsychosisRealityCheck()
{
    if (ACoopSurvivalCharacter* SurvivalCharacter = Cast<ACoopSurvivalCharacter>(GetPawn()))
    {
        if (UPlayerPsychosisComponent* Psychosis = SurvivalCharacter->GetPsychosisComponent())
        {
            Psychosis->PerformRealityCheck(false);
        }
    }
}
