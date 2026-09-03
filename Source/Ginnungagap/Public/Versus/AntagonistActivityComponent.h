#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Versus/AntagonistActivityTypes.h"
#include "AntagonistActivityComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAntagonistActivityChanged,
	const FAntagonistActivitySnapshot&, Snapshot);

UCLASS(ClassGroup=(Versus), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UAntagonistActivityComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAntagonistActivityComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(BlueprintCallable, Category="Versus|Activities")
	bool StartActivity(AActor* Source);

	UFUNCTION(BlueprintCallable, Category="Versus|Activities")
	void SubmitInput(EActivityInput Input);

	UFUNCTION(BlueprintCallable, Category="Versus|Activities")
	void CancelActivity();

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	bool IsActivityActive() const { return Snapshot.State == EPlayerActivityState::Active; }

	UFUNCTION(BlueprintPure, Category="Versus|Activities")
	const FAntagonistActivitySnapshot& GetSnapshot() const { return Snapshot; }

	UPROPERTY(BlueprintAssignable, Category="Versus|Activities")
	FOnAntagonistActivityChanged OnActivityChanged;

private:
	UFUNCTION(Server, Reliable)
	void ServerStartActivity(AActor* Source);

	UFUNCTION(Server, Reliable)
	void ServerSubmitInput(EActivityInput Input);

	UFUNCTION(Server, Reliable)
	void ServerCancelActivity();

	UFUNCTION()
	void OnRep_Snapshot();

	bool StartAuthoritative(AActor* Source);
	void SubmitAuthoritative(EActivityInput Input);
	void BuildSequence();
	void Finish(EPlayerActivityState FinalState);
	void BroadcastChanged();
	bool SubmitSequenceInput(EActivityInput Input);
	bool IsBalanceStable() const;

	UPROPERTY(ReplicatedUsing=OnRep_Snapshot)
	FAntagonistActivitySnapshot Snapshot;

	UPROPERTY(Replicated)
	TObjectPtr<AActor> ActivitySource;

	FAntagonistActivityDefinition ActiveDefinition;
	TArray<EActivityInput> InputSequence;
	float ElapsedSeconds = 0.0f;
	uint8 PreviousMovementMode = 0;
	uint8 PreviousCustomMovementMode = 0;
};

