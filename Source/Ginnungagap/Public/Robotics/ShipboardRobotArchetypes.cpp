#include "Robotics/ShipboardRobotArchetypes.h"

#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/DamageType.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"

namespace
{
    const TCHAR* JackRoot = TEXT("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/");
    const TCHAR* RobotMaterialRoot = TEXT("/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/");

    UStaticMesh* LoadStaticMesh(const FString& AssetPath)
    {
        return LoadObject<UStaticMesh>(nullptr, *AssetPath);
    }

    UStaticMesh* LoadJackPart(const TCHAR* AssetName)
    {
        const FString Path = FString(JackRoot) + AssetName + TEXT(".") + AssetName;
        return LoadStaticMesh(Path);
    }

    UStaticMesh* LoadFabPart(const TCHAR* RelativePath, const TCHAR* AssetName)
    {
        const FString Path = FString(TEXT("/Game/Modular_Scifi_Mechanic_Base/"))
            + RelativePath + TEXT("/") + AssetName + TEXT(".") + AssetName;
        return LoadStaticMesh(Path);
    }

    UMaterialInterface* LoadRobotMaterial(const TCHAR* AssetName)
    {
        const FString Path = FString(RobotMaterialRoot) + AssetName + TEXT(".") + AssetName;
        return LoadObject<UMaterialInterface>(nullptr, *Path);
    }

    UStaticMeshComponent* CreateRobotPart(
        AActor* Owner,
        const FName Name,
        USceneComponent* Parent,
        UStaticMesh* Mesh,
        UMaterialInterface* MaterialOverride = nullptr)
    {
        UStaticMeshComponent* Component = Owner->CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Component->SetupAttachment(Parent);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetStaticMesh(Mesh);
        if (MaterialOverride)
        {
            for (int32 MaterialIndex = 0; MaterialIndex < 4; ++MaterialIndex)
            {
                Component->SetMaterial(MaterialIndex, MaterialOverride);
            }
        }
        return Component;
    }
}

AShipboardRobotBase::AShipboardRobotBase()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;

    AssemblyRoot = CreateDefaultSubobject<USceneComponent>(TEXT("AssemblyRoot"));
    RootComponent = AssemblyRoot;

    CollisionBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("CollisionBounds"));
    CollisionBounds->SetupAttachment(AssemblyRoot);
    CollisionBounds->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    CollisionBounds->SetGenerateOverlapEvents(true);
    CollisionBounds->SetCanEverAffectNavigation(true);

    StatusLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("StatusLight"));
    StatusLight->SetupAttachment(AssemblyRoot);
    StatusLight->SetRelativeLocation(FVector(35.0f, 0.0f, 100.0f));
    StatusLight->SetAttenuationRadius(180.0f);
    StatusLight->SetIntensity(65.0f);
    StatusLight->SetLightColor(FLinearColor(0.12f, 0.72f, 1.0f));
    StatusLight->SetCastShadows(false);
}

void AShipboardRobotBase::BeginPlay()
{
    Super::BeginPlay();
    CurrentIntegrity = FMath::Clamp(CurrentIntegrity, 0.0f, MaxIntegrity);
    BatteryCharge = FMath::Clamp(BatteryCharge, 0.0f, 1.0f);
    RefreshRobotState();
}

void AShipboardRobotBase::SetOperational(const bool bNewOperational)
{
    if (bOperational == bNewOperational)
    {
        return;
    }

    bOperational = bNewOperational
        && !bBloomCorrupted
        && CurrentIntegrity > 0.0f
        && BatteryCharge > 0.0f;
    if (!bOperational)
    {
        bWorking = false;
    }
    ReceiveOperationalStateChanged(bOperational);
    RefreshRobotState();
}

void AShipboardRobotBase::SetWorking(const bool bNewWorking)
{
    const bool bCanWork = bOperational && !bBloomCorrupted
        && CurrentIntegrity > 0.0f && BatteryCharge > 0.0f;
    const bool bResolvedWorking = bNewWorking && bCanWork;
    if (bWorking == bResolvedWorking)
    {
        return;
    }

    bWorking = bResolvedWorking;
    RefreshRobotState();
}

float AShipboardRobotBase::ApplyRobotDamage(const float DamageAmount)
{
    const float AppliedDamage = FMath::Min(FMath::Max(DamageAmount, 0.0f), CurrentIntegrity);
    if (AppliedDamage <= 0.0f)
    {
        return 0.0f;
    }

    CurrentIntegrity -= AppliedDamage;
    if (CurrentIntegrity <= 0.0f)
    {
        CurrentIntegrity = 0.0f;
        bOperational = false;
        bWorking = false;
    }
    OnRep_Resources();
    RefreshRobotState();
    return AppliedDamage;
}

float AShipboardRobotBase::RepairRobot(const float RepairAmount, const bool bReactivate)
{
    const float AppliedRepair = FMath::Min(FMath::Max(RepairAmount, 0.0f), MaxIntegrity - CurrentIntegrity);
    if (AppliedRepair > 0.0f)
    {
        CurrentIntegrity += AppliedRepair;
        OnRep_Resources();
    }
    if (bReactivate && !bBloomCorrupted && CurrentIntegrity > 0.0f && BatteryCharge > 0.0f)
    {
        SetOperational(true);
    }
    else
    {
        RefreshRobotState();
    }
    return AppliedRepair;
}

float AShipboardRobotBase::ConsumePower(const float RequestedCharge)
{
    const float ConsumedCharge = FMath::Min(FMath::Max(RequestedCharge, 0.0f), BatteryCharge);
    if (ConsumedCharge <= 0.0f)
    {
        return 0.0f;
    }

    BatteryCharge -= ConsumedCharge;
    if (BatteryCharge <= KINDA_SMALL_NUMBER)
    {
        BatteryCharge = 0.0f;
        bOperational = false;
        bWorking = false;
    }
    OnRep_Resources();
    RefreshRobotState();
    return ConsumedCharge;
}

float AShipboardRobotBase::RechargeRobot(const float ChargeAmount, const bool bReactivate)
{
    const float AppliedCharge = FMath::Min(FMath::Max(ChargeAmount, 0.0f), 1.0f - BatteryCharge);
    if (AppliedCharge > 0.0f)
    {
        BatteryCharge += AppliedCharge;
        OnRep_Resources();
    }
    if (bReactivate && !bBloomCorrupted && CurrentIntegrity > 0.0f && BatteryCharge > 0.0f)
    {
        SetOperational(true);
    }
    else
    {
        RefreshRobotState();
    }
    return AppliedCharge;
}

float AShipboardRobotBase::AdvanceWork(const float WorkUnits)
{
    if (!CanPerformWork() || WorkUnits <= 0.0f)
    {
        return 0.0f;
    }

    const float RequestedDrain = WorkUnits * FMath::Max(Capabilities.PowerDrainPerWorkUnit, 0.0f);
    const float AvailableUnits = RequestedDrain > 0.0f
        ? WorkUnits * FMath::Min(1.0f, BatteryCharge / RequestedDrain)
        : WorkUnits;
    ConsumePower(AvailableUnits * Capabilities.PowerDrainPerWorkUnit);
    return AvailableUnits * FMath::Max(Capabilities.WorkRate, 0.0f);
}

bool AShipboardRobotBase::CanPerformWork() const
{
    return RobotState == EShipboardRobotState::Working
        && bOperational && !bBloomCorrupted
        && CurrentIntegrity > 0.0f && BatteryCharge > 0.0f;
}

float AShipboardRobotBase::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);
    return ApplyRobotDamage(DamageAmount);
}

void AShipboardRobotBase::OnInteract_Implementation(APawn* InstigatorPawn)
{
    if (!InstigatorPawn || bBloomCorrupted)
    {
        return;
    }

    if (RobotState == EShipboardRobotState::Standby)
    {
        SetWorking(true);
    }
    else if (RobotState == EShipboardRobotState::Working)
    {
        SetWorking(false);
    }
    else if (RobotState == EShipboardRobotState::Disabled
        && CurrentIntegrity > 0.0f && BatteryCharge > 0.0f)
    {
        SetOperational(true);
    }
}

void AShipboardRobotBase::OnBloomCorruption_Implementation()
{
    if (bBloomCorrupted)
    {
        return;
    }

    bWasWorkingBeforeCorruption = bWorking;
    bBloomCorrupted = true;
    SetOperational(false);
    ReceiveBloomStateChanged(true);
}

void AShipboardRobotBase::OnBloomPurged_Implementation()
{
    if (!bBloomCorrupted)
    {
        return;
    }

    bBloomCorrupted = false;
    SetOperational(CurrentIntegrity > 0.0f && BatteryCharge > 0.0f);
    SetWorking(bWasWorkingBeforeCorruption);
    ReceiveBloomStateChanged(false);
}

bool AShipboardRobotBase::CanBeBloomCorrupted_Implementation() const
{
    return !bBloomCorrupted && CurrentIntegrity > 0.0f;
}

void AShipboardRobotBase::RefreshRobotState()
{
    EShipboardRobotState NewState = EShipboardRobotState::Standby;
    if (bBloomCorrupted)
    {
        NewState = EShipboardRobotState::Corrupted;
    }
    else if (!bOperational || CurrentIntegrity <= 0.0f || BatteryCharge <= 0.0f)
    {
        NewState = EShipboardRobotState::Disabled;
    }
    else if (bWorking)
    {
        NewState = EShipboardRobotState::Working;
    }

    if (RobotState != NewState)
    {
        const EShipboardRobotState PreviousState = RobotState;
        RobotState = NewState;
        OnRep_RobotState(PreviousState);
    }
    else
    {
        UpdateStatusLight();
    }
}

void AShipboardRobotBase::UpdateStatusLight()
{
    if (!StatusLight)
    {
        return;
    }

    switch (RobotState)
    {
    case EShipboardRobotState::Working:
        StatusLight->SetVisibility(true);
        StatusLight->SetIntensity(180.0f);
        StatusLight->SetLightColor(FLinearColor(0.15f, 1.0f, 0.42f));
        break;
    case EShipboardRobotState::Disabled:
        StatusLight->SetVisibility(true);
        StatusLight->SetIntensity(32.0f);
        StatusLight->SetLightColor(FLinearColor(1.0f, 0.08f, 0.04f));
        break;
    case EShipboardRobotState::Corrupted:
        StatusLight->SetVisibility(true);
        StatusLight->SetIntensity(240.0f);
        StatusLight->SetLightColor(FLinearColor(0.72f, 0.08f, 1.0f));
        break;
    default:
        StatusLight->SetVisibility(true);
        StatusLight->SetIntensity(65.0f);
        StatusLight->SetLightColor(FLinearColor(0.12f, 0.72f, 1.0f));
        break;
    }
}

void AShipboardRobotBase::OnRep_RobotState(const EShipboardRobotState PreviousState)
{
    UpdateStatusLight();
    OnRobotStateChanged.Broadcast(PreviousState, RobotState);
    ReceiveRobotStateChanged(PreviousState, RobotState);
}

void AShipboardRobotBase::OnRep_Resources()
{
    const float IntegrityFraction = MaxIntegrity > 0.0f ? CurrentIntegrity / MaxIntegrity : 0.0f;
    OnRobotResourcesChanged.Broadcast(IntegrityFraction, BatteryCharge);
    ReceiveRobotResourcesChanged(IntegrityFraction, BatteryCharge);
}

void AShipboardRobotBase::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AShipboardRobotBase, bOperational);
    DOREPLIFETIME(AShipboardRobotBase, bWorking);
    DOREPLIFETIME(AShipboardRobotBase, bBloomCorrupted);
    DOREPLIFETIME(AShipboardRobotBase, CurrentIntegrity);
    DOREPLIFETIME(AShipboardRobotBase, BatteryCharge);
    DOREPLIFETIME(AShipboardRobotBase, RobotState);
}

ACompactMaintenanceRobot::ACompactMaintenanceRobot()
{
    RobotRole = EShipboardRobotRole::Maintenance;
    MaxIntegrity = 80.0f;
    CurrentIntegrity = MaxIntegrity;
    Capabilities.WorkRate = 1.35f;
    Capabilities.RepairOutput = 25.0f;
    Capabilities.CarryCapacityKg = 40.0f;
    Capabilities.SensorRangeCm = 2400.0f;
    Capabilities.PowerDrainPerWorkUnit = 0.007f;
    CollisionBounds->SetBoxExtent(FVector(58.0f, 52.0f, 45.0f));
    CollisionBounds->SetRelativeLocation(FVector(0.0f, 0.0f, 45.0f));

    UStaticMesh* JackBody = LoadJackPart(TEXT("SM_JACK_BODY"));
    UStaticMesh* JackArm = LoadJackPart(TEXT("SM_JACK_ARM"));
    UStaticMesh* Scanner = LoadFabPart(TEXT("Mesh/SM/PROP/LAMP"), TEXT("SM_SCANNER_01"));
    UStaticMesh* MechaArm = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_MECHA_ARM_01"));
    UMaterialInterface* ArmorLight = LoadRobotMaterial(TEXT("M_Remaster_ArmorLight"));
    UMaterialInterface* Structure = LoadRobotMaterial(TEXT("M_Remaster_Structure"));

    Chassis = CreateRobotPart(this, TEXT("Chassis"), AssemblyRoot, JackBody, ArmorLight);
    Chassis->SetRelativeLocation(FVector(0.0f, 0.0f, 66.0f));
    Chassis->SetRelativeScale3D(FVector(1.05f, 1.15f, 0.56f));

    SensorHead = CreateRobotPart(this, TEXT("SensorHead"), AssemblyRoot, Scanner, Structure);
    SensorHead->SetRelativeLocation(FVector(47.0f, 0.0f, 76.0f));
    SensorHead->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    SensorHead->SetRelativeScale3D(FVector(0.58f));

    FrontLeftLeg = CreateRobotPart(this, TEXT("FrontLeftLeg"), AssemblyRoot, JackArm, Structure);
    FrontLeftLeg->SetRelativeLocation(FVector(29.0f, -35.0f, 31.0f));
    FrontLeftLeg->SetRelativeRotation(FRotator(8.0f, 0.0f, -14.0f));
    FrontLeftLeg->SetRelativeScale3D(FVector(0.48f));

    FrontRightLeg = CreateRobotPart(this, TEXT("FrontRightLeg"), AssemblyRoot, JackArm, Structure);
    FrontRightLeg->SetRelativeLocation(FVector(29.0f, 35.0f, 31.0f));
    FrontRightLeg->SetRelativeRotation(FRotator(-8.0f, 180.0f, 14.0f));
    FrontRightLeg->SetRelativeScale3D(FVector(0.48f));

    RearLeftLeg = CreateRobotPart(this, TEXT("RearLeftLeg"), AssemblyRoot, JackArm, Structure);
    RearLeftLeg->SetRelativeLocation(FVector(-29.0f, -35.0f, 31.0f));
    RearLeftLeg->SetRelativeRotation(FRotator(-8.0f, 0.0f, -14.0f));
    RearLeftLeg->SetRelativeScale3D(FVector(0.48f));

    RearRightLeg = CreateRobotPart(this, TEXT("RearRightLeg"), AssemblyRoot, JackArm, Structure);
    RearRightLeg->SetRelativeLocation(FVector(-29.0f, 35.0f, 31.0f));
    RearRightLeg->SetRelativeRotation(FRotator(8.0f, 180.0f, 14.0f));
    RearRightLeg->SetRelativeScale3D(FVector(0.48f));

    ToolArm = CreateRobotPart(this, TEXT("ToolArm"), AssemblyRoot, MechaArm, Structure);
    ToolArm->SetRelativeLocation(FVector(-8.0f, -23.0f, 87.0f));
    ToolArm->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
    ToolArm->SetRelativeScale3D(FVector(0.22f));

    StatusLight->SetRelativeLocation(FVector(52.0f, 0.0f, 78.0f));
}

ATallUtilityRobot::ATallUtilityRobot()
{
    RobotRole = EShipboardRobotRole::Utility;
    MaxIntegrity = 140.0f;
    CurrentIntegrity = MaxIntegrity;
    Capabilities.WorkRate = 1.0f;
    Capabilities.RepairOutput = 10.0f;
    Capabilities.CarryCapacityKg = 180.0f;
    Capabilities.SensorRangeCm = 3000.0f;
    Capabilities.PowerDrainPerWorkUnit = 0.01f;
    CollisionBounds->SetBoxExtent(FVector(52.0f, 60.0f, 132.0f));
    CollisionBounds->SetRelativeLocation(FVector(0.0f, 0.0f, 132.0f));

    UStaticMesh* BodyMesh = LoadJackPart(TEXT("SM_JACK_BODY"));
    UStaticMesh* HeadMesh = LoadJackPart(TEXT("SM_JACK_HEAD"));
    UStaticMesh* ArmMesh = LoadJackPart(TEXT("SM_JACK_ARM"));
    UStaticMesh* LegMesh = LoadJackPart(TEXT("SM_JACK_LEG"));
    UStaticMesh* PanelMesh = LoadFabPart(TEXT("Mesh/SM/PROP/OTHERS"), TEXT("SM_PANEL_01"));
    UMaterialInterface* ArmorLight = LoadRobotMaterial(TEXT("M_Remaster_ArmorLight"));
    UMaterialInterface* Structure = LoadRobotMaterial(TEXT("M_Remaster_Structure"));

    Body = CreateRobotPart(this, TEXT("Body"), AssemblyRoot, BodyMesh, ArmorLight);
    Body->SetRelativeLocation(FVector(0.0f, 0.0f, 151.0f));

    Head = CreateRobotPart(this, TEXT("Head"), AssemblyRoot, HeadMesh, ArmorLight);
    Head->SetRelativeLocation(FVector(8.0f, 0.0f, 224.0f));
    Head->SetRelativeScale3D(FVector(1.05f));

    LeftArm = CreateRobotPart(this, TEXT("LeftArm"), AssemblyRoot, ArmMesh, Structure);
    LeftArm->SetRelativeLocation(FVector(0.0f, -49.0f, 145.0f));
    LeftArm->SetRelativeRotation(FRotator(0.0f, 0.0f, -7.0f));

    RightArm = CreateRobotPart(this, TEXT("RightArm"), AssemblyRoot, ArmMesh, Structure);
    RightArm->SetRelativeLocation(FVector(0.0f, 49.0f, 145.0f));
    RightArm->SetRelativeRotation(FRotator(0.0f, 180.0f, 7.0f));

    LeftLeg = CreateRobotPart(this, TEXT("LeftLeg"), AssemblyRoot, LegMesh, Structure);
    LeftLeg->SetRelativeLocation(FVector(0.0f, -24.0f, 44.0f));

    RightLeg = CreateRobotPart(this, TEXT("RightLeg"), AssemblyRoot, LegMesh, Structure);
    RightLeg->SetRelativeLocation(FVector(0.0f, 24.0f, 44.0f));
    RightLeg->SetRelativeScale3D(FVector(1.0f, -1.0f, 1.0f));

    ChestDisplay = CreateRobotPart(this, TEXT("ChestDisplay"), AssemblyRoot, PanelMesh);
    ChestDisplay->SetRelativeLocation(FVector(38.0f, 0.0f, 166.0f));
    ChestDisplay->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    ChestDisplay->SetRelativeScale3D(FVector(0.22f));

    StatusLight->SetRelativeLocation(FVector(28.0f, 0.0f, 235.0f));
}

AHeavyCargoRobot::AHeavyCargoRobot()
{
    RobotRole = EShipboardRobotRole::Cargo;
    MaxIntegrity = 280.0f;
    CurrentIntegrity = MaxIntegrity;
    Capabilities.WorkRate = 0.72f;
    Capabilities.RepairOutput = 5.0f;
    Capabilities.CarryCapacityKg = 1400.0f;
    Capabilities.SensorRangeCm = 1800.0f;
    Capabilities.PowerDrainPerWorkUnit = 0.015f;
    CollisionBounds->SetBoxExtent(FVector(92.0f, 112.0f, 140.0f));
    CollisionBounds->SetRelativeLocation(FVector(0.0f, 0.0f, 140.0f));

    UStaticMesh* BodyMesh = LoadJackPart(TEXT("SM_JACK_BODY"));
    UStaticMesh* HeadMesh = LoadJackPart(TEXT("SM_JACK_HEAD"));
    UStaticMesh* ArmMesh = LoadJackPart(TEXT("SM_JACK_ARM"));
    UStaticMesh* LegMesh = LoadJackPart(TEXT("SM_JACK_LEG"));
    UStaticMesh* CargoPodMesh = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_ELECTRIC_BOX_01_CLOSE"));
    UStaticMesh* CraneMesh = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_MECHA_ARM_03"));
    UMaterialInterface* ArmorLight = LoadRobotMaterial(TEXT("M_Remaster_ArmorLight"));
    UMaterialInterface* Structure = LoadRobotMaterial(TEXT("M_Remaster_Structure"));
    UMaterialInterface* SafetyOrange = LoadRobotMaterial(TEXT("M_Remaster_SafetyOrange"));

    Body = CreateRobotPart(this, TEXT("Body"), AssemblyRoot, BodyMesh, ArmorLight);
    Body->SetRelativeLocation(FVector(0.0f, 0.0f, 165.0f));
    Body->SetRelativeScale3D(FVector(1.65f, 1.9f, 1.25f));

    Head = CreateRobotPart(this, TEXT("Head"), AssemblyRoot, HeadMesh, ArmorLight);
    Head->SetRelativeLocation(FVector(18.0f, 0.0f, 252.0f));
    Head->SetRelativeScale3D(FVector(1.3f));

    LeftArm = CreateRobotPart(this, TEXT("LeftArm"), AssemblyRoot, ArmMesh, Structure);
    LeftArm->SetRelativeLocation(FVector(0.0f, -88.0f, 164.0f));
    LeftArm->SetRelativeRotation(FRotator(0.0f, 0.0f, -10.0f));
    LeftArm->SetRelativeScale3D(FVector(1.5f));

    RightArm = CreateRobotPart(this, TEXT("RightArm"), AssemblyRoot, ArmMesh, Structure);
    RightArm->SetRelativeLocation(FVector(0.0f, 88.0f, 164.0f));
    RightArm->SetRelativeRotation(FRotator(0.0f, 180.0f, 10.0f));
    RightArm->SetRelativeScale3D(FVector(1.5f));

    LeftLeg = CreateRobotPart(this, TEXT("LeftLeg"), AssemblyRoot, LegMesh, Structure);
    LeftLeg->SetRelativeLocation(FVector(0.0f, -50.0f, 50.0f));
    LeftLeg->SetRelativeScale3D(FVector(1.55f, 1.55f, 1.22f));

    RightLeg = CreateRobotPart(this, TEXT("RightLeg"), AssemblyRoot, LegMesh, Structure);
    RightLeg->SetRelativeLocation(FVector(0.0f, 50.0f, 50.0f));
    RightLeg->SetRelativeScale3D(FVector(1.55f, -1.55f, 1.22f));

    LeftCargoPod = CreateRobotPart(this, TEXT("LeftCargoPod"), AssemblyRoot, CargoPodMesh, SafetyOrange);
    LeftCargoPod->SetRelativeLocation(FVector(-46.0f, -61.0f, 181.0f));
    LeftCargoPod->SetRelativeRotation(FRotator(90.0f, 0.0f, 0.0f));
    LeftCargoPod->SetRelativeScale3D(FVector(0.6f));

    RightCargoPod = CreateRobotPart(this, TEXT("RightCargoPod"), AssemblyRoot, CargoPodMesh, SafetyOrange);
    RightCargoPod->SetRelativeLocation(FVector(-46.0f, 61.0f, 181.0f));
    RightCargoPod->SetRelativeRotation(FRotator(90.0f, 180.0f, 0.0f));
    RightCargoPod->SetRelativeScale3D(FVector(0.6f));

    IndustrialTool = CreateRobotPart(this, TEXT("IndustrialTool"), AssemblyRoot, CraneMesh, Structure);
    IndustrialTool->SetRelativeLocation(FVector(-48.0f, -36.0f, 235.0f));
    IndustrialTool->SetRelativeRotation(FRotator(0.0f, 180.0f, 0.0f));
    IndustrialTool->SetRelativeScale3D(FVector(0.35f));

    StatusLight->SetRelativeLocation(FVector(34.0f, 0.0f, 265.0f));
}

ASecuritySentryRobot::ASecuritySentryRobot()
{
    RobotRole = EShipboardRobotRole::Security;
    MaxIntegrity = 200.0f;
    CurrentIntegrity = MaxIntegrity;
    Capabilities.WorkRate = 0.9f;
    Capabilities.RepairOutput = 0.0f;
    Capabilities.CarryCapacityKg = 80.0f;
    Capabilities.SensorRangeCm = 4200.0f;
    Capabilities.PowerDrainPerWorkUnit = 0.012f;
    CollisionBounds->SetBoxExtent(FVector(76.0f, 72.0f, 82.0f));
    CollisionBounds->SetRelativeLocation(FVector(0.0f, 0.0f, 82.0f));

    UStaticMesh* ChassisMesh = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_POWER_GENERATOR_01"));
    UStaticMesh* ClampMesh = LoadJackPart(TEXT("SM_JACK_ARM"));
    UStaticMesh* MagPadMesh = LoadFabPart(TEXT("Mesh/SM/PROP/OTHERS"), TEXT("SM_PANEL_01"));
    UStaticMesh* BodyMesh = LoadJackPart(TEXT("SM_JACK_BODY"));
    UStaticMesh* ScannerMesh = LoadFabPart(TEXT("Mesh/SM/PROP/LAMP"), TEXT("SM_SCANNER_01"));
    UStaticMesh* ArmMesh = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_MECHA_ARM_02"));
    UStaticMesh* PodMesh = LoadFabPart(TEXT("Mesh/SM/PROP/MACHINE"), TEXT("SM_ELECTRIC_BOX_01_CLOSE"));
    UMaterialInterface* ArmorLight = LoadRobotMaterial(TEXT("M_Remaster_ArmorLight"));
    UMaterialInterface* Structure = LoadRobotMaterial(TEXT("M_Remaster_Structure"));
    UMaterialInterface* SafetyOrange = LoadRobotMaterial(TEXT("M_Remaster_SafetyOrange"));

    Chassis = CreateRobotPart(this, TEXT("Chassis"), AssemblyRoot, ChassisMesh, ArmorLight);
    Chassis->SetRelativeLocation(FVector(0.0f, 0.0f, 68.0f));
    Chassis->SetRelativeScale3D(FVector(0.30f, 0.36f, 0.25f));

    FrontLeftClamp = CreateRobotPart(this, TEXT("FrontLeftClamp"), AssemblyRoot, ClampMesh, Structure);
    FrontLeftClamp->SetRelativeLocation(FVector(37.0f, -42.0f, 34.0f));
    FrontLeftClamp->SetRelativeRotation(FRotator(20.0f, 0.0f, -27.0f));
    FrontLeftClamp->SetRelativeScale3D(FVector(0.52f));

    FrontRightClamp = CreateRobotPart(this, TEXT("FrontRightClamp"), AssemblyRoot, ClampMesh, Structure);
    FrontRightClamp->SetRelativeLocation(FVector(37.0f, 42.0f, 34.0f));
    FrontRightClamp->SetRelativeRotation(FRotator(20.0f, 180.0f, 27.0f));
    FrontRightClamp->SetRelativeScale3D(FVector(0.52f));

    RearLeftClamp = CreateRobotPart(this, TEXT("RearLeftClamp"), AssemblyRoot, ClampMesh, Structure);
    RearLeftClamp->SetRelativeLocation(FVector(-37.0f, -42.0f, 34.0f));
    RearLeftClamp->SetRelativeRotation(FRotator(-20.0f, 0.0f, -27.0f));
    RearLeftClamp->SetRelativeScale3D(FVector(0.52f));

    RearRightClamp = CreateRobotPart(this, TEXT("RearRightClamp"), AssemblyRoot, ClampMesh, Structure);
    RearRightClamp->SetRelativeLocation(FVector(-37.0f, 42.0f, 34.0f));
    RearRightClamp->SetRelativeRotation(FRotator(-20.0f, 180.0f, 27.0f));
    RearRightClamp->SetRelativeScale3D(FVector(0.52f));

    FrontLeftMagPad = CreateRobotPart(this, TEXT("FrontLeftMagPad"), AssemblyRoot, MagPadMesh, SafetyOrange);
    FrontLeftMagPad->SetRelativeLocation(FVector(52.0f, -50.0f, 12.0f));
    FrontLeftMagPad->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
    FrontLeftMagPad->SetRelativeScale3D(FVector(0.30f, 0.28f, 0.80f));

    FrontRightMagPad = CreateRobotPart(this, TEXT("FrontRightMagPad"), AssemblyRoot, MagPadMesh, SafetyOrange);
    FrontRightMagPad->SetRelativeLocation(FVector(52.0f, 50.0f, 12.0f));
    FrontRightMagPad->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
    FrontRightMagPad->SetRelativeScale3D(FVector(0.30f, 0.28f, 0.80f));

    RearLeftMagPad = CreateRobotPart(this, TEXT("RearLeftMagPad"), AssemblyRoot, MagPadMesh, SafetyOrange);
    RearLeftMagPad->SetRelativeLocation(FVector(-52.0f, -50.0f, 12.0f));
    RearLeftMagPad->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
    RearLeftMagPad->SetRelativeScale3D(FVector(0.30f, 0.28f, 0.80f));

    RearRightMagPad = CreateRobotPart(this, TEXT("RearRightMagPad"), AssemblyRoot, MagPadMesh, SafetyOrange);
    RearRightMagPad->SetRelativeLocation(FVector(-52.0f, 50.0f, 12.0f));
    RearRightMagPad->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
    RearRightMagPad->SetRelativeScale3D(FVector(0.30f, 0.28f, 0.80f));

    ArmorBody = CreateRobotPart(this, TEXT("ArmorBody"), AssemblyRoot, BodyMesh, ArmorLight);
    ArmorBody->SetRelativeLocation(FVector(-8.0f, 0.0f, 119.0f));
    ArmorBody->SetRelativeScale3D(FVector(1.0f, 1.15f, 0.55f));

    SensorHead = CreateRobotPart(this, TEXT("SensorHead"), AssemblyRoot, ScannerMesh, Structure);
    SensorHead->SetRelativeLocation(FVector(46.0f, 0.0f, 143.0f));
    SensorHead->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    SensorHead->SetRelativeScale3D(FVector(0.72f));

    ResponseArm = CreateRobotPart(this, TEXT("ResponseArm"), AssemblyRoot, ArmMesh, Structure);
    ResponseArm->SetRelativeLocation(FVector(-16.0f, -37.0f, 121.0f));
    ResponseArm->SetRelativeRotation(FRotator(-5.0f, 180.0f, -8.0f));
    ResponseArm->SetRelativeScale3D(FVector(0.24f));

    PowerPod = CreateRobotPart(this, TEXT("PowerPod"), AssemblyRoot, PodMesh, SafetyOrange);
    PowerPod->SetRelativeLocation(FVector(-37.0f, 33.0f, 112.0f));
    PowerPod->SetRelativeRotation(FRotator(90.0f, 180.0f, 0.0f));
    PowerPod->SetRelativeScale3D(FVector(0.42f));

    StatusLight->SetRelativeLocation(FVector(53.0f, 0.0f, 146.0f));
}

void ASecuritySentryRobot::SetMagneticAnchorsEngaged(const bool bEngaged)
{
    bMagneticAnchorsEngaged = bEngaged && bOperational && !bBloomCorrupted;
}

void ASecuritySentryRobot::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(ASecuritySentryRobot, bMagneticAnchorsEngaged);
}
