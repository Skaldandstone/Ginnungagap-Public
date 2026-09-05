#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AstrophysicsHazardComponent.h"
#include "Meta/CharacterProfile.h"
#include "CoopSurvivalCharacter.generated.h"

// Runtime component declarations are kept lightweight so this character remains valid in packaged builds.
class USurvivalHUDWidget;
class ASurvivalPlayerController;
class UEquipmentComponent;
class UZeroGGravityComponent;
class UInteractionComponent;
class UBioScannerComponent;
class UCharacterProfileSubsystem;
class UClassSkillComponent;
class UInventoryComponent;
class USkeletalMesh;
class USkeletalMeshComponent;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UChildActorComponent;
class AActor;
class UMaterialInstanceDynamic;
class UPathogenLoadComponent;
class UPlayerActivityComponent;
class UPointLightComponent;
class UPrimitiveComponent;
class USoundBase;
class UParticleSystem;
class UPlayerStatusEffectComponent;
class UPlayerNoiseEmitterComponent;
class UPlayerVisibilityComponent;
class UPlayerPsychosisComponent;
class UWeaponMountComponent;
class UTeamAffiliationComponent;
class UChildActorComponent;
class AShipboardWeapon;

UENUM(BlueprintType)
enum class EMagneticGloveHand : uint8
{
    Left,
    Right
};

UCLASS()
class GINNUNGAGAP_API ACoopSurvivalCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ACoopSurvivalCharacter();
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
        class AController* EventInstigator, AActor* DamageCauser) override;

    UPROPERTY(ReplicatedUsing=OnRep_PressureSuitRole, EditAnywhere, BlueprintReadWrite, Category="Appearance|Pressure Suit")
    EPressureSuitRole PressureSuitRole = GinnungagapDefaults::StartingSuitRole;

    UFUNCTION(BlueprintCallable, Category="Appearance|Pressure Suit")
    void SetPressureSuitRole(EPressureSuitRole NewRole);

    UFUNCTION(Server, Reliable)
    void ServerSetPressureSuitRole(EPressureSuitRole NewRole);

    UFUNCTION()
    void OnRep_PressureSuitRole();

    /** Keeps the fitted cryo layer independent from the rigid pressure-oversuit modules. */
    UPROPERTY(ReplicatedUsing=OnRep_PressureOversuitEquipped, EditAnywhere, BlueprintReadWrite, Category="Appearance|Pressure Suit")
    bool bPressureOversuitEquipped = false;

    UFUNCTION(BlueprintCallable, Category="Appearance|Pressure Suit")
    void SetPressureOversuitEquipped(bool bEquipped);

    UFUNCTION(Server, Reliable)
    void ServerSetPressureOversuitEquipped(bool bEquipped);

    UFUNCTION()
    void OnRep_PressureOversuitEquipped();

    /**
     * Raises suit integrity by a fraction of the full 0..1 scale, clamped. Authority only.
     *
     * Integrity is the stat a vacuum actually spends -- pressure failure drains it as
     * (1 - integrity) per second, compounding -- and until this existed nothing in the game put it
     * back. The suit repair bench repaired equipment durability, a different number, and a player
     * who did everything the demo asked still walked into the breach room with the 0.8 they woke
     * with. Returns the integrity after the repair.
     */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category="Equipment")
    float RepairSuitIntegrity(float Fraction);

    UFUNCTION(BlueprintPure, Category="Equipment")
    float GetSuitIntegrity() const { return SuitIntegrity; }

    /** Swappable assembled MetaHuman class used by the character creator. */
    UPROPERTY(ReplicatedUsing=OnRep_MetaHumanCharacterClass, EditAnywhere, BlueprintReadWrite, Category="Appearance|Character")
    TSubclassOf<AActor> MetaHumanCharacterClass;

    UFUNCTION(BlueprintCallable, Category="Appearance|Character")
    void SetMetaHumanCharacterClass(TSubclassOf<AActor> NewCharacterClass);

    /** Resolves a stable character-creator ID such as PlayerFace01 to its assembled Blueprint. */
    UFUNCTION(BlueprintCallable, Category="Appearance|Character")
    bool SetMetaHumanPreset(FName PresetId);

    UFUNCTION(Server, Reliable)
    void ServerSetMetaHumanCharacterClass(TSubclassOf<AActor> NewCharacterClass);

    UFUNCTION()
    void OnRep_MetaHumanCharacterClass();

    /** The independently swappable garment worn over the player body/undersuit. */
    UFUNCTION(BlueprintPure, Category="Appearance|Primary Oversuit")
    USkeletalMeshComponent* GetPrimaryOversuitMesh() const { return PrimaryOversuitMesh; }

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    UFUNCTION() void ActivateSkillSlot1();
    UFUNCTION() void ActivateSkillSlot2();
    UFUNCTION() void ActivateSkillSlot3();

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION()
    void OnRep_Health();

    UFUNCTION()
    void OnRep_Oxygen();

    UFUNCTION()
    void OnRep_Radiation();

    UFUNCTION()
    void OnRep_SuitIntegrity();

    UFUNCTION()
    void OnRep_Stability();

    UFUNCTION(BlueprintCallable)
    void UpdateSurvival(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float SuitIntegrity, float Stability);

    UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category="Equipment")
    void OnEquipmentChanged();

    UFUNCTION(BlueprintCallable, Category="Equipment")
    void RefreshEquipmentVisuals();

    UFUNCTION(BlueprintCallable, Category="Zero G")
    void ApplyThrust(FVector Direction, float DeltaTime);

    UFUNCTION(BlueprintCallable, Category="Zero G")
    void PushOffSurface();

    /** Toggles the boot magnets. A nearby metal surface becomes the character's floor. */
    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void ToggleMagneticBoots();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void SetMagneticBootsEnabled(bool bEnabled);

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    bool AreMagneticBootsEnabled() const { return bMagneticBootsEnabled; }

    /** Holds a glove magnet against the metal under the reticle and reels the player toward it. */
    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void BeginMagneticGloveGrip();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void EndMagneticGloveGrip();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void BeginRightMagneticGloveGrip();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void EndRightMagneticGloveGrip();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void ThrowMagneticObject();

    /** Uses the suit pack to rotate until the character's feet face the aimed-at surface. */
    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void BeginRotationThruster();

    UFUNCTION(BlueprintCallable, Category="Zero G|Magnetic Suit")
    void EndRotationThruster();

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    bool IsLeftMagneticGloveActive() const { return bLeftMagneticGloveActive; }

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    bool IsRightMagneticGloveActive() const { return bRightMagneticGloveActive; }

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    bool IsRotationThrusterActive() const { return bRotationThrusterActive; }

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    bool HasValidMagneticTarget() const { return bHasValidMagneticTarget; }

    UFUNCTION(BlueprintPure, Category="Zero G|Magnetic Suit")
    float GetThrusterFuelPercent() const { return ThrusterFuelPercent; }

    UFUNCTION(BlueprintCallable, Category="Interaction")
    UInteractionComponent* GetInteractionComponent() const { return InteractionComponent; }

    UFUNCTION(BlueprintCallable, Category="Interaction")
    UBioScannerComponent* GetBioScannerComponent() const { return BioScannerComponent; }

    UFUNCTION(BlueprintCallable, Category="Activity")
    UPlayerActivityComponent* GetPlayerActivityComponent() const { return PlayerActivityComponent; }

    UFUNCTION(BlueprintPure, Category="Survival|Status Effects")
    UPlayerStatusEffectComponent* GetStatusEffectComponent() const { return StatusEffectComponent; }

    UFUNCTION(BlueprintPure, Category="Progression")
    UClassSkillComponent* GetSkillComponent() const { return SkillComponent; }

    /**
     * Weapon the crew member starts a run holding, or none.
     *
     * Left unset by default on purpose. Which of the weapon definitions belongs in a given scenario
     * is a design decision, and a hard-coded default would quietly become the answer everywhere.
     * Set it on a pawn Blueprint, or leave it empty and hand one over mid-mission with
     * GrantStartingWeapon -- the demo's workshop objective is written for the second.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Weapons")
    TSubclassOf<class AShipboardWeapon> StartingWeaponClass;

    /** Definition applied to the starting weapon. Without one the actor spawns inert. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category="Weapons")
    TObjectPtr<class UShipboardWeaponDefinition> StartingWeaponDefinition;

    /**
     * Spawns and mounts StartingWeaponClass. Server only, and refuses if something is already
     * mounted so handing a weapon over twice cannot silently discard the first.
     *
     * Returns false when nothing is configured, which is not an error -- an unarmed start is a
     * legitimate scenario.
     */
    UFUNCTION(BlueprintCallable, Category="Weapons")
    bool GrantStartingWeapon();

    /** Triggers the active in a payload slot, 0-based. Bound to the ability-bar keys. */
    UFUNCTION(BlueprintCallable, Category="Progression")
    bool ActivateSkillSlot(int32 SlotIndex);

    UFUNCTION(BlueprintPure, Category="Stealth")
    UPlayerNoiseEmitterComponent* GetNoiseEmitterComponent() const { return NoiseEmitterComponent; }

    UFUNCTION(BlueprintPure, Category="Stealth")
    UPlayerVisibilityComponent* GetVisibilityComponent() const { return VisibilityComponent; }

    /** Loudness a thrown object makes on landing; exposed for the stealth tuning tests. */
    UFUNCTION(BlueprintPure, Category="Stealth")
    float GetThrownObjectImpactLoudness() const { return ThrownObjectImpactLoudness; }

    UFUNCTION(BlueprintPure, Category="Survival|Psychosis")
    UPlayerPsychosisComponent* GetPsychosisComponent() const { return PsychosisComponent; }

    UFUNCTION(Client, Reliable, Category="Survival|Psychosis")
    void ClientApplyPsychosisGrounding(float DurationSeconds, float TreatmentStrength);

    UFUNCTION(BlueprintPure, Category="Survival")
    UAstrophysicsHazardComponent* GetHazardComponent() const { return HazardComponent; }

    UFUNCTION(BlueprintPure, Category="Versus")
    UTeamAffiliationComponent* GetTeamAffiliationComponent() const { return TeamAffiliationComponent; }

    UFUNCTION(BlueprintCallable, Category="Inventory")
    UInventoryComponent* GetInventoryComponent() const { return InventoryComponent; }

    /** Uses the first carried supply that would do something now (oxygen when low, a kit when hurt); the H key. */
    UFUNCTION(BlueprintCallable, Category="Inventory")
    bool UseBestSupply();

    UFUNCTION(Server, Reliable)
    void ServerUseBestSupply();

    UFUNCTION(BlueprintPure, Category="Weapon")
    UWeaponMountComponent* GetWeaponMountComponent() const { return WeaponMountComponent; }

    /**
     * Where a mounted tool sits in the right hand: the mount re-parents from the camera to the
     * body's hand_r while something is mounted, and the arm comes up under HoldAnimation, an
     * additive played through the body's DefaultSlot so the legs keep walking. Offsets are the
     * grip relative to the hand bone.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Weapon|Hold")
    FVector HandGripLocation = FVector(4.0f, 2.0f, 0.0f);

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Weapon|Hold")
    FRotator HandGripRotation = FRotator(0.0f, 180.0f, 0.0f);

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Weapon|Hold")
    TObjectPtr<class UAnimSequenceBase> HoldAnimation;

    /** Seconds into HoldAnimation where the arm is out; the pose is held there. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Weapon|Hold")
    float HoldAnimationTime = 1.6f;

    UFUNCTION()
    void HandleMountedWeaponChanged(class AShipboardWeapon* Weapon);

    UFUNCTION(BlueprintCallable, Category="Weapon")
    void FirePrimaryWeapon();

    UFUNCTION(BlueprintCallable, Category="Weapon")
    void ToggleUnsafeWeaponModification();

    /** Adds movement only when the mounted weapon's physical envelope has clearance. */
    UFUNCTION(BlueprintCallable, Category="Weapon|Traversal")
    bool TryAddTraversalMovementInput(const FVector& WorldDirection, float ScaleValue);

    UFUNCTION(BlueprintPure, Category="Weapon|Traversal")
    bool IsWeaponTraversalBlocked() const { return bWeaponTraversalBlocked; }

    UFUNCTION(BlueprintPure, Category="Weapon|Traversal")
    AActor* GetWeaponTraversalBlocker() const { return WeaponTraversalBlocker.Get(); }

    /** Hook for a shoulder check, contact sound, reticle warning, or contextual camera response. */
    UFUNCTION(BlueprintImplementableEvent, Category="Weapon|Traversal")
    void ReceiveWeaponTraversalBlocked(AActor* BlockingActor, AShipboardWeapon* MountedWeapon);

    UFUNCTION(BlueprintCallable, Category="Camera")
    class USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

    UFUNCTION(BlueprintCallable, Category="Camera")
    class UCameraComponent* GetThirdPersonCamera() const { return ThirdPersonCamera; }

    UFUNCTION(BlueprintCallable, Category="Camera")
    class UCameraComponent* GetFirstPersonCamera() const { return FirstPersonCamera; }

    UFUNCTION(BlueprintCallable, Category="Camera")
    void SetFirstPersonView(bool bEnableFirstPerson);

    UFUNCTION(BlueprintPure, Category="Camera")
    bool IsFirstPersonView() const { return bFirstPersonView; }

    UFUNCTION(BlueprintCallable, Category="Character")
    void ApplyAppearanceCosmetic(ECharacterAppearance Appearance);

	/** Applies the identity fields supported by the current character rig. Modular face/hair
	 *  Blueprints can extend the native body/skin pass through ReceiveCharacterIdentityApplied. */
	UFUNCTION(BlueprintCallable, Category="Character")
	void ApplyCharacterIdentity(const FCharacterProfile& Profile);

    /** Removes pressure-suit and equipment layers for the identity/undersuit creator preview. */
    UFUNCTION(BlueprintCallable, Category="Character|Preview")
    void SetCharacterCreatorPreviewMode(bool bEnabled);

    UFUNCTION(BlueprintPure, Category="Character|MetaHuman")
    AActor* GetMetaHumanVisualActor() const;

	UFUNCTION(BlueprintImplementableEvent, Category="Character")
	void ReceiveCharacterIdentityApplied(const FCharacterProfile& Profile);

    UFUNCTION()
    void OnCharacterProfileChanged(const FCharacterProfile& NewProfile);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Zero G")
    float ThrusterAcceleration = 600.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Zero G")
    float PushOffImpulseStrength = 500.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticBootTraceDistance = 180.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticGloveReach = 300.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticGlovePullAcceleration = 900.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float RotationThrusterDegreesPerSecond = 120.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticSurfaceAlignSpeed = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticObjectPullForce = 65000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float MagneticObjectThrowImpulse = 90000.0f;

    UPROPERTY(Replicated, EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit", meta=(ClampMin="0.0", ClampMax="100.0"))
    float ThrusterFuelPercent = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float ThrusterFuelDrainPerSecond = 16.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float ThrusterFuelRechargePerSecond = 9.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit")
    float ThrusterRestartFuelPercent = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit|Feedback")
    TObjectPtr<USoundBase> MagnetEngageSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit|Feedback")
    TObjectPtr<USoundBase> MagnetReleaseSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit|Feedback")
    TObjectPtr<USoundBase> ThrusterLoopSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zero G|Magnetic Suit|Feedback")
    TObjectPtr<UParticleSystem> ThrusterParticle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Camera")
    float GravityRollInterpSpeed = 4.0f;

    UPROPERTY(ReplicatedUsing=OnRep_Oxygen, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float OxygenLevelPercent = 100.0f;

    UPROPERTY(ReplicatedUsing=OnRep_Health, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float HealthPercent = 100.0f;

    UPROPERTY(ReplicatedUsing=OnRep_Radiation, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float RadiationDoseSv = 0.0f;

    UPROPERTY(ReplicatedUsing=OnRep_SuitIntegrity, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Equipment")
    float SuitIntegrity = 0.8f;

    UPROPERTY(ReplicatedUsing=OnRep_Stability, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Equipment")
    float Stability = 0.5f;

    UPROPERTY(ReplicatedUsing=OnRep_Death, EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    bool bIsDead = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float OxygenDrainMultiplier = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Trauma", meta=(ClampMin="0.0"))
    float CollisionStressThreshold = 350.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Trauma", meta=(ClampMin="0.0"))
    float CollisionFractureThreshold = 750.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Trauma", meta=(ClampMin="0.0"))
    float CollisionHemorrhageThreshold = 1200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival|Trauma", meta=(ClampMin="0.0"))
    float CollisionTraumaCooldownSeconds = 0.75f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Weapon|Traversal", meta=(ClampMin="0.0"))
    float WeaponClearanceProbeDistanceCm = 35.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Weapon|Traversal", meta=(ClampMin="0.0"))
    float WeaponClearanceVelocityLookAheadSeconds = 0.12f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Weapon|Traversal", meta=(ClampMin="0.0"))
    float WeaponTraversalFeedbackCooldownSeconds = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Respawn")
    float RespawnDelaySeconds = 5.0f;

    /**
     * Damage is ignored for this long after a checkpoint respawn. A checkpoint is recorded where
     * the player completes an objective; if a threat is standing there when they die nearby, they
     * respawn into its reach and die again on the same spot, indefinitely. Long enough to move or
     * raise a weapon, short enough not to read as invulnerability.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Survival")
    float RespawnGraceSeconds = 3.0f;

    float LastRespawnWorldSeconds = -1000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Respawn")
    FVector RespawnLocationOffset = FVector(0.0f, 0.0f, 0.0f);

private:
    void ApplyPressureSuitVisuals();
    void ConfigureCharacterModelLayers();
    void UpdateFirstPersonHeadVisibility();
    bool IsAllowedMetaHumanClass(TSubclassOf<AActor> CandidateClass) const;
    void ApplyMetaHumanVisual(ECharacterFacePreset FacePreset, ECharacterHairStyle HairStyle);
    UClass* ResolveMetaHumanVisualClass(ECharacterFacePreset FacePreset) const;
    USkeletalMesh* ResolvePrimaryOversuitMesh() const;
    /** The assembled MetaHuman's undersuit garment: hidden under a worn oversuit, shown without one. */
    void SetUndersuitGarmentHidden(bool bHideGarment);
    void UpdateSuitConditionVisuals();
    void ValidateSuitAttachmentBones() const;
    void RespawnFromCheckpoint();

    /** Low-cost modular pressure-suit pieces attached to the mannequin skeleton. */
    UPROPERTY(VisibleAnywhere, Category="Appearance|Pressure Suit")
    TArray<TObjectPtr<UStaticMeshComponent>> PressureSuitParts;

    /**
     * A complete, separately authored oversuit. The assigned mesh must be rebound to the
     * character skeleton before use so it can follow the body through Leader Pose.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Appearance|Primary Oversuit", meta=(AllowPrivateAccess="true"))
    TObjectPtr<USkeletalMeshComponent> PrimaryOversuitMesh;

    /** Authored skinned cryo/bodysuit; shares the Manny skeleton and follows its pose exactly. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Appearance|Undersuit", meta=(AllowPrivateAccess="true"))
    TObjectPtr<USkeletalMeshComponent> CryoBodysuitMesh;

    /** Assembled MetaHuman supplies the head, face rig, eyes, teeth, and groom layers; driven by MetaHumanCharacterClass/SetMetaHumanPreset. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Appearance|Character", meta=(AllowPrivateAccess="true"))
    TObjectPtr<UChildActorComponent> MetaHumanActorComponent;

    /** Assembled MetaHuman actor for the preset-enum appearance path; the gameplay mesh remains an invisible animation driver. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Appearance|MetaHuman", meta=(AllowPrivateAccess="true"))
    TObjectPtr<UChildActorComponent> MetaHumanVisual;

    UPROPERTY(Transient)
    bool bCharacterCreatorPreviewMode = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Appearance|Primary Oversuit", meta=(AllowPrivateAccess="true"))
    TSoftObjectPtr<USkeletalMesh> CrewPrimaryOversuit;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Appearance|Primary Oversuit", meta=(AllowPrivateAccess="true"))
    TSoftObjectPtr<USkeletalMesh> EngineeringPrimaryOversuit;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Appearance|Primary Oversuit", meta=(AllowPrivateAccess="true"))
    TSoftObjectPtr<USkeletalMesh> MedicalPrimaryOversuit;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Appearance|Primary Oversuit", meta=(AllowPrivateAccess="true"))
    TSoftObjectPtr<USkeletalMesh> SecurityPrimaryOversuit;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMaterialInstanceDynamic>> PressureSuitDynamicMaterials;

    /** Indexed by EEquipmentType; hidden unless that equipment type is currently worn. */
    UPROPERTY(VisibleAnywhere, Category="Appearance|Equipment")
    TArray<TObjectPtr<UStaticMeshComponent>> WearableEquipmentParts;

    UPROPERTY()
    float TimeSinceDeath = 0.0f;

    double LastCollisionTraumaTime = -DBL_MAX;

    UPROPERTY(Transient)
    bool bWeaponTraversalBlocked = false;

    UPROPERTY(Transient)
    TWeakObjectPtr<AActor> WeaponTraversalBlocker;

    double LastWeaponTraversalFeedbackTime = -DBL_MAX;
    double LastWeaponTraversalBlockedTime = -DBL_MAX;

    FTransform InitialSpawnTransform = FTransform::Identity;

    UFUNCTION()
    void OnRep_Death();

    UFUNCTION()
    void HandleActorHit(AActor* SelfActor, AActor* OtherActor, FVector NormalImpulse, const FHitResult& Hit);

    void UpdateGravityAlignedCameraRoll(float DeltaTime);
    void UpdateWeaponTraversalCollision(float DeltaTime);
    void NotifyWeaponTraversalBlocked(const FHitResult& BlockingHit);
    void UpdateMagneticSuit(float DeltaTime);
    void UpdateMagneticSuitVisuals();
    bool FindMetalSurface(const FVector& Start, const FVector& Direction, float Distance, FHitResult& OutHit) const;
    bool IsMetalSurface(const FHitResult& Hit) const;
    void BeginGloveGrip(EMagneticGloveHand Hand);
    void EndGloveGrip(EMagneticGloveHand Hand);
    void UpdateGloveGrip(EMagneticGloveHand Hand, float DeltaTime);
    void ReleaseAllMagneticSystems();
    void HandlePrimaryWeaponFire();

    UFUNCTION(Server, Reliable)
    void ServerSetMagneticBootsEnabled(bool bEnabled);

    UFUNCTION(Server, Reliable)
    void ServerRequestGloveGrip(EMagneticGloveHand Hand, UPrimitiveComponent* TargetComponent, FVector_NetQuantize TargetLocation);

    UFUNCTION(Server, Reliable)
    void ServerReleaseGloveGrip(EMagneticGloveHand Hand);

    UFUNCTION(Server, Reliable)
    void ServerThrowMagneticObject(EMagneticGloveHand Hand, FVector_NetQuantizeNormal ThrowDirection);

    UFUNCTION(Server, Reliable)
    void ServerSetRotationThruster(bool bActive, FVector_NetQuantizeNormal SurfaceNormal);

    UFUNCTION()
    void OnRep_MagneticSuitState();

    FVector LastHitSurfaceNormal = FVector::ZeroVector;

    UPROPERTY(ReplicatedUsing=OnRep_MagneticSuitState, VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Zero G|Magnetic Suit")
    bool bMagneticBootsEnabled = false;

    UPROPERTY(ReplicatedUsing=OnRep_MagneticSuitState, VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Zero G|Magnetic Suit")
    bool bMagneticGlovesActive = false;

    UPROPERTY(ReplicatedUsing=OnRep_MagneticSuitState, VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Zero G|Magnetic Suit")
    bool bLeftMagneticGloveActive = false;

    UPROPERTY(ReplicatedUsing=OnRep_MagneticSuitState, VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Zero G|Magnetic Suit")
    bool bRightMagneticGloveActive = false;

    UPROPERTY(ReplicatedUsing=OnRep_MagneticSuitState)
    bool bRotationThrusterActive = false;
    FVector MagneticSurfaceNormal = FVector::ZeroVector;
    FVector GloveGripLocation = FVector::ZeroVector;
    TWeakObjectPtr<UPrimitiveComponent> GloveGripComponent;
    FVector RightGloveGripLocation = FVector::ZeroVector;
    TWeakObjectPtr<UPrimitiveComponent> RightGloveGripComponent;
    bool bHasValidMagneticTarget = false;
    bool bThrusterFuelLockedOut = false;

    UPROPERTY(VisibleAnywhere, Category="Appearance|Pressure Suit")
    TObjectPtr<UPointLightComponent> LeftBootMagnetLight;
    UPROPERTY(VisibleAnywhere, Category="Appearance|Pressure Suit")
    TObjectPtr<UPointLightComponent> RightBootMagnetLight;
    UPROPERTY(VisibleAnywhere, Category="Appearance|Pressure Suit")
    TObjectPtr<UPointLightComponent> LeftGloveMagnetLight;
    UPROPERTY(VisibleAnywhere, Category="Appearance|Pressure Suit")
    TObjectPtr<UPointLightComponent> RightGloveMagnetLight;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float BodyTemperatureC = 37.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (AllowPrivateAccess = "true"), Category="Survival")
    float StaminaPercent = 100.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Components")
    UAstrophysicsHazardComponent* HazardComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Components")
    TObjectPtr<UPlayerStatusEffectComponent> StatusEffectComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Components")
    TObjectPtr<UPlayerPsychosisComponent> PsychosisComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="UI")
    TObjectPtr<USurvivalHUDWidget> HUDWidget;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Components")
    class USpringArmComponent* CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Components")
    class UCameraComponent* ThirdPersonCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Camera")
    TObjectPtr<class UCameraComponent> FirstPersonCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Camera")
    /** First person is the normal gameplay view; contextual traversal or scripted beats may opt into third person. */
    bool bFirstPersonView = true;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Equipment")
    UEquipmentComponent* EquipmentComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Zero G")
    TObjectPtr<UZeroGGravityComponent> ZeroGGravityComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Interaction")
    TObjectPtr<UInteractionComponent> InteractionComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Interaction")
    TObjectPtr<UBioScannerComponent> BioScannerComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Activity")
    TObjectPtr<UPlayerActivityComponent> PlayerActivityComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Progression")
    TObjectPtr<UClassSkillComponent> SkillComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Versus")
    TObjectPtr<UTeamAffiliationComponent> TeamAffiliationComponent;

    /** Emits movement and (opt-in) microphone noise for the stealth/perception system. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Stealth")
    TObjectPtr<UPlayerNoiseEmitterComponent> NoiseEmitterComponent;

    /** Supplies how easy this character is to see, queried by observers during AI perception. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"), Category="Stealth")
    TObjectPtr<UPlayerVisibilityComponent> VisibilityComponent;

    /**
     * Noise a thrown object makes where it lands. This is what turns the existing throw verb into
     * a distraction: the noise is reported at the impact point, not at the thrower, so an
     * investigating AI walks toward the object rather than toward the player.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(AllowPrivateAccess="true", ClampMin="0.0", ClampMax="1.0"), Category="Stealth")
    float ThrownObjectImpactLoudness = 0.7f;

    /**
     * Impact speed at or above which a thrown object makes its full noise. Below this it scales
     * down, so nudging something is not the same as hurling it across a compartment.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(AllowPrivateAccess="true", ClampMin="1.0"), Category="Stealth")
    float ThrownObjectLoudImpactSpeed = 600.0f;

    /** Reports the landing noise for an object this character threw, then stops tracking it. */
    UFUNCTION()
    void HandleThrownObjectImpact(UPrimitiveComponent* HitComponent, AActor* OtherActor,
        UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit);

    /**
     * Components thrown by this character and still awaiting their first impact. Weak so a
     * destroyed or streamed-out object cannot keep a stale binding alive.
     */
    TArray<TWeakObjectPtr<UPrimitiveComponent>> TrackedThrownComponents;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Inventory")
    TObjectPtr<UInventoryComponent> InventoryComponent;

    /** Shared physical mount: its weapon can be handed unchanged to an aerial or robotic drone. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Weapon")
    TObjectPtr<UWeaponMountComponent> WeaponMountComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta = (AllowPrivateAccess = "true"), Category="Components")
    TObjectPtr<UPathogenLoadComponent> PathogenLoadComponent;
};
