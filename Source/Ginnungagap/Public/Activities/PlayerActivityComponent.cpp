#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimInstance.h"
#include "Activities/PlayerActivityComponent.h"
#include "Activities/PlayerActivitySource.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "Bloom/BloomDirector.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "CoopSurvivalCharacter.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Equipment/EquipmentComponent.h"
#include "UI/UiSoundSubsystem.h"
#include "Stealth/NoisePerceptionSubsystem.h"

UPlayerActivityComponent::UPlayerActivityComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.05f;
    SetIsReplicatedByDefault(true);
}

void UPlayerActivityComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UPlayerActivityComponent, Snapshot);
    DOREPLIFETIME(UPlayerActivityComponent, ActivitySource);
}

bool UPlayerActivityComponent::StartActivity(AActor* Source, const FPlayerActivityDefinition& Definition)
{
    if (!GetOwner() || !GetOwner()->HasAuthority())
    {
        ServerStartActivity(Source, Definition);
        return Source != nullptr && !IsActivityActive();
    }
    return StartActivityAuthoritative(Source, Definition);
}

void UPlayerActivityComponent::ServerStartActivity_Implementation(AActor* Source, const FPlayerActivityDefinition& Definition)
{
    // Never trust client-authored duration, range, or input sequences.
    if (Source && Source->Implements<UPlayerActivitySource>())
    {
        if (APawn* Player = Cast<APawn>(GetOwner()))
            StartActivityAuthoritative(Source, IPlayerActivitySource::Execute_GetActivityDefinition(Source, Player));
    }
}

bool UPlayerActivityComponent::StartActivityAuthoritative(AActor* Source, const FPlayerActivityDefinition& Definition)
{
    APawn* Player = Cast<APawn>(GetOwner());
    if (!Player || !Source || IsActivityActive() || !Source->Implements<UPlayerActivitySource>()) return false;
    if (!IPlayerActivitySource::Execute_CanStartActivity(Source, Player)) return false;
    if (FVector::DistSquared(Player->GetActorLocation(), Source->GetActorLocation()) > FMath::Square(Definition.MaxRange)) return false;

    ActivitySource = Source;
    ActiveDefinition = Definition;
    ActiveDefinition.Mechanic = ResolveMechanic(Definition);
    ActivityElapsed = 0.0f;
    Snapshot.State = EPlayerActivityState::Active;
    Snapshot.Type = Definition.Type;
    Snapshot.DisplayName = Definition.DisplayName;
    Snapshot.bThirdPersonView = Definition.bThirdPersonView;
    Snapshot.Progress = 0.0f;
    Snapshot.Mechanic = ActiveDefinition.Mechanic;
    Snapshot.Mistakes = 0;
    Snapshot.PositiveConnections = 0;
    Snapshot.ToolOffset = FVector2D::ZeroVector;
    Snapshot.ToolAccuracy = 1.0f;
    Snapshot.BloomInterference = Definition.bBloomSensitive ? Definition.MinimumBloomInterference : 0.0f;
    if (Definition.bBloomSensitive)
    {
        if (const UGameInstance* GameInstance = GetWorld() ? GetWorld()->GetGameInstance() : nullptr)
            if (const UBloomDirector* Bloom = GameInstance->GetSubsystem<UBloomDirector>())
                Snapshot.BloomInterference = FMath::Max(Snapshot.BloomInterference,
                    FMath::Clamp(static_cast<float>(static_cast<uint8>(Bloom->GetCurrentStage())) / 5.0f * Definition.BloomInterferenceScale, 0.0f, 1.0f));
    }
    BuildPuzzleSequence();
    Snapshot.CurrentInputIndex = 0;
    Snapshot.TotalInputs = ActiveDefinition.InputSequence.Num();
    Snapshot.ExpectedInput = ActiveDefinition.InputSequence.IsEmpty() ? EActivityInput::Primary : ActiveDefinition.InputSequence[0];
    UpdateDerivedPuzzleState();
    if (Definition.bLockMovement)
    {
        if (ACharacter* Character = Cast<ACharacter>(Player))
        {
            PreviousMovementMode = static_cast<uint8>(Character->GetCharacterMovement()->MovementMode);
            PreviousCustomMovementMode = Character->GetCharacterMovement()->CustomMovementMode;
            Character->GetCharacterMovement()->DisableMovement();
        }
    }
    BroadcastChanged();
    return true;
}

void UPlayerActivityComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    // Activities that are about the body (a squeeze through a gap) are watched from outside: the
    // owner's view goes to third person while one runs and returns to what it was after.
    if (ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(GetOwner()); Crew && Crew->IsLocallyControlled())
    {
        const bool bWantThird = IsActivityActive() && Snapshot.bThirdPersonView;
        if (bWantThird && !bViewSwitchedForActivity)
        {
            bViewWasFirstPerson = Crew->IsFirstPersonView();
            if (bViewWasFirstPerson) Crew->SetFirstPersonView(false);
            bViewSwitchedForActivity = true;
        }
        else if (!bWantThird && bViewSwitchedForActivity)
        {
            if (bViewWasFirstPerson) Crew->SetFirstPersonView(true);
            bViewSwitchedForActivity = false;
        }
    }
    // The body at work, on every machine: each kind of activity plays its clip on the crew while
    // it runs and lets go when it ends. Fab's interaction and free animation packs, retargeted to
    // Manny (tools/retarget_ue4_anims.py); Lyra's crouch set for the rest.
    if (ACharacter* Body = Cast<ACharacter>(GetOwner()))
    {
        UAnimInstance* Anim = Body->GetMesh() ? Body->GetMesh()->GetAnimInstance() : nullptr;
        const bool bWantPose = IsActivityActive();
        if (bWantPose && !bCrawlPosePlaying && Anim)
        {
            const TCHAR* Clip = nullptr;
            float Rate = 1.0f;
            const FString Name = Snapshot.DisplayName.ToString();
            if (Snapshot.bThirdPersonView)
            {
                // A crawl through a duct on the belly; a squeeze through a gap sideways on.
                Clip = Name.Contains(TEXT("rawl")) ? TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Prone/RT_anim_Prone_Fwd_Loop_R.RT_anim_Prone_Fwd_Loop_R")
                                                   : TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_Narrow.RT_A_Narrow");
                Rate = Name.Contains(TEXT("rawl")) ? 0.8f : 0.6f;
            }
            else switch (Snapshot.Type)
            {
            case EPlayerActivityType::Welding:
                Clip = TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_Door_CrowbarBrake.RT_A_Door_CrowbarBrake"); Rate = 0.5f; break;
            case EPlayerActivityType::HullPatching:
            case EPlayerActivityType::PipeSealing:
                Clip = TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_PlaceDevice.RT_A_PlaceDevice"); Rate = 0.7f; break;
            case EPlayerActivityType::ComponentReplacement:
            case EPlayerActivityType::Fabrication:
                Clip = TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_PlaceDeviceFloor.RT_A_PlaceDeviceFloor"); Rate = 0.7f; break;
            default:
                Clip = TEXT("/Game/Characters/Mannequins/Anims/Retargeted/Interaction/RT_A_KeyBoardUse.RT_A_KeyBoardUse"); Rate = 1.0f; break;
            }
            UAnimSequenceBase* Loaded = Clip ? LoadObject<UAnimSequenceBase>(nullptr, Clip) : nullptr;
            if (!Loaded)
            {
                Loaded = LoadObject<UAnimSequenceBase>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Lyra/crouch/MM_Unarmed_Crouch_Idle.MM_Unarmed_Crouch_Idle"));
            }
            if (Loaded)
            {
                CrawlLoop = Loaded;
                Anim->PlaySlotAnimationAsDynamicMontage(Loaded, TEXT("DefaultSlot"), 0.25f, 0.25f, Rate, 0, -1.0f, 0.0f);
                bCrawlPosePlaying = true;
            }
        }
        else if (!bWantPose && bCrawlPosePlaying)
        {
            if (Anim) Anim->StopSlotAnimation(0.25f, TEXT("DefaultSlot"));
            bCrawlPosePlaying = false;
        }
    }
    if (!GetOwner() || !GetOwner()->HasAuthority() || !IsActivityActive()) return;
    float TaskEfficiency = 1.0f;
    if (const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(GetOwner()))
        if (const UPlayerStatusEffectComponent* StatusEffects = Character->GetStatusEffectComponent())
            TaskEfficiency = StatusEffects->GetTaskEfficiencyMultiplier();
    ActivityElapsed += DeltaTime;
    if (!IsValid(ActivitySource)) { FinishActivity(EPlayerActivityState::Cancelled); return; }

    // Shipboard work is audible. Reported from the source rather than the worker so the noise
    // comes from the machinery being operated, which is where an investigating AI should look.
    // The subsystem coalesces per instigator, so reporting every tick is intended and cheap.
    if (ActiveDefinition.WorkNoiseLoudness > 0.0f)
    {
        if (UWorld* World = GetWorld())
        {
            if (UNoisePerceptionSubsystem* Perception = World->GetSubsystem<UNoisePerceptionSubsystem>())
            {
                Perception->ReportNoise(ActivitySource->GetActorLocation(),
                    ActiveDefinition.WorkNoiseLoudness, ENoiseCategory::Tool, GetOwner());
            }
        }
    }
    if (ActiveDefinition.bCancelWhenOutOfRange && FVector::DistSquared(GetOwner()->GetActorLocation(), ActivitySource->GetActorLocation()) > FMath::Square(ActiveDefinition.MaxRange))
    {
        FinishActivity(EPlayerActivityState::Cancelled);
        return;
    }
    if (Snapshot.Mechanic == EActivityMechanic::ToolPath)
    {
        // The seam advances beneath the tool and does not run dead straight: a plate's edge wanders,
        // slowly and then not so slowly, and the torch has to follow it -- holding still is not
        // welding. Bloom adds its own organic pull on top.
        const float SeamWander = FMath::Sin(ActivityElapsed * 0.9f) * 0.34f + FMath::Sin(ActivityElapsed * 2.3f + 1.1f) * 0.16f;
        const float BloomDrift = FMath::Sin(ActivityElapsed * (1.7f + Snapshot.BloomInterference * 2.0f)) * Snapshot.BloomInterference * 0.38f;
        Snapshot.SeamOffset = FMath::Clamp(SeamWander + BloomDrift, -1.0f, 1.0f);
        const float Error = FMath::Abs(Snapshot.ToolOffset.Y - Snapshot.SeamOffset);
        Snapshot.ToolAccuracy = FMath::Clamp(1.0f - Error / FMath::Max(ActiveDefinition.ToolPathTolerance, 0.05f), 0.0f, 1.0f);
        if (Snapshot.ToolAccuracy > 0.0f)
            Snapshot.Progress = FMath::Clamp(Snapshot.Progress + DeltaTime / FMath::Max(ActiveDefinition.DurationSeconds, 0.1f) * Snapshot.ToolAccuracy * TaskEfficiency, 0.0f, 1.0f);
        else if (Snapshot.BloomInterference >= 0.6f)
            Snapshot.Progress = FMath::Max(0.0f, Snapshot.Progress - DeltaTime * 0.08f * Snapshot.BloomInterference);
        BroadcastChanged();
        if (Snapshot.Progress >= 1.0f) FinishActivity(EPlayerActivityState::Completed);
    }
    else if (ActiveDefinition.InputSequence.IsEmpty())
    {
        Snapshot.Progress = FMath::Clamp(Snapshot.Progress + DeltaTime * TaskEfficiency / FMath::Max(ActiveDefinition.DurationSeconds, 0.1f), 0.0f, 1.0f);
        BroadcastChanged();
        if (Snapshot.Progress >= 1.0f) FinishActivity(EPlayerActivityState::Completed);
    }
}

void UPlayerActivityComponent::SubmitInput(EActivityInput Input)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) ServerSubmitInput(Input);
    else SubmitInputAuthoritative(Input);
}

void UPlayerActivityComponent::ServerSubmitInput_Implementation(EActivityInput Input) { SubmitInputAuthoritative(Input); }

void UPlayerActivityComponent::SubmitInputAuthoritative(EActivityInput Input)
{
    if (!IsActivityActive() || ActiveDefinition.InputSequence.IsEmpty()) return;
    if (Input != ActiveDefinition.InputSequence[Snapshot.CurrentInputIndex])
    {
        ++Snapshot.Mistakes;
        // Puppeteer-tier interference can invalidate the last unconfirmed match.
        if (Snapshot.BloomInterference >= 0.6f && Snapshot.CurrentInputIndex > 0)
            --Snapshot.CurrentInputIndex;
        Snapshot.Progress = static_cast<float>(Snapshot.CurrentInputIndex) / ActiveDefinition.InputSequence.Num();
        Snapshot.PositiveConnections = Snapshot.Mechanic == EActivityMechanic::CableMatching ? Snapshot.CurrentInputIndex : 0;
        UpdateDerivedPuzzleState();
        if (Snapshot.Mistakes >= ActiveDefinition.AllowedMistakes) FinishActivity(EPlayerActivityState::Failed);
        else BroadcastChanged();
        return;
    }
    ++Snapshot.CurrentInputIndex;
    Snapshot.Progress = static_cast<float>(Snapshot.CurrentInputIndex) / ActiveDefinition.InputSequence.Num();
    Snapshot.PositiveConnections = Snapshot.Mechanic == EActivityMechanic::CableMatching ? Snapshot.CurrentInputIndex : 0;
    UpdateDerivedPuzzleState();
    if (Snapshot.CurrentInputIndex >= ActiveDefinition.InputSequence.Num()) FinishActivity(EPlayerActivityState::Completed);
    else { Snapshot.ExpectedInput = ActiveDefinition.InputSequence[Snapshot.CurrentInputIndex]; BroadcastChanged(); }
}

void UPlayerActivityComponent::SubmitToolDelta(FVector2D Delta)
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) ServerSubmitToolDelta(Delta);
    else SubmitToolDeltaAuthoritative(Delta);
}

void UPlayerActivityComponent::ServerSubmitToolDelta_Implementation(FVector2D Delta) { SubmitToolDeltaAuthoritative(Delta); }

void UPlayerActivityComponent::SubmitToolDeltaAuthoritative(FVector2D Delta)
{
    if (!UsesToolPath()) return;
    Snapshot.ToolOffset = FVector2D(
        FMath::Clamp(Snapshot.ToolOffset.X + Delta.X * 0.025f, -1.0f, 1.0f),
        FMath::Clamp(Snapshot.ToolOffset.Y + Delta.Y * 0.025f, -1.0f, 1.0f));
}

EActivityMechanic UPlayerActivityComponent::ResolveMechanic(const FPlayerActivityDefinition& Definition) const
{
    if (Definition.Mechanic != EActivityMechanic::Automatic) return Definition.Mechanic;
    if (Definition.Type == EPlayerActivityType::Welding) return EActivityMechanic::ToolPath;
    if (Definition.Type == EPlayerActivityType::Scan) return EActivityMechanic::GenomeSequence;
    if (Definition.Type == EPlayerActivityType::Rewire) return EActivityMechanic::CableMatching;
    return EActivityMechanic::Timed;
}

void UPlayerActivityComponent::BuildPuzzleSequence()
{
    if (ActiveDefinition.Mechanic != EActivityMechanic::GenomeSequence &&
        ActiveDefinition.Mechanic != EActivityMechanic::CableMatching &&
        ActiveDefinition.Mechanic != EActivityMechanic::OrderedAssembly &&
        ActiveDefinition.Mechanic != EActivityMechanic::DiagnosticSequence) return;
    if (!ActiveDefinition.InputSequence.IsEmpty()) return;
    const int32 ExtraBloomSteps = FMath::RoundToInt(Snapshot.BloomInterference * 3.0f);
    const int32 Steps = FMath::Clamp(ActiveDefinition.PuzzleSteps + ExtraBloomSteps, 1, 16);
    FRandomStream PuzzleRandom(GetTypeHash(ActivitySource->GetFName()) ^ FMath::RoundToInt(GetWorld()->GetTimeSeconds() * 10.0f));
    for (int32 Index = 0; Index < Steps; ++Index)
        ActiveDefinition.InputSequence.Add(static_cast<EActivityInput>(PuzzleRandom.RandRange(0, 3)));
}

void UPlayerActivityComponent::UpdateDerivedPuzzleState()
{
    const float PuzzleProgress = Snapshot.TotalInputs > 0
        ? static_cast<float>(Snapshot.CurrentInputIndex) / Snapshot.TotalInputs : Snapshot.Progress;
    Snapshot.ConsumablePercent = FMath::Clamp(1.0f - Snapshot.Mistakes * 0.12f - PuzzleProgress * 0.08f, 0.0f, 1.0f);
    const float Evidence = static_cast<float>(Snapshot.CurrentInputIndex + 1);
    Snapshot.ConfidencePercent = FMath::Clamp((Evidence - Snapshot.Mistakes * 0.65f) / FMath::Max(Evidence, 1.0f), 0.0f, 1.0f);

    if (Snapshot.Mechanic == EActivityMechanic::GenomeSequence)
    {
        if (PuzzleProgress < 0.2f) Snapshot.ProcedurePhase = EActivityProcedurePhase::Prepare;
        else if (PuzzleProgress < 0.75f) Snapshot.ProcedurePhase = EActivityProcedurePhase::Diagnose;
        else Snapshot.ProcedurePhase = EActivityProcedurePhase::Verify;
    }
    else if (Snapshot.Mechanic == EActivityMechanic::CableMatching)
    {
        if (PuzzleProgress < 0.2f) Snapshot.ProcedurePhase = EActivityProcedurePhase::Diagnose;
        else if (PuzzleProgress < 0.55f) Snapshot.ProcedurePhase = EActivityProcedurePhase::Repair;
        else if (PuzzleProgress < 0.85f) Snapshot.ProcedurePhase = EActivityProcedurePhase::Balance;
        else Snapshot.ProcedurePhase = EActivityProcedurePhase::Verify;

        Snapshot.Voltage = FMath::Max(0.0f, 28.7f - Snapshot.Mistakes * 1.8f - Snapshot.BloomInterference * 1.2f);
        Snapshot.CurrentAmps = 4.2f + PuzzleProgress * 9.5f + Snapshot.Mistakes * 1.4f + Snapshot.BloomInterference * 1.8f;
        Snapshot.LoadPercent = Snapshot.CurrentAmps / 15.0f;
        Snapshot.bOverload = Snapshot.LoadPercent > 0.95f;
        Snapshot.bContinuityPassed = Snapshot.CurrentInputIndex >= Snapshot.TotalInputs && !Snapshot.bOverload;
    }
}

void UPlayerActivityComponent::CancelActivity()
{
    if (!GetOwner() || !GetOwner()->HasAuthority()) ServerCancelActivity();
    else FinishActivity(EPlayerActivityState::Cancelled);
}

void UPlayerActivityComponent::ServerCancelActivity_Implementation() { FinishActivity(EPlayerActivityState::Cancelled); }

void UPlayerActivityComponent::FinishActivity(EPlayerActivityState FinalState)
{
    if (!IsActivityActive()) return;
    APawn* Player = Cast<APawn>(GetOwner());
    AActor* CompletedSource = ActivitySource;
    const EPlayerActivityType FinishedType = ActiveDefinition.Type;
    Snapshot.State = FinalState;
    if (FinalState == EPlayerActivityState::Completed && IsValid(CompletedSource) && CompletedSource->Implements<UPlayerActivitySource>())
        IPlayerActivitySource::Execute_OnActivityCompleted(CompletedSource, Player);

    // The interface says what happened. Completed and failed are different sounds on purpose: a
    // player mid-repair is usually looking at the panel rather than at the progress bar, and the
    // sound is what tells them which way it went.
    if (UGameInstance* GameInstance = GetOwner() ? GetOwner()->GetGameInstance() : nullptr)
    {
        if (UUiSoundSubsystem* UiSound = GameInstance->GetSubsystem<UUiSoundSubsystem>())
        {
            if (FinalState == EPlayerActivityState::Completed)
            {
                UiSound->PlayUiSound(EUiSoundEvent::Confirm);
            }
            else if (FinalState == EPlayerActivityState::Failed)
            {
                UiSound->PlayUiSound(EUiSoundEvent::Reject);
            }
        }
    }

    // Failing an activity costs more than the time spent on it.
    //
    // Deliberately only on Failed, not on Cancelled. A player who walks away from a panel has
    // decided something; a player whose weld went wrong has had something happen to them, and only
    // the second is stressful. Conflating them would make backing out of a menu injurious.
    if (FinalState == EPlayerActivityState::Failed)
    {
        if (UPlayerStatusEffectComponent* Status = GetOwner()
            ? GetOwner()->FindComponentByClass<UPlayerStatusEffectComponent>() : nullptr)
        {
            Status->ApplyStressEvent(EPlayerStressEvent::FailedTask);

            // A botched weld can burn the welder, and how likely that is depends on the state of
            // their gear. This is the consequence durability has been missing: until now worn
            // equipment only ever locked an action out, which the player experiences as the game
            // saying no rather than as a risk they took.
            //
            // Condition comes from GetWorstSlotCondition because there is no distinct tool slot --
            // EEquipmentSlot is Head/Chest/Arms/Legs/Accessory, all armour. That is the honest
            // approximation available today and not the intended model: the welder's own condition
            // is what should drive this. Tracked in TRO-267.
            if (FinishedType == EPlayerActivityType::Welding)
            {
                if (UEquipmentComponent* Equipment = GetOwner()
                    ? GetOwner()->FindComponentByClass<UEquipmentComponent>() : nullptr)
                {
                    Status->ApplyWeldingBackfire(Equipment->GetWorstSlotCondition());
                }
            }
        }
    }
    if (ActiveDefinition.bLockMovement)
        if (ACharacter* Character = Cast<ACharacter>(Player)) Character->GetCharacterMovement()->SetMovementMode(static_cast<EMovementMode>(PreviousMovementMode), PreviousCustomMovementMode);
    ActivitySource = nullptr;
    ActiveDefinition = FPlayerActivityDefinition();
    BroadcastChanged();
}

void UPlayerActivityComponent::OnRep_Snapshot() { BroadcastChanged(); }
void UPlayerActivityComponent::BroadcastChanged() { OnActivityChanged.Broadcast(Snapshot); }
