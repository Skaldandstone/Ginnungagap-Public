#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerActivityTypes.h"
#include "PlayerActivityComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPlayerActivityChanged, const FPlayerActivitySnapshot&, Snapshot);

UCLASS(ClassGroup=(Gameplay), meta=(BlueprintSpawnableComponent))
class GINNUNGAGAP_API UPlayerActivityComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPlayerActivityComponent();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION(BlueprintCallable, Category="Activity")
    bool StartActivity(AActor* Source, const FPlayerActivityDefinition& Definition);

    UFUNCTION(BlueprintCallable, Category="Activity")
    void SubmitInput(EActivityInput Input);

    /** Camera/look delta steers tool-path activities such as welding. */
    UFUNCTION(BlueprintCallable, Category="Activity")
    void SubmitToolDelta(FVector2D Delta);

    UFUNCTION(BlueprintPure, Category="Activity")
    bool UsesToolPath() const { return IsActivityActive() && Snapshot.Mechanic == EActivityMechanic::ToolPath; }

    UFUNCTION(BlueprintCallable, Category="Activity")
    void CancelActivity();

    UFUNCTION(BlueprintPure, Category="Activity")
    bool IsActivityActive() const { return Snapshot.State == EPlayerActivityState::Active; }

    UFUNCTION(BlueprintPure, Category="Activity")
    const FPlayerActivitySnapshot& GetSnapshot() const { return Snapshot; }
    /** What the active activity is being done to (a station, a door), or null between activities. */
    AActor* GetActivitySource() const { return ActivitySource; }

    UPROPERTY(BlueprintAssignable, Category="Activity")
    FOnPlayerActivityChanged OnActivityChanged;

private:
    UFUNCTION(Server, Reliable)
    void ServerStartActivity(AActor* Source, const FPlayerActivityDefinition& Definition);

    UFUNCTION(Server, Reliable)
    void ServerSubmitInput(EActivityInput Input);

    UFUNCTION(Server, Unreliable)
    void ServerSubmitToolDelta(FVector2D Delta);

    UFUNCTION(Server, Reliable)
    void ServerCancelActivity();

    UFUNCTION()
    void OnRep_Snapshot();

    bool StartActivityAuthoritative(AActor* Source, const FPlayerActivityDefinition& Definition);
    void SubmitInputAuthoritative(EActivityInput Input);
    void SubmitToolDeltaAuthoritative(FVector2D Delta);
    EActivityMechanic ResolveMechanic(const FPlayerActivityDefinition& Definition) const;
    void BuildPuzzleSequence();
    void UpdateDerivedPuzzleState();
    void FinishActivity(EPlayerActivityState FinalState);
    void BroadcastChanged();

    UPROPERTY(ReplicatedUsing=OnRep_Snapshot)
    FPlayerActivitySnapshot Snapshot;

    /** Owner-side: whether this component moved the view to third person for the running activity, and what it was before. */
    bool bViewSwitchedForActivity = false;
    bool bViewWasFirstPerson = true;

    UPROPERTY(Replicated)
    TObjectPtr<AActor> ActivitySource;

    /** The crouch-walk loop played on the body during a squeeze or crawl, and whether it is playing. */
    UPROPERTY()
    TObjectPtr<class UAnimSequenceBase> CrawlLoop;
    bool bCrawlPosePlaying = false;
    /** The crawl goes down through Stand_To_Prone and comes up through Prone_To_Stand; the loop runs between. */
    FTimerHandle CrawlTransitionTimer;
    bool bCrawlTransitionPending = false;

    FPlayerActivityDefinition ActiveDefinition;
    uint8 PreviousMovementMode = 0;
    uint8 PreviousCustomMovementMode = 0;
    float ActivityElapsed = 0.0f;
};
