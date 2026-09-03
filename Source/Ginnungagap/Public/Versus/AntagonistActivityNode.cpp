#include "Versus/AntagonistActivityNode.h"

#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "Versus/AntagonistActivityCatalog.h"
#include "Versus/AntagonistActivityComponent.h"
#include "Versus/VersusPlayerState.h"

AAntagonistActivityNode::AAntagonistActivityNode()
{
	bReplicates = true;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
}

void AAntagonistActivityNode::OnInteract_Implementation(APawn* InstigatorPawn)
{
	if (!InstigatorPawn || !bEnabled || RemainingUses == 0) return;
	if (UAntagonistActivityComponent* Component =
		InstigatorPawn->FindComponentByClass<UAntagonistActivityComponent>())
	{
		if (Component->IsActivityActive()) Component->SubmitInput(EActivityInput::Primary);
		else Component->StartActivity(this);
	}
}

FAntagonistActivityDefinition AAntagonistActivityNode::GetAntagonistActivityDefinition_Implementation(APawn* InstigatorPawn) const
{
	return UAntagonistActivityCatalog::GetActivity(ActivityId);
}

bool AAntagonistActivityNode::CanStartAntagonistActivity_Implementation(APawn* InstigatorPawn) const
{
	const AVersusPlayerState* State = InstigatorPawn
		? InstigatorPawn->GetPlayerState<AVersusPlayerState>() : nullptr;
	return bEnabled && RemainingUses != 0 && State
		&& UAntagonistActivityCatalog::CanFactionPerformActivity(State->AntagonistFaction, ActivityId);
}

void AAntagonistActivityNode::OnAntagonistActivityCompleted_Implementation(
	APawn* InstigatorPawn, FName CompletionEffectId)
{
	if (!HasAuthority()) return;
	++CompletionCount;
	if (RemainingUses > 0)
	{
		--RemainingUses;
		bEnabled = RemainingUses != 0;
	}
	ForceNetUpdate();
	ReceiveAntagonistActivityCompleted(InstigatorPawn, CompletionEffectId);
}

void AAntagonistActivityNode::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AAntagonistActivityNode, ActivityId);
	DOREPLIFETIME(AAntagonistActivityNode, bEnabled);
	DOREPLIFETIME(AAntagonistActivityNode, RemainingUses);
	DOREPLIFETIME(AAntagonistActivityNode, CompletionCount);
}

