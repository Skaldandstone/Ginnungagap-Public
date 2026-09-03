#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Versus/VersusTypes.h"
#include "TeamAffiliationComponent.generated.h"

UCLASS(ClassGroup=(Versus), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UTeamAffiliationComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTeamAffiliationComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(Replicated, EditAnywhere, BlueprintReadOnly, Category="Versus")
	EVersusTeam Team = EVersusTeam::IndependentAI;

	UPROPERTY(Replicated, EditAnywhere, BlueprintReadOnly, Category="Versus")
	EAntagonistFaction Faction = EAntagonistFaction::None;

	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Versus")
	void SetAffiliation(EVersusTeam NewTeam, EAntagonistFaction NewFaction);

	UFUNCTION(BlueprintPure, Category="Versus")
	bool IsHostileTo(const AActor* OtherActor) const;

	UFUNCTION(BlueprintPure, Category="Versus")
	static bool AreActorsHostile(const AActor* SourceActor, const AActor* TargetActor);

	UFUNCTION(BlueprintPure, Category="Versus")
	static bool AreAffiliationsHostile(EVersusTeam SourceTeam, EAntagonistFaction SourceFaction,
		EVersusTeam TargetTeam, EAntagonistFaction TargetFaction);

	UFUNCTION(BlueprintPure, Category="Versus")
	static UTeamAffiliationComponent* FindAffiliation(const AActor* Actor);
};
