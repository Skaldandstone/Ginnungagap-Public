#include "RunOutcomeSubsystem.h"
#include "RunSaveGame.h"
#include "../Progression/ClassSkillTreeSubsystem.h"
#include "../Bloom/BloomDirector.h"
#include "../StarSystem/JumpSequenceSubsystem.h"
#include "../Ship/EscapePodSystem.h"
#include "../CoopSurvivalCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"

// Progression and expedition-resume data use different USaveGame classes and must never share a slot.
const TCHAR* URunOutcomeSubsystem::SaveSlotName = TEXT("GinnungagapProgressionSave");

void URunOutcomeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

	URunSaveGame* Save = Cast<URunSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, 0));
	if (!Save)
	{
		// One-time compatibility with early builds that stored both save types in the run slot.
		Save = Cast<URunSaveGame>(UGameplayStatics::LoadGameFromSlot(TEXT("GinnungagapRunSave"), 0));
	}
	if (Save)
	{
        TotalBankedCurrency = Save->BankedCurrency;
        CurrentPlayerRole = Save->SelectedRole;
        CurrentRoleSkills = Save->RoleSkills;
        CurrentRoleSkillPoints = Save->RoleSkillPoints;
    }
}

void URunOutcomeSubsystem::Deinitialize()
{
    if (UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr)
    {
        World->GetTimerManager().ClearTimer(SelfDestructTimerHandle);
    }

    Super::Deinitialize();
}

bool URunOutcomeSubsystem::ArmSelfDestruct()
{
    if (bRunResolved || bSelfDestructArmed)
    {
        return false;
    }

    bSelfDestructArmed = true;
    SelfDestructSecondsRemaining = SelfDestructCountdownSeconds;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            World->GetTimerManager().SetTimer(SelfDestructTimerHandle, this, &URunOutcomeSubsystem::TickSelfDestructCountdown, 1.0f, true);
        }
    }

    return true;
}

bool URunOutcomeSubsystem::CancelSelfDestruct()
{
    if (!bSelfDestructArmed)
    {
        return false;
    }

    bSelfDestructArmed = false;
    SelfDestructSecondsRemaining = 0.0f;

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UWorld* World = GI->GetWorld())
        {
            World->GetTimerManager().ClearTimer(SelfDestructTimerHandle);
        }
    }

    return true;
}

void URunOutcomeSubsystem::TickSelfDestructCountdown()
{
    SelfDestructSecondsRemaining = FMath::Max(0.0f, SelfDestructSecondsRemaining - 1.0f);
    OnSelfDestructTick(SelfDestructSecondsRemaining);

    if (SelfDestructSecondsRemaining <= 0.0f)
    {
        if (UGameInstance* GI = GetGameInstance())
        {
            if (UWorld* World = GI->GetWorld())
            {
                World->GetTimerManager().ClearTimer(SelfDestructTimerHandle);
            }
        }

        DetonateSelfDestruct();
    }
}

void URunOutcomeSubsystem::DetonateSelfDestruct()
{
    bSelfDestructArmed = false;

    UGameInstance* GI = GetGameInstance();
    UWorld* World = GI ? GI->GetWorld() : nullptr;
    UBloomDirector* Director = GI ? GI->GetSubsystem<UBloomDirector>() : nullptr;

    if (Director && Director->RollForSelfDestructCounter())
    {
        // The event is presentation only -- a BlueprintImplementableEvent with no C++ body and no
        // override, so on its own it did nothing at all. Without the resolve below, a countered
        // scuttle silently disarmed the ship and let the run carry on: no ending, no feedback, and
        // ERunOutcome::SelfDestructCountered was a value nothing ever assigned.
        OnSelfDestructCountered();
        ResolveRun(ERunOutcome::SelfDestructCountered);
        return;
    }

    if (World)
    {
        for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
        {
            ACoopSurvivalCharacter* Character = *It;
            bool bReachedEscapePod = false;

            for (TActorIterator<AEscapePodSystem> PodIt(World); PodIt; ++PodIt)
            {
                if (PodIt->bIsOccupied && PodIt->OccupyingCharacter.Get() == Character && PodIt->IsFunctioning())
                {
                    bReachedEscapePod = true;
                    break;
                }
            }

            if (!bReachedEscapePod)
            {
                Character->HealthPercent = 0.0f;
                Character->bIsDead = true;
            }
        }
    }

    if (Director)
    {
        Director->ForceResetBloom();
    }

    ResolveRun(ERunOutcome::SelfDestructSuccess);
}

void URunOutcomeSubsystem::EvaluateDestinationArrival()
{
    if (bRunResolved)
    {
        return;
    }

    UGameInstance* GI = GetGameInstance();
    UBloomDirector* Director = GI ? GI->GetSubsystem<UBloomDirector>() : nullptr;

    if (Director && Director->IsPresentThreat())
    {
        ResolveRun(ERunOutcome::HardLoss_BloomReachedDestination);
    }
    else
    {
        ResolveRun(ERunOutcome::Victory);
    }
}

void URunOutcomeSubsystem::ResolveRun(ERunOutcome Outcome)
{
    if (bRunResolved)
    {
        return;
    }

    bRunResolved = true;
    CurrentOutcome = Outcome;

    UGameInstance* GI = GetGameInstance();
    UWorld* World = GI ? GI->GetWorld() : nullptr;
    UBloomDirector* Director = GI ? GI->GetSubsystem<UBloomDirector>() : nullptr;
    UJumpSequenceSubsystem* JumpSequence = GI ? GI->GetSubsystem<UJumpSequenceSubsystem>() : nullptr;

    bool bPlayerSurvived = false;
    if (World)
    {
        for (TActorIterator<ACoopSurvivalCharacter> It(World); It; ++It)
        {
            if (!It->bIsDead)
            {
                bPlayerSurvived = true;
                break;
            }
        }
    }

    const bool bBloomEradicated = Outcome == ERunOutcome::SelfDestructSuccess || (Director && Director->IsFullyEradicated());
    const int32 JumpsCompleted = JumpSequence ? JumpSequence->JumpsCompleted : 0;

    int32 CurrencyEarned = JumpsCompleted * CurrencyPerJump;
    if (bPlayerSurvived)
    {
        CurrencyEarned += PlayerSurvivalBonus;
    }
    if (bBloomEradicated)
    {
        CurrencyEarned += BloomEradicationBonus;
    }
    if (bPlayerSurvived && bBloomEradicated)
    {
        CurrencyEarned += PerfectRunBonus;
    }

    if (Outcome == ERunOutcome::HardLoss_BloomReachedDestination)
    {
        CurrencyEarned = FMath::RoundToInt(CurrencyEarned * HardLossCurrencyMultiplier);
    }

    TotalBankedCurrency += CurrencyEarned;

    // Award skill points: base 1 point per jump, +2 if survived, +3 if bloom eradicated, +1 bonus if perfect
    int32 SkillPointsEarned = JumpsCompleted;
    if (bPlayerSurvived)
    {
        SkillPointsEarned += 2;
    }
    if (bBloomEradicated)
    {
        SkillPointsEarned += 3;
    }
    if (bPlayerSurvived && bBloomEradicated)
    {
        SkillPointsEarned += 1;
    }

    CurrentRoleSkillPoints.FindOrAdd(CurrentPlayerRole) += SkillPointsEarned;
    LastRoleSkillPointsEarned = SkillPointsEarned;

    SaveProgression();

    LastCurrencyEarned = CurrencyEarned;
    OnRunResolved(Outcome, CurrencyEarned, TotalBankedCurrency);
}

void URunOutcomeSubsystem::SetPlayerRole(EPressureSuitRole NewRole)
{
    CurrentPlayerRole = NewRole;
}

EPressureSuitRole URunOutcomeSubsystem::GetPlayerRole() const
{
    return CurrentPlayerRole;
}

int32 URunOutcomeSubsystem::GetRoleSkillPoints(EPressureSuitRole Role) const
{
    if (const int32* Points = CurrentRoleSkillPoints.Find(Role))
    {
        return *Points;
    }
    return 0;
}

FClassSkillsArray URunOutcomeSubsystem::GetRoleSkills(EPressureSuitRole Role) const
{
    if (const FClassSkillsArray* Skills = CurrentRoleSkills.Find(Role))
    {
        return *Skills;
    }
    return FClassSkillsArray();
}

UClassSkillTreeSubsystem* URunOutcomeSubsystem::GetSkillTree() const
{
    UGameInstance* GameInstance = GetGameInstance();
    return GameInstance ? GameInstance->GetSubsystem<UClassSkillTreeSubsystem>() : nullptr;
}

void URunOutcomeSubsystem::SaveProgression()
{
    // One place that knows the full shape of a save. This was previously copied at four call
    // sites, which is how a new progression field ends up persisted from three of them.
    URunSaveGame* Save = Cast<URunSaveGame>(UGameplayStatics::CreateSaveGameObject(URunSaveGame::StaticClass()));
    if (!Save)
    {
        return;
    }

    Save->BankedCurrency = TotalBankedCurrency;
    Save->SelectedRole = CurrentPlayerRole;
    Save->RoleSkills = CurrentRoleSkills;
    Save->RoleSkillPoints = CurrentRoleSkillPoints;
    UGameplayStatics::SaveGameToSlot(Save, SaveSlotName, 0);
}

bool URunOutcomeSubsystem::UnlockClassSkill(EPressureSuitRole Role, const FString& SkillID)
{
    UClassSkillTreeSubsystem* SkillTree = GetSkillTree();
    if (!SkillTree)
    {
        return false;
    }

    FClassSkillsArray& Owned = CurrentRoleSkills.FindOrAdd(Role);
    int32& Points = CurrentRoleSkillPoints.FindOrAdd(Role);

    // The catalogue decides legality and price. Taking a cost from the caller let a widget name
    // its own, and skipped prerequisites entirely.
    if (!SkillTree->CanUnlockSkill(Role, SkillID, Owned, Points))
    {
        return false;
    }

    const int32 Cost = SkillTree->GetNextRankCost(SkillID, Owned);
    Points -= Cost;

    int32& Rank = Owned.SkillRanks.FindOrAdd(SkillID);
    Rank = FMath::Max(0, Rank) + 1;

    SaveProgression();
    return true;
}

bool URunOutcomeSubsystem::UnlockClassSkillWithCurrency(EPressureSuitRole Role, const FString& SkillID)
{
    UClassSkillTreeSubsystem* SkillTree = GetSkillTree();
    if (!SkillTree)
    {
        return false;
    }

    FClassSkillsArray& Owned = CurrentRoleSkills.FindOrAdd(Role);

    // Currency buys the same node on the same rules, so pass the rank cost as the available points
    // to reuse the one legality check rather than writing a second, divergent one.
    const int32 RankCost = SkillTree->GetNextRankCost(SkillID, Owned);
    if (!SkillTree->CanUnlockSkill(Role, SkillID, Owned, RankCost))
    {
        return false;
    }

    const int32 CurrencyCost = SkillTree->GetNextRankCurrencyCost(SkillID, Owned);
    if (TotalBankedCurrency < CurrencyCost)
    {
        return false;
    }

    TotalBankedCurrency -= CurrencyCost;

    int32& Rank = Owned.SkillRanks.FindOrAdd(SkillID);
    Rank = FMath::Max(0, Rank) + 1;

    SaveProgression();
    return true;
}

bool URunOutcomeSubsystem::SetEquippedActiveSkills(EPressureSuitRole Role, const TArray<FString>& SkillIDs)
{
    UClassSkillTreeSubsystem* SkillTree = GetSkillTree();
    if (!SkillTree)
    {
        return false;
    }

    if (SkillIDs.Num() > FClassProgression::MaxEquippedActiveSkills)
    {
        return false;
    }

    FClassSkillsArray& Owned = CurrentRoleSkills.FindOrAdd(Role);

    // Validate the whole set before committing any of it, so a rejected pick cannot leave the
    // loadout half-applied.
    TArray<FString> Validated;
    for (const FString& SkillID : SkillIDs)
    {
        const FClassSkill Skill = SkillTree->GetSkillByID(SkillID);
        const bool bLegal = Skill.Activation == ESkillActivation::Active
            && SkillTree->IsSkillVisibleToRole(Skill, Role)
            && SkillTree->GetOwnedRank(SkillID, Owned) > 0
            && !Validated.Contains(SkillID);

        if (!bLegal)
        {
            return false;
        }
        Validated.Add(SkillID);
    }

    Owned.EquippedActiveSkills = Validated;
    SaveProgression();
    return true;
}

void URunOutcomeSubsystem::AwardPersistentCurrency(int32 Amount)
{
    if (Amount <= 0)
    {
        return;
    }

    TotalBankedCurrency += Amount;
    SaveProgression();
}
