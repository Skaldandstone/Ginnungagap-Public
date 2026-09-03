#include "Versus/TeamAffiliationComponent.h"

#include "CoopSurvivalCharacter.h"
#include "Net/UnrealNetwork.h"

UTeamAffiliationComponent::UTeamAffiliationComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
}

void UTeamAffiliationComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UTeamAffiliationComponent, Team);
	DOREPLIFETIME(UTeamAffiliationComponent, Faction);
}

void UTeamAffiliationComponent::SetAffiliation(EVersusTeam NewTeam, EAntagonistFaction NewFaction)
{
	if (!GetOwner() || !GetOwner()->HasAuthority())
	{
		return;
	}
	Team = NewTeam;
	Faction = NewTeam == EVersusTeam::Protagonist ? EAntagonistFaction::None : NewFaction;
	GetOwner()->ForceNetUpdate();
}

UTeamAffiliationComponent* UTeamAffiliationComponent::FindAffiliation(const AActor* Actor)
{
	return Actor ? Actor->FindComponentByClass<UTeamAffiliationComponent>() : nullptr;
}

bool UTeamAffiliationComponent::AreActorsHostile(const AActor* SourceActor, const AActor* TargetActor)
{
	if (!SourceActor || !TargetActor || SourceActor == TargetActor)
	{
		return false;
	}

	const UTeamAffiliationComponent* Source = FindAffiliation(SourceActor);
	const UTeamAffiliationComponent* Target = FindAffiliation(TargetActor);
	if (!Source || !Target)
	{
		// Preserve legacy co-op enemy behavior for actors that have not opted into versus affiliation.
		return Cast<ACoopSurvivalCharacter>(TargetActor) != nullptr;
	}
	return AreAffiliationsHostile(Source->Team, Source->Faction, Target->Team, Target->Faction);
}

bool UTeamAffiliationComponent::AreAffiliationsHostile(EVersusTeam SourceTeam,
	EAntagonistFaction SourceFaction, EVersusTeam TargetTeam, EAntagonistFaction TargetFaction)
{
	if (SourceTeam == EVersusTeam::Spectator || TargetTeam == EVersusTeam::Spectator)
	{
		return false;
	}
	if (SourceTeam == EVersusTeam::Protagonist && TargetTeam == EVersusTeam::Protagonist)
	{
		return false;
	}
	if (SourceTeam == EVersusTeam::Protagonist || TargetTeam == EVersusTeam::Protagonist)
	{
		return true;
	}

	// Antagonist players and independent AI only cooperate when their faction matches.
	return SourceFaction == EAntagonistFaction::None || SourceFaction != TargetFaction;
}

bool UTeamAffiliationComponent::IsHostileTo(const AActor* OtherActor) const
{
	return AreActorsHostile(GetOwner(), OtherActor);
}
