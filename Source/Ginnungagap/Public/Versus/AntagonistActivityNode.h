#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/Interactable.h"
#include "Versus/AntagonistActivitySource.h"
#include "AntagonistActivityNode.generated.h"

class UStaticMeshComponent;

UCLASS(Blueprintable)
class GINNUNGAGAP_API AAntagonistActivityNode : public AActor,
	public IInteractable, public IAntagonistActivitySource
{
	GENERATED_BODY()

public:
	AAntagonistActivityNode();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
	virtual void OnInteract_Implementation(APawn* InstigatorPawn) override;
	virtual FAntagonistActivityDefinition GetAntagonistActivityDefinition_Implementation(APawn* InstigatorPawn) const override;
	virtual bool CanStartAntagonistActivity_Implementation(APawn* InstigatorPawn) const override;
	virtual void OnAntagonistActivityCompleted_Implementation(APawn* InstigatorPawn, FName CompletionEffectId) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Versus|Activities")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category="Versus|Activities")
	FName ActivityId = TEXT("Bloom_ConsumeBiomass");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category="Versus|Activities")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category="Versus|Activities", meta=(ClampMin="-1"))
	int32 RemainingUses = -1;

	UPROPERTY(BlueprintReadOnly, Replicated, Category="Versus|Activities")
	int32 CompletionCount = 0;

	UFUNCTION(BlueprintImplementableEvent, Category="Versus|Activities")
	void ReceiveAntagonistActivityCompleted(APawn* InstigatorPawn, FName CompletionEffectId);
};

