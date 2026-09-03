#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShipNavigationSubsystem.generated.h"

class AShipSection;

UCLASS()
class GINNUNGAGAP_API UShipNavigationSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;

    void RegisterSection(AShipSection* Section);
    void UnregisterSection(AShipSection* Section);

    UFUNCTION(BlueprintCallable, Category = "Ship Navigation")
    AShipSection* GetSectionContainingLocation(const FVector& Location) const;

    UFUNCTION(BlueprintCallable, Category = "Ship Navigation")
    bool FindSectionPath(AShipSection* Start, AShipSection* End, TArray<AShipSection*>& OutPath, bool bRespectSealedDoors = true) const;

protected:
    UPROPERTY()
    TArray<TObjectPtr<AShipSection>> AllSections;

private:
    void ValidateSectionConnections() const;
};
