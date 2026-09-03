#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "../Bloom/BloomDirector.h"
#include "HorrorEnemy.generated.h"

class APatrollingEnemyController;
class UZeroGGravityComponent;
class UTeamAffiliationComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnHorrorEnemyKilled);

UCLASS()
class GINNUNGAGAP_API AHorrorEnemy : public ACharacter
{
    GENERATED_BODY()

public:
    AHorrorEnemy();
    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
        class AController* EventInstigator, AActor* DamageCauser) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Enemy")
    TObjectPtr<class UStaticMeshComponent> ProxyVisualMesh;

    UFUNCTION(BlueprintPure, Category="Versus")
    UTeamAffiliationComponent* GetTeamAffiliationComponent() const { return TeamAffiliationComponent; }

protected:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Enemy")
    float DamagePerSecond = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Enemy")
    float AttackRange = 150.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    bool bUseSimpleAI = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AI")
    TArray<FVector> PatrolPoints;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
    float MaxHealth = 100.0f;

    UPROPERTY(ReplicatedUsing = OnRep_Health, BlueprintReadOnly, Category = "Health")
    float Health = 100.0f;

    UFUNCTION(BlueprintPure, Category = "Health")
    bool IsDead() const { return Health <= 0.0f; }

    UPROPERTY(BlueprintAssignable, Category = "Health")
    FOnHorrorEnemyKilled OnEnemyKilled;

    UFUNCTION(BlueprintCallable, Category = "Bloom")
    void ReceiveHazardExposure(EBloomHazardType HazardType, float Amount);

protected:
    UFUNCTION()
    void OnRep_Health();

    UFUNCTION(BlueprintImplementableEvent, Category = "Health")
    void ReceiveHealthChanged(float NewHealth, float MaximumHealth);

    UFUNCTION(BlueprintImplementableEvent, Category = "Health")
    void ReceiveKilled(AActor* DamageCauser);

    void HandleKilled(AActor* DamageCauser);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category = "Zero G")
    TObjectPtr<UZeroGGravityComponent> ZeroGGravityComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Versus")
    TObjectPtr<UTeamAffiliationComponent> TeamAffiliationComponent;
};
