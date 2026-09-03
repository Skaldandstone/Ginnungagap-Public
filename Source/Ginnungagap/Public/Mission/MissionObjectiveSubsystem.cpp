#include "Mission/MissionObjectiveSubsystem.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "UI/UiSoundSubsystem.h"

bool UMissionObjectiveSubsystem::AddObjective(const FMissionObjectiveDefinition& Definition)
{
    if (Definition.ObjectiveId.IsNone() || Definition.TargetProgress <= 0.0f || Objectives.Contains(Definition.ObjectiveId))
    {
        return false;
    }

    const bool bCouldJump = CanBeginJump();
    FMissionObjectiveRuntime Runtime;
    Runtime.Definition = Definition;
    Runtime.State = Definition.bAutoActivate && ArePrerequisitesComplete(Definition)
        ? EMissionObjectiveState::Active
        : EMissionObjectiveState::Pending;
    Objectives.Add(Definition.ObjectiveId, Runtime);
    NotifyChanged(Definition.ObjectiveId, Runtime.State, bCouldJump);
    return true;
}

bool UMissionObjectiveSubsystem::ActivateObjective(FName ObjectiveId)
{
    FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective || Objective->State != EMissionObjectiveState::Pending || !ArePrerequisitesComplete(Objective->Definition))
    {
        return false;
    }

    const bool bCouldJump = CanBeginJump();
    Objective->State = EMissionObjectiveState::Active;
    NotifyChanged(ObjectiveId, Objective->State, bCouldJump);
    return true;
}

bool UMissionObjectiveSubsystem::SetObjectiveProgress(FName ObjectiveId, float NewProgress)
{
    FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective || Objective->State != EMissionObjectiveState::Active)
    {
        return false;
    }

    Objective->CurrentProgress = FMath::Clamp(NewProgress, 0.0f, Objective->Definition.TargetProgress);
    if (Objective->CurrentProgress >= Objective->Definition.TargetProgress)
    {
        return CompleteObjective(ObjectiveId);
    }

    OnObjectiveChanged.Broadcast(ObjectiveId, Objective->State);
    return true;
}

bool UMissionObjectiveSubsystem::AddObjectiveProgress(FName ObjectiveId, float ProgressDelta)
{
    const FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    return Objective && ProgressDelta > 0.0f
        ? SetObjectiveProgress(ObjectiveId, Objective->CurrentProgress + ProgressDelta)
        : false;
}

bool UMissionObjectiveSubsystem::CompleteObjective(FName ObjectiveId)
{
    FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective || Objective->IsResolved())
    {
        return false;
    }

    const bool bCouldJump = CanBeginJump();
    Objective->CurrentProgress = Objective->Definition.TargetProgress;
    Objective->State = EMissionObjectiveState::Completed;

    if (Objective->Definition.CurrencyReward > 0)
    {
        if (UGameInstance* GameInstance = GetGameInstance())
        {
            if (URunOutcomeSubsystem* RunOutcome = GameInstance->GetSubsystem<URunOutcomeSubsystem>())
            {
                RunOutcome->AwardPersistentCurrency(Objective->Definition.CurrencyReward);
            }
        }
    }

    // The demo is five objectives long and completing one is its only real punctuation. Louder than
    // the confirm an activity gets, because it happens five times rather than constantly.
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UUiSoundSubsystem* UiSound = GameInstance->GetSubsystem<UUiSoundSubsystem>())
        {
            UiSound->PlayUiSound(EUiSoundEvent::ObjectiveComplete);
        }
    }

    NotifyChanged(ObjectiveId, Objective->State, bCouldJump);
    ActivateEligibleObjectives();
    return true;
}

bool UMissionObjectiveSubsystem::FailObjective(FName ObjectiveId, FText FailureReason)
{
    FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective || Objective->IsResolved())
    {
        return false;
    }

    const bool bCouldJump = CanBeginJump();
    Objective->State = EMissionObjectiveState::Failed;
    Objective->FailureReason = MoveTemp(FailureReason);
    NotifyChanged(ObjectiveId, Objective->State, bCouldJump);
    ActivateEligibleObjectives();
    return true;
}

bool UMissionObjectiveSubsystem::AbandonObjective(FName ObjectiveId)
{
    FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective || !Objective->Definition.bOptional || Objective->IsResolved())
    {
        return false;
    }

    const bool bCouldJump = CanBeginJump();
    Objective->State = EMissionObjectiveState::Abandoned;
    NotifyChanged(ObjectiveId, Objective->State, bCouldJump);
    ActivateEligibleObjectives();
    return true;
}

void UMissionObjectiveSubsystem::ResetForNextSystem()
{
    const bool bCouldJump = CanBeginJump();
    for (auto It = Objectives.CreateIterator(); It; ++It)
    {
        if (!It.Value().Definition.bPersistsAcrossSystems)
        {
            It.RemoveCurrent();
        }
    }
    if (bCouldJump != CanBeginJump())
    {
        OnJumpReadinessChanged.Broadcast(CanBeginJump());
    }
}

void UMissionObjectiveSubsystem::ResetAllObjectives()
{
    const bool bCouldJump = CanBeginJump();
    Objectives.Reset();
    if (bCouldJump != CanBeginJump())
    {
        OnJumpReadinessChanged.Broadcast(CanBeginJump());
    }
}

void UMissionObjectiveSubsystem::RestoreCompletedObjectives(const TArray<FName>& ObjectiveIds)
{
    const bool bCouldJump = CanBeginJump();
    for (const FName ObjectiveId : ObjectiveIds)
    {
        FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
        if (!Objective || Objective->State == EMissionObjectiveState::Completed)
        {
            continue;
        }
        Objective->CurrentProgress = Objective->Definition.TargetProgress;
        Objective->State = EMissionObjectiveState::Completed;
        OnObjectiveChanged.Broadcast(ObjectiveId, Objective->State);
    }
    ActivateEligibleObjectives();
    if (bCouldJump != CanBeginJump())
    {
        OnJumpReadinessChanged.Broadcast(CanBeginJump());
    }
}

bool UMissionObjectiveSubsystem::GetObjective(FName ObjectiveId, FMissionObjectiveRuntime& OutObjective) const
{
    const FMissionObjectiveRuntime* Objective = Objectives.Find(ObjectiveId);
    if (!Objective)
    {
        return false;
    }
    OutObjective = *Objective;
    return true;
}

TArray<FMissionObjectiveRuntime> UMissionObjectiveSubsystem::GetAllObjectives(bool bIncludeHidden) const
{
    TArray<FMissionObjectiveRuntime> Result;
    for (const TPair<FName, FMissionObjectiveRuntime>& Pair : Objectives)
    {
        if (bIncludeHidden || !Pair.Value.Definition.bHiddenUntilActive || Pair.Value.State != EMissionObjectiveState::Pending)
        {
            Result.Add(Pair.Value);
        }
    }
    return Result;
}

TArray<FMissionObjectiveRuntime> UMissionObjectiveSubsystem::GetActiveObjectives() const
{
    TArray<FMissionObjectiveRuntime> Result;
    for (const TPair<FName, FMissionObjectiveRuntime>& Pair : Objectives)
    {
        if (Pair.Value.State == EMissionObjectiveState::Active)
        {
            Result.Add(Pair.Value);
        }
    }
    return Result;
}

bool UMissionObjectiveSubsystem::AreRequiredObjectivesResolved() const
{
    for (const TPair<FName, FMissionObjectiveRuntime>& Pair : Objectives)
    {
        const FMissionObjectiveRuntime& Objective = Pair.Value;
        if (!Objective.Definition.bOptional && !Objective.IsResolved())
        {
            return false;
        }
    }
    return true;
}

bool UMissionObjectiveSubsystem::CanBeginJump() const
{
    for (const TPair<FName, FMissionObjectiveRuntime>& Pair : Objectives)
    {
        const FMissionObjectiveRuntime& Objective = Pair.Value;
        if (!Objective.Definition.bOptional && Objective.Definition.bBlocksJumpWhileUnresolved && !Objective.IsResolved())
        {
            return false;
        }
    }
    return true;
}

bool UMissionObjectiveSubsystem::ArePrerequisitesComplete(const FMissionObjectiveDefinition& Definition) const
{
    for (const FName PrerequisiteId : Definition.PrerequisiteObjectiveIds)
    {
        const FMissionObjectiveRuntime* Prerequisite = Objectives.Find(PrerequisiteId);
        if (!Prerequisite || Prerequisite->State != EMissionObjectiveState::Completed)
        {
            return false;
        }
    }
    return true;
}

void UMissionObjectiveSubsystem::ActivateEligibleObjectives()
{
    TArray<FName> Eligible;
    for (const TPair<FName, FMissionObjectiveRuntime>& Pair : Objectives)
    {
        if (Pair.Value.State == EMissionObjectiveState::Pending
            && Pair.Value.Definition.bAutoActivate
            && ArePrerequisitesComplete(Pair.Value.Definition))
        {
            Eligible.Add(Pair.Key);
        }
    }

    for (const FName ObjectiveId : Eligible)
    {
        ActivateObjective(ObjectiveId);
    }
}

void UMissionObjectiveSubsystem::NotifyChanged(FName ObjectiveId, EMissionObjectiveState State, bool bPreviousJumpReadiness)
{
    OnObjectiveChanged.Broadcast(ObjectiveId, State);
    const bool bCanJump = CanBeginJump();
    if (bCanJump != bPreviousJumpReadiness)
    {
        OnJumpReadinessChanged.Broadcast(bCanJump);
    }
}
