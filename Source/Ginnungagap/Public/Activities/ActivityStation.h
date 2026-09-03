#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/Interactable.h"
#include "Activities/PlayerActivitySource.h"
#include "Activities/ActivityPopulationTypes.h"
#include "ActivityStation.generated.h"

class UStaticMeshComponent;

UCLASS(Blueprintable)
class GINNUNGAGAP_API AActivityStation : public AActor, public IInteractable, public IPlayerActivitySource
{
    GENERATED_BODY()

public:
    AActivityStation();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Activity")
    TObjectPtr<UStaticMeshComponent> Mesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category="Activity")
    FPlayerActivityDefinition Activity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, ReplicatedUsing=OnRep_StationRuntimeState, Category="Activity")
    bool bEnabled = true;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity")
    int32 CompletionCount = 0;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Population")
    FName StationId = NAME_None;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Population")
    FName OwningRoomCode = NAME_None;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Population")
    int32 PopulationSeed = 0;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Population")
    int32 PopulationSlotIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Population")
    EActivityStationMount MountType = EActivityStationMount::Automatic;

    UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_StationRuntimeState, Category="Activity|Condition")
    EActivityStationCondition Condition = EActivityStationCondition::Serviceable;

    UPROPERTY(BlueprintReadOnly, Replicated, Category="Activity|Condition")
    EActivityStationRarity Rarity = EActivityStationRarity::Routine;

    UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_StationRuntimeState, Category="Activity|Condition",
        meta=(ClampMin="0.0", ClampMax="1.0"))
    float ConditionPercent = 1.0f;

    /** Negative values allow unlimited uses. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, ReplicatedUsing=OnRep_StationRuntimeState, Category="Activity|Availability")
    int32 RemainingUses = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Availability", meta=(ClampMin="0.0"))
    float CooldownSeconds = 12.0f;

    UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_StationRuntimeState, Category="Activity|Availability")
    float CooldownEndServerTime = 0.0f;

    UFUNCTION(BlueprintImplementableEvent, Category="Activity")
    void ReceiveActivityCompleted(APawn* Player);

    UFUNCTION(BlueprintImplementableEvent, Category="Activity")
    void OnStationRuntimeStateChanged();

    UFUNCTION(BlueprintCallable, Category="Activity|Population")
    void ConfigureProceduralStation(FName InStationId, FName InRoomCode, int32 InPopulationSeed,
        int32 InSlotIndex, EActivityStationMount InMount, EActivityStationCondition InCondition,
        EActivityStationRarity InRarity, float InConditionPercent, int32 InRemainingUses);

    UFUNCTION(BlueprintCallable, Category="Activity|Persistence")
    void RestoreRuntimeState(int32 InCompletionCount, EActivityStationCondition InCondition,
        float InConditionPercent, int32 InRemainingUses, bool bInEnabled);

    UFUNCTION(BlueprintPure, Category="Activity|Availability")
    float GetCooldownRemaining() const;

    UFUNCTION(BlueprintPure, Category="Activity|Availability")
    bool IsStationAvailable() const;

    UFUNCTION(BlueprintPure, Category="Activity|Availability")
    FText GetStationStatusText() const;

    virtual void OnInteract_Implementation(APawn* InstigatorPawn) override;
    virtual FText GetInteractionPrompt_Implementation(APawn* Viewer) const override;
    virtual FPlayerActivityDefinition GetActivityDefinition_Implementation(APawn* Player) const override;
    virtual bool CanStartActivity_Implementation(APawn* Player) const override;
    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    UFUNCTION()
    void OnRep_StationRuntimeState();
};
