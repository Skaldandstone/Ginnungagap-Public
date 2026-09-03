// Copyright Epic Games, Inc. All Rights Reserved.

#include "AI/PatrollingEnemyController.h"
#include "AI/HorrorEnemy.h"
#include "CoopSurvivalCharacter.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Ship/ShipSection.h"
#include "Ship/ShipNavigationSubsystem.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Navigation/PathFollowingComponent.h"
#include "Bloom/BloomDirector.h"
#include "Engine/GameInstance.h"
#include "Stealth/NoisePerceptionSubsystem.h"
#include "Stealth/PlayerVisibilityComponent.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "Threats/EncounterPacingSubsystem.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Versus/VersusGameState.h"

APatrollingEnemyController::APatrollingEnemyController()
{
    PrimaryActorTick.bCanEverTick = true;
}

void APatrollingEnemyController::BeginPlay()
{
    Super::BeginPlay();

    InitializePatrolPoints();

    if (BehaviorTree)
    {
        RunBehaviorTree(BehaviorTree);
    }
}

void APatrollingEnemyController::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    UpdatePlayerDetection(DeltaTime);
    UpdateHearing(DeltaTime);

    UEncounterPacingSubsystem* Pacing = GetWorld()
        ? GetWorld()->GetSubsystem<UEncounterPacingSubsystem>() : nullptr;

    if (DetectedTarget)
    {
        // Reported every frame while the target is held rather than only on the transition. The
        // subsystem ignores a repeat of the phase it is already in, and reporting once on the edge
        // would mean a hunter that re-acquires the player during Relief -- which is exactly the
        // moment it matters -- fails to escalate because it never lost them long enough to
        // transition.
        if (Pacing)
        {
            Pacing->NotifyPlayerDetected();
        }
        TimeSinceLostPlayer = 0.0f;
        PursuedTarget = DetectedTarget;
    }
    else if (TimeSinceLostPlayer < LoseInterestTime)
    {
        TimeSinceLostPlayer += DeltaTime;

        // Crossing the threshold is the enemy giving up, which is the player having got away with
        // it. Credited exactly once, on the frame it crosses, because the condition stays true
        // afterwards and this would otherwise fire every tick until something else was seen.
        if (TimeSinceLostPlayer >= LoseInterestTime)
        {
            if (AActor* Escaped = PursuedTarget.Get())
            {
                if (UPlayerStatusEffectComponent* Status =
                    Escaped->FindComponentByClass<UPlayerStatusEffectComponent>())
                {
                    Status->ApplyStressEvent(EPlayerStressEvent::SurvivedEncounter);
                }
            }

            // The same moment ends the pressure. Reported rather than inferred, because "gave up"
            // is a thing only the controller knows -- it is not the frame the player broke line of
            // sight, it is LoseInterestTime after it.
            if (Pacing)
            {
                Pacing->NotifyEncounterSurvived();
            }
            PursuedTarget = nullptr;
        }
    }

    // Sight outranks hearing: a confirmed visible target supersedes any noise investigation.
    if (DetectedTarget)
    {
        Awareness = EEnemyAwareness::Alert;
        InvestigateTimeRemaining = 0.0f;
        bInvestigateMoveIssued = false;
    }
    else if (InvestigateTimeRemaining > 0.0f)
    {
        Awareness = EEnemyAwareness::Suspicious;
        InvestigateTimeRemaining -= DeltaTime;
    }
    else
    {
        Awareness = EEnemyAwareness::Unaware;
        bInvestigateMoveIssued = false;
    }

    // A BehaviorTree, if assigned, is fully responsible for movement (see BeginPlay/RunBehaviorTree
    // and UBTTask_MoveToPatrolPoint). Without one, drive patrol/chase movement natively below so
    // enemies still move.
    if (BehaviorTree)
    {
        return;
    }

    if (bAnchored)
    {
        if (GetMoveStatus() != EPathFollowingStatus::Idle)
        {
            StopMovement();
        }
        bPatrolMoveInProgress = false;
        bInvestigateMoveIssued = false;
        return;
    }

	APawn* CommandedPawn = GetPawn();
	if (const UTeamAffiliationComponent* Affiliation =
		CommandedPawn ? CommandedPawn->FindComponentByClass<UTeamAffiliationComponent>() : nullptr)
	{
		if (const AVersusGameState* VersusState = GetWorld()->GetGameState<AVersusGameState>())
		{
			FAntagonistCommandOrder Order;
			if (VersusState->GetHighestPriorityOrderForFaction(Affiliation->Faction, Order))
			{
				bPatrolMoveInProgress = false;
				if (IsValid(Order.TargetActor)) MoveToActor(Order.TargetActor, PatrolAcceptanceRadius);
				else MoveToLocation(Order.TargetLocation, PatrolAcceptanceRadius);
				return;
			}
		}
	}

    if (ACharacter* ControlledCharacter = Cast<ACharacter>(GetPawn()))
    {
        if (UCharacterMovementComponent* MovementComponent = ControlledCharacter->GetCharacterMovement())
        {
            switch (Awareness)
            {
            case EEnemyAwareness::Alert:      MovementComponent->MaxWalkSpeed = ChaseSpeed; break;
            case EEnemyAwareness::Suspicious: MovementComponent->MaxWalkSpeed = InvestigateSpeed; break;
            default:                          MovementComponent->MaxWalkSpeed = PatrolSpeed; break;
            }
        }
    }

    if (DetectedTarget)
    {
        bPatrolMoveInProgress = false;
        MoveToActor(DetectedTarget, PatrolAcceptanceRadius);
        return;
    }

    // Heard something but cannot see it: move to the noise and search there. The patrol route is
    // deliberately left untouched so the AI resumes where it left off once the search expires.
    if (Awareness == EEnemyAwareness::Suspicious)
    {
        if (!bInvestigateMoveIssued)
        {
            bPatrolMoveInProgress = false;
            bInvestigateMoveIssued = true;
            MoveToLocation(InvestigationLocation, PatrolAcceptanceRadius);
        }
        return;
    }

    if (GetMoveStatus() != EPathFollowingStatus::Idle)
    {
        return;
    }

    if (PatrolSections.Num() > 0)
    {
        if (bPatrolMoveInProgress)
        {
            bPatrolMoveInProgress = false;
            AdvancePatrolStep();
        }

        AShipSection* Target = GetCurrentPatrolTarget();
        if (!Target)
        {
            ComputePathToNextSection();
            Target = GetCurrentPatrolTarget();
        }

        if (Target)
        {
            MoveToLocation(Target->GetActorLocation(), PatrolAcceptanceRadius);
            bPatrolMoveInProgress = true;
        }
    }
    else if (PatrolPoints.Num() > 0)
    {
        if (bPatrolMoveInProgress)
        {
            CurrentPatrolIndex = (CurrentPatrolIndex + 1) % PatrolPoints.Num();
            bPatrolMoveInProgress = false;
        }

        MoveToLocation(PatrolPoints[CurrentPatrolIndex], PatrolAcceptanceRadius);
        bPatrolMoveInProgress = true;
    }
}

void APatrollingEnemyController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    OwnerEnemy = Cast<AHorrorEnemy>(InPawn);
}

void APatrollingEnemyController::InitializePatrolPoints()
{
    CurrentPatrolIndex = 0;
}

bool APatrollingEnemyController::IsBloomAligned() const
{
    const APawn* ControlledPawn = GetPawn();
    if (!ControlledPawn)
    {
        return false;
    }

    const UTeamAffiliationComponent* Affiliation = ControlledPawn->FindComponentByClass<UTeamAffiliationComponent>();
    return Affiliation && Affiliation->Faction == EAntagonistFaction::Bloom;
}

float APatrollingEnemyController::GetBloomPerceptionScale() const
{
    // Only the organism adapts. A pirate boarding party does not get sharper senses because the
    // Bloom matured somewhere else on the ship.
    if (!bAdaptsWithBloomStage || !IsBloomAligned())
    {
        return 1.0f;
    }

    const UWorld* World = GetWorld();
    const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    const UBloomDirector* Bloom = GameInstance ? GameInstance->GetSubsystem<UBloomDirector>() : nullptr;
    if (!Bloom)
    {
        return 1.0f;
    }

    // Latent maps to 1.0 (no advantage) and Manifestation to the configured maximum, so the
    // curve stays anchored at both ends even if stages are added between them.
    constexpr float LastStage = static_cast<float>(EBloomStage::Manifestation);
    const float StageAlpha = FMath::Clamp(
        static_cast<float>(static_cast<uint8>(Bloom->GetCurrentStage())) / LastStage, 0.0f, 1.0f);
    return FMath::Lerp(1.0f, FMath::Max(1.0f, MaxBloomPerceptionScale), StageAlpha);
}

float APatrollingEnemyController::GetPacingPerceptionScale() const
{
    if (!bObeysEncounterPacing)
    {
        return 1.0f;
    }

    const UWorld* World = GetWorld();
    const UEncounterPacingSubsystem* Pacing =
        World ? World->GetSubsystem<UEncounterPacingSubsystem>() : nullptr;

    // No pacing subsystem is a legitimate state, not a failure: a test map or a level that wants
    // its threats unpaced simply does not have one, and 1.0 means "behave exactly as before".
    return Pacing ? Pacing->GetPerceptionScale() : 1.0f;
}

void APatrollingEnemyController::UpdatePlayerDetection(float DeltaTime)
{
    APawn* ControlledPawn = GetPawn();
    if (!ControlledPawn)
    {
        DetectedTarget = nullptr;
        PendingVisualTarget = nullptr;
        DetectionProgress = 0.0f;
        return;
    }

    // Boarders and creatures must remain dangerous in co-op instead of tunnelling on player 0.
    PendingVisualTarget = nullptr;
    float BestExposure = 0.0f;

    const FVector ObserverLocation = ControlledPawn->GetActorLocation();
    const FVector ObserverForward = ControlledPawn->GetActorForwardVector();
    const float ConeCosine = FMath::Cos(FMath::DegreesToRadians(VisionConeHalfAngleDegrees));

    // A maturing Bloom sees further and recognises faster. Cone angle is deliberately left alone:
    // widening it toward 360 would undo the "approach from behind" counterplay entirely, whereas
    // range and speed pressure the player without removing an option.
    // Both scales, multiplied. See the header for why they stay separate.
    const float BloomScale = GetBloomPerceptionScale() * GetPacingPerceptionScale();
    const bool bIsBloomHost = IsBloomAligned();
    const float EffectiveDetectionRange = DetectionRange * BloomScale;

    for (TActorIterator<APawn> It(GetWorld()); It; ++It)
    {
        APawn* Candidate = *It;
        if (!IsValid(Candidate) || Candidate == ControlledPawn
            || !UTeamAffiliationComponent::AreActorsHostile(ControlledPawn, Candidate))
        {
            continue;
        }
        if (const ACoopSurvivalCharacter* Crew = Cast<ACoopSurvivalCharacter>(Candidate); Crew && Crew->bIsDead)
        {
            continue;
        }
        if (const AHorrorEnemy* Enemy = Cast<AHorrorEnemy>(Candidate); Enemy && Enemy->IsDead())
        {
            continue;
        }

        const FVector ToCandidate = Candidate->GetActorLocation() - ObserverLocation;
        const float Distance = ToCandidate.Size();
        if (Distance > EffectiveDetectionRange || Distance <= KINDA_SMALL_NUMBER)
        {
            continue;
        }

        // Vision is a forward cone, not a sphere: approaching from behind is now viable.
        const float Facing = FVector::DotProduct(ObserverForward, ToCandidate / Distance);
        if (Facing < ConeCosine)
        {
            continue;
        }

        if (!LineOfSightTo(Candidate))
        {
            continue;
        }

        // Closer and more central targets resolve faster, and the target's own state (darkness,
        // stillness) scales how quickly it is noticed at all.
        float Exposure = 1.0f - (Distance / EffectiveDetectionRange);
        Exposure *= FMath::GetMappedRangeValueClamped(FVector2D(ConeCosine, 1.0f), FVector2D(0.6f, 1.0f), Facing);

        if (const UPlayerVisibilityComponent* Visibility = Candidate->FindComponentByClass<UPlayerVisibilityComponent>())
        {
            Exposure *= Visibility->GetVisibilityMultiplier();

            // The organism learns only from tactics used against it: a pirate boarding party
            // watching someone hide in the dark teaches the Bloom nothing.
            if (bIsBloomHost)
            {
                Visibility->ReportActiveTacticsToBloom();
            }
        }

        if (Exposure > BestExposure)
        {
            BestExposure = Exposure;
            PendingVisualTarget = Candidate;
        }
    }

    if (PendingVisualTarget)
    {
        DetectionProgress = FMath::Clamp(
            DetectionProgress + BestExposure * DetectionBuildRate * BloomScale * DeltaTime, 0.0f, 1.0f);
    }
    else
    {
        DetectionProgress = FMath::Clamp(
            DetectionProgress - DetectionDecayRate * DeltaTime, 0.0f, 1.0f);
    }

    // Confirmed only once certainty is earned. Losing sight drains it, so breaking line of sight
    // during a partial sighting genuinely lets a player slip away.
    if (PendingVisualTarget && DetectionProgress >= ConfirmedDetectionThreshold)
    {
        DetectedTarget = PendingVisualTarget;
    }
    else if (!PendingVisualTarget && DetectionProgress <= 0.0f)
    {
        DetectedTarget = nullptr;
    }
    else if (DetectedTarget && DetectionProgress < SuspicionDetectionThreshold)
    {
        DetectedTarget = nullptr;
    }

    // A partial sighting is still worth walking over to check, even before identification.
    if (!DetectedTarget && PendingVisualTarget && DetectionProgress >= SuspicionDetectionThreshold)
    {
        InvestigationLocation = PendingVisualTarget->GetActorLocation();
        InvestigateTimeRemaining = FMath::Max(InvestigateTimeRemaining, InvestigateDurationSeconds);
        bInvestigateMoveIssued = false;
    }
}

void APatrollingEnemyController::UpdateHearing(float DeltaTime)
{
    APawn* ControlledPawn = GetPawn();
    UWorld* World = GetWorld();
    if (!ControlledPawn || !World)
    {
        return;
    }

    // Hearing resolves on the authority alongside the rest of the perception state.
    if (World->GetNetMode() == NM_Client)
    {
        return;
    }

    UNoisePerceptionSubsystem* Perception = World->GetSubsystem<UNoisePerceptionSubsystem>();
    if (!Perception)
    {
        return;
    }

    FNoiseEvent Heard;
    float Strength = 0.0f;
    if (!Perception->QueryLoudestAudibleNoise(ControlledPawn->GetActorLocation(),
        HearingRangeScale * GetBloomPerceptionScale() * GetPacingPerceptionScale(),
        ControlledPawn, Heard, Strength))
    {
        return;
    }

    // Only react to noise from something this AI would actually be hostile toward. Without this,
    // a boarding party would investigate its own squadmates' footsteps.
    if (const AActor* Source = Heard.Instigator.Get())
    {
        if (!UTeamAffiliationComponent::AreActorsHostile(ControlledPawn, Source))
        {
            return;
        }
    }

    // Re-target if this is meaningfully somewhere new, otherwise just refresh the search timer so
    // a continuously noisy target keeps the AI engaged rather than resetting its path every tick.
    const bool bNewLocation = FVector::DistSquared(InvestigationLocation, Heard.Location) > FMath::Square(150.0f);
    if (bNewLocation)
    {
        InvestigationLocation = Heard.Location;
        bInvestigateMoveIssued = false;
    }

    InvestigateTimeRemaining = FMath::Max(InvestigateTimeRemaining, InvestigateDurationSeconds);
}

bool APatrollingEnemyController::ComputePathToNextSection()
{
    if (PatrolSections.Num() == 0)
    {
        return false;
    }

    APawn* ControlledPawn = GetPawn();
    UWorld* World = GetWorld();
    if (!ControlledPawn || !World)
    {
        return false;
    }

    UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>();
    if (!Navigation)
    {
        return false;
    }

    AShipSection* CurrentSection = Navigation->GetSectionContainingLocation(ControlledPawn->GetActorLocation());
    if (!CurrentSection)
    {
        return false;
    }

    const int32 NumSections = PatrolSections.Num();
    for (int32 Attempt = 0; Attempt < NumSections; ++Attempt)
    {
        AShipSection* TargetSection = PatrolSections[CurrentSectionTargetIndex];
        TArray<AShipSection*> FoundPath;

        if (TargetSection && Navigation->FindSectionPath(CurrentSection, TargetSection, FoundPath))
        {
            CurrentPath = FoundPath;
            CurrentPathStepIndex = 0;
            return true;
        }

        CurrentSectionTargetIndex = (CurrentSectionTargetIndex + 1) % NumSections;
    }

    CurrentPath.Reset();
    CurrentPathStepIndex = 0;
    return false;
}

AShipSection* APatrollingEnemyController::GetCurrentPatrolTarget() const
{
    return CurrentPath.IsValidIndex(CurrentPathStepIndex) ? CurrentPath[CurrentPathStepIndex] : nullptr;
}

void APatrollingEnemyController::AdvancePatrolStep()
{
    CurrentPathStepIndex++;

    if (!CurrentPath.IsValidIndex(CurrentPathStepIndex))
    {
        if (PatrolSections.Num() > 0)
        {
            CurrentSectionTargetIndex = (CurrentSectionTargetIndex + 1) % PatrolSections.Num();
        }

        ComputePathToNextSection();
    }
}
