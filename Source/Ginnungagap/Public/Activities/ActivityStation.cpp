#include "Activities/ActivityStation.h"
#include "Activities/PlayerActivityComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"

AActivityStation::AActivityStation()
{
    bReplicates = true;
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    SetRootComponent(Mesh);
    Activity.DisplayName = NSLOCTEXT("Activities", "DefaultActivity", "Work");
}

void AActivityStation::OnInteract_Implementation(APawn* InstigatorPawn)
{
    if (!InstigatorPawn || !IsStationAvailable()) return;
    if (UPlayerActivityComponent* Component = InstigatorPawn->FindComponentByClass<UPlayerActivityComponent>())
    {
        if (Component->IsActivityActive()) Component->SubmitInput(EActivityInput::Primary);
        else Component->StartActivity(this, IPlayerActivitySource::Execute_GetActivityDefinition(this, InstigatorPawn));
    }
}

FPlayerActivityDefinition AActivityStation::GetActivityDefinition_Implementation(APawn* Player) const
{
    FPlayerActivityDefinition Definition = Activity;
    const float Wear = 1.0f - FMath::Clamp(ConditionPercent, 0.0f, 1.0f);
    Definition.DurationSeconds *= 1.0f + Wear * 0.35f;
    Definition.PuzzleSteps = FMath::Clamp(Definition.PuzzleSteps + FMath::RoundToInt(Wear * 2.0f), 1, 16);
    if (Condition == EActivityStationCondition::BloomTouched)
        Definition.MinimumBloomInterference = FMath::Max(Definition.MinimumBloomInterference, 0.45f);
    else if (Condition == EActivityStationCondition::BloomOverrun)
        Definition.MinimumBloomInterference = FMath::Max(Definition.MinimumBloomInterference, 0.8f);
    return Definition;
}

bool AActivityStation::CanStartActivity_Implementation(APawn* Player) const
{
    return Player != nullptr && IsStationAvailable();
}

void AActivityStation::OnActivityCompleted_Implementation(APawn* Player)
{
    ++CompletionCount;
    ConditionPercent = FMath::Clamp(ConditionPercent - 0.025f, 0.0f, 1.0f);
    if (RemainingUses > 0)
    {
        --RemainingUses;
        if (RemainingUses == 0)
        {
            bEnabled = false;
        }
    }
    CooldownEndServerTime = GetWorld() ? GetWorld()->GetTimeSeconds() + CooldownSeconds : 0.0f;
    ForceNetUpdate();
    ReceiveActivityCompleted(Player);
}

void AActivityStation::ConfigureProceduralStation(FName InStationId, FName InRoomCode,
    int32 InPopulationSeed, int32 InSlotIndex, EActivityStationMount InMount,
    EActivityStationCondition InCondition, EActivityStationRarity InRarity,
    float InConditionPercent, int32 InRemainingUses)
{
    if (!HasAuthority()) return;
    StationId = InStationId;
    OwningRoomCode = InRoomCode;
    PopulationSeed = InPopulationSeed;
    PopulationSlotIndex = InSlotIndex;
    MountType = InMount;
    Condition = InCondition;
    Rarity = InRarity;
    ConditionPercent = FMath::Clamp(InConditionPercent, 0.0f, 1.0f);
    RemainingUses = InRemainingUses;
    ForceNetUpdate();
}

void AActivityStation::RestoreRuntimeState(int32 InCompletionCount,
    EActivityStationCondition InCondition, float InConditionPercent, int32 InRemainingUses, bool bInEnabled)
{
    if (!HasAuthority()) return;
    CompletionCount = FMath::Max(0, InCompletionCount);
    Condition = InCondition;
    ConditionPercent = FMath::Clamp(InConditionPercent, 0.0f, 1.0f);
    RemainingUses = InRemainingUses;
    bEnabled = bInEnabled && RemainingUses != 0;
    CooldownEndServerTime = 0.0f;
    ForceNetUpdate();
}

float AActivityStation::GetCooldownRemaining() const
{
    return GetWorld() ? FMath::Max(0.0f, CooldownEndServerTime - GetWorld()->GetTimeSeconds()) : 0.0f;
}

bool AActivityStation::IsStationAvailable() const
{
    return bEnabled && RemainingUses != 0 && GetCooldownRemaining() <= 0.0f;
}

FText AActivityStation::GetStationStatusText() const
{
    if (!bEnabled || RemainingUses == 0)
        return NSLOCTEXT("Activities", "StationDepleted", "DEPLETED");
    if (GetCooldownRemaining() > 0.0f)
        return FText::Format(NSLOCTEXT("Activities", "StationCooldown", "CYCLING {0}s"),
            FText::AsNumber(FMath::CeilToInt(GetCooldownRemaining())));
    switch (Condition)
    {
    case EActivityStationCondition::Pristine: return NSLOCTEXT("Activities", "StationPristine", "PRISTINE");
    case EActivityStationCondition::Worn: return NSLOCTEXT("Activities", "StationWorn", "WORN");
    case EActivityStationCondition::Faulted: return NSLOCTEXT("Activities", "StationFaulted", "FAULTED");
    case EActivityStationCondition::BloomTouched: return NSLOCTEXT("Activities", "StationBloomTouched", "BLOOM SIGNAL");
    case EActivityStationCondition::BloomOverrun: return NSLOCTEXT("Activities", "StationBloomOverrun", "BLOOM OVERRUN");
    default: return NSLOCTEXT("Activities", "StationServiceable", "SERVICEABLE");
    }
}

void AActivityStation::OnRep_StationRuntimeState()
{
    OnStationRuntimeStateChanged();
}

void AActivityStation::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AActivityStation, Activity);
    DOREPLIFETIME(AActivityStation, bEnabled);
    DOREPLIFETIME(AActivityStation, CompletionCount);
    DOREPLIFETIME(AActivityStation, StationId);
    DOREPLIFETIME(AActivityStation, OwningRoomCode);
    DOREPLIFETIME(AActivityStation, PopulationSeed);
    DOREPLIFETIME(AActivityStation, PopulationSlotIndex);
    DOREPLIFETIME(AActivityStation, MountType);
    DOREPLIFETIME(AActivityStation, Condition);
    DOREPLIFETIME(AActivityStation, Rarity);
    DOREPLIFETIME(AActivityStation, ConditionPercent);
    DOREPLIFETIME(AActivityStation, RemainingUses);
    DOREPLIFETIME(AActivityStation, CooldownEndServerTime);
}


FText AActivityStation::GetInteractionPrompt_Implementation(APawn* Viewer) const
{
	// A station that cannot be used right now still says so, with the reason it already computes
	// for its own status readout. Going silent would be indistinguishable from the station not
	// being interactive at all, which is how a player concludes a broken machine is scenery.
	if (!IsStationAvailable())
	{
		return GetStationStatusText();
	}

	return Activity.DisplayName.IsEmpty()
		? NSLOCTEXT("Activities", "PromptGenericStation", "Use station")
		: Activity.DisplayName;
}
