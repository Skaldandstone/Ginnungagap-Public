#include "Ship/ModularShipRoom.h"

#include "Components/BoxComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/PointLight.h"
#include "Engine/TextRenderActor.h"
#include "Net/UnrealNetwork.h"
#include "Ship/ShipDamageComponent.h"

bool FShipRoomGameplayProfile::IsValid(FString* OutError) const
{
    FString Error;
    if (PowerPriority < 0 || PowerPriority > 10)
    {
        Error = TEXT("Room power priority must be between zero and ten.");
    }
    else if (NominalPowerDraw < 0.0f)
    {
        Error = TEXT("Room nominal power draw cannot be negative.");
    }
    else if (SafeOccupancy < 0)
    {
        Error = TEXT("Room safe occupancy cannot be negative.");
    }
    else if (HazardTier < 0 || HazardTier > 5 || LootTier < 0 || LootTier > 5)
    {
        Error = TEXT("Room hazard and loot tiers must be between zero and five.");
    }
    if (OutError)
    {
        *OutError = Error;
    }
    return Error.IsEmpty();
}

bool FShipRoomModuleDefinition::IsValid(FString* OutError) const
{
    FString Error;
    if (RoomCode.IsNone())
    {
        Error = TEXT("RoomCode must not be empty.");
    }
    else if (DisplayName.IsEmpty())
    {
        Error = FString::Printf(TEXT("Room %s must have a display name."), *RoomCode.ToString());
    }
    else if (ModuleSize.X < 100.0 || ModuleSize.Y < 100.0 || ModuleSize.Z < 100.0)
    {
        Error = FString::Printf(TEXT("Room %s dimensions must each be at least 100 units."), *RoomCode.ToString());
    }
    else if ((RoomId > 0) != (RoomTypeId > 0))
    {
        Error = FString::Printf(TEXT("Room %s must assign room id and room type id together."), *RoomCode.ToString());
    }
    else if (RoomId > 0 && PlacementSection.IsNone())
    {
        Error = FString::Printf(TEXT("Room %s placement identity requires a section."), *RoomCode.ToString());
    }
    else if (SameTypeExclusionDistance < 0)
    {
        Error = FString::Printf(TEXT("Room %s same-type exclusion distance cannot be negative."), *RoomCode.ToString());
    }

    if (OutError)
    {
        *OutError = Error;
    }
    return Error.IsEmpty();
}

bool FShipRoomConnectionDefinition::IsValid(FString* OutError) const
{
    FString Error;
    if (RoomA.IsNone() || RoomB.IsNone())
    {
        Error = TEXT("Both connection endpoints require room codes.");
    }
    else if (RoomA == RoomB)
    {
        Error = FString::Printf(TEXT("Room %s cannot connect to itself."), *RoomA.ToString());
    }
    else if (TransferCoefficient < 0.0f || TransferCoefficient > 1.0f)
    {
        Error = TEXT("Connection transfer coefficient must be between zero and one.");
    }
    if (OutError)
    {
        *OutError = Error;
    }
    return Error.IsEmpty();
}

AModularShipRoom::AModularShipRoom()
{
    bReplicates = true;
    ForwardSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadForward"));
    ForwardSocket->SetupAttachment(RootComponent);
    AftSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadAft"));
    AftSocket->SetupAttachment(RootComponent);
    PortSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadPort"));
    PortSocket->SetupAttachment(RootComponent);
    StarboardSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadStarboard"));
    StarboardSocket->SetupAttachment(RootComponent);
    ForwardPortSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadForwardPort"));
    ForwardPortSocket->SetupAttachment(RootComponent);
    ForwardStarboardSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadForwardStarboard"));
    ForwardStarboardSocket->SetupAttachment(RootComponent);
    AftPortSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadAftPort"));
    AftPortSocket->SetupAttachment(RootComponent);
    AftStarboardSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadAftStarboard"));
    AftStarboardSocket->SetupAttachment(RootComponent);
    UpSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadUp"));
    UpSocket->SetupAttachment(RootComponent);
    DownSocket = CreateDefaultSubobject<USceneComponent>(TEXT("BulkheadDown"));
    DownSocket->SetupAttachment(RootComponent);
    EnabledSockets = { EShipRoomSocket::Forward, EShipRoomSocket::Aft,
        EShipRoomSocket::Port, EShipRoomSocket::Starboard, EShipRoomSocket::ForwardPort,
        EShipRoomSocket::ForwardStarboard, EShipRoomSocket::AftPort, EShipRoomSocket::AftStarboard,
        EShipRoomSocket::Up, EShipRoomSocket::Down };
    UpdateSocketTransforms();
}

void AModularShipRoom::BeginPlay()
{
    Super::BeginPlay();
    if (DamageState)
    {
        DamageState->OnDamageStateChanged.AddDynamic(this, &AModularShipRoom::HandleDamageStateChanged);
    }
    RefreshOperationalState();
}

void AModularShipRoom::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AModularShipRoom, OperationalState);
    DOREPLIFETIME(AModularShipRoom, bPowered);
    DOREPLIFETIME(AModularShipRoom, bQuarantined);
    DOREPLIFETIME(AModularShipRoom, bEmergencyPower);
    DOREPLIFETIME(AModularShipRoom, RoomId);
    DOREPLIFETIME(AModularShipRoom, RoomTypeId);
    DOREPLIFETIME(AModularShipRoom, PlacementSection);
    DOREPLIFETIME(AModularShipRoom, SameTypeExclusionDistance);
    DOREPLIFETIME(AModularShipRoom, bAllowSameTypeClusterInSection);
}

void AModularShipRoom::ConfigureRoom(FName InRoomCode, const FText& InDisplayName,
    EShipRoomArchetype InArchetype, EShipSectionType InSectionType, const FVector& InModuleSize)
{
    RoomCode = InRoomCode;
    DisplayName = InDisplayName;
    Archetype = InArchetype;
    SectionType = InSectionType;
    ModuleSize.X = FMath::Max(100.0, InModuleSize.X);
    ModuleSize.Y = FMath::Max(100.0, InModuleSize.Y);
    ModuleSize.Z = FMath::Max(100.0, InModuleSize.Z);

    if (SectionBounds)
    {
        SectionBounds->SetBoxExtent(ModuleSize * 0.5);
    }

    Tags.AddUnique(TEXT("ModularShipRoom"));
    Tags.AddUnique(RoomCode);
    UpdateSocketTransforms();
}

void AModularShipRoom::ConfigurePlacementIdentity(int32 InRoomId, int32 InRoomTypeId,
    FName InPlacementSection, int32 InSameTypeExclusionDistance,
    bool bInAllowSameTypeClusterInSection)
{
    RoomId = FMath::Max(0, InRoomId);
    RoomTypeId = FMath::Max(0, InRoomTypeId);
    PlacementSection = InPlacementSection;
    SameTypeExclusionDistance = FMath::Max(0, InSameTypeExclusionDistance);
    bAllowSameTypeClusterInSection = bInAllowSameTypeClusterInSection;

    if (RoomId > 0)
    {
        Tags.AddUnique(FName(*FString::Printf(TEXT("RoomId=%d"), RoomId)));
    }
    if (RoomTypeId > 0)
    {
        Tags.AddUnique(FName(*FString::Printf(TEXT("RoomTypeId=%d"), RoomTypeId)));
    }
    if (!PlacementSection.IsNone())
    {
        Tags.AddUnique(FName(*FString::Printf(TEXT("PlacementSection=%s"), *PlacementSection.ToString())));
    }
}

USceneComponent* AModularShipRoom::GetBulkheadSocket(EShipRoomSocket Socket) const
{
    switch (Socket)
    {
    case EShipRoomSocket::Forward: return ForwardSocket;
    case EShipRoomSocket::Aft: return AftSocket;
    case EShipRoomSocket::Port: return PortSocket;
    case EShipRoomSocket::Starboard: return StarboardSocket;
    case EShipRoomSocket::ForwardPort: return ForwardPortSocket;
    case EShipRoomSocket::ForwardStarboard: return ForwardStarboardSocket;
    case EShipRoomSocket::AftPort: return AftPortSocket;
    case EShipRoomSocket::AftStarboard: return AftStarboardSocket;
    case EShipRoomSocket::Up: return UpSocket;
    case EShipRoomSocket::Down: return DownSocket;
    default: return nullptr;
    }
}

FTransform AModularShipRoom::GetBulkheadSocketTransform(EShipRoomSocket Socket) const
{
    if (const USceneComponent* SocketComponent = GetBulkheadSocket(Socket))
    {
        return SocketComponent->GetComponentTransform();
    }
    return GetActorTransform();
}

bool AModularShipRoom::IsSocketEnabled(EShipRoomSocket Socket) const
{
    return EnabledSockets.Contains(Socket);
}

bool AModularShipRoom::IsSocketConnected(EShipRoomSocket Socket) const
{
    return ConnectedRooms.Contains(Socket) && IsValid(ConnectedRooms.FindRef(Socket));
}

bool AModularShipRoom::ConnectRoom(EShipRoomSocket LocalSocket, AModularShipRoom* OtherRoom,
    EShipRoomSocket OtherSocket)
{
    if (!OtherRoom || OtherRoom == this || !IsSocketEnabled(LocalSocket)
        || !OtherRoom->IsSocketEnabled(OtherSocket) || IsSocketConnected(LocalSocket)
        || OtherRoom->IsSocketConnected(OtherSocket))
    {
        return false;
    }

    ConnectedRooms.Add(LocalSocket, OtherRoom);
    OtherRoom->ConnectedRooms.Add(OtherSocket, this);
    return true;
}

void AModularShipRoom::DisconnectRoom(EShipRoomSocket LocalSocket)
{
    AModularShipRoom* OtherRoom = ConnectedRooms.FindRef(LocalSocket);
    ConnectedRooms.Remove(LocalSocket);
    if (!OtherRoom)
    {
        return;
    }

    for (auto It = OtherRoom->ConnectedRooms.CreateIterator(); It; ++It)
    {
        if (It.Value() == this)
        {
            It.RemoveCurrent();
        }
    }
}

AModularShipRoom* AModularShipRoom::GetConnectedRoom(EShipRoomSocket LocalSocket) const
{
    return ConnectedRooms.FindRef(LocalSocket);
}

bool AModularShipRoom::ValidateRoom(FString& OutError) const
{
    FShipRoomModuleDefinition Definition;
    Definition.RoomCode = RoomCode;
    Definition.RoomId = RoomId;
    Definition.RoomTypeId = RoomTypeId;
    Definition.PlacementSection = PlacementSection;
    Definition.SameTypeExclusionDistance = SameTypeExclusionDistance;
    Definition.bAllowSameTypeClusterInSection = bAllowSameTypeClusterInSection;
    Definition.DisplayName = DisplayName;
    Definition.Archetype = Archetype;
    Definition.SectionType = SectionType;
    Definition.ModuleSize = ModuleSize;
    if (!Definition.IsValid(&OutError))
    {
        return false;
    }
    if (EnabledSockets.IsEmpty())
    {
        OutError = FString::Printf(TEXT("Room %s must expose at least one bulkhead socket."), *RoomCode.ToString());
        return false;
    }
    if (!GameplayProfile.IsValid(&OutError))
    {
        return false;
    }
    OutError.Reset();
    return true;
}

void AModularShipRoom::SetPowered(bool bInPowered)
{
    if (!HasAuthority() || bPowered == bInPowered)
    {
        return;
    }
    bPowered = bInPowered;
    RefreshOperationalState();
}

void AModularShipRoom::SetQuarantined(bool bInQuarantined)
{
    if (!HasAuthority() || bQuarantined == bInQuarantined)
    {
        return;
    }
    bQuarantined = bInQuarantined;
    RefreshOperationalState();
}

void AModularShipRoom::SetEmergencyPower(bool bInEmergencyPower)
{
    if (!HasAuthority() || bEmergencyPower == bInEmergencyPower)
    {
        return;
    }
    bEmergencyPower = bInEmergencyPower;
    RefreshOperationalState();
}

void AModularShipRoom::RefreshOperationalState()
{
    EShipRoomOperationalState NewState = EShipRoomOperationalState::Nominal;
    if (Contamination >= 0.25f)
    {
        NewState = EShipRoomOperationalState::BloomCorrupted;
    }
    else if (bQuarantined)
    {
        NewState = EShipRoomOperationalState::Quarantined;
    }
    else if (DamageState && DamageState->AtmospherePercent < 20.0f)
    {
        NewState = EShipRoomOperationalState::Decompressed;
    }
    else if (DamageState && DamageState->GetDangerScore() >= 0.45f)
    {
        NewState = EShipRoomOperationalState::Damaged;
    }
    else if (!bPowered)
    {
        NewState = EShipRoomOperationalState::Unpowered;
    }
    else if (DamageState && DamageState->GetDangerScore() >= 0.15f)
    {
        NewState = EShipRoomOperationalState::Alert;
    }
    else if (bEmergencyPower)
    {
        // Below every fault above: a room that is decompressed, damaged or corrupted says so first.
        // Above Nominal: emergency power is what a powered room is until the main bus is back.
        NewState = EShipRoomOperationalState::EmergencyPower;
    }

    const EShipRoomOperationalState PreviousState = OperationalState;
    OperationalState = NewState;
    ApplyOperationalPresentation();
    if (PreviousState != OperationalState)
    {
        OnOperationalStateChanged.Broadcast(PreviousState, OperationalState);
        ForceNetUpdate();
    }
}

bool AModularShipRoom::IsHabitable() const
{
    return OperationalState != EShipRoomOperationalState::Decompressed
        && OperationalState != EShipRoomOperationalState::BloomCorrupted
        && (!DamageState || DamageState->AtmospherePercent >= 20.0f);
}

float AModularShipRoom::GetReadinessScore() const
{
    const float Atmosphere = DamageState ? DamageState->AtmospherePercent / 100.0f : 1.0f;
    const float Integrity = DamageState ? DamageState->HullIntegrity : 1.0f;
    const float Power = bPowered ? 1.0f : 0.25f;
    const float ContaminationFactor = 1.0f - FMath::Clamp(Contamination, 0.0f, 1.0f);
    const float QuarantineFactor = bQuarantined ? 0.5f : 1.0f;
    return FMath::Clamp(Atmosphere * Integrity * Power * ContaminationFactor * QuarantineFactor, 0.0f, 1.0f);
}

void AModularShipRoom::HandleDamageStateChanged()
{
    RefreshOperationalState();
}

void AModularShipRoom::OnRep_OperationalState(EShipRoomOperationalState PreviousState)
{
    ApplyOperationalPresentation();
    if (PreviousState != OperationalState)
    {
        OnOperationalStateChanged.Broadcast(PreviousState, OperationalState);
    }
}

void AModularShipRoom::ApplyOperationalPresentation()
{
    static const FName StateTags[] = { TEXT("RoomState_Nominal"), TEXT("RoomState_Alert"),
        TEXT("RoomState_Unpowered"), TEXT("RoomState_Damaged"), TEXT("RoomState_Decompressed"),
        TEXT("RoomState_Quarantined"), TEXT("RoomState_BloomCorrupted"), TEXT("RoomState_EmergencyPower") };
    for (const FName Tag : StateTags)
    {
        Tags.Remove(Tag);
    }
    Tags.AddUnique(StateTags[static_cast<int32>(OperationalState)]);

    UPointLightComponent* Light = IdentityLight
        ? IdentityLight->FindComponentByClass<UPointLightComponent>() : nullptr;
    if (!Light)
    {
        return;
    }
    FLinearColor Color = FLinearColor(0.25f, 0.65f, 1.0f);
    float Intensity = 1250.0f;
    switch (OperationalState)
    {
    case EShipRoomOperationalState::Alert: Color = FLinearColor(1.0f, 0.55f, 0.05f); Intensity = 1600.0f; break;
    case EShipRoomOperationalState::Unpowered: Color = FLinearColor(0.08f, 0.12f, 0.16f); Intensity = 80.0f; break;
    case EShipRoomOperationalState::Damaged: Color = FLinearColor(1.0f, 0.12f, 0.02f); Intensity = 1900.0f; break;
    case EShipRoomOperationalState::Decompressed: Color = FLinearColor(0.15f, 0.35f, 1.0f); Intensity = 950.0f; break;
    case EShipRoomOperationalState::Quarantined: Color = FLinearColor(1.0f, 0.75f, 0.02f); Intensity = 1500.0f; break;
    case EShipRoomOperationalState::BloomCorrupted: Color = FLinearColor(0.45f, 0.03f, 0.75f); Intensity = 1750.0f; break;
    // Deep red, well under Damaged's brightness: the ship is lit, not on fire. Warm enough to sit
    // with the corridors' amber emergency fixtures rather than fight them.
    case EShipRoomOperationalState::EmergencyPower: Color = FLinearColor(1.0f, 0.16f, 0.06f); Intensity = 900.0f; break;
    default: break;
    }
    Light->SetLightColor(Color);
    Light->SetIntensity(Intensity);
}

EShipRoomSocket AModularShipRoom::GetOppositeSocket(EShipRoomSocket Socket)
{
    switch (Socket)
    {
    case EShipRoomSocket::Forward: return EShipRoomSocket::Aft;
    case EShipRoomSocket::Aft: return EShipRoomSocket::Forward;
    case EShipRoomSocket::Port: return EShipRoomSocket::Starboard;
    case EShipRoomSocket::Starboard: return EShipRoomSocket::Port;
    case EShipRoomSocket::ForwardPort: return EShipRoomSocket::AftPort;
    case EShipRoomSocket::ForwardStarboard: return EShipRoomSocket::AftStarboard;
    case EShipRoomSocket::AftPort: return EShipRoomSocket::ForwardPort;
    case EShipRoomSocket::AftStarboard: return EShipRoomSocket::ForwardStarboard;
    case EShipRoomSocket::Up: return EShipRoomSocket::Down;
    case EShipRoomSocket::Down: return EShipRoomSocket::Up;
    default: return EShipRoomSocket::Forward;
    }
}

void AModularShipRoom::UpdateSocketTransforms()
{
    const FVector HalfSize = ModuleSize * 0.5;
    ForwardSocket->SetRelativeLocationAndRotation(FVector(HalfSize.X, 0.0, 0.0), FRotator(0.0, 0.0, 0.0));
    AftSocket->SetRelativeLocationAndRotation(FVector(-HalfSize.X, 0.0, 0.0), FRotator(0.0, 180.0, 0.0));
    PortSocket->SetRelativeLocationAndRotation(FVector(0.0, -HalfSize.Y, 0.0), FRotator(0.0, -90.0, 0.0));
    StarboardSocket->SetRelativeLocationAndRotation(FVector(0.0, HalfSize.Y, 0.0), FRotator(0.0, 90.0, 0.0));
    ForwardPortSocket->SetRelativeLocationAndRotation(FVector(HalfSize.X, -HalfSize.Y * 0.55, 0.0), FRotator::ZeroRotator);
    ForwardStarboardSocket->SetRelativeLocationAndRotation(FVector(HalfSize.X, HalfSize.Y * 0.55, 0.0), FRotator::ZeroRotator);
    AftPortSocket->SetRelativeLocationAndRotation(FVector(-HalfSize.X, -HalfSize.Y * 0.55, 0.0), FRotator(0.0, 180.0, 0.0));
    AftStarboardSocket->SetRelativeLocationAndRotation(FVector(-HalfSize.X, HalfSize.Y * 0.55, 0.0), FRotator(0.0, 180.0, 0.0));
    UpSocket->SetRelativeLocationAndRotation(FVector(0.0, 0.0, HalfSize.Z), FRotator(-90.0, 0.0, 0.0));
    DownSocket->SetRelativeLocationAndRotation(FVector(0.0, 0.0, -HalfSize.Z), FRotator(90.0, 0.0, 0.0));
}
