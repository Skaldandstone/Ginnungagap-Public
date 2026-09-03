#pragma once

#include "CoreMinimal.h"
#include "Ship/ShipSection.h"
#include "ModularShipRoom.generated.h"

// Runtime-forward declarations keep this contract independent of editor-only headers.
class USceneComponent;
class APointLight;
class ATextRenderActor;

/** Player-facing function of a reusable ship room module. */
UENUM(BlueprintType)
enum class EShipRoomArchetype : uint8
{
    Companionway,
    Bridge,
    SensorOperations,
    MedicalBay,
    CrewBerthing,
    CargoBay,
    DamageControl,
    Engineering,
    ReactorControl,
    EscapeBay,
    Armory
};

/** Cardinal and vertical connection points shared by every room kit piece. */
UENUM(BlueprintType)
enum class EShipRoomSocket : uint8
{
    Forward,
    Aft,
    Port,
    Starboard,
    ForwardPort,
    ForwardStarboard,
    AftPort,
    AftStarboard,
    Up,
    Down
};

UENUM(BlueprintType)
enum class EShipRoomAccessTier : uint8
{
    Public,
    Crew,
    Restricted,
    Secure
};

UENUM(BlueprintType)
enum class EShipRoomOperationalState : uint8
{
    Nominal,
    Alert,
    Unpowered,
    Damaged,
    Decompressed,
    Quarantined,
    BloomCorrupted,
    /**
     * Powered, but off the emergency bus rather than the main one: the ship is running, and it is
     * running on alarms. Appended last so the state-tag table and any saved enum values keep
     * their indices.
     */
    EmergencyPower
};

USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipRoomGameplayProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay", meta = (ClampMin = "0", ClampMax = "10"))
    int32 PowerPriority = 5;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay", meta = (ClampMin = "0.0"))
    float NominalPowerDraw = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay", meta = (ClampMin = "0"))
    int32 SafeOccupancy = 4;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay", meta = (ClampMin = "0", ClampMax = "5"))
    int32 HazardTier = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay", meta = (ClampMin = "0", ClampMax = "5"))
    int32 LootTier = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay")
    EShipRoomAccessTier AccessTier = EShipRoomAccessTier::Crew;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Gameplay")
    bool bCriticalForJump = false;

    bool IsValid(FString* OutError = nullptr) const;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnShipRoomOperationalStateChanged,
    EShipRoomOperationalState, PreviousState, EShipRoomOperationalState, NewState);

/** Explicit, serializable edge in a modular ship layout graph. */
USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipRoomConnectionDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Connection")
    FName RoomA;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Connection")
    EShipRoomSocket SocketA = EShipRoomSocket::Forward;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Connection")
    FName RoomB;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Connection")
    EShipRoomSocket SocketB = EShipRoomSocket::Aft;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Connection", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float TransferCoefficient = 1.0f;

    bool IsValid(FString* OutError = nullptr) const;
};

/** Serializable recipe used by procedural layouts and hand-authored Blueprint assemblers. */
USTRUCT(BlueprintType)
struct GINNUNGAGAP_API FShipRoomModuleDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    FName RoomCode = TEXT("ROOM-00");

    /** Stable numeric identity for saves and deterministic generation. Zero means legacy/unassigned. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 RoomId = 0;

    /** Reusable functional type. Instances with the same type obey the proximity policy. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 RoomTypeId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Placement")
    FName PlacementSection = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 SameTypeExclusionDistance = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Placement")
    bool bAllowSameTypeClusterInSection = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    EShipRoomArchetype Archetype = EShipRoomArchetype::Companionway;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    EShipSectionType SectionType = EShipSectionType::Corridor;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    FVector RelativeLocation = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module", meta = (ClampMin = "100.0"))
    FVector ModuleSize = FVector(1300.0, 1040.0, 600.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module")
    FLinearColor AccentColor = FLinearColor(0.15f, 0.65f, 1.0f);

    bool IsValid(FString* OutError = nullptr) const;
};

/**
 * A reusable room module with stable identity and standardized bulkhead sockets.
 * Art can replace the generated shell while layout, navigation, atmosphere and
 * save data continue to address the same room actor.
 */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AModularShipRoom : public AShipSection
{
    GENERATED_BODY()

public:
    AModularShipRoom();
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Room Module")
    FName RoomCode = TEXT("ROOM-00");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 RoomId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 RoomTypeId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Room Module|Placement")
    FName PlacementSection = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Room Module|Placement", meta = (ClampMin = "0"))
    int32 SameTypeExclusionDistance = 3;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Room Module|Placement")
    bool bAllowSameTypeClusterInSection = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Room Module")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Room Module")
    EShipRoomArchetype Archetype = EShipRoomArchetype::Companionway;

    /** Full interior size in Unreal units. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Room Module", meta = (ClampMin = "100.0"))
    FVector ModuleSize = FVector(1300.0, 1040.0, 600.0);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Room Module|Sockets")
    TArray<EShipRoomSocket> EnabledSockets;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Room Module|Gameplay")
    FShipRoomGameplayProfile GameplayProfile;

    UPROPERTY(ReplicatedUsing = OnRep_OperationalState, BlueprintReadOnly, Category = "Room Module|State")
    EShipRoomOperationalState OperationalState = EShipRoomOperationalState::Nominal;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Room Module|State")
    bool bPowered = true;

    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Room Module|State")
    bool bQuarantined = false;

    /**
     * Power is up but it is the emergency bus. Lights come back red, not white: the trailer beat
     * sheet's "lights recover to an emergency-red state", which until this flag existed the game
     * could not express -- restoring power took a room straight to Nominal's cold blue.
     */
    UPROPERTY(Replicated, BlueprintReadOnly, Category = "Room Module|State")
    bool bEmergencyPower = false;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Anchors")
    TObjectPtr<AActor> SystemAnchor;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Anchors")
    TObjectPtr<AActor> LootAnchor;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Anchors")
    TObjectPtr<AActor> MaintenanceAnchor;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Presentation")
    TObjectPtr<APointLight> IdentityLight;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Presentation")
    TObjectPtr<ATextRenderActor> CodeSign;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Room Module|Presentation")
    TObjectPtr<ATextRenderActor> NameSign;

    UPROPERTY(BlueprintAssignable, Category = "Room Module|State")
    FOnShipRoomOperationalStateChanged OnOperationalStateChanged;

    UFUNCTION(BlueprintCallable, Category = "Room Module")
    void ConfigureRoom(FName InRoomCode, const FText& InDisplayName, EShipRoomArchetype InArchetype,
        EShipSectionType InSectionType, const FVector& InModuleSize);

    UFUNCTION(BlueprintCallable, Category = "Room Module|Placement")
    void ConfigurePlacementIdentity(int32 InRoomId, int32 InRoomTypeId, FName InPlacementSection,
        int32 InSameTypeExclusionDistance = 3, bool bInAllowSameTypeClusterInSection = false);

    UFUNCTION(BlueprintPure, Category = "Room Module|Placement")
    bool HasPlacementIdentity() const { return RoomId > 0 && RoomTypeId > 0; }

    UFUNCTION(BlueprintPure, Category = "Room Module")
    USceneComponent* GetBulkheadSocket(EShipRoomSocket Socket) const;

    UFUNCTION(BlueprintPure, Category = "Room Module")
    FTransform GetBulkheadSocketTransform(EShipRoomSocket Socket) const;

    UFUNCTION(BlueprintPure, Category = "Room Module")
    bool IsSocketEnabled(EShipRoomSocket Socket) const;

    UFUNCTION(BlueprintPure, Category = "Room Module")
    bool IsSocketConnected(EShipRoomSocket Socket) const;

    UFUNCTION(BlueprintCallable, Category = "Room Module")
    bool ConnectRoom(EShipRoomSocket LocalSocket, AModularShipRoom* OtherRoom, EShipRoomSocket OtherSocket);

    UFUNCTION(BlueprintCallable, Category = "Room Module")
    void DisconnectRoom(EShipRoomSocket LocalSocket);

    UFUNCTION(BlueprintPure, Category = "Room Module")
    AModularShipRoom* GetConnectedRoom(EShipRoomSocket LocalSocket) const;

    UFUNCTION(BlueprintPure, Category = "Room Module")
    bool ValidateRoom(FString& OutError) const;

    UFUNCTION(BlueprintPure, Category = "Room Module")
    static EShipRoomSocket GetOppositeSocket(EShipRoomSocket Socket);

    UFUNCTION(BlueprintCallable, Category = "Room Module|State")
    void SetPowered(bool bInPowered);

    UFUNCTION(BlueprintCallable, Category = "Room Module|State")
    void SetQuarantined(bool bInQuarantined);

    UFUNCTION(BlueprintCallable, Category = "Room Module|State")
    void SetEmergencyPower(bool bInEmergencyPower);

    UFUNCTION(BlueprintCallable, Category = "Room Module|State")
    void RefreshOperationalState();

    UFUNCTION(BlueprintPure, Category = "Room Module|State")
    bool IsHabitable() const;

    UFUNCTION(BlueprintPure, Category = "Room Module|State")
    float GetReadinessScore() const;

private:
    void UpdateSocketTransforms();
    void ApplyOperationalPresentation();

    UFUNCTION()
    void HandleDamageStateChanged();

    UFUNCTION()
    void OnRep_OperationalState(EShipRoomOperationalState PreviousState);

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> ForwardSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> AftSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> PortSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> StarboardSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> ForwardPortSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> ForwardStarboardSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> AftPortSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> AftStarboardSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> UpSocket;

    UPROPERTY(VisibleAnywhere, Category = "Room Module|Sockets")
    TObjectPtr<USceneComponent> DownSocket;

    UPROPERTY(VisibleInstanceOnly, Category = "Room Module|Sockets")
    TMap<EShipRoomSocket, TObjectPtr<AModularShipRoom>> ConnectedRooms;
};
