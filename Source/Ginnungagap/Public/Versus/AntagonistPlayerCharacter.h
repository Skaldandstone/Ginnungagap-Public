#pragma once

#include "CoreMinimal.h"
#include "Threats/ShipboardThreat.h"
#include "Versus/VersusTypes.h"
#include "AntagonistPlayerCharacter.generated.h"

UCLASS(Blueprintable)
class GINNUNGAGAP_API AAntagonistPlayerCharacter : public AShipboardThreat
{
	GENERATED_BODY()

public:
	AAntagonistPlayerCharacter();

	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(ReplicatedUsing=OnRep_PlayerFaction, EditAnywhere, BlueprintReadOnly, Category="Versus")
	EAntagonistFaction PlayerFaction = EAntagonistFaction::Bloom;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus|Combat", meta=(ClampMin="0.0"))
	float PlayerAttackDamage = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus|Combat", meta=(ClampMin="50.0"))
	float PlayerAttackRange = 225.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Versus|Combat", meta=(ClampMin="0.1"))
	float PlayerAttackCooldown = 1.0f;

	UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Versus")
	void ConfigureForFaction(EAntagonistFaction NewFaction);

	UFUNCTION(BlueprintCallable, Category="Versus|Combat")
	void PrimaryAntagonistAttack();

	UFUNCTION(BlueprintPure, Category="Versus|Progression")
	float GetUnlockedEffectMagnitude(FName EffectId) const;

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	class UAntagonistActivityComponent* GetAntagonistActivityComponent() const { return AntagonistActivityComponent; }

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	class UInteractionComponent* GetInteractionComponent() const { return InteractionComponent; }

	UFUNCTION(BlueprintImplementableEvent, Category="Versus|Combat")
	void ReceiveAntagonistAttack(AActor* HitActor, FVector ImpactPoint);

protected:
	UFUNCTION(Server, Reliable)
	void ServerPrimaryAntagonistAttack(FVector_NetQuantize AimOrigin, FVector_NetQuantizeNormal AimDirection);

	UFUNCTION()
	void OnRep_PlayerFaction();

private:
	void ApplyFactionPresentation();
	void ExecutePrimaryAttack(const FVector& AimOrigin, const FVector& AimDirection);
	double LastPlayerAttackTime = -1000.0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Versus|Activities")
	TObjectPtr<class UAntagonistActivityComponent> AntagonistActivityComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Versus|Activities")
	TObjectPtr<class UInteractionComponent> InteractionComponent;
};
