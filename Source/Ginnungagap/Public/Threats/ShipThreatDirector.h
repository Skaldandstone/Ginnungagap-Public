#pragma once

#include "CoreMinimal.h"
#include "Bloom/BloomDirector.h"
#include "GameFramework/Actor.h"
#include "Threats/ThreatTypes.h"
#include "ShipThreatDirector.generated.h"

class AShipboardThreat;
class AShipSection;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnThreatEncounterStateChanged, FName, EncounterId,
    EThreatEncounterState, NewState);

/**
 * Owns one self-contained mission encounter. Multiple directors may be active at once, and none
 * of them mutate Bloom state; their Bloom flags only decide whether an encounter is eligible.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AShipThreatDirector : public AActor
{
    GENERATED_BODY()

public:
    AShipThreatDirector();

    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    EThreatEncounterPreset Preset = EThreatEncounterPreset::PirateBoarding;

    /** Used when Preset is Custom; populated from the selected preset otherwise. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    FThreatEncounterDefinition EncounterDefinition;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Threat")
    bool bAutoStart = true;

    /** Optional authored spawn anchors. Ship sections are used next, then a radius fallback. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Threat|Spawning")
    TArray<TObjectPtr<AActor>> SpawnAnchors;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Threat")
    TArray<TObjectPtr<AShipboardThreat>> ActiveThreats;

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Threat")
    EThreatEncounterState EncounterState = EThreatEncounterState::Dormant;

    UPROPERTY(BlueprintAssignable, Category="Threat")
    FOnThreatEncounterStateChanged OnEncounterStateChanged;

    UFUNCTION(BlueprintCallable, Category="Threat")
    bool StartEncounter();

    UFUNCTION(BlueprintCallable, Category="Threat")
    void CancelEncounter(bool bDestroyRemainingThreats = true);

    UFUNCTION(BlueprintPure, Category="Threat")
    bool CanStartEncounter() const;

    UFUNCTION(BlueprintPure, Category="Threat")
    int32 GetRemainingThreatCount() const;

    UFUNCTION(BlueprintPure, Category="Threat")
    static FThreatEncounterDefinition BuildPresetDefinition(EThreatEncounterPreset ForPreset);

private:
    UFUNCTION()
    void HandleThreatKilled();

    UFUNCTION()
    void HandleBloomStageChanged(EBloomStage NewStage);

    void RegisterMissionObjective();
    void CompleteEncounter();
    FTransform ChooseSpawnTransform(FRandomStream& Random, int32 SpawnIndex,
        const TArray<AShipSection*>& Sections) const;
};
