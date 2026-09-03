#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "../Bloom/BloomHost.h"
#include "CrewCorpse.generated.h"

class UZeroGGravityComponent;
class AAIController;

UCLASS()
class GINNUNGAGAP_API ACrewCorpse : public ACharacter, public IBloomHost
{
    GENERATED_BODY()

public:
    ACrewCorpse();

protected:
    virtual void BeginPlay() override;

public:
    virtual void OnBloomPossession_Implementation() override;
    virtual bool CanBeBloomPossessed_Implementation() const override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bloom")
    TSubclassOf<AAIController> PossessionControllerClass;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category = "Zero G")
    TObjectPtr<UZeroGGravityComponent> ZeroGGravityComponent;

    UPROPERTY(BlueprintReadOnly, Category = "Bloom")
    bool bIsPossessed = false;
};
