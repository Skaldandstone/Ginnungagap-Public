#pragma once

#include "CoreMinimal.h"
#include "AI/HorrorEnemy.h"
#include "Threats/ThreatTypes.h"
#include "ShipboardThreat.generated.h"

class ACoopSurvivalCharacter;

/**
 * A mission hostile that is deliberately independent from Bloom infection state. The existing
 * HorrorEnemy remains the Bloom pawn; this subclass supplies human and non-Bloom alien tuning.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipboardThreat : public AHorrorEnemy
{
    GENERATED_BODY()

public:
    AShipboardThreat();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(ReplicatedUsing=OnRep_Archetype, EditAnywhere, BlueprintReadOnly, Category="Threat")
    EThreatArchetype Archetype = EThreatArchetype::PirateBreacher;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Threat")
    FThreatArchetypeTuning Tuning;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat|Combat", meta=(ClampMin="0.1"))
    float AttackInterval = 1.0f;

    UFUNCTION(BlueprintCallable, Category="Threat")
    void ConfigureArchetype(EThreatArchetype NewArchetype);

    UFUNCTION(BlueprintPure, Category="Threat")
    static FThreatArchetypeTuning GetArchetypeTuning(EThreatArchetype ForArchetype);

    UFUNCTION(BlueprintPure, Category="Threat")
    EThreatFaction GetThreatFaction() const { return Tuning.Faction; }

    UFUNCTION(BlueprintPure, Category="Threat")
    EThreatBodyPlan GetBodyPlan() const { return Tuning.BodyPlan; }

    UFUNCTION(BlueprintPure, Category="Threat")
    EThreatCombatRole GetCombatRole() const { return Tuning.CombatRole; }

    UFUNCTION(BlueprintImplementableEvent, Category="Threat|Combat")
    void ReceiveThreatAttack(AActor* TargetActor, EThreatCombatRole AttackRole);

protected:
    UFUNCTION()
    void OnRep_Archetype();

private:
    AActor* FindAttackTarget() const;
    void ApplyArchetypeVisuals();

    float TimeUntilNextAttack = 0.0f;
};
