#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DebrisField.generated.h"

/**
 * A stretch of corridor or trunk choked with wreckage that cannot be cut or bypassed: the crew
 * take the boots off, push off the walls and drift through the gaps in it, three-dimensionally.
 * The volume tells the character (and so the HUD) they are in one, and gives the walkers in the
 * tests the two ends to cross between. The wreckage itself is the generator's: blockers that
 * leave a winding gap, dressed with kit pieces.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API ADebrisField : public AActor
{
    GENERATED_BODY()

public:
    ADebrisField();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Debris")
    TObjectPtr<class UBoxComponent> Volume;

    /** Where the field starts and ends along its length, in world space, for a walker that has to cross it without floating. */
    UFUNCTION(BlueprintCallable, Category = "Debris")
    void GetEnds(FVector& OutA, FVector& OutB) const;

    /** The end farther from a point: where to come out. */
    FVector FarEnd(const FVector& From) const;

protected:
    UFUNCTION()
    void OnVolumeBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
    UFUNCTION()
    void OnVolumeEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);
};
