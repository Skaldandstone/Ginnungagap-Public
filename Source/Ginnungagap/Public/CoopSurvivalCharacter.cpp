// Copyright Epic Games, Inc. All Rights Reserved.

#include "CoopSurvivalCharacter.h"
#include "Net/UnrealNetwork.h"
#include "AstrophysicsHazardComponent.h"
#include "UI/SurvivalHUDWidget.h"
#include "Equipment/EquipmentComponent.h"
#include "Equipment/ExpeditionLoadoutSubsystem.h"
#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Engine/GameInstance.h"
#include "GameFramework/SpringArmComponent.h"
#include "Ship/ZeroGGravityComponent.h"
#include "Interaction/InteractionComponent.h"
#include "Interaction/BioScannerComponent.h"
#include "Activities/PlayerActivityComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "Meta/CharacterProfileSubsystem.h"
#include "Progression/ClassSkillComponent.h"
#include "Meta/RunOutcomeSubsystem.h"
#include "Inventory/InventoryComponent.h"
#include "Weapons/CaptiveBoltDriver.h"
#include "Weapons/ShipboardWeapon.h"
#include "Weapons/WeaponMountComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Components/CapsuleComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/MetaHumanCopyPoseAnimInstance.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Bloom/PathogenLoadComponent.h"
#include "LevelSetup/ShipCheckpointSubsystem.h"
#include "StatusEffects/PlayerStatusEffectComponent.h"
#include "StatusEffects/PlayerPsychosisComponent.h"
#include "Versus/TeamAffiliationComponent.h"
#include "Stealth/PlayerNoiseEmitterComponent.h"
#include "Stealth/PlayerVisibilityComponent.h"
#include "Stealth/NoisePerceptionSubsystem.h"

namespace
{
    /**
     * A MetaHuman assembled actor spawns with static scene components, and a static component
     * cannot be moved in game: attached to the character it stayed exactly where the character
     * first stood, a second body standing at the spawn point while the crew walked away (James
     * saw "random suits" in the casualty station; the survey walk listed two faces on deck 3 while
     * the crew was on deck 11). Every scene component is made movable and the actor snapped back
     * onto its holder.
     */
    void TetherChildActor(UChildActorComponent* Holder)
    {
        AActor* Child = Holder ? Holder->GetChildActor() : nullptr;
        if (!Child) return;
        for (USceneComponent* Scene : TInlineComponentArray<USceneComponent*>(Child))
        {
            if (Scene && Scene->Mobility != EComponentMobility::Movable) Scene->SetMobility(EComponentMobility::Movable);
        }
        if (Child->GetRootComponent() && Child->GetRootComponent()->GetAttachParent() != Holder)
        {
            Child->AttachToComponent(Holder, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        }
        else if (Child->GetRootComponent())
        {
            Child->GetRootComponent()->SetRelativeTransform(FTransform::Identity);
        }
    }
}

ACoopSurvivalCharacter::ACoopSurvivalCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    bReplicates = true;

    HazardComponent = CreateDefaultSubobject<UAstrophysicsHazardComponent>(TEXT("HazardComponent"));
    StatusEffectComponent = CreateDefaultSubobject<UPlayerStatusEffectComponent>(TEXT("StatusEffectComponent"));
    PsychosisComponent = CreateDefaultSubobject<UPlayerPsychosisComponent>(TEXT("PsychosisComponent"));
    EquipmentComponent = CreateDefaultSubobject<UEquipmentComponent>(TEXT("EquipmentComponent"));
    ZeroGGravityComponent = CreateDefaultSubobject<UZeroGGravityComponent>(TEXT("ZeroGGravityComponent"));
    InteractionComponent = CreateDefaultSubobject<UInteractionComponent>(TEXT("InteractionComponent"));
    BioScannerComponent = CreateDefaultSubobject<UBioScannerComponent>(TEXT("BioScannerComponent"));
    PlayerActivityComponent = CreateDefaultSubobject<UPlayerActivityComponent>(TEXT("PlayerActivityComponent"));
    SkillComponent = CreateDefaultSubobject<UClassSkillComponent>(TEXT("SkillComponent"));
    InventoryComponent = CreateDefaultSubobject<UInventoryComponent>(TEXT("InventoryComponent"));
    PathogenLoadComponent = CreateDefaultSubobject<UPathogenLoadComponent>(TEXT("PathogenLoadComponent"));
    TeamAffiliationComponent = CreateDefaultSubobject<UTeamAffiliationComponent>(TEXT("TeamAffiliationComponent"));
    NoiseEmitterComponent = CreateDefaultSubobject<UPlayerNoiseEmitterComponent>(TEXT("NoiseEmitterComponent"));
    VisibilityComponent = CreateDefaultSubobject<UPlayerVisibilityComponent>(TEXT("VisibilityComponent"));
    TeamAffiliationComponent->Team = EVersusTeam::Protagonist;
    TeamAffiliationComponent->Faction = EAntagonistFaction::None;

    // Ship crews use a common, animation-compatible human rig. The modular hard-suit
    // silhouette is deliberately compact and utilitarian instead of a bulky EVA design.
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> CrewMesh(
        TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> CryoBodysuitAsset(
        TEXT("/Game/Characters/Player/Undersuit/CryoBodysuitV32/SK_CryoBodysuit_V32_Manny.SK_CryoBodysuit_V32_Manny"));
    static ConstructorHelpers::FClassFinder<UAnimInstance> CrewAnim(
        TEXT("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"));

    // The oversuit the player actually wears. The four per-role slots were declared and never
    // filled, so ResolvePrimaryOversuitMesh returned null and the character ran the whole demo in
    // its undersuit.
    //
    // The Space Marshal shell, re-imported against SK_Mannequin so it can be driven by
    // SetLeaderPoseComponent, which binds by skeleton identity rather than similarity. The shipped
    // asset carries its own duplicate skeleton and cannot be worn; the two hierarchies are in fact
    // the same 89 bones with the same names, so this is a re-import rather than a retarget. See
    // tools/rebind_space_marshal_to_manny.py.
    //
    // All four roles wear it for now. The per-role garments -- Crew, Engineering, Medical and
    // Security "Work_I01" -- are all still on an 80-bone SM_Male_Oversuit_UE5 skeleton and would
    // each need the same treatment before they can be worn at all.
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> PrimaryOversuitAsset(
        TEXT("/Game/Characters/PlayerSuits/PrimaryOversuits/SpaceMarshalManny/"
             "SK_SpaceMarshal_Manny.SK_SpaceMarshal_Manny"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
        TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(
        TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SuitMaterial(
        TEXT("/Game/Assets/Materials/M_SpaceSuit_Damaged.M_SpaceSuit_Damaged"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ArmorMaterial(
        TEXT("/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark"));

    GetCapsuleComponent()->InitCapsuleSize(42.0f, 96.0f);
    if (CrewMesh.Succeeded())
    {
        GetMesh()->SetSkeletalMesh(CrewMesh.Object);
        GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -90.0f));
        GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
        if (CrewAnim.Succeeded())
        {
            GetMesh()->SetAnimInstanceClass(CrewAnim.Class);
        }
        if (SuitMaterial.Succeeded())
        {
            for (int32 Slot = 0; Slot < GetMesh()->GetNumMaterials(); ++Slot)
            {
                GetMesh()->SetMaterial(Slot, SuitMaterial.Object);
            }
        }
    }

    // Primary oversuits remain independent assets rather than baked player or undersuit
    // geometry. They share animation through Leader Pose after being rebound to this skeleton.
    PrimaryOversuitMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("PrimaryOversuitMesh"));
    PrimaryOversuitMesh->SetupAttachment(GetMesh());
    PrimaryOversuitMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PrimaryOversuitMesh->SetGenerateOverlapEvents(false);
    PrimaryOversuitMesh->SetCastShadow(true);
    PrimaryOversuitMesh->SetVisibility(false, true);
    PrimaryOversuitMesh->SetLeaderPoseComponent(GetMesh());

    if (PrimaryOversuitAsset.Succeeded())
    {
        CrewPrimaryOversuit = PrimaryOversuitAsset.Object;
        EngineeringPrimaryOversuit = PrimaryOversuitAsset.Object;
        MedicalPrimaryOversuit = PrimaryOversuitAsset.Object;
        SecurityPrimaryOversuit = PrimaryOversuitAsset.Object;
    }

    CryoBodysuitMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("CryoBodysuitMesh"));
    CryoBodysuitMesh->SetupAttachment(GetMesh());
    CryoBodysuitMesh->SetRelativeTransform(FTransform::Identity);
    CryoBodysuitMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CryoBodysuitMesh->SetGenerateOverlapEvents(false);
    CryoBodysuitMesh->SetCastShadow(true);
    CryoBodysuitMesh->SetVisibility(false, true);
    if (CryoBodysuitAsset.Succeeded())
    {
        CryoBodysuitMesh->SetSkeletalMesh(CryoBodysuitAsset.Object);
        CryoBodysuitMesh->SetLeaderPoseComponent(GetMesh());
    }

    MetaHumanActorComponent = CreateDefaultSubobject<UChildActorComponent>(TEXT("MetaHumanActor"));
    MetaHumanActorComponent->SetChildActorOwnerOnCreation(true);
    MetaHumanActorComponent->SetupAttachment(RootComponent);
    MetaHumanActorComponent->SetRelativeLocation(FVector(0.0f, 0.0f, -90.0f));
    MetaHumanActorComponent->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));

    // The assembled MetaHuman remains a distinct visual actor. Its body copies the gameplay
    // driver's pose by bone name, avoiding unsafe Leader Pose indexing across different rigs.
    MetaHumanVisual = CreateDefaultSubobject<UChildActorComponent>(TEXT("MetaHumanVisual"));
    MetaHumanVisual->SetChildActorOwnerOnCreation(true);
    MetaHumanVisual->SetupAttachment(GetMesh());
    MetaHumanVisual->SetRelativeTransform(FTransform::Identity);

    UMaterialInterface* PressureSuitArmorMaterial = ArmorMaterial.Object;
    auto AddSuitPart = [this, PressureSuitArmorMaterial](const TCHAR* Name, UStaticMesh* Shape, const FName Bone,
        const FVector Location, const FRotator Rotation, const FVector Scale)
    {
        UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Part->SetupAttachment(GetMesh(), Bone);
        Part->SetStaticMesh(Shape);
        Part->SetRelativeLocation(Location);
        Part->SetRelativeRotation(Rotation);
        Part->SetRelativeScale3D(Scale);
        Part->SetMobility(EComponentMobility::Movable);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetCastShadow(true);
        if (PressureSuitArmorMaterial)
        {
            Part->SetMaterial(0, PressureSuitArmorMaterial);
        }
        PressureSuitParts.Add(Part);
    };

    if (CubeMesh.Succeeded() && SphereMesh.Succeeded() && CylinderMesh.Succeeded())
    {
        AddSuitPart(TEXT("HelmetShell"), SphereMesh.Object, TEXT("head"), FVector(2, 0, 2), FRotator::ZeroRotator, FVector(.18f, .18f, .21f));
        AddSuitPart(TEXT("HelmetVisor"), SphereMesh.Object, TEXT("head"), FVector(10, 0, 2), FRotator::ZeroRotator, FVector(.11f, .17f, .14f));
        AddSuitPart(TEXT("PressureCollar"), CylinderMesh.Object, TEXT("neck_01"), FVector::ZeroVector, FRotator::ZeroRotator, FVector(.16f, .16f, .055f));
        AddSuitPart(TEXT("ChestPlate"), CubeMesh.Object, TEXT("spine_03"), FVector(8, 0, 1), FRotator(0, 90, 0), FVector(.075f, .22f, .18f));
        AddSuitPart(TEXT("LifeSupportPack"), CubeMesh.Object, TEXT("spine_03"), FVector(-12, 0, 1), FRotator(0, 90, 0), FVector(.10f, .20f, .25f));
        AddSuitPart(TEXT("ChestControlUnit"), CubeMesh.Object, TEXT("spine_03"), FVector(16, -8, 2), FRotator(0, 90, 0), FVector(.035f, .07f, .07f));
        AddSuitPart(TEXT("LeftShoulder"), SphereMesh.Object, TEXT("upperarm_l"), FVector(2, 0, 0), FRotator(0, 90, 0), FVector(.11f, .13f, .13f));
        AddSuitPart(TEXT("RightShoulder"), SphereMesh.Object, TEXT("upperarm_r"), FVector(2, 0, 0), FRotator(0, 90, 0), FVector(.11f, .13f, .13f));
        AddSuitPart(TEXT("LeftForearmComputer"), CubeMesh.Object, TEXT("lowerarm_l"), FVector(12, 0, 5), FRotator::ZeroRotator, FVector(.055f, .09f, .045f));
        AddSuitPart(TEXT("LeftKneePad"), CubeMesh.Object, TEXT("calf_l"), FVector(3, 0, 0), FRotator(0, 90, 0), FVector(.05f, .09f, .08f));
        AddSuitPart(TEXT("RightKneePad"), CubeMesh.Object, TEXT("calf_r"), FVector(3, 0, 0), FRotator(0, 90, 0), FVector(.05f, .09f, .08f));
        AddSuitPart(TEXT("LeftBootShell"), CubeMesh.Object, TEXT("foot_l"), FVector(7, 0, 1), FRotator::ZeroRotator, FVector(.13f, .09f, .065f));
        AddSuitPart(TEXT("RightBootShell"), CubeMesh.Object, TEXT("foot_r"), FVector(7, 0, 1), FRotator::ZeroRotator, FVector(.13f, .09f, .065f));
        AddSuitPart(TEXT("LeftGlove"), SphereMesh.Object, TEXT("hand_l"), FVector::ZeroVector, FRotator::ZeroRotator, FVector(.08f));
        AddSuitPart(TEXT("RightGlove"), SphereMesh.Object, TEXT("hand_r"), FVector::ZeroVector, FRotator::ZeroRotator, FVector(.08f));
        AddSuitPart(TEXT("LeftThighPouch"), CubeMesh.Object, TEXT("thigh_l"), FVector(0, 9, -4), FRotator::ZeroRotator, FVector(.06f, .11f, .14f));
        AddSuitPart(TEXT("RightThighPouch"), CubeMesh.Object, TEXT("thigh_r"), FVector(0, -9, -4), FRotator::ZeroRotator, FVector(.06f, .11f, .14f));
    }

    auto AddMagnetLight = [this](const TCHAR* Name, const FName Bone, const FVector& Location,
        const FLinearColor& Color, float Intensity, float Radius)
    {
        UPointLightComponent* Light = CreateDefaultSubobject<UPointLightComponent>(Name);
        Light->SetupAttachment(GetMesh(), Bone);
        Light->SetRelativeLocation(Location);
        Light->SetLightColor(Color);
        Light->SetIntensity(Intensity);
        Light->SetAttenuationRadius(Radius);
        Light->SetCastShadows(false);
        Light->SetVisibility(false);
        return Light;
    };
    const FLinearColor MagnetRed(1.0f, 0.025f, 0.01f, 1.0f);
    LeftBootMagnetLight = AddMagnetLight(TEXT("LeftBootMagnetLight"), TEXT("foot_l"), FVector(8, 0, -3), MagnetRed, 1800.0f, 75.0f);
    RightBootMagnetLight = AddMagnetLight(TEXT("RightBootMagnetLight"), TEXT("foot_r"), FVector(8, 0, -3), MagnetRed, 1800.0f, 75.0f);
    LeftGloveMagnetLight = AddMagnetLight(TEXT("LeftGloveMagnetLight"), TEXT("hand_l"), FVector::ZeroVector, FLinearColor(1.0f, 0.08f, 0.025f), 950.0f, 105.0f);
    // The wrist lamp: a spot on the left forearm, thrown the way the hand points (a bone's X
    // runs down its length), off until the crew are in the suit and switch it on.
    // The leak: the hideout pack's smoke, tiny, at the chest seam, off until the suit is torn.
    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> LeakSystem(TEXT("/Game/Scifi_Hideout/FX/NS_smoke.NS_smoke"));
    SuitLeak = CreateDefaultSubobject<UNiagaraComponent>(TEXT("SuitLeak"));
    SuitLeak->SetupAttachment(GetMesh(), TEXT("spine_03"));
    if (LeakSystem.Succeeded()) SuitLeak->SetAsset(LeakSystem.Object);
    SuitLeak->SetRelativeLocation(FVector(14.0f, 6.0f, 0.0f));
    SuitLeak->SetRelativeRotation(FRotator(0.0f, 0.0f, -70.0f));
    SuitLeak->SetRelativeScale3D(FVector(0.12f, 0.12f, 0.12f));
    SuitLeak->SetAutoActivate(false);
    WristLamp = CreateDefaultSubobject<USpotLightComponent>(TEXT("WristLamp"));
    WristLamp->SetupAttachment(GetMesh(), TEXT("hand_l"));
    WristLamp->SetRelativeLocation(FVector(-6.0f, 0.0f, 2.0f));
    WristLamp->SetRelativeRotation(FRotator::ZeroRotator);
    WristLamp->SetLightColor(FLinearColor(0.92f, 0.95f, 1.0f));
    WristLamp->SetIntensity(6500.0f);
    WristLamp->SetAttenuationRadius(3200.0f);
    WristLamp->SetInnerConeAngle(18.0f);
    WristLamp->SetOuterConeAngle(34.0f);
    WristLamp->SetCastShadows(true);
    WristLamp->SetVisibility(false);
    // The housing: a flat block strapped over the back of the forearm, with a lens on its end. It
    // is what the crew see of the lamp in first person, where the suit itself is not drawn.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> HousingMaterial(TEXT("/Game/Modular_Scifi_Mechanic_Base/Material/MI/MI_Metal_05.MI_Metal_05"));
    WristLampHousing = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WristLampHousing"));
    WristLampHousing->SetupAttachment(GetMesh(), TEXT("hand_l"));
    if (CubeMesh.Succeeded()) WristLampHousing->SetStaticMesh(CubeMesh.Object);
    if (HousingMaterial.Succeeded()) WristLampHousing->SetMaterial(0, HousingMaterial.Object);
    WristLampHousing->SetRelativeLocation(FVector(-14.0f, 0.0f, 4.5f));
    WristLampHousing->SetRelativeScale3D(FVector(0.14f, 0.05f, 0.035f));
    WristLampHousing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WristLampHousing->SetCastShadow(false);
    WristLampHousing->SetVisibility(false);
    WristLampLens = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WristLampLens"));
    WristLampLens->SetupAttachment(WristLampHousing);
    if (CylinderMesh.Succeeded()) WristLampLens->SetStaticMesh(CylinderMesh.Object);
    if (SuitMaterial.Succeeded()) WristLampLens->SetMaterial(0, SuitMaterial.Object);
    WristLampLens->SetRelativeLocation(FVector(0.5f, 0.0f, 0.0f));
    WristLampLens->SetRelativeRotation(FRotator(90.0f, 0.0f, 0.0f));
    WristLampLens->SetRelativeScale3D(FVector(0.5f, 0.7f, 0.12f));
    WristLampLens->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WristLampLens->SetCastShadow(false);
    WristLampLens->SetVisibility(false);

    RightGloveMagnetLight = AddMagnetLight(TEXT("RightGloveMagnetLight"), TEXT("hand_r"), FVector::ZeroVector, FLinearColor(1.0f, 0.08f, 0.025f), 950.0f, 105.0f);

    auto AddWearable = [this](const TCHAR* Name, const TCHAR* AssetPath, const FName Bone,
        const FVector Location, const FRotator Rotation)
    {
        UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Part->SetupAttachment(GetMesh(), Bone);
        Part->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, AssetPath));
        Part->SetRelativeLocation(Location);
        Part->SetRelativeRotation(Rotation);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetGenerateOverlapEvents(false);
        Part->SetVisibility(false, true);
        WearableEquipmentParts.Add(Part);
    };
    AddWearable(TEXT("EquippedHelmetVisor"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_HelmetLamp.SM_Equip_HelmetLamp"), TEXT("head"), FVector(2,-14,9), FRotator(0,90,0));
    AddWearable(TEXT("EquippedThermalPlating"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_ThermalPlating.SM_Equip_ThermalPlating"), TEXT("spine_03"), FVector(9,0,0), FRotator(0,90,0));
    AddWearable(TEXT("EquippedRadiationShield"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_RadiationShield.SM_Equip_RadiationShield"), TEXT("spine_03"), FVector(-14,0,0), FRotator(0,90,0));
    AddWearable(TEXT("EquippedPressureSeal"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_PressureSeal.SM_Equip_PressureSeal"), TEXT("neck_01"), FVector::ZeroVector, FRotator::ZeroRotator);
    AddWearable(TEXT("EquippedArmorPlating"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_ArmorPauldron.SM_Equip_ArmorPauldron"), TEXT("upperarm_r"), FVector(2,0,0), FRotator(0,90,0));
    AddWearable(TEXT("EquippedOxygenFilter"), TEXT("/Game/Characters/Player/Equipment/Meshes/SM_Equip_OxygenFilter.SM_Equip_OxygenFilter"), TEXT("spine_03"), FVector(-16,10,-4), FRotator(0,90,0));

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 400.0f;
    CameraBoom->bUsePawnControlRotation = false;
    CameraBoom->bInheritPitch = false;
    CameraBoom->bInheritYaw = false;
    CameraBoom->bInheritRoll = false;

    ThirdPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ThirdPersonCamera"));
    ThirdPersonCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    ThirdPersonCamera->bUsePawnControlRotation = false;
    ThirdPersonCamera->SetAutoActivate(false);

    FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
    FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
    // Forward of the oversuit's chest: at 10 cm the suit's own collar and shoulders sat across
    // the bottom of the frame whenever the crew looked down at a floor console (the survey walk's
    // "own body in view" finding); the eye is at the visor, not the back of the helmet.
    // Ten centimetres forward: further, and the eye trace stood past what a wall console offers to
    // look at. The suit no longer sits across the frame because the owner does not see it at all.
    FirstPersonCamera->SetRelativeLocation(FVector(10.0f, 0.0f, 68.0f));
    FirstPersonCamera->bUsePawnControlRotation = true;
    FirstPersonCamera->SetAutoActivate(true);

    WeaponMountComponent = CreateDefaultSubobject<UWeaponMountComponent>(TEXT("WeaponMountComponent"));
    WeaponMountComponent->SetupAttachment(FirstPersonCamera);
    // Held a little further out and lower than a rifle stance: the tools are pistol-sized meshes
    // whose grips sat inside the camera's near field and filled half the view.
    WeaponMountComponent->SetRelativeLocation(FVector(46.0f, 18.0f, -15.0f));
    WeaponMountComponent->SetRelativeRotation(FRotator::ZeroRotator);
    WeaponMountComponent->OperatorType = EWeaponOperatorType::Player;
    WeaponMountComponent->bSpawnDefaultWeapon = true;
    WeaponMountComponent->DefaultWeaponClass = ACaptiveBoltDriver::StaticClass();

    // These bulky pieces would intersect the default first-person view. Owner-no-see leaves the
    // complete suit visible to other players and is cleared whenever a contextual third-person
    // sequence takes control of the camera.
    for (UStaticMeshComponent* Part : PressureSuitParts)
    {
        if (!Part) continue;
        const FName Name = Part->GetFName();
        const bool bHideInFirstPerson = Name == TEXT("HelmetShell") || Name == TEXT("HelmetVisor") ||
            Name == TEXT("PressureCollar") || Name == TEXT("LifeSupportPack");
        Part->SetOwnerNoSee(bHideInFirstPerson);
    }

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->SetMovementMode(MOVE_Flying);
        Movement->GravityScale = 0.0f;
        Movement->BrakingDecelerationFlying = 0.0f;
        Movement->BrakingFrictionFactor = 0.0f;
        Movement->MaxFlySpeed = 100000.0f;
    }
}

void ACoopSurvivalCharacter::BeginPlay()
{
    Super::BeginPlay();

    if (WeaponMountComponent)
    {
        WeaponMountComponent->OnMountedWeaponChanged.AddUniqueDynamic(this, &ACoopSurvivalCharacter::HandleMountedWeaponChanged);
        if (WeaponMountComponent->GetMountedWeapon())
        {
            HandleMountedWeaponChanged(WeaponMountComponent->GetMountedWeapon());
        }
    }

    InitialSpawnTransform = GetActorTransform();

    ConfigureCharacterModelLayers();
    ApplyPressureSuitVisuals();
    RefreshEquipmentVisuals();
    ValidateSuitAttachmentBones();

    OnActorHit.AddDynamic(this, &ACoopSurvivalCharacter::HandleActorHit);

    if (UGameInstance* GI = GetGameInstance())
    {
		if (UExpeditionLoadoutSubsystem* Loadout = GI->GetSubsystem<UExpeditionLoadoutSubsystem>())
		{
			Loadout->ApplyLoadout(EquipmentComponent);
		}

        if (UCharacterProfileSubsystem* ProfileSubsystem = GI->GetSubsystem<UCharacterProfileSubsystem>())
        {
            const FCharacterProfile& Profile = ProfileSubsystem->GetProfile();
			ApplyCharacterIdentity(Profile);
            ApplyAppearanceCosmetic(Profile.AppearanceVariant);
            if (IsLocallyControlled())
            {
                SetPressureSuitRole(Profile.SuitRole);
                SetMetaHumanPreset(Profile.MetaHumanPresetId);
            }

            ProfileSubsystem->OnCharacterProfileChanged.AddDynamic(this, &ACoopSurvivalCharacter::OnCharacterProfileChanged);
        }

        // Pull role, owned ranks and the equipped loadout in one step. Replaying unlocks
        // individually was only necessary when each one mutated character stats on the way past.
        if (SkillComponent)
        {
            SkillComponent->ReloadFromProgression();
        }
    }
}

void ACoopSurvivalCharacter::HandleMountedWeaponChanged(AShipboardWeapon* Weapon)
{
    if (!WeaponMountComponent || !GetMesh())
    {
        return;
    }
    if (!HoldAnimation)
    {
        HoldAnimation = LoadObject<UAnimSequenceBase>(nullptr,
            TEXT("/Game/Characters/Mannequins/Anims/Tools/A_ToolHold_Combo_B.A_ToolHold_Combo_B"));
    }
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (Weapon)
    {
        if (bFirstPersonView && FirstPersonCamera)
        {
            // In first person the body is not drawn and the arm's pose is nobody's business: the
            // tool rides the camera, lower right, pointing down the view, the way the empty mount
            // does. Third person hands it to the hand, where the hold pose carries it.
            WeaponMountComponent->AttachToComponent(FirstPersonCamera, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
            // The mount is the tool's nose; turned to point down the view its body runs back toward
            // the eye, so the nose sits well forward and the body fills the lower right.
            WeaponMountComponent->SetRelativeLocation(FVector(90.0f, 21.0f, -26.0f));
            WeaponMountComponent->SetRelativeRotation(FRotator(-6.0f, 180.0f, 0.0f));
        }
        else
        {
            WeaponMountComponent->AttachToComponent(GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, TEXT("hand_r"));
            WeaponMountComponent->SetRelativeLocation(HandGripLocation);
            WeaponMountComponent->SetRelativeRotation(HandGripRotation);
        }
        if (Anim && HoldAnimation)
        {
            // Held on the frame where the arm is out: a play rate of nearly nothing from that time.
            Anim->PlaySlotAnimationAsDynamicMontage(HoldAnimation, TEXT("DefaultSlot"), 0.3f, 0.3f, 0.001f, 1, -1.0f, HoldAnimationTime);
        }
    }
    else
    {
        WeaponMountComponent->AttachToComponent(FirstPersonCamera, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
        // Held like a tool, not carried like a tray: the powertool's length runs along its own X, and
        // at yaw 0 that lay across the bottom of the frame. Turned to point down the view, lifted
        // into the lower right where a right hand holds it.
        WeaponMountComponent->SetRelativeLocation(FVector(42.0f, 24.0f, -10.0f));
        WeaponMountComponent->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
        if (Anim && HoldAnimation)
        {
            Anim->StopSlotAnimation(0.3f, TEXT("DefaultSlot"));
        }
    }
}

void ACoopSurvivalCharacter::RefreshEquipmentVisuals()
{
    for (UStaticMeshComponent* Part : WearableEquipmentParts)
    {
        if (Part) Part->SetVisibility(false, true);
    }
    if (!EquipmentComponent) return;
    for (const FEquipmentSlotState& Slot : EquipmentComponent->EquipmentSlots)
    {
        if (!Slot.bEquipped) continue;
        const int32 Index = static_cast<int32>(Slot.EquippedItem.Type);
        if (WearableEquipmentParts.IsValidIndex(Index) && WearableEquipmentParts[Index])
        {
            WearableEquipmentParts[Index]->SetVisibility(true, true);
        }
    }
}

void ACoopSurvivalCharacter::Tick(float DeltaTime)
{
    if (bWeaponTraversalBlocked && GetWorld()
        && GetWorld()->GetTimeSeconds() - LastWeaponTraversalBlockedTime > 0.15)
    {
        bWeaponTraversalBlocked = false;
        WeaponTraversalBlocker.Reset();
    }
    // Character movement and zero-G inertia only know about the capsule. Clamp an existing
    // velocity against the mounted weapon before the movement component advances this frame.
    UpdateWeaponTraversalCollision(DeltaTime);
    Super::Tick(DeltaTime);
    UpdateFloatPose();

    if (bIsDead)
    {
        if (bMagneticBootsEnabled || bMagneticGlovesActive || bRotationThrusterActive) ReleaseAllMagneticSystems();
        TimeSinceDeath += DeltaTime;
        if (HasAuthority() && TimeSinceDeath >= RespawnDelaySeconds)
        {
            RespawnFromCheckpoint();
        }
    }

    UpdateGravityAlignedCameraRoll(DeltaTime);
    UpdateMagneticSuit(DeltaTime);
    UpdateSuitConditionVisuals();
}

void ACoopSurvivalCharacter::SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAction(TEXT("PrimaryFire"), IE_Pressed, this, &ACoopSurvivalCharacter::HandlePrimaryWeaponFire);
    PlayerInputComponent->BindAction(TEXT("ToggleWeaponModification"), IE_Pressed, this, &ACoopSurvivalCharacter::ToggleUnsafeWeaponModification);
    PlayerInputComponent->BindAction(TEXT("ToggleMagneticBoots"), IE_Pressed, this, &ACoopSurvivalCharacter::ToggleMagneticBoots);
    PlayerInputComponent->BindAction(TEXT("ToggleWristLamp"), IE_Pressed, this, &ACoopSurvivalCharacter::ToggleWristLamp);
    PlayerInputComponent->BindAction(TEXT("MagneticGloveGrip"), IE_Pressed, this, &ACoopSurvivalCharacter::BeginMagneticGloveGrip);
    PlayerInputComponent->BindAction(TEXT("MagneticGloveGrip"), IE_Released, this, &ACoopSurvivalCharacter::EndMagneticGloveGrip);
    PlayerInputComponent->BindAction(TEXT("RightMagneticGloveGrip"), IE_Pressed, this, &ACoopSurvivalCharacter::BeginRightMagneticGloveGrip);
    PlayerInputComponent->BindAction(TEXT("RightMagneticGloveGrip"), IE_Released, this, &ACoopSurvivalCharacter::EndRightMagneticGloveGrip);
    PlayerInputComponent->BindAction(TEXT("ThrowMagneticObject"), IE_Pressed, this, &ACoopSurvivalCharacter::ThrowMagneticObject);
    PlayerInputComponent->BindAction(TEXT("RotationThruster"), IE_Pressed, this, &ACoopSurvivalCharacter::BeginRotationThruster);
    PlayerInputComponent->BindAction(TEXT("RotationThruster"), IE_Released, this, &ACoopSurvivalCharacter::EndRotationThruster);

    // One binding per payload slot rather than a single cycling key: an ability you have to scroll
    // to is one you will not reach in the moment that made you bring it.
    PlayerInputComponent->BindAction(TEXT("ActivateSkillSlot1"), IE_Pressed, this, &ACoopSurvivalCharacter::ActivateSkillSlot1);
    PlayerInputComponent->BindAction(TEXT("ActivateSkillSlot2"), IE_Pressed, this, &ACoopSurvivalCharacter::ActivateSkillSlot2);
    PlayerInputComponent->BindAction(TEXT("ActivateSkillSlot3"), IE_Pressed, this, &ACoopSurvivalCharacter::ActivateSkillSlot3);
}

void ACoopSurvivalCharacter::ActivateSkillSlot1() { ActivateSkillSlot(0); }
void ACoopSurvivalCharacter::ActivateSkillSlot2() { ActivateSkillSlot(1); }
void ACoopSurvivalCharacter::ActivateSkillSlot3() { ActivateSkillSlot(2); }

bool ACoopSurvivalCharacter::ActivateSkillSlot(int32 SlotIndex)
{
    // Refused while dead so a corpse cannot spend a charge, and so the bar does not appear live
    // during the respawn wait.
    if (bIsDead || !SkillComponent)
    {
        return false;
    }
    return SkillComponent->ActivateSkillSlot(SlotIndex);
}

void ACoopSurvivalCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(ACoopSurvivalCharacter, OxygenLevelPercent);
    DOREPLIFETIME(ACoopSurvivalCharacter, HealthPercent);
    DOREPLIFETIME(ACoopSurvivalCharacter, RadiationDoseSv);
    DOREPLIFETIME(ACoopSurvivalCharacter, SuitIntegrity);
    DOREPLIFETIME(ACoopSurvivalCharacter, Stability);
    DOREPLIFETIME(ACoopSurvivalCharacter, bIsDead);
    DOREPLIFETIME(ACoopSurvivalCharacter, PressureSuitRole);
    DOREPLIFETIME(ACoopSurvivalCharacter, bPressureOversuitEquipped);
    DOREPLIFETIME(ACoopSurvivalCharacter, MetaHumanCharacterClass);
    DOREPLIFETIME(ACoopSurvivalCharacter, bMagneticBootsEnabled);
    DOREPLIFETIME(ACoopSurvivalCharacter, bWristLampOn);
    DOREPLIFETIME(ACoopSurvivalCharacter, bMagneticGlovesActive);
    DOREPLIFETIME(ACoopSurvivalCharacter, bLeftMagneticGloveActive);
    DOREPLIFETIME(ACoopSurvivalCharacter, bRightMagneticGloveActive);
    DOREPLIFETIME(ACoopSurvivalCharacter, bRotationThrusterActive);
    DOREPLIFETIME(ACoopSurvivalCharacter, ThrusterFuelPercent);
}

bool ACoopSurvivalCharacter::GrantStartingWeapon()
{
    // Nothing configured is a valid scenario, not a failure: a crew member can legitimately start
    // a run with empty hands, and the demo hands a weapon over at the workshop rather than in cryo.
    if (!StartingWeaponClass || !WeaponMountComponent)
    {
        return false;
    }

    // Server only. The mount is BlueprintAuthorityOnly, so a client call would spawn an actor that
    // never mounts and then leak.
    if (!HasAuthority())
    {
        return false;
    }

    // Refuse rather than replace. Silently discarding a mounted weapon would lose whatever the
    // player had picked up, and a second grant is far more likely to be a double-fire than intent.
    if (WeaponMountComponent->GetMountedWeapon())
    {
        return false;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    // Deferred so the definition is in place before BeginPlay runs. AShipboardWeapon calls
    // RefreshFromDefinition there, so assigning first means the weapon configures itself exactly
    // as a placed one does -- the same idiom AShipThreatDirector uses for its archetypes. Setting
    // the definition after spawning would leave the weapon inert until something re-refreshed it.
    const FTransform SpawnTransform = GetActorTransform();
    AShipboardWeapon* Weapon = World->SpawnActorDeferred<AShipboardWeapon>(
        StartingWeaponClass, SpawnTransform, this, nullptr,
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Weapon)
    {
        return false;
    }

    if (StartingWeaponDefinition)
    {
        Weapon->Definition = StartingWeaponDefinition;
    }

    Weapon->FinishSpawning(SpawnTransform);

    if (!WeaponMountComponent->MountWeapon(Weapon))
    {
        // Do not leave an unmounted weapon lying at the player's feet as a side effect of a failed
        // grant; that reads as a bug to a player and is one.
        Weapon->Destroy();
        return false;
    }

    return true;
}

void ACoopSurvivalCharacter::HandlePrimaryWeaponFire()
{
    FirePrimaryWeapon();
}

void ACoopSurvivalCharacter::FirePrimaryWeapon()
{
    if (!WeaponMountComponent || !FirstPersonCamera || bIsDead)
    {
        return;
    }
    WeaponMountComponent->FireWeapon(FirstPersonCamera->GetComponentLocation(), FirstPersonCamera->GetForwardVector());
}

void ACoopSurvivalCharacter::ToggleUnsafeWeaponModification()
{
    if (!WeaponMountComponent || !WeaponMountComponent->GetMountedWeapon() || bIsDead)
    {
        return;
    }
    const bool bEnableUnsafe = !WeaponMountComponent->GetMountedWeapon()->bUnsafeModificationInstalled;
    WeaponMountComponent->SetUnsafeModificationInstalled(bEnableUnsafe);
}

bool ACoopSurvivalCharacter::TryAddTraversalMovementInput(const FVector& WorldDirection, float ScaleValue)
{
    if (FMath::IsNearlyZero(ScaleValue) || WorldDirection.IsNearlyZero())
    {
        return true;
    }

    if (!WeaponMountComponent || !WeaponMountComponent->GetMountedWeapon())
    {
        AddMovementInput(WorldDirection, ScaleValue);
        return true;
    }

    const FVector RequestedDirection = WorldDirection.GetSafeNormal() * FMath::Sign(ScaleValue);
    float ProbeDistance = WeaponClearanceProbeDistanceCm;
    if (const UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        ProbeDistance += FMath::Max(0.0f, FVector::DotProduct(Movement->Velocity, RequestedDirection))
            * GetWorld()->GetDeltaSeconds();
    }

    FHitResult BlockingHit;
    if (!WeaponMountComponent->CanMoveMountedWeapon(RequestedDirection, ProbeDistance, BlockingHit))
    {
        NotifyWeaponTraversalBlocked(BlockingHit);
        return false;
    }

    bWeaponTraversalBlocked = false;
    WeaponTraversalBlocker.Reset();
    AddMovementInput(WorldDirection, ScaleValue);
    return true;
}

void ACoopSurvivalCharacter::UpdateWeaponTraversalCollision(float DeltaTime)
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!Movement || !WeaponMountComponent || !WeaponMountComponent->GetMountedWeapon()
        || Movement->Velocity.IsNearlyZero())
    {
        return;
    }

    const float Speed = Movement->Velocity.Size();
    const float ProbeDistance = WeaponClearanceProbeDistanceCm
        + Speed * FMath::Max(DeltaTime, WeaponClearanceVelocityLookAheadSeconds);
    FHitResult BlockingHit;
    if (WeaponMountComponent->CanMoveMountedWeapon(Movement->Velocity, ProbeDistance, BlockingHit))
    {
        return;
    }

    const FVector BlockingNormal = BlockingHit.Normal.GetSafeNormal();
    const float IntoSurfaceSpeed = FVector::DotProduct(Movement->Velocity, BlockingNormal);
    if (!BlockingNormal.IsNearlyZero() && IntoSurfaceSpeed < 0.0f)
    {
        // Preserve tangential velocity so a floating player can slide the carried tool free.
        Movement->Velocity -= BlockingNormal * IntoSurfaceSpeed;
    }
    else
    {
        Movement->Velocity = FVector::ZeroVector;
    }
    NotifyWeaponTraversalBlocked(BlockingHit);
}

void ACoopSurvivalCharacter::NotifyWeaponTraversalBlocked(const FHitResult& BlockingHit)
{
    bWeaponTraversalBlocked = true;
    WeaponTraversalBlocker = BlockingHit.GetActor();

    const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
    LastWeaponTraversalBlockedTime = Now;
    if (Now - LastWeaponTraversalFeedbackTime < WeaponTraversalFeedbackCooldownSeconds)
    {
        return;
    }
    LastWeaponTraversalFeedbackTime = Now;
    ReceiveWeaponTraversalBlocked(BlockingHit.GetActor(),
        WeaponMountComponent ? WeaponMountComponent->GetMountedWeapon() : nullptr);
}

void ACoopSurvivalCharacter::OnRep_Health()
{
}

void ACoopSurvivalCharacter::OnRep_Oxygen()
{
}

void ACoopSurvivalCharacter::OnRep_Radiation()
{
}

void ACoopSurvivalCharacter::OnRep_SuitIntegrity()
{
    UpdateSuitConditionVisuals();
}

void ACoopSurvivalCharacter::OnRep_Stability()
{
}

void ACoopSurvivalCharacter::OnRep_Death()
{
    if (bIsDead)
    {
        ReleaseAllMagneticSystems();
    }
}

float ACoopSurvivalCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    const float AppliedDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    // See RespawnGraceSeconds: found by a walkthrough that died at the power station on a loop,
    // respawning on its own checkpoint a metre from the threat that killed it.
    if (GetWorld() && GetWorld()->GetTimeSeconds() - LastRespawnWorldSeconds < RespawnGraceSeconds)
    {
        return 0.0f;
    }
    if (!HasAuthority() || bIsDead || AppliedDamage <= 0.0f)
    {
        return AppliedDamage;
    }

    // An intact pressure suit softens impacts but never makes the wearer immune to combat.
    const float SuitMitigation = FMath::Lerp(1.0f, 0.55f, FMath::Clamp(SuitIntegrity, 0.0f, 1.0f));
    HealthPercent = FMath::Clamp(HealthPercent - AppliedDamage * SuitMitigation, 0.0f, 100.0f);
    OnRep_Health();
    if (HealthPercent <= 0.0f)
    {
        bIsDead = true;
        OnRep_Death();
    }
    return AppliedDamage;
}

void ACoopSurvivalCharacter::UpdateSurvival(float DeltaTime, const FPhysicsEnvironmentState& EnvironmentState, float InSuitIntegrity, float InStability)
{
    if (!HazardComponent || bIsDead)
    {
        return;
    }

    const float StatusOxygenMultiplier = StatusEffectComponent ? StatusEffectComponent->GetAdditionalOxygenDrainMultiplier() : 1.0f;

    // Skills are read live at point of use, never written into character properties on unlock.
    // Stateless cannot drift, cannot double-apply when a rank is bought mid-session, and needs no
    // matching teardown -- the previous design compounded every purchase against an empty removal.
    const float SkillOxygenMultiplier = SkillComponent
        ? SkillComponent->GetCostMultiplier(SkillEffects::OxygenConsumption)
        : 1.0f;
    OxygenLevelPercent = FMath::Clamp(OxygenLevelPercent - HazardComponent->BaseOxygenConsumptionPerSecond * OxygenDrainMultiplier * StatusOxygenMultiplier * SkillOxygenMultiplier * DeltaTime, 0.0f, 100.0f);
    // Equipment resistances are read live rather than cached on equip. Stateless means they cannot
    // drift out of sync with what is actually worn, and durability failure (which silently
    // unequips a slot in DegradeEquipment) takes effect immediately instead of leaving a stale
    // bonus applied.
    const FEquipmentStats EquipmentBonuses = EquipmentComponent
        ? EquipmentComponent->GetTotalBonuses()
        : FEquipmentStats();

    // Baseline shielding is the suit itself; RadiationResistance is a 0-100 percentage of the
    // remaining unshielded fraction. Capped below 1.0 so no loadout grants total immunity.
    const float BaseShielding = 0.5f;
    const float SkillShielding = SkillComponent ? SkillComponent->GetEffect(SkillEffects::RadiationShielding) : 0.0f;
    const float ResistanceFraction = FMath::Clamp(
        EquipmentBonuses.RadiationResistance / 100.0f + SkillShielding, 0.0f, 1.0f);
    const float ShieldingFactor = FMath::Min(BaseShielding + (1.0f - BaseShielding) * ResistanceFraction, 0.95f);
    RadiationDoseSv += HazardComponent->ComputeRadiationDoseSv(DeltaTime, EnvironmentState, ShieldingFactor);

    // SuitIntegrityBonus (0-50%) raises the integrity the pressure model sees, so a sealed loadout
    // resists decompression longer without inflating the displayed suit integrity itself.
    const float SkillSealBonus = SkillComponent ? SkillComponent->GetEffect(SkillEffects::SuitSealIntegrity) : 0.0f;
    const float IntegrityBonusFraction = FMath::Clamp(
        EquipmentBonuses.SuitIntegrityBonus / 100.0f + SkillSealBonus, 0.0f, 1.0f);
    const float EffectiveIntegrity = FMath::Clamp(InSuitIntegrity + IntegrityBonusFraction, 0.0f, 1.0f);
    SuitIntegrity = FMath::Clamp(SuitIntegrity - HazardComponent->ComputePressureFailure(DeltaTime, EnvironmentState, EffectiveIntegrity), 0.0f, 1.0f);

    // Training raises the stability the model sees rather than the displayed value, so a skilled
    // spacer resists tumbling without the HUD claiming they are steadier than they are.
    const float SkillStability = SkillComponent ? SkillComponent->GetEffect(SkillEffects::MicrogravityControl) : 0.0f;
    const float EffectiveStability = FMath::Clamp(InStability + SkillStability, 0.0f, 1.0f);
    Stability = FMath::Clamp(Stability - HazardComponent->ComputeMicrogravityInstability(DeltaTime, EnvironmentState, EffectiveStability), 0.0f, 1.0f);
    if (StatusEffectComponent && HasAuthority())
    {
        const float SuitProtection = FMath::Clamp(SuitIntegrity, 0.0f, 1.0f);
        const float SkillExposureMultiplier = SkillComponent
            ? SkillComponent->GetCostMultiplier(SkillEffects::ExposureResistance)
            : 1.0f;
        StatusEffectComponent->ApplyEnvironmentalExposure(EnvironmentState,
            FMath::Lerp(1.0f, 0.15f, SuitProtection) * SkillExposureMultiplier);
    }

    if (SuitIntegrity <= 0.0f)
    {
        ReleaseAllMagneticSystems();
    }

    if (OxygenLevelPercent <= 0.0f || RadiationDoseSv >= HazardComponent->RadiationDoseLimitSv)
    {
        bIsDead = true;
    }
}

void ACoopSurvivalCharacter::ApplyThrust(FVector Direction, float DeltaTime)
{
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        const float MobilityMultiplier = StatusEffectComponent ? StatusEffectComponent->GetMobilityMultiplier() : 1.0f;
        Movement->Velocity += Direction.GetSafeNormal() * ThrusterAcceleration * MobilityMultiplier * DeltaTime;
    }
}

void ACoopSurvivalCharacter::ClientApplyPsychosisGrounding_Implementation(float DurationSeconds, float TreatmentStrength)
{
    if (PsychosisComponent)
    {
        PsychosisComponent->ApplyGrounding(DurationSeconds, TreatmentStrength);
    }
}

void ACoopSurvivalCharacter::PushOffSurface()
{
    if (LastHitSurfaceNormal.IsNearlyZero())
    {
        return;
    }

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->Velocity += LastHitSurfaceNormal.GetSafeNormal() * PushOffImpulseStrength;
    }

    LastHitSurfaceNormal = FVector::ZeroVector;
}

void ACoopSurvivalCharacter::HandleActorHit(AActor* SelfActor, AActor* OtherActor, FVector NormalImpulse, const FHitResult& Hit)
{
    LastHitSurfaceNormal = Hit.ImpactNormal;
    if (!HasAuthority() || bIsDead || !StatusEffectComponent || !GetWorld()) return;

    const double Now = GetWorld()->GetTimeSeconds();
    if (Now - LastCollisionTraumaTime < CollisionTraumaCooldownSeconds) return;

    const float CharacterMass = GetCharacterMovement() ? FMath::Max(1.0f, GetCharacterMovement()->Mass) : 100.0f;
    const float ImpactSpeedEquivalent = NormalImpulse.Size() / CharacterMass;
    if (ImpactSpeedEquivalent < CollisionStressThreshold) return;

    LastCollisionTraumaTime = Now;
    const float SuitProtection = FMath::Lerp(1.0f, 0.55f, FMath::Clamp(SuitIntegrity, 0.0f, 1.0f));
    const float StressSeverity = FMath::Clamp((ImpactSpeedEquivalent - CollisionStressThreshold) / 900.0f, 0.15f, 1.0f) * SuitProtection;
    StatusEffectComponent->ApplyStatusEffect(EPlayerStatusEffect::AcuteStress, StressSeverity, 45.0f, EPlayerStatusSource::Trauma);

    if (ImpactSpeedEquivalent >= CollisionFractureThreshold)
    {
        const float Severity = FMath::Clamp((ImpactSpeedEquivalent - CollisionFractureThreshold) / 1000.0f, 0.2f, 1.0f) * SuitProtection;
        StatusEffectComponent->ApplyStatusEffect(EPlayerStatusEffect::Fracture, Severity, -1.0f, EPlayerStatusSource::Trauma);
        HealthPercent = FMath::Max(0.0f, HealthPercent - Severity * 12.0f);
    }
    if (ImpactSpeedEquivalent >= CollisionHemorrhageThreshold)
    {
        const float Severity = FMath::Clamp((ImpactSpeedEquivalent - CollisionHemorrhageThreshold) / 1200.0f, 0.2f, 1.0f) * SuitProtection;
        StatusEffectComponent->ApplyStatusEffect(EPlayerStatusEffect::Hemorrhage, Severity, -1.0f, EPlayerStatusSource::Trauma);
    }
}

void ACoopSurvivalCharacter::UpdateGravityAlignedCameraRoll(float DeltaTime)
{
    if (!CameraBoom)
    {
        return;
    }

    const AController* PlayerController = GetController();
    if (!PlayerController)
    {
        return;
    }

    const UCharacterMovementComponent* Movement = GetCharacterMovement();
    const FVector LocalUp = Movement ? -Movement->GetGravityDirection() : FVector::UpVector;

    const FRotator ControlRotation = PlayerController->GetControlRotation();
    const FVector ViewForward = ControlRotation.Vector();

    if (FMath::Abs(FVector::DotProduct(ViewForward, LocalUp)) > 0.98f)
    {
        // View direction is nearly parallel to the gravity-up reference: MakeFromXZ would
        // produce a degenerate basis, so hold last frame's roll instead of snapping/NaN-ing.
        return;
    }

    const FRotator DesiredRotation = FRotationMatrix::MakeFromXZ(ViewForward, LocalUp).Rotator();
    const FRotator NewRotation = FMath::RInterpTo(CameraBoom->GetComponentRotation(), DesiredRotation, DeltaTime, GravityRollInterpSpeed);

    CameraBoom->SetWorldRotation(NewRotation);
}

void ACoopSurvivalCharacter::ApplyAppearanceCosmetic(ECharacterAppearance Appearance)
{
    if (!GetMesh())
    {
        return;
    }

    // Material index 0 is the base character mesh
    UMaterialInstance* CosmeticMaterial = nullptr;

    switch (Appearance)
    {
        case ECharacterAppearance::Default:
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_Default")));
            break;
        case ECharacterAppearance::ArcticCamo:
            // Load arctic camo material - Arctic_Camo material
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_ArcticCamo")));
            break;
        case ECharacterAppearance::DeepSea:
            // Load deep sea material
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_DeepSea")));
            break;
        case ECharacterAppearance::Hazmat:
            // Load hazmat material
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_Hazmat")));
            break;
        case ECharacterAppearance::Veteran:
            // Load veteran material
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_Veteran")));
            break;
        case ECharacterAppearance::Specter:
            // Load specter material
            CosmeticMaterial = Cast<UMaterialInstance>(StaticLoadObject(UMaterialInstance::StaticClass(),
                nullptr, TEXT("/Game/Materials/Characters/MI_Specter")));
            break;
    }

    if (CosmeticMaterial)
    {
        GetMesh()->SetMaterial(0, CosmeticMaterial);
    }
}

void ACoopSurvivalCharacter::OnCharacterProfileChanged(const FCharacterProfile& NewProfile)
{
	ApplyCharacterIdentity(NewProfile);
    ApplyAppearanceCosmetic(NewProfile.AppearanceVariant);
    if (IsLocallyControlled())
    {
        SetPressureSuitRole(NewProfile.SuitRole);
        SetMetaHumanPreset(NewProfile.MetaHumanPresetId);
    }
}

void ACoopSurvivalCharacter::ApplyCharacterIdentity(const FCharacterProfile& Profile)
{
	if (!GetMesh()) return;

	// The fallback content set has two animation-compatible human bases. Face presets 01-03
	// use Manny and 04-12 use Quinn; assembled MetaHuman Blueprints replace this mapping
	// through ReceiveCharacterIdentityApplied without changing saved profiles.
	static TSoftObjectPtr<USkeletalMesh> MannyMesh(FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")));
	static TSoftObjectPtr<USkeletalMesh> QuinnMesh(FSoftObjectPath(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple")));
	const bool bUseQuinn = static_cast<uint8>(Profile.FacePreset) >= static_cast<uint8>(ECharacterFacePreset::Face04);
	if (USkeletalMesh* IdentityMesh = (bUseQuinn ? QuinnMesh : MannyMesh).LoadSynchronous())
	{
		if (GetMesh()->GetSkeletalMeshAsset() != IdentityMesh)
		{
			GetMesh()->SetSkeletalMeshAsset(IdentityMesh);
		}
	}

	// These are silhouette adjustments only: the collision capsule and movement metrics stay
	// identical across presets so character creation never changes gameplay reach or clearance.
	FVector BodyScale(1.0f);
	switch (Profile.BodyPreset)
	{
		case ECharacterBodyPreset::Light: BodyScale = FVector(0.98f, 0.92f, 0.98f); break;
		case ECharacterBodyPreset::Broad: BodyScale = FVector(1.01f, 1.07f, 1.01f); break;
		case ECharacterBodyPreset::Heavy: BodyScale = FVector(1.02f, 1.12f, 1.02f); break;
		case ECharacterBodyPreset::Average:
		default: break;
	}
	GetMesh()->SetRelativeScale3D(BodyScale);
	ApplyMetaHumanVisual(Profile.FacePreset, Profile.HairStyle);

	static const FLinearColor SkinTones[] = {
		FLinearColor(0.96f,0.78f,0.66f), FLinearColor(0.88f,0.66f,0.52f),
		FLinearColor(0.76f,0.52f,0.38f), FLinearColor(0.64f,0.42f,0.29f),
		FLinearColor(0.51f,0.31f,0.21f), FLinearColor(0.39f,0.22f,0.15f),
		FLinearColor(0.28f,0.15f,0.11f), FLinearColor(0.18f,0.09f,0.07f)
	};
	const int32 ToneIndex = FMath::Clamp(static_cast<int32>(Profile.SkinTone), 0, UE_ARRAY_COUNT(SkinTones)-1);
	for (int32 Slot = 0; Slot < GetMesh()->GetNumMaterials(); ++Slot)
	{
		if (UMaterialInterface* Base = GetMesh()->GetMaterial(Slot))
		{
			UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Base);
			if (!Dynamic)
			{
				Dynamic = UMaterialInstanceDynamic::Create(Base, this);
				GetMesh()->SetMaterial(Slot, Dynamic);
			}
			Dynamic->SetVectorParameterValue(TEXT("SkinTone"), SkinTones[ToneIndex]);
			Dynamic->SetScalarParameterValue(TEXT("FacePreset"), static_cast<float>(Profile.FacePreset));
			Dynamic->SetScalarParameterValue(TEXT("HairStyle"), static_cast<float>(Profile.HairStyle));
		}
	}

	ReceiveCharacterIdentityApplied(Profile);
}

UClass* ACoopSurvivalCharacter::ResolveMetaHumanVisualClass(ECharacterFacePreset FacePreset) const
{
    const int32 FaceNumber = static_cast<int32>(FacePreset) + 1;
    const FString AssetName = FString::Printf(TEXT("BP_PlayerFace%02d"), FaceNumber);
    const FString ClassPath = FString::Printf(
        TEXT("/Game/Characters/MetaHumans/Assembled/PlayerFace%02d/%s.%s_C"),
        FaceNumber, *AssetName, *AssetName);
    return FSoftClassPath(ClassPath).TryLoadClass<AActor>();
}

void ACoopSurvivalCharacter::ApplyMetaHumanVisual(ECharacterFacePreset FacePreset, ECharacterHairStyle HairStyle)
{
    if (!MetaHumanVisual || !GetMesh())
    {
        return;
    }

    UClass* VisualClass = ResolveMetaHumanVisualClass(FacePreset);
    if (!VisualClass)
    {
        MetaHumanVisual->SetChildActorClass(nullptr);
        if (CryoBodysuitMesh)
        {
            CryoBodysuitMesh->SetVisibility(false, true);
        }
        GetMesh()->SetVisibility(true, false);
        return;
    }

    if (MetaHumanVisual->GetChildActorClass() != VisualClass)
    {
        MetaHumanVisual->SetChildActorClass(VisualClass);
    }

    TetherChildActor(MetaHumanVisual);
    AActor* VisualActor = MetaHumanVisual->GetChildActor();
    if (!VisualActor)
    {
        if (CryoBodysuitMesh)
        {
            CryoBodysuitMesh->SetVisibility(false, true);
        }
        GetMesh()->SetVisibility(true, false);
        return;
    }

    TArray<USkeletalMeshComponent*> MeshComponents;
    VisualActor->GetComponents<USkeletalMeshComponent>(MeshComponents);
    USkeletalMeshComponent* MetaHumanBody = nullptr;
    USkeletalMeshComponent* MetaHumanOutfit = nullptr;
    for (USkeletalMeshComponent* Component : MeshComponents)
    {
        if (!Component)
        {
            continue;
        }
        if (Component->GetFName() == TEXT("Body"))
        {
            MetaHumanBody = Component;
        }
        else if (Component->GetFName() == TEXT("SkeletalMesh"))
        {
            MetaHumanOutfit = Component;
        }
    }

    if (!MetaHumanBody)
    {
        MetaHumanVisual->SetChildActorClass(nullptr);
        if (CryoBodysuitMesh)
        {
            CryoBodysuitMesh->SetVisibility(false, true);
        }
        GetMesh()->SetVisibility(true, false);
        return;
    }

    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    MetaHumanBody->SetAnimInstanceClass(UMetaHumanCopyPoseAnimInstance::StaticClass());
    MetaHumanBody->AddTickPrerequisiteComponent(GetMesh());
    MetaHumanBody->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    if (CryoBodysuitMesh && CryoBodysuitMesh->GetSkeletalMeshAsset())
    {
        CryoBodysuitMesh->SetLeaderPoseComponent(GetMesh());
        CryoBodysuitMesh->AddTickPrerequisiteComponent(GetMesh());
        CryoBodysuitMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        CryoBodysuitMesh->SetVisibility(true, true);
    }
    if (MetaHumanOutfit)
    {
        // Epic's assembled default garment is a loose T-shirt/shorts placeholder. Keep the
        // component available for a future fitted garment asset, but do not render it over
        // the dedicated cryo-bodysuit body surface.
        MetaHumanOutfit->SetLeaderPoseComponent(MetaHumanBody);
    }

    const bool bShowHair = HairStyle != ECharacterHairStyle::Shaved &&
        HairStyle != ECharacterHairStyle::Covered;
    MetaHumanVisual->SetVisibility(true, true);
    TArray<UPrimitiveComponent*> PrimitiveComponents;
    VisualActor->GetComponents<UPrimitiveComponent>(PrimitiveComponents);
    for (UPrimitiveComponent* Component : PrimitiveComponents)
    {
        if (Component && Component->GetFName() == TEXT("Hair"))
        {
            Component->SetVisibility(bShowHair, true);
        }
    }
    if (MetaHumanOutfit)
    {
        // Apply after the recursive parent visibility update above.
        MetaHumanOutfit->SetVisibility(false, true);
    }
    // The body remains the hidden animation bridge for the face; the authored V32 garment
    // provides the visible torso and limbs without a T-shirt-dependent body cutout.
    MetaHumanBody->SetVisibility(false, false);

    // Keep the driver alive for movement/animation, but never render it through the MetaHuman.
    GetMesh()->SetVisibility(false, false);
    UpdateFirstPersonHeadVisibility();
}

AActor* ACoopSurvivalCharacter::GetMetaHumanVisualActor() const
{
    return MetaHumanVisual ? MetaHumanVisual->GetChildActor() : nullptr;
}

void ACoopSurvivalCharacter::SetCharacterCreatorPreviewMode(bool bEnabled)
{
    bCharacterCreatorPreviewMode = bEnabled;
    UpdateFirstPersonHeadVisibility();
    if (!bEnabled)
    {
        ApplyPressureSuitVisuals();
        RefreshEquipmentVisuals();
        return;
    }

    if (PrimaryOversuitMesh)
    {
        PrimaryOversuitMesh->SetVisibility(false, true);
    }
    for (UStaticMeshComponent* Part : PressureSuitParts)
    {
        if (Part) Part->SetVisibility(false, true);
    }
    for (UStaticMeshComponent* Part : WearableEquipmentParts)
    {
        if (Part) Part->SetVisibility(false, true);
    }
    for (UPointLightComponent* Light : {LeftBootMagnetLight.Get(), RightBootMagnetLight.Get(),
        LeftGloveMagnetLight.Get(), RightGloveMagnetLight.Get()})
    {
        if (Light) Light->SetVisibility(false);
    }
}

bool ACoopSurvivalCharacter::IsMetalSurface(const FHitResult& Hit) const
{
    const UPrimitiveComponent* Component = Hit.GetComponent();
    const AActor* Actor = Hit.GetActor();
    // Authored props can opt in explicitly. World-static ship geometry is metal by default,
    // which keeps every deck, bulkhead and overhead usable without hand-tagging a whole map.
    return (Component && (Component->ComponentHasTag(TEXT("Metal")) || Component->ComponentHasTag(TEXT("Metallic")) ||
        Component->GetCollisionObjectType() == ECC_WorldStatic)) ||
        (Actor && (Actor->ActorHasTag(TEXT("Metal")) || Actor->ActorHasTag(TEXT("Metallic"))));
}

bool ACoopSurvivalCharacter::FindMetalSurface(const FVector& Start, const FVector& Direction, float Distance, FHitResult& OutHit) const
{
    FCollisionQueryParams Params(SCENE_QUERY_STAT(MagneticSuitTrace), false, this);
    // Look through dynamic occluders to the ship itself. Pickups block the visibility channel so
    // the interaction focus trace can find them, and their 95 cm interaction spheres sit under this
    // trace whenever a player stands near one -- the boots then read "not metal" and refuse to
    // engage, or release mid-stride. Found on the first frame of the demo, with a tool placed at
    // the player's feet. Physics props keep blocking, so a tagged metal crate still counts.
    FCollisionResponseParams Responses(ECR_Block);
    Responses.CollisionResponse.SetResponse(ECC_WorldDynamic, ECR_Ignore);
    if (!GetWorld() || !GetWorld()->LineTraceSingleByChannel(OutHit, Start,
        Start + Direction.GetSafeNormal() * Distance, ECC_Visibility, Params, Responses))
    {
        return false;
    }
    return IsMetalSurface(OutHit);
}

void ACoopSurvivalCharacter::UpdateFloatPose()
{
    // Adrift: flying with no boots on the deck and no activity in hand. Lyra's fall loop at a
    // third speed reads as a body hanging in the air; it stops the moment the boots take hold.
    UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
    const UCharacterMovementComponent* Movement = GetCharacterMovement();
    const bool bAdrift = Anim && Movement && Movement->MovementMode == MOVE_Flying && !bMagneticBootsEnabled && !bIsDead
        && !(PlayerActivityComponent && PlayerActivityComponent->IsActivityActive());
    if (bAdrift && !bFloatPosePlaying)
    {
        if (!FloatLoop)
        {
            FloatLoop = LoadObject<UAnimSequenceBase>(nullptr, TEXT("/Game/Characters/Mannequins/Anims/Lyra/Jump/MM_Unarmed_Jump_Fall_Loop.MM_Unarmed_Jump_Fall_Loop"));
        }
        if (FloatLoop)
        {
            Anim->PlaySlotAnimationAsDynamicMontage(FloatLoop, TEXT("DefaultSlot"), 0.5f, 0.5f, 0.3f, 10000, -1.0f, 0.0f);
            bFloatPosePlaying = true;
        }
    }
    else if (!bAdrift && bFloatPosePlaying)
    {
        Anim->StopSlotAnimation(0.4f, TEXT("DefaultSlot"));
        bFloatPosePlaying = false;
        // The tool's hold pose was on the same slot; put it back if a tool is in hand.
        if (WeaponMountComponent && WeaponMountComponent->GetMountedWeapon()) { HandleMountedWeaponChanged(WeaponMountComponent->GetMountedWeapon()); }
    }
}

void ACoopSurvivalCharacter::PlayGesture(const TCHAR* ClipPath, float Rate)
{
    UAnimInstance* Anim = GetMesh() ? GetMesh()->GetAnimInstance() : nullptr;
    UAnimSequenceBase* Clip = ClipPath ? LoadObject<UAnimSequenceBase>(nullptr, ClipPath) : nullptr;
    if (!Anim || !Clip || (PlayerActivityComponent && PlayerActivityComponent->IsActivityActive())) return;
    Anim->PlaySlotAnimationAsDynamicMontage(Clip, TEXT("DefaultSlot"), 0.2f, 0.25f, Rate, 1, -1.0f, 0.0f);
    // The tool's hold rides the same slot; the gesture ends and the hold is put back.
    if (WeaponMountComponent && WeaponMountComponent->GetMountedWeapon())
    {
        FTimerHandle Handle;
        const float Seconds = Clip->GetPlayLength() / FMath::Max(Rate, 0.01f);
        GetWorldTimerManager().SetTimer(Handle, [this]() { if (WeaponMountComponent && WeaponMountComponent->GetMountedWeapon()) HandleMountedWeaponChanged(WeaponMountComponent->GetMountedWeapon()); }, Seconds + 0.2f, false);
    }
}

void ACoopSurvivalCharacter::ToggleWristLamp()
{
    SetWristLampOn(!bWristLampOn);
}

void ACoopSurvivalCharacter::SetWristLampOn(bool bOn)
{
    // The lamp is in the suit's sleeve: nothing to switch on in a cryo bodysuit.
    if (bOn && !bPressureOversuitEquipped) return;
    bWristLampOn = bOn;
    UpdateWristLampVisuals();
    if (!HasAuthority()) ServerSetWristLamp(bOn);
}

void ACoopSurvivalCharacter::ServerSetWristLamp_Implementation(bool bOn)
{
    bWristLampOn = bOn && bPressureOversuitEquipped;
    UpdateWristLampVisuals();
}

void ACoopSurvivalCharacter::OnRep_WristLamp()
{
    UpdateWristLampVisuals();
}

void ACoopSurvivalCharacter::UpdateWristLampVisuals()
{
    const bool bLit = bWristLampOn && bPressureOversuitEquipped;
    if (WristLamp) WristLamp->SetVisibility(bLit);
    // The housing shows whenever the suit is on; the lens only with the lamp lit.
    if (WristLampHousing) WristLampHousing->SetVisibility(bPressureOversuitEquipped);
    if (WristLampLens) WristLampLens->SetVisibility(bLit);
}

void ACoopSurvivalCharacter::ToggleMagneticBoots()
{
    SetMagneticBootsEnabled(!bMagneticBootsEnabled);
}

void ACoopSurvivalCharacter::SetMagneticBootsEnabled(bool bEnabled)
{
    if (bEnabled && (bIsDead || SuitIntegrity <= 0.0f)) return;
    // The boots are part of the pressure suit: nothing to switch on in a cryo bodysuit.
    if (bEnabled && !bPressureOversuitEquipped) return;
    if (bEnabled)
    {
        FHitResult Hit;
        if (!FindMetalSurface(GetActorLocation(), -GetActorUpVector(), MagneticBootTraceDistance, Hit))
        {
            return;
        }
        MagneticSurfaceNormal = Hit.ImpactNormal.GetSafeNormal();
    }
    bMagneticBootsEnabled = bEnabled;
    if (!bEnabled)
    {
        if (UCharacterMovementComponent* Movement = GetCharacterMovement())
        {
            Movement->GravityScale = 0.0f;
            Movement->SetMovementMode(MOVE_Flying);
        }
        // Under drive the deck is still down: the ship's gravity takes the character back next tick.
        if (UZeroGGravityComponent* ShipGravity = FindComponentByClass<UZeroGGravityComponent>())
        {
            ShipGravity->Reassert();
        }
    }
    UpdateMagneticSuitVisuals();
    if (USoundBase* Sound = bEnabled ? MagnetEngageSound.Get() : MagnetReleaseSound.Get())
    {
        UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation());
    }
    if (bEnabled)
    {
        if (APlayerController* PC = Cast<APlayerController>(GetController()))
        {
            PC->PlayDynamicForceFeedback(0.22f, 0.12f, true, true, true, true, EDynamicForceFeedbackAction::Start);
        }
    }
    if (!HasAuthority()) ServerSetMagneticBootsEnabled(bEnabled);
}

void ACoopSurvivalCharacter::ServerSetMagneticBootsEnabled_Implementation(bool bEnabled)
{
    if (bEnabled)
    {
        FHitResult Hit;
        bEnabled = FindMetalSurface(GetActorLocation(), -GetActorUpVector(), MagneticBootTraceDistance, Hit);
        if (bEnabled) MagneticSurfaceNormal = Hit.ImpactNormal.GetSafeNormal();
    }
    bMagneticBootsEnabled = bEnabled && !bIsDead;
    UpdateMagneticSuitVisuals();
}

void ACoopSurvivalCharacter::BeginMagneticGloveGrip()
{
    BeginGloveGrip(EMagneticGloveHand::Left);
}

void ACoopSurvivalCharacter::EndMagneticGloveGrip()
{
    EndGloveGrip(EMagneticGloveHand::Left);
}

void ACoopSurvivalCharacter::BeginRightMagneticGloveGrip()
{
    BeginGloveGrip(EMagneticGloveHand::Right);
}

void ACoopSurvivalCharacter::EndRightMagneticGloveGrip()
{
    EndGloveGrip(EMagneticGloveHand::Right);
}

void ACoopSurvivalCharacter::BeginGloveGrip(EMagneticGloveHand Hand)
{
    if (bIsDead) return;
    const UCameraComponent* ViewCamera = bFirstPersonView ? FirstPersonCamera.Get() : ThirdPersonCamera;
    const FVector Start = ViewCamera ? ViewCamera->GetComponentLocation() : GetActorLocation();
    const FVector Forward = ViewCamera ? ViewCamera->GetForwardVector() : GetActorForwardVector();
    FHitResult Hit;
    if (FindMetalSurface(Start, Forward, MagneticGloveReach, Hit))
    {
        const bool bLeft = Hand == EMagneticGloveHand::Left;
        if (bLeft)
        {
            bLeftMagneticGloveActive = true;
            GloveGripLocation = Hit.ImpactPoint;
            GloveGripComponent = Hit.GetComponent();
        }
        else
        {
            bRightMagneticGloveActive = true;
            RightGloveGripLocation = Hit.ImpactPoint;
            RightGloveGripComponent = Hit.GetComponent();
        }
        bMagneticGlovesActive = bLeftMagneticGloveActive || bRightMagneticGloveActive;
        UpdateMagneticSuitVisuals();
        if (MagnetEngageSound) UGameplayStatics::PlaySoundAtLocation(this, MagnetEngageSound, Hit.ImpactPoint);
        if (APlayerController* PC = Cast<APlayerController>(GetController()))
        {
            PC->PlayDynamicForceFeedback(0.16f, 0.08f, true, true, true, true, EDynamicForceFeedbackAction::Start);
        }
        if (!HasAuthority()) ServerRequestGloveGrip(Hand, Hit.GetComponent(), Hit.ImpactPoint);
    }
}

void ACoopSurvivalCharacter::EndGloveGrip(EMagneticGloveHand Hand)
{
    if (Hand == EMagneticGloveHand::Left)
    {
        bLeftMagneticGloveActive = false;
        GloveGripComponent.Reset();
    }
    else
    {
        bRightMagneticGloveActive = false;
        RightGloveGripComponent.Reset();
    }
    bMagneticGlovesActive = bLeftMagneticGloveActive || bRightMagneticGloveActive;
    UpdateMagneticSuitVisuals();
    if (MagnetReleaseSound) UGameplayStatics::PlaySoundAtLocation(this, MagnetReleaseSound, GetActorLocation());
    if (!HasAuthority()) ServerReleaseGloveGrip(Hand);
}

void ACoopSurvivalCharacter::ServerRequestGloveGrip_Implementation(EMagneticGloveHand Hand, UPrimitiveComponent* TargetComponent, FVector_NetQuantize TargetLocation)
{
    if (bIsDead || !IsValid(TargetComponent) || FVector::DistSquared(GetActorLocation(), TargetLocation) > FMath::Square(MagneticGloveReach * 1.25f)) return;
    const bool bMetal = TargetComponent->ComponentHasTag(TEXT("Metal")) || TargetComponent->ComponentHasTag(TEXT("Metallic")) ||
        TargetComponent->GetCollisionObjectType() == ECC_WorldStatic ||
        (TargetComponent->GetOwner() && (TargetComponent->GetOwner()->ActorHasTag(TEXT("Metal")) || TargetComponent->GetOwner()->ActorHasTag(TEXT("Metallic"))));
    if (!bMetal) return;
    if (Hand == EMagneticGloveHand::Left)
    {
        bLeftMagneticGloveActive = true; GloveGripComponent = TargetComponent; GloveGripLocation = TargetLocation;
    }
    else
    {
        bRightMagneticGloveActive = true; RightGloveGripComponent = TargetComponent; RightGloveGripLocation = TargetLocation;
    }
    bMagneticGlovesActive = true;
    UpdateMagneticSuitVisuals();
}

void ACoopSurvivalCharacter::ServerReleaseGloveGrip_Implementation(EMagneticGloveHand Hand)
{
    EndGloveGrip(Hand);
}

void ACoopSurvivalCharacter::ThrowMagneticObject()
{
    const UCameraComponent* ViewCamera = bFirstPersonView ? FirstPersonCamera.Get() : ThirdPersonCamera;
    const FVector Direction = ViewCamera ? ViewCamera->GetForwardVector() : GetActorForwardVector();
    const EMagneticGloveHand Hand = bRightMagneticGloveActive ? EMagneticGloveHand::Right : EMagneticGloveHand::Left;
    if (!HasAuthority()) ServerThrowMagneticObject(Hand, Direction);
    else ServerThrowMagneticObject_Implementation(Hand, Direction);
}

void ACoopSurvivalCharacter::ServerThrowMagneticObject_Implementation(EMagneticGloveHand Hand, FVector_NetQuantizeNormal ThrowDirection)
{
    TWeakObjectPtr<UPrimitiveComponent>& Grip = Hand == EMagneticGloveHand::Left ? GloveGripComponent : RightGloveGripComponent;
    if (Grip.IsValid() && Grip->IsSimulatingPhysics())
    {
        UPrimitiveComponent* Thrown = Grip.Get();
        Thrown->AddImpulse(ThrowDirection.GetSafeNormal() * MagneticObjectThrowImpulse, NAME_None, true);

        // Listen for where it lands so the throw becomes a distraction rather than just a shove.
        // Hit events are usually off for ordinary physics props, so enable them explicitly.
        if (ThrownObjectImpactLoudness > 0.0f && !TrackedThrownComponents.Contains(Thrown))
        {
            Thrown->SetNotifyRigidBodyCollision(true);
            Thrown->OnComponentHit.AddDynamic(this, &ACoopSurvivalCharacter::HandleThrownObjectImpact);
            TrackedThrownComponents.Add(Thrown);
        }
    }
    EndGloveGrip(Hand);
}

void ACoopSurvivalCharacter::HandleThrownObjectImpact(UPrimitiveComponent* HitComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComponent, FVector NormalImpulse, const FHitResult& Hit)
{
    if (!HasAuthority() || !HitComponent)
    {
        return;
    }

    // One noise per throw. A tumbling object would otherwise fire on every bounce, and the
    // landing point is the readable signal an investigating AI should act on.
    HitComponent->OnComponentHit.RemoveDynamic(this, &ACoopSurvivalCharacter::HandleThrownObjectImpact);
    TrackedThrownComponents.RemoveAll([HitComponent](const TWeakObjectPtr<UPrimitiveComponent>& Tracked)
    {
        return !Tracked.IsValid() || Tracked.Get() == HitComponent;
    });

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UNoisePerceptionSubsystem* Perception = World->GetSubsystem<UNoisePerceptionSubsystem>();
    if (!Perception)
    {
        return;
    }

    // Scale by impact speed so a gentle nudge is not as loud as a hard throw.
    const float ImpactSpeed = HitComponent->GetComponentVelocity().Size();
    const float Scale = FMath::Clamp(ImpactSpeed / FMath::Max(ThrownObjectLoudImpactSpeed, 1.0f), 0.0f, 1.0f);
    const float Loudness = ThrownObjectImpactLoudness * Scale;
    if (Loudness <= 0.0f)
    {
        return;
    }

    // Reported at the impact point and attributed to the object rather than the thrower: the
    // whole point of a distraction is that the AI investigates the noise, not the player who
    // caused it. Attributing it to the player would let hostility/self-ignore rules discard it.
    AActor* NoiseInstigator = HitComponent->GetOwner();
    Perception->ReportNoise(Hit.ImpactPoint, Loudness, ENoiseCategory::Impact,
        NoiseInstigator ? NoiseInstigator : HitComponent->GetOwner());
}

void ACoopSurvivalCharacter::BeginRotationThruster()
{
    if (bIsDead || bThrusterFuelLockedOut || ThrusterFuelPercent <= 0.0f) return;
    const UCameraComponent* ViewCamera = bFirstPersonView ? FirstPersonCamera.Get() : ThirdPersonCamera;
    const FVector Start = ViewCamera ? ViewCamera->GetComponentLocation() : GetActorLocation();
    const FVector Forward = ViewCamera ? ViewCamera->GetForwardVector() : GetActorForwardVector();
    FHitResult Hit;
    if (FindMetalSurface(Start, Forward, MagneticBootTraceDistance * 4.0f, Hit))
    {
        MagneticSurfaceNormal = Hit.ImpactNormal.GetSafeNormal();
        bRotationThrusterActive = true;
        if (!HasAuthority()) ServerSetRotationThruster(true, MagneticSurfaceNormal);
        if (ThrusterLoopSound) UGameplayStatics::PlaySoundAtLocation(this, ThrusterLoopSound, GetActorLocation());
        if (ThrusterParticle) UGameplayStatics::SpawnEmitterAttached(ThrusterParticle, GetMesh(), TEXT("spine_03"), FVector(-20, 0, 0), FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true);
    }
}

void ACoopSurvivalCharacter::EndRotationThruster()
{
    bRotationThrusterActive = false;
    if (!HasAuthority()) ServerSetRotationThruster(false, MagneticSurfaceNormal);
}

void ACoopSurvivalCharacter::ServerSetRotationThruster_Implementation(bool bActive, FVector_NetQuantizeNormal SurfaceNormal)
{
    bRotationThrusterActive = bActive && !bIsDead && ThrusterFuelPercent > 0.0f;
    if (bRotationThrusterActive) MagneticSurfaceNormal = SurfaceNormal.GetSafeNormal();
}

void ACoopSurvivalCharacter::UpdateMagneticSuit(float DeltaTime)
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!Movement) return;

    if (bRotationThrusterActive && !MagneticSurfaceNormal.IsNearlyZero() && ThrusterFuelPercent > 0.0f)
    {
        const FQuat Delta = FQuat::FindBetweenNormals(-GetActorUpVector(), -MagneticSurfaceNormal);
        const FQuat Target = Delta * GetActorQuat();
        const float Alpha = FMath::Clamp(FMath::DegreesToRadians(RotationThrusterDegreesPerSecond) * DeltaTime, 0.0f, 1.0f);
        SetActorRotation(FQuat::Slerp(GetActorQuat(), Target, Alpha));
        // Propellant discipline reduces what a burn costs; it never enlarges the tank, so the
        // ceiling on sustained thrust is unchanged.
        const float SkillPropellantMultiplier = SkillComponent
            ? SkillComponent->GetCostMultiplier(SkillEffects::ThrusterEfficiency)
            : 1.0f;
        ThrusterFuelPercent = FMath::Max(0.0f, ThrusterFuelPercent - ThrusterFuelDrainPerSecond * SkillPropellantMultiplier * DeltaTime);
        if (ThrusterFuelPercent <= 0.0f)
        {
            bThrusterFuelLockedOut = true;
            EndRotationThruster();
        }
    }
    else
    {
        ThrusterFuelPercent = FMath::Min(100.0f, ThrusterFuelPercent + ThrusterFuelRechargePerSecond * DeltaTime);
        if (ThrusterFuelPercent >= ThrusterRestartFuelPercent) bThrusterFuelLockedOut = false;
    }

    if (IsLocallyControlled())
    {
        const UCameraComponent* ViewCamera = bFirstPersonView ? FirstPersonCamera.Get() : ThirdPersonCamera;
        FHitResult TargetHit;
        bHasValidMagneticTarget = ViewCamera && FindMetalSurface(ViewCamera->GetComponentLocation(), ViewCamera->GetForwardVector(), MagneticGloveReach, TargetHit);
    }

    if (bMagneticBootsEnabled)
    {
        FHitResult Hit;
        bool bFoundSurface = FindMetalSurface(GetActorLocation(), -GetActorUpVector(), MagneticBootTraceDistance, Hit);
        if (!bFoundSurface)
        {
            const FVector CornerDirection = (GetActorForwardVector() - GetActorUpVector() * 0.65f).GetSafeNormal();
            bFoundSurface = FindMetalSurface(GetActorLocation(), CornerDirection, MagneticBootTraceDistance * 1.35f, Hit);
        }
        if (bFoundSurface)
        {
            const FVector TargetNormal = Hit.ImpactNormal.GetSafeNormal();
            MagneticSurfaceNormal = MagneticSurfaceNormal.IsNearlyZero() ? TargetNormal :
                FMath::VInterpTo(MagneticSurfaceNormal, TargetNormal, DeltaTime, MagneticSurfaceAlignSpeed).GetSafeNormal();
            Movement->SetGravityDirection(-MagneticSurfaceNormal);
            Movement->GravityScale = 1.0f;
            if (Movement->MovementMode != MOVE_Walking) Movement->SetMovementMode(MOVE_Walking);
        }
        else
        {
            SetMagneticBootsEnabled(false);
        }
    }

    UpdateGloveGrip(EMagneticGloveHand::Left, DeltaTime);
    UpdateGloveGrip(EMagneticGloveHand::Right, DeltaTime);
}

void ACoopSurvivalCharacter::UpdateGloveGrip(EMagneticGloveHand Hand, float DeltaTime)
{
    const bool bActive = Hand == EMagneticGloveHand::Left ? bLeftMagneticGloveActive : bRightMagneticGloveActive;
    TWeakObjectPtr<UPrimitiveComponent>& Grip = Hand == EMagneticGloveHand::Left ? GloveGripComponent : RightGloveGripComponent;
    const FVector GripLocation = Hand == EMagneticGloveHand::Left ? GloveGripLocation : RightGloveGripLocation;
    if (!bActive) return;
    if (!Grip.IsValid()) { EndGloveGrip(Hand); return; }

    const FVector PullDirection = (GripLocation - GetActorLocation()).GetSafeNormal();
    if (Grip->IsSimulatingPhysics())
    {
        if (HasAuthority()) Grip->AddForceAtLocation(-PullDirection * MagneticObjectPullForce, GripLocation);
    }
    else if (IsLocallyControlled())
    {
        GetCharacterMovement()->Velocity += PullDirection * MagneticGlovePullAcceleration * DeltaTime;
    }
}

bool ACoopSurvivalCharacter::UseBestSupply()
{
    if (!HasAuthority())
    {
        ServerUseBestSupply();
        return true;
    }
    if (!InventoryComponent) return false;
    for (const FInventoryStack& Stack : InventoryComponent->GetStacks())
    {
        if (Stack.Item && InventoryComponent->CanUseItem(Stack.Item))
        {
            return InventoryComponent->UseItem(Stack.Item);
        }
    }
    return false;
}

void ACoopSurvivalCharacter::ServerUseBestSupply_Implementation()
{
    UseBestSupply();
}

void ACoopSurvivalCharacter::ReleaseAllMagneticSystems()
{
    bRotationThrusterActive = false;
    bMagneticBootsEnabled = false;
    bLeftMagneticGloveActive = false;
    bRightMagneticGloveActive = false;
    bMagneticGlovesActive = false;
    GloveGripComponent.Reset();
    RightGloveGripComponent.Reset();
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->GravityScale = 0.0f;
        Movement->SetMovementMode(MOVE_Flying);
    }
    // A respawn releases everything, and under drive gravity that left the crew floating for the
    // rest of the session (found by the survey walk): the ship's gravity is applied again next tick.
    if (UZeroGGravityComponent* ShipGravity = FindComponentByClass<UZeroGGravityComponent>())
    {
        ShipGravity->Reassert();
    }
    UpdateMagneticSuitVisuals();
}

void ACoopSurvivalCharacter::OnRep_MagneticSuitState()
{
    UpdateMagneticSuitVisuals();
}

void ACoopSurvivalCharacter::UpdateMagneticSuitVisuals()
{
    if (LeftBootMagnetLight) LeftBootMagnetLight->SetVisibility(bMagneticBootsEnabled);
    if (RightBootMagnetLight) RightBootMagnetLight->SetVisibility(bMagneticBootsEnabled);
    if (LeftGloveMagnetLight) LeftGloveMagnetLight->SetVisibility(bLeftMagneticGloveActive);
    if (RightGloveMagnetLight) RightGloveMagnetLight->SetVisibility(bRightMagneticGloveActive);

    for (UStaticMeshComponent* Part : PressureSuitParts)
    {
        if (!Part) continue;
        const FName Name = Part->GetFName();
        const bool bBoot = Name == TEXT("LeftBootShell") || Name == TEXT("RightBootShell");
        const bool bGlove = Name == TEXT("LeftGlove") || Name == TEXT("RightGlove");
        if (bBoot || bGlove)
        {
            if (UMaterialInstanceDynamic* Material = Cast<UMaterialInstanceDynamic>(Part->GetMaterial(0)))
            {
                const bool bLeftGlove = Name == TEXT("LeftGlove");
                const bool bActive = bBoot ? bMagneticBootsEnabled : (bLeftGlove ? bLeftMagneticGloveActive : bRightMagneticGloveActive);
                Material->SetVectorParameterValue(TEXT("MagnetGlowColor"), FLinearColor(1.0f, 0.025f, 0.01f));
                Material->SetScalarParameterValue(TEXT("MagnetGlowStrength"), bActive ? (bBoot ? 8.0f : 4.0f) : 0.0f);
            }
        }
    }
}

void ACoopSurvivalCharacter::SetFirstPersonView(bool bEnableFirstPerson)
{
    if (!IsLocallyControlled()) return;
    bFirstPersonView = bEnableFirstPerson;
    FirstPersonCamera->SetActive(bFirstPersonView);
    ThirdPersonCamera->SetActive(!bFirstPersonView);
    // The tool's mount depends on the view: re-seat it.
    if (WeaponMountComponent && WeaponMountComponent->GetMountedWeapon()) { HandleMountedWeaponChanged(WeaponMountComponent->GetMountedWeapon()); }
    GetMesh()->SetOwnerNoSee(false);
    UpdateFirstPersonHeadVisibility();

    for (UStaticMeshComponent* Part : PressureSuitParts)
    {
        if (!Part) continue;
        const FName Name = Part->GetFName();
        const bool bHideInFirstPerson = Name == TEXT("HelmetShell") || Name == TEXT("HelmetVisor") ||
            Name == TEXT("PressureCollar") || Name == TEXT("LifeSupportPack");
        Part->SetOwnerNoSee(bFirstPersonView && bHideInFirstPerson);
    }
}

void ACoopSurvivalCharacter::UpdateFirstPersonHeadVisibility()
{
    // Both assembled-head paths can exist. Hide only head surfaces from their owner,
    // retaining body visibility, animation, and the view seen by other players.
    const bool bHideFromOwner = bFirstPersonView && !bCharacterCreatorPreviewMode;

    // The oversuit carries its own head, helmet and visor, and the first-person camera sits
    // inside them: without this the owner looks out through the back of their own face. A
    // skeletal mesh cannot owner-hide a section, so on the locally controlled character the head
    // sections are switched off in first person and back on in third; a remote copy of this
    // character is not locally controlled and keeps its helmet.
    if (PrimaryOversuitMesh && PrimaryOversuitMesh->GetSkeletalMeshAsset() && IsLocallyControlled())
    {
        static const TSet<FName> HeadSlots = { TEXT("Head"), TEXT("Eyelash"), TEXT("Tongue"), TEXT("Upper_Teeth"), TEXT("Lower_Teeth"),
            TEXT("HeadCap"), TEXT("SM_Helm"), TEXT("MS_Visor"), TEXT("Helmet"), TEXT("Visor") };
        // The whole suit, not only its head: looking down at a floor console put the collar and
        // shoulders across the bottom of the frame (the survey walk's "own body in view"). First
        // person is the view from inside the visor; the suit is what everyone else sees.
        PrimaryOversuitMesh->SetOwnerNoSee(bHideFromOwner);
        USkeletalMesh* Oversuit = PrimaryOversuitMesh->GetSkeletalMeshAsset();
        const TArray<FSkeletalMaterial>& Materials = Oversuit->GetMaterials();
        if (const FSkeletalMeshRenderData* Render = Oversuit->GetResourceForRendering())
        {
            for (int32 LOD = 0; LOD < Render->LODRenderData.Num(); ++LOD)
            {
                const FSkeletalMeshLODRenderData& LODData = Render->LODRenderData[LOD];
                for (int32 Section = 0; Section < LODData.RenderSections.Num(); ++Section)
                {
                    const int32 MaterialIndex = LODData.RenderSections[Section].MaterialIndex;
                    if (!Materials.IsValidIndex(MaterialIndex)) continue;
                    if (HeadSlots.Contains(Materials[MaterialIndex].MaterialSlotName))
                    {
                        PrimaryOversuitMesh->ShowMaterialSection(MaterialIndex, Section, !bHideFromOwner, LOD);
                    }
                }
            }
        }
    }
    for (UChildActorComponent* HeadSource : {MetaHumanActorComponent.Get(), MetaHumanVisual.Get()})
    {
        AActor* HeadActor = HeadSource ? HeadSource->GetChildActor() : nullptr;
        if (!HeadActor) continue;
        // Child actors default to no owner. Attachment alone does not make OwnerNoSee work.
        // Also repair existing Blueprint component defaults that predate this constructor.
        HeadActor->SetOwner(this);
        TArray<UPrimitiveComponent*> Components;
        HeadActor->GetComponents<UPrimitiveComponent>(Components);
        for (UPrimitiveComponent* Component : Components)
        {
            if (!Component) continue;
            const FName Name = Component->GetFName();
            // The assembled body ("SkeletalMesh" / "Body") is hidden too: the oversuit is what the
            // owner sees of themselves, and the body's copied pose leaves its arms where the
            // first-person camera shows a gloved hand hanging in the top-left of the view.
            if (Name == TEXT("Face") || Name == TEXT("Hair") || Name == TEXT("Eyebrows") ||
                Name == TEXT("Fuzz") || Name == TEXT("Eyelashes") || Name == TEXT("Mustache") ||
                Name == TEXT("Beard") || Name == TEXT("SkeletalMesh") || Name == TEXT("Body"))
            {
                Component->SetOwnerNoSee(bHideFromOwner);
            }
        }
    }
}

void ACoopSurvivalCharacter::ValidateSuitAttachmentBones() const
{
    if (!GetMesh() || !GetMesh()->GetSkeletalMeshAsset()) return;
    static const FName RequiredBones[] = {
        TEXT("head"), TEXT("neck_01"), TEXT("spine_03"), TEXT("upperarm_l"), TEXT("upperarm_r"),
        TEXT("lowerarm_l"), TEXT("hand_l"), TEXT("hand_r"), TEXT("thigh_l"), TEXT("thigh_r"),
        TEXT("calf_l"), TEXT("calf_r"), TEXT("foot_l"), TEXT("foot_r")
    };
    for (const FName BoneName : RequiredBones)
    {
        if (GetMesh()->GetBoneIndex(BoneName) == INDEX_NONE)
        {
            UE_LOG(LogTemp, Error, TEXT("Pressure suit attachment bone missing from player rig: %s"), *BoneName.ToString());
        }
    }
}

void ACoopSurvivalCharacter::RespawnFromCheckpoint()
{
    bool bRestoredCheckpoint = false;
    if (UGameInstance* GameInstance = GetGameInstance())
    {
        if (UShipCheckpointSubsystem* Checkpoints = GameInstance->GetSubsystem<UShipCheckpointSubsystem>())
        {
            bRestoredCheckpoint = Checkpoints->RestoreCheckpoint(GetWorld(), this);
        }
    }
    if (!bRestoredCheckpoint)
    {
        SetActorTransform(InitialSpawnTransform, false, nullptr, ETeleportType::TeleportPhysics);
    }

    OxygenLevelPercent = 100.0f;
    HealthPercent = 100.0f;
    RadiationDoseSv = 0.0f;
    SuitIntegrity = FMath::Max(SuitIntegrity, 0.5f);
    Stability = FMath::Max(Stability, 0.5f);
    ThrusterFuelPercent = 100.0f;
    bThrusterFuelLockedOut = false;
    ReleaseAllMagneticSystems();
    LastRespawnWorldSeconds = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    if (StatusEffectComponent)
    {
        StatusEffectComponent->ClearAllStatusEffects();
    }
    TimeSinceDeath = 0.0f;
    bIsDead = false;
    OnRep_Death();
}

void ACoopSurvivalCharacter::SetPressureSuitRole(EPressureSuitRole NewRole)
{
    PressureSuitRole = NewRole;
    ApplyPressureSuitVisuals();
    if (!HasAuthority())
    {
        ServerSetPressureSuitRole(NewRole);
    }
}

void ACoopSurvivalCharacter::ServerSetPressureSuitRole_Implementation(EPressureSuitRole NewRole)
{
    PressureSuitRole = NewRole;
    ApplyPressureSuitVisuals();
}

void ACoopSurvivalCharacter::OnRep_PressureSuitRole()
{
    ApplyPressureSuitVisuals();
}

float ACoopSurvivalCharacter::RepairSuitIntegrity(float Fraction)
{
    if (HasAuthority() && Fraction > 0.0f)
    {
        SuitIntegrity = FMath::Clamp(SuitIntegrity + Fraction, 0.0f, 1.0f);
        OnRep_SuitIntegrity();
    }
    return SuitIntegrity;
}

void ACoopSurvivalCharacter::SetPressureOversuitEquipped(bool bEquipped)
{
    bPressureOversuitEquipped = bEquipped;
    ApplyPressureSuitVisuals();
    UpdateWristLampVisuals();
    if (!HasAuthority())
    {
        ServerSetPressureOversuitEquipped(bEquipped);
    }
}

void ACoopSurvivalCharacter::ServerSetPressureOversuitEquipped_Implementation(bool bEquipped)
{
    bPressureOversuitEquipped = bEquipped;
    ApplyPressureSuitVisuals();
    UpdateWristLampVisuals();
}

void ACoopSurvivalCharacter::OnRep_PressureOversuitEquipped()
{
    ApplyPressureSuitVisuals();
    UpdateWristLampVisuals();
}

void ACoopSurvivalCharacter::SetMetaHumanCharacterClass(TSubclassOf<AActor> NewCharacterClass)
{
    if (!IsAllowedMetaHumanClass(NewCharacterClass))
    {
        UE_LOG(LogTemp, Warning, TEXT("Rejected character class outside the assembled MetaHuman library: %s"),
            NewCharacterClass ? *NewCharacterClass->GetPathName() : TEXT("None"));
        return;
    }
    if (MetaHumanCharacterClass == NewCharacterClass)
    {
        ConfigureCharacterModelLayers();
        return;
    }
    MetaHumanCharacterClass = NewCharacterClass;
    OnRep_MetaHumanCharacterClass();
    if (!HasAuthority())
    {
        ServerSetMetaHumanCharacterClass(NewCharacterClass);
    }
}

bool ACoopSurvivalCharacter::SetMetaHumanPreset(FName PresetId)
{
    const FString Preset = PresetId.ToString();
    if (!Preset.StartsWith(TEXT("PlayerFace")) || Preset.Len() > 32)
    {
        return false;
    }
    for (const TCHAR Character : Preset)
    {
        if (!FChar::IsAlnum(Character) && Character != TEXT('_'))
        {
            return false;
        }
    }

    const FString ClassPath = FString::Printf(
        TEXT("/Game/Characters/MetaHumans/Assembled/%s/BP_%s.BP_%s_C"), *Preset, *Preset, *Preset);
    if (UClass* PresetClass = LoadClass<AActor>(nullptr, *ClassPath))
    {
        SetMetaHumanCharacterClass(PresetClass);
        return true;
    }
    return false;
}

void ACoopSurvivalCharacter::ServerSetMetaHumanCharacterClass_Implementation(TSubclassOf<AActor> NewCharacterClass)
{
    if (!IsAllowedMetaHumanClass(NewCharacterClass))
    {
        return;
    }
    MetaHumanCharacterClass = NewCharacterClass;
    OnRep_MetaHumanCharacterClass();
}

bool ACoopSurvivalCharacter::IsAllowedMetaHumanClass(TSubclassOf<AActor> CandidateClass) const
{
    return CandidateClass
        && CandidateClass->GetPathName().StartsWith(TEXT("/Game/Characters/MetaHumans/Assembled/"));
}

void ACoopSurvivalCharacter::OnRep_MetaHumanCharacterClass()
{
    if (!MetaHumanActorComponent)
    {
        return;
    }

    MetaHumanActorComponent->SetChildActorClass(MetaHumanCharacterClass);
    ConfigureCharacterModelLayers();
}

void ACoopSurvivalCharacter::ConfigureCharacterModelLayers()
{
    if (!MetaHumanCharacterClass)
    {
        MetaHumanCharacterClass = LoadClass<AActor>(nullptr,
            TEXT("/Game/Characters/MetaHumans/Assembled/PlayerFace01/BP_PlayerFace01.BP_PlayerFace01_C"));
        if (MetaHumanActorComponent && MetaHumanCharacterClass)
        {
            MetaHumanActorComponent->SetChildActorClass(MetaHumanCharacterClass);
        }
    }

    TetherChildActor(MetaHumanActorComponent);
    TetherChildActor(MetaHumanVisual);
    AActor* MetaHumanActor = MetaHumanActorComponent ? MetaHumanActorComponent->GetChildActor() : nullptr;
    UpdateFirstPersonHeadVisibility();
    if (!MetaHumanActor || !CryoBodysuitMesh || !CryoBodysuitMesh->GetSkeletalMeshAsset())
    {
        GetMesh()->SetHiddenInGame(false, false);
        if (CryoBodysuitMesh)
        {
            CryoBodysuitMesh->SetHiddenInGame(true, false);
        }
        return;
    }

    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    GetMesh()->SetHiddenInGame(true, false);
    // V32's preserved source geometry is malformed. Keep it available for source recovery, but use
    // the body-profile-specific V34 garment in the assembled MetaHuman clothing slot at runtime.
    CryoBodysuitMesh->SetHiddenInGame(true, false);

    TArray<USkeletalMeshComponent*> MetaHumanMeshes;
    MetaHumanActor->GetComponents<USkeletalMeshComponent>(MetaHumanMeshes);
    USkeletalMeshComponent* MetaHumanBodyDriver = nullptr;
    for (USkeletalMeshComponent* Component : MetaHumanMeshes)
    {
        if (Component && Component->GetName().Equals(TEXT("Body"), ESearchCase::IgnoreCase))
        {
            MetaHumanBodyDriver = Component;
            Component->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
            Component->SetLeaderPoseComponent(GetMesh());
            Component->SetHiddenInGame(true, false);
            break;
        }
    }

    USkeletalMesh* FittedCryoBodysuit = nullptr;
    if (MetaHumanCharacterClass && MetaHumanCharacterClass->GetPathName().Contains(TEXT("PlayerFace01")))
    {
        FittedCryoBodysuit = LoadObject<USkeletalMesh>(nullptr,
            TEXT("/Game/Characters/Player/Undersuit/CryoBodysuitV34/SK_CryoBodysuit_V34_Face01.SK_CryoBodysuit_V34_Face01"));
    }

    for (USkeletalMeshComponent* Component : MetaHumanMeshes)
    {
        if (!Component)
        {
            continue;
        }

        const FString LayerName = Component->GetName();
        const USkeletalMesh* LayerMesh = Component->GetSkeletalMeshAsset();
        const FString LayerMeshPath = LayerMesh ? LayerMesh->GetPathName() : FString();
        const bool bBodyDriver = LayerName.Equals(TEXT("Body"), ESearchCase::IgnoreCase);
        const bool bGarmentSlot = LayerName.Equals(TEXT("SkeletalMesh"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Torso"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Legs"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Feet"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Shoes"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Top"), ESearchCase::IgnoreCase)
            || LayerName.Contains(TEXT("Bottom"), ESearchCase::IgnoreCase)
            || LayerMeshPath.Contains(TEXT("/Clothing/"), ESearchCase::IgnoreCase)
            || LayerMeshPath.Contains(TEXT("Outfit"), ESearchCase::IgnoreCase)
            || LayerMeshPath.Contains(TEXT("/CryoBodysuitV34/"), ESearchCase::IgnoreCase);

        if (bBodyDriver)
        {
            Component->SetHiddenInGame(true, false);
        }
        else if (bGarmentSlot)
        {
            if (FittedCryoBodysuit && MetaHumanBodyDriver)
            {
                Component->SetSkeletalMesh(FittedCryoBodysuit);
                Component->SetLeaderPoseComponent(MetaHumanBodyDriver);
                // Under a worn oversuit the garment stays hidden (see SetUndersuitGarmentHidden).
                const bool bOversuitWorn = bPressureOversuitEquipped;
                Component->SetHiddenInGame(bOversuitWorn, false);
            }
            else
            {
                Component->SetHiddenInGame(true, false);
            }
        }
        else
        {
            Component->SetHiddenInGame(false, false);
        }
    }
}

void ACoopSurvivalCharacter::SetUndersuitGarmentHidden(bool bHideGarment)
{
    AActor* MetaHumanActor = MetaHumanActorComponent ? MetaHumanActorComponent->GetChildActor() : nullptr;
    if (!MetaHumanActor)
    {
        return;
    }
    TArray<USkeletalMeshComponent*> MetaHumanMeshes;
    MetaHumanActor->GetComponents<USkeletalMeshComponent>(MetaHumanMeshes);
    for (USkeletalMeshComponent* Component : MetaHumanMeshes)
    {
        if (!Component) continue;
        const USkeletalMesh* LayerMesh = Component->GetSkeletalMeshAsset();
        const FString LayerMeshPath = LayerMesh ? LayerMesh->GetPathName() : FString();
        const bool bGarment = Component->GetName().Equals(TEXT("SkeletalMesh"), ESearchCase::IgnoreCase)
            || LayerMeshPath.Contains(TEXT("/CryoBodysuitV34/"), ESearchCase::IgnoreCase)
            || LayerMeshPath.Contains(TEXT("/Clothing/"), ESearchCase::IgnoreCase);
        if (bGarment)
        {
            Component->SetHiddenInGame(bHideGarment, false);
        }
    }
}

void ACoopSurvivalCharacter::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (MetaHumanActorComponent && MetaHumanCharacterClass
        && MetaHumanActorComponent->GetChildActorClass() != MetaHumanCharacterClass)
    {
        MetaHumanActorComponent->SetChildActorClass(MetaHumanCharacterClass);
    }
    ConfigureCharacterModelLayers();
    ApplyPressureSuitVisuals();
}

void ACoopSurvivalCharacter::ApplyPressureSuitVisuals()
{
    if (bCharacterCreatorPreviewMode)
    {
        if (PrimaryOversuitMesh) PrimaryOversuitMesh->SetVisibility(false, true);
        for (UStaticMeshComponent* Part : PressureSuitParts)
        {
            if (Part) Part->SetVisibility(false, true);
        }
        return;
    }

    static const TMap<FName, FString> MeshPaths = {
        { TEXT("HelmetShell"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_HelmetShell.SM_Suit_HelmetShell") },
        { TEXT("HelmetVisor"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Visor.SM_Suit_Visor") },
        { TEXT("PressureCollar"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_PressureCollar.SM_Suit_PressureCollar") },
        { TEXT("ChestPlate"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ChestPlate.SM_Suit_ChestPlate") },
        { TEXT("LifeSupportPack"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_LifeSupportPack.SM_Suit_LifeSupportPack") },
        { TEXT("LeftShoulder"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ShoulderPad.SM_Suit_ShoulderPad") },
        { TEXT("RightShoulder"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ShoulderPad.SM_Suit_ShoulderPad") },
        { TEXT("LeftForearmComputer"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ForearmComputer.SM_Suit_ForearmComputer") },
        { TEXT("LeftKneePad"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_KneePad.SM_Suit_KneePad") },
        { TEXT("RightKneePad"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_KneePad.SM_Suit_KneePad") },
        { TEXT("LeftBootShell"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_BootShell.SM_Suit_BootShell") },
        { TEXT("RightBootShell"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_BootShell.SM_Suit_BootShell") },
        { TEXT("LeftGlove"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Glove.SM_Suit_Glove") },
        { TEXT("RightGlove"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Glove.SM_Suit_Glove") },
        { TEXT("LeftThighPouch"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ThighPouch.SM_Suit_ThighPouch") },
        { TEXT("RightThighPouch"), TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_ThighPouch.SM_Suit_ThighPouch") }
    };

    const TCHAR* RoleMaterialPath = TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Crew.MI_Suit_Crew");
    const TCHAR* RoleModulePath = TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Crew.SM_Suit_Module_Crew");
    FLinearColor RoleColor(0.05f, 0.28f, 0.80f, 1.0f);
    float RoleModuleScale = 1.0f;
    float RoleModuleEmission = 0.25f;
    float RigidColorStrength = 0.42f;
    switch (PressureSuitRole)
    {
        case EPressureSuitRole::Engineering:
            RoleMaterialPath = TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Engineering.MI_Suit_Engineering");
            RoleModulePath = TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Engineering.SM_Suit_Module_Engineering");
            RoleColor = FLinearColor(0.95f, 0.30f, 0.025f, 1.0f);
            RoleModuleScale = 1.12f; RoleModuleEmission = 0.45f; RigidColorStrength = 0.50f; break;
        case EPressureSuitRole::Medical:
            RoleMaterialPath = TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Medical.MI_Suit_Medical");
            RoleModulePath = TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Medical.SM_Suit_Module_Medical");
            RoleColor = FLinearColor(0.04f, 0.72f, 0.52f, 1.0f);
            RoleModuleScale = 1.05f; RoleModuleEmission = 0.35f; RigidColorStrength = 0.40f; break;
        case EPressureSuitRole::Security:
            RoleMaterialPath = TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Security.MI_Suit_Security");
            RoleModulePath = TEXT("/Game/Characters/Player/Suit/Meshes/SM_Suit_Module_Security.SM_Suit_Module_Security");
            RoleColor = FLinearColor(0.78f, 0.035f, 0.025f, 1.0f);
            RoleModuleScale = 1.18f; RoleModuleEmission = 0.55f; RigidColorStrength = 0.58f; break;
        default: break;
    }

    UMaterialInterface* RoleMaterial = LoadObject<UMaterialInterface>(nullptr, RoleMaterialPath);
    UMaterialInterface* VisorMaterial = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/Characters/Player/Suit/Materials/MI_Suit_Visor.MI_Suit_Visor"));

    PressureSuitDynamicMaterials.Reset();

    USkeletalMesh* DesiredPrimaryOversuit = ResolvePrimaryOversuitMesh();
    // The oversuit is worn only once it is equipped at the rack: the crew wake in the bodysuit.
    const bool bHasPrimaryOversuit = DesiredPrimaryOversuit != nullptr && bPressureOversuitEquipped;
    if (PrimaryOversuitMesh)
    {
        PrimaryOversuitMesh->SetSkeletalMesh(DesiredPrimaryOversuit);
        PrimaryOversuitMesh->SetVisibility(bHasPrimaryOversuit, true);
        PrimaryOversuitMesh->SetLeaderPoseComponent(GetMesh());

        if (bHasPrimaryOversuit)
        {
            // Every call here made a new dynamic instance of whatever the slot held, so after
            // three calls the slot held a MID of a MID of a MID and the renderer drew the default
            // grey in its place: the crew wore a white plaster suit. Instance the asset's own
            // material each time instead.
            const TArray<FSkeletalMaterial>& AssetMaterials = DesiredPrimaryOversuit->GetMaterials();
            const int32 OversuitMaterialCount = PrimaryOversuitMesh->GetNumMaterials();
            for (int32 Slot = 0; Slot < OversuitMaterialCount; ++Slot)
            {
                UMaterialInterface* BaseMaterial = AssetMaterials.IsValidIndex(Slot) ? AssetMaterials[Slot].MaterialInterface.Get() : PrimaryOversuitMesh->GetMaterial(Slot);
                while (UMaterialInstanceDynamic* AsDynamic = Cast<UMaterialInstanceDynamic>(BaseMaterial))
                {
                    BaseMaterial = AsDynamic->Parent;
                }
                if (BaseMaterial)
                {
                    UMaterialInstanceDynamic* DynamicMaterial =
                        UMaterialInstanceDynamic::Create(BaseMaterial, this);
                    DynamicMaterial->SetVectorParameterValue(TEXT("SuitColor"), RoleColor);
                    DynamicMaterial->SetScalarParameterValue(TEXT("RoleColorStrength"), 0.22f);
                    PrimaryOversuitMesh->SetMaterial(Slot, DynamicMaterial);
                    PressureSuitDynamicMaterials.Add(DynamicMaterial);
                }
            }
        }
    }

    if (RoleMaterial && GetMesh())
    {
        const int32 MaterialSlotCount = FMath::Max(1, GetMesh()->GetNumMaterials());
        for (int32 Slot = 0; Slot < MaterialSlotCount; ++Slot)
        {
            UMaterialInstanceDynamic* BodyMaterial = UMaterialInstanceDynamic::Create(RoleMaterial, this);
            BodyMaterial->SetVectorParameterValue(TEXT("SuitColor"), RoleColor);
            BodyMaterial->SetScalarParameterValue(TEXT("RoleColorStrength"), 0.22f);
            GetMesh()->SetMaterial(Slot, BodyMaterial);
            PressureSuitDynamicMaterials.Add(BodyMaterial);
        }
    }
    // The undersuit garment on the assembled MetaHuman is worn under the oversuit, and drawn over
    // it wherever it is the larger of the two: with the Space Marshal on, the crew read as a white
    // plaster figure (the garment's default white cloth) with the Marshal's silhouette. Hide it
    // while an oversuit is worn.
    SetUndersuitGarmentHidden(bPressureOversuitEquipped || bHasPrimaryOversuit);

    for (UStaticMeshComponent* Part : PressureSuitParts)
    {
        if (!Part)
        {
            continue;
        }

        // The primitives and early modular pieces are a development fallback only. A complete
        // primary oversuit (either the swappable role mesh or the equipped pressure oversuit)
        // owns the silhouette and must never be visually layered with them.
        const bool bOversuitVisible = bHasPrimaryOversuit;
        // Unsuited, no parts at all: the bodysuit shows. Suited without the role mesh, the fallback.
        Part->SetVisibility(bPressureOversuitEquipped && !bOversuitVisible, true);
        if (bOversuitVisible || !bPressureOversuitEquipped)
        {
            continue;
        }

        const FString DynamicModulePath = RoleModulePath;
        const FString* Path = Part->GetFName() == TEXT("ChestControlUnit") ? &DynamicModulePath : MeshPaths.Find(Part->GetFName());
        if (Path)
        {
            if (UStaticMesh* SuitMesh = LoadObject<UStaticMesh>(nullptr, **Path))
            {
                Part->SetStaticMesh(SuitMesh);
                Part->SetRelativeScale3D(FVector::OneVector);
                const FName PartName = Part->GetFName();
                if (PartName == TEXT("HelmetShell"))
                {
                    Part->SetRelativeLocation(FVector(2.0f, 0.0f, 2.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                }
                else if (PartName == TEXT("HelmetVisor"))
                {
                    Part->SetRelativeLocation(FVector(2.0f, 0.0f, 1.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                }
                else if (PartName == TEXT("PressureCollar"))
                {
                    Part->SetRelativeLocation(FVector(0.0f, 0.0f, -2.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.94f));
                }
                else if (PartName == TEXT("ChestPlate"))
                {
                    Part->SetRelativeLocation(FVector(23.0f, 0.0f, 3.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                }
                else if (PartName == TEXT("LifeSupportPack"))
                {
                    Part->SetRelativeLocation(FVector(-19.0f, 0.0f, 3.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(1.02f));
                }
                else if (PartName == TEXT("ChestControlUnit"))
                {
                    Part->SetRelativeLocation(FVector(29.0f, 0.0f, 8.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(RoleModuleScale));
                }
                else if (PartName == TEXT("LeftShoulder") || PartName == TEXT("RightShoulder"))
                {
                    Part->SetRelativeLocation(FVector(1.0f, 0.0f, 0.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.64f));
                }
                else if (PartName == TEXT("LeftKneePad") || PartName == TEXT("RightKneePad"))
                {
                    Part->SetRelativeLocation(FVector(7.0f, 0.0f, 0.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.74f));
                }
                else if (PartName == TEXT("LeftBootShell") || PartName == TEXT("RightBootShell"))
                {
                    Part->SetRelativeLocation(FVector(5.0f, 0.0f, 1.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.88f));
                }
                else if (PartName == TEXT("LeftForearmComputer"))
                {
                    Part->SetRelativeLocation(FVector(11.0f, 0.0f, 4.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.82f));
                }
                else if (PartName == TEXT("LeftThighPouch"))
                {
                    Part->SetRelativeLocation(FVector(0.0f, 13.0f, -2.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.78f));
                }
                else if (PartName == TEXT("RightThighPouch"))
                {
                    Part->SetRelativeLocation(FVector(0.0f, -13.0f, -2.0f));
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.78f));
                }
                else if (PartName == TEXT("LeftGlove") || PartName == TEXT("RightGlove"))
                {
                    Part->SetRelativeLocation(FVector::ZeroVector);
                    Part->SetRelativeRotation(FRotator::ZeroRotator);
                    Part->SetRelativeScale3D(FVector(0.92f));
                }
            }
        }

        if (Part->GetFName() == TEXT("HelmetVisor"))
        {
            UMaterialInstanceDynamic* DynamicVisor = UMaterialInstanceDynamic::Create(VisorMaterial, this);
            DynamicVisor->SetVectorParameterValue(TEXT("SuitColor"),
                FLinearColor(0.004f, 0.01f, 0.016f, 1.0f) + RoleColor * 0.025f);
            Part->SetCastShadow(false);
            Part->SetMaterial(0, DynamicVisor);
        }
        else if (RoleMaterial)
        {
            UMaterialInstanceDynamic* DynamicMaterial = UMaterialInstanceDynamic::Create(RoleMaterial, this);
            DynamicMaterial->SetVectorParameterValue(TEXT("SuitColor"), RoleColor);
            const FName PartName = Part->GetFName();
            const bool bRigidAccent = PartName != TEXT("HelmetVisor");
            DynamicMaterial->SetScalarParameterValue(TEXT("RoleColorStrength"), bRigidAccent ? RigidColorStrength : 0.22f);
            DynamicMaterial->SetScalarParameterValue(TEXT("RoleEmissionStrength"),
                PartName == TEXT("ChestControlUnit") ? RoleModuleEmission : 0.0f);
            Part->SetMaterial(0, DynamicMaterial);
            PressureSuitDynamicMaterials.Add(DynamicMaterial);
        }
    }
    UpdateSuitConditionVisuals();
    UpdateMagneticSuitVisuals();
}

USkeletalMesh* ACoopSurvivalCharacter::ResolvePrimaryOversuitMesh() const
{
    const TSoftObjectPtr<USkeletalMesh>* SelectedMesh = &CrewPrimaryOversuit;
    switch (PressureSuitRole)
    {
        case EPressureSuitRole::Engineering:
            SelectedMesh = &EngineeringPrimaryOversuit;
            break;
        case EPressureSuitRole::Medical:
            SelectedMesh = &MedicalPrimaryOversuit;
            break;
        case EPressureSuitRole::Security:
            SelectedMesh = &SecurityPrimaryOversuit;
            break;
        default:
            break;
    }

    return SelectedMesh->IsNull() ? nullptr : SelectedMesh->LoadSynchronous();
}

void ACoopSurvivalCharacter::UpdateSuitConditionVisuals()
{
    const float DamageAmount = 1.0f - FMath::Clamp(SuitIntegrity, 0.0f, 1.0f);
    // Venting below sixty percent, and visibly worse as it falls: the crew can see the leak they
    // are losing air through, and where to patch.
    if (SuitLeak)
    {
        const bool bVent = bPressureOversuitEquipped && !bIsDead && SuitIntegrity < 0.6f;
        if (bVent != bSuitLeakVenting)
        {
            if (bVent) SuitLeak->Activate(true); else SuitLeak->Deactivate();
            bSuitLeakVenting = bVent;
        }
        if (bVent)
        {
            const float Scale = FMath::Lerp(0.08f, 0.3f, FMath::Clamp((0.6f - SuitIntegrity) / 0.6f, 0.0f, 1.0f));
            SuitLeak->SetRelativeScale3D(FVector(Scale));
        }
    }
    const float GrimeAmount = FMath::Clamp(DamageAmount * 0.65f + RadiationDoseSv * 0.025f, 0.0f, 1.0f);
    float BloomAmount = 0.0f;
    if (PathogenLoadComponent && PathogenLoadComponent->SubstrateQuality > 0.0f)
    {
        BloomAmount = FMath::Clamp(PathogenLoadComponent->PathogenLoad / PathogenLoadComponent->SubstrateQuality, 0.0f, 1.0f);
    }
    for (UMaterialInstanceDynamic* Material : PressureSuitDynamicMaterials)
    {
        if (!Material) continue;
        Material->SetScalarParameterValue(TEXT("DamageAmount"), DamageAmount);
        Material->SetScalarParameterValue(TEXT("GrimeAmount"), GrimeAmount);
        Material->SetScalarParameterValue(TEXT("BloomAmount"), BloomAmount);
    }
}
