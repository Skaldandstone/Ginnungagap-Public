#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PathogenLoadComponent.generated.h"

UENUM(BlueprintType)
enum class EInfectionState : uint8
{
    Clean,
    Exposed,
    Incubating,
    Symptomatic
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnBecameSymptomatic);

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPathogenLoadComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPathogenLoadComponent();
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintCallable, Category = "Pathogen")
    void ApplyExposure(float Concentration, float DeltaTime);

    UFUNCTION(BlueprintCallable, Category = "Pathogen")
    float ConsumeSheddingOutput(float DeltaTime);

    UFUNCTION(BlueprintCallable, Category = "Pathogen")
    void PurgeInfection();

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Pathogen")
    EInfectionState InfectionState = EInfectionState::Clean;

    UPROPERTY(BlueprintReadOnly, Category = "Pathogen")
    float AccumulatedDose = 0.0f;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Pathogen")
    float PathogenLoad = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float Resistance = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float InfectiousDoseThreshold = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float SymptomaticThreshold = 50.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float ReplicationRate = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float SubstrateQuality = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Pathogen")
    float SheddingRate = 0.1f;

    UPROPERTY(BlueprintAssignable, Category = "Pathogen")
    FOnBecameSymptomatic OnBecameSymptomatic;

private:
    void TickInfectionProgress(float DeltaTime);
};
