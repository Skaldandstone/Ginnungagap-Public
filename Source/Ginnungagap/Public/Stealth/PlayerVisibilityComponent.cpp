#include "Stealth/PlayerVisibilityComponent.h"

#include "Engine/World.h"
#include "CoopSurvivalCharacter.h"
#include "Progression/ClassSkillComponent.h"
#include "Ship/ModularShipRoom.h"
#include "Ship/ShipNavigationSubsystem.h"

UPlayerVisibilityComponent::UPlayerVisibilityComponent()
{
    // Purely a query surface: observers pull from it during their own perception update, so there
    // is nothing to advance on a tick of its own.
    PrimaryComponentTick.bCanEverTick = false;
}

float UPlayerVisibilityComponent::GetLightExposure() const
{
    const AActor* Owner = GetOwner();
    UWorld* World = GetWorld();
    if (!Owner || !World)
    {
        return 1.0f;
    }

    const UShipNavigationSubsystem* Navigation = World->GetSubsystem<UShipNavigationSubsystem>();
    if (!Navigation)
    {
        return 1.0f;
    }

    // Outside any registered room (EVA, unbuilt space) there is no power state to read from, so
    // treat the actor as fully lit rather than granting free concealment.
    const AShipSection* Section = Navigation->GetSectionContainingLocation(Owner->GetActorLocation());
    const AModularShipRoom* Room = Cast<const AModularShipRoom>(Section);
    if (!Room)
    {
        return 1.0f;
    }

    const bool bDark = !Room->bPowered
        || Room->OperationalState == EShipRoomOperationalState::Unpowered;

    if (!bDark)
    {
        return 1.0f;
    }

    // A Bloom that has learned to hunt in the dark gives back less concealment. Interpolating
    // toward 1.0 (fully visible) rather than scaling the multiplier keeps the erosion bounded by
    // the same floor the director enforces.
    const float Effectiveness = GetTacticEffectiveness(EBloomStealthTactic::Darkness);
    return FMath::Lerp(1.0f, DarkroomVisibility, Effectiveness);
}

float UPlayerVisibilityComponent::GetTacticEffectiveness(EBloomStealthTactic Tactic) const
{
    const UWorld* World = GetWorld();
    const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    const UBloomDirector* Bloom = GameInstance ? GameInstance->GetSubsystem<UBloomDirector>() : nullptr;

    // No director (tests, or a level without the Bloom) means no adaptation: tactics work fully.
    return Bloom ? Bloom->GetStealthTacticEffectiveness(Tactic) : 1.0f;
}

float UPlayerVisibilityComponent::GetMovementExposure() const
{
    const AActor* Owner = GetOwner();
    if (!Owner)
    {
        return 1.0f;
    }

    const float Speed = Owner->GetVelocity().Size();
    const float Effectiveness = GetTacticEffectiveness(EBloomStealthTactic::Stillness);
    const float AdaptedStillVisibility = FMath::Lerp(1.0f, StillVisibility, Effectiveness);

    return FMath::GetMappedRangeValueClamped(
        FVector2D(StillSpeedThreshold, FullyVisibleSpeed),
        FVector2D(AdaptedStillVisibility, 1.0f),
        Speed);
}

void UPlayerVisibilityComponent::ReportActiveTacticsToBloom() const
{
    const UWorld* World = GetWorld();
    const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
    UBloomDirector* Bloom = GameInstance ? GameInstance->GetSubsystem<UBloomDirector>() : nullptr;
    if (!Bloom)
    {
        return;
    }

    // Only count a tactic when it is actually being used against an observer. Standing in a dark
    // room alone teaches the organism nothing; being *missed* because of the dark is what it
    // learns from.
    if (GetLightExposure() < 1.0f)
    {
        Bloom->RegisterStealthTacticUse(EBloomStealthTactic::Darkness);
    }
    if (GetMovementExposure() < 1.0f)
    {
        Bloom->RegisterStealthTacticUse(EBloomStealthTactic::Stillness);
    }
}

float UPlayerVisibilityComponent::GetVisibilityMultiplier() const
{
    // Multiplicative rather than additive so the two factors compound: standing still in a dark
    // room is meaningfully better than either one alone, which is what makes both worth doing.
    float Combined = GetLightExposure() * GetMovementExposure();

    // Signature reduction scales the result but cannot breach MinimumVisibility below: a body in a
    // lit compartment is never invisible, however well dressed for it.
    if (const ACoopSurvivalCharacter* Character = Cast<ACoopSurvivalCharacter>(GetOwner()))
    {
        if (const UClassSkillComponent* Skills = Character->GetSkillComponent())
        {
            Combined *= Skills->GetCostMultiplier(SkillEffects::VisibilitySignature);
        }
    }

    return FMath::Clamp(Combined, MinimumVisibility, 1.0f);
}
