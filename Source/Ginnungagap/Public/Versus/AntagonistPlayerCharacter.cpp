#include "Versus/AntagonistPlayerCharacter.h"

#include "Components/InputComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"
#include "Versus/AntagonistSkillTreeSubsystem.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Versus/VersusPlayerState.h"
#include "Versus/AntagonistActivityComponent.h"
#include "Interaction/InteractionComponent.h"

AAntagonistPlayerCharacter::AAntagonistPlayerCharacter()
{
	bUseSimpleAI = false;
	AutoPossessAI = EAutoPossessAI::Disabled;
	AntagonistActivityComponent = CreateDefaultSubobject<UAntagonistActivityComponent>(TEXT("AntagonistActivityComponent"));
	InteractionComponent = CreateDefaultSubobject<UInteractionComponent>(TEXT("InteractionComponent"));
}

void AAntagonistPlayerCharacter::BeginPlay()
{
	Super::BeginPlay();
	if (HasAuthority())
	{
		ConfigureForFaction(PlayerFaction);
	}
}

void AAntagonistPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	if (PlayerInputComponent)
	{
		PlayerInputComponent->BindAction(TEXT("PrimaryFire"), IE_Pressed,
			this, &AAntagonistPlayerCharacter::PrimaryAntagonistAttack);
	}
}

void AAntagonistPlayerCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AAntagonistPlayerCharacter, PlayerFaction);
}

void AAntagonistPlayerCharacter::ConfigureForFaction(EAntagonistFaction NewFaction)
{
	if (!HasAuthority())
	{
		return;
	}
	PlayerFaction = NewFaction == EAntagonistFaction::None ? EAntagonistFaction::Bloom : NewFaction;
	if (UTeamAffiliationComponent* Affiliation = GetTeamAffiliationComponent())
	{
		Affiliation->SetAffiliation(EVersusTeam::Antagonist, PlayerFaction);
	}
	ApplyFactionPresentation();
	ForceNetUpdate();
}

void AAntagonistPlayerCharacter::OnRep_PlayerFaction()
{
	ApplyFactionPresentation();
}

void AAntagonistPlayerCharacter::ApplyFactionPresentation()
{
	EThreatArchetype RepresentativeArchetype = EThreatArchetype::AlienBipedHunter;
	switch (PlayerFaction)
	{
	case EAntagonistFaction::Pirates:
		RepresentativeArchetype = EThreatArchetype::PirateBreacher;
		break;
	case EAntagonistFaction::Rebels:
		RepresentativeArchetype = EThreatArchetype::RebelSaboteur;
		break;
	case EAntagonistFaction::Alien:
		RepresentativeArchetype = EThreatArchetype::AlienQuadrupedStalker;
		break;
	case EAntagonistFaction::Bloom:
	case EAntagonistFaction::None:
	default:
		RepresentativeArchetype = EThreatArchetype::AlienBipedHunter;
		break;
	}

	ConfigureArchetype(RepresentativeArchetype);
	if (UTeamAffiliationComponent* Affiliation = GetTeamAffiliationComponent(); Affiliation && HasAuthority())
	{
		// ConfigureArchetype applies its AI faction, so restore the player-controlled identity.
		Affiliation->SetAffiliation(EVersusTeam::Antagonist, PlayerFaction);
	}

	PlayerAttackDamage = Tuning.DamagePerAttack;
	PlayerAttackRange = FMath::Max(175.0f, Tuning.AttackRange);
	PlayerAttackCooldown = Tuning.AttackInterval;
}

void AAntagonistPlayerCharacter::PrimaryAntagonistAttack()
{
	if (IsDead())
	{
		return;
	}
	FVector AimOrigin = GetPawnViewLocation();
	FVector AimDirection = GetActorForwardVector();
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		FRotator ViewRotation;
		PC->GetPlayerViewPoint(AimOrigin, ViewRotation);
		AimDirection = ViewRotation.Vector();
	}
	if (HasAuthority())
	{
		ExecutePrimaryAttack(AimOrigin, AimDirection);
	}
	else
	{
		ServerPrimaryAntagonistAttack(AimOrigin, AimDirection.GetSafeNormal());
	}
}

void AAntagonistPlayerCharacter::ServerPrimaryAntagonistAttack_Implementation(
	FVector_NetQuantize AimOrigin, FVector_NetQuantizeNormal AimDirection)
{
	ExecutePrimaryAttack(AimOrigin, AimDirection);
}

void AAntagonistPlayerCharacter::ExecutePrimaryAttack(const FVector& AimOrigin, const FVector& AimDirection)
{
	if (!HasAuthority() || IsDead() || AimDirection.IsNearlyZero() || !GetWorld())
	{
		return;
	}
	const double Now = GetWorld()->GetTimeSeconds();
	const float CooldownMultiplier = 1.0f + GetUnlockedEffectMagnitude(TEXT("HostAbilityCooldown"));
	if (Now - LastPlayerAttackTime < FMath::Max(0.1f, PlayerAttackCooldown * CooldownMultiplier))
	{
		return;
	}
	LastPlayerAttackTime = Now;

	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(AntagonistPrimaryAttack), true, this);
	Params.AddIgnoredActor(this);
	const FVector End = AimOrigin + AimDirection.GetSafeNormal() * PlayerAttackRange;
	const bool bHit = GetWorld()->SweepSingleByChannel(Hit, AimOrigin, End, FQuat::Identity,
		ECC_Visibility, FCollisionShape::MakeSphere(28.0f), Params);
	AActor* HitActor = bHit ? Hit.GetActor() : nullptr;
	if (HitActor && UTeamAffiliationComponent::AreActorsHostile(this, HitActor))
	{
		UGameplayStatics::ApplyPointDamage(HitActor, PlayerAttackDamage, AimDirection, Hit,
			GetController(), this, UDamageType::StaticClass());
	}
	ReceiveAntagonistAttack(HitActor, bHit ? Hit.ImpactPoint : End);
}

float AAntagonistPlayerCharacter::GetUnlockedEffectMagnitude(FName EffectId) const
{
	const AVersusPlayerState* State = GetPlayerState<AVersusPlayerState>();
	const UGameInstance* GameInstance = GetGameInstance();
	const UAntagonistSkillTreeSubsystem* Tree = GameInstance
		? GameInstance->GetSubsystem<UAntagonistSkillTreeSubsystem>() : nullptr;
	if (!State || !Tree)
	{
		return 0.0f;
	}

	float Total = 0.0f;
	for (const FName SkillId : State->UnlockedAntagonistSkillIds)
	{
		const FAntagonistSkill Skill = Tree->GetSkill(SkillId);
		if (Skill.Faction == PlayerFaction && Skill.EffectId == EffectId)
		{
			Total += Skill.EffectMagnitude;
		}
	}
	return Total;
}
