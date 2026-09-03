#pragma once

#include "CoreMinimal.h"
#include "PlayerActivityTypes.generated.h"

UENUM(BlueprintType)
enum class EPlayerActivityType : uint8
{
    Scan,
    Repair,
    Build,
    Rewire,
    Welding,
    HullPatching,
    FireSuppression,
    PipeSealing,
    ComponentReplacement,
    Fabrication,
    SensorCalibration,
    Decontamination,
    MedicalStabilization,
    BreakerRerouting,
    MechanicalOverride,
    AirlockRepressurization,
    ScrubberService,
    CoolantBalancing,
    BatteryRecovery,
    ReactorStartup,
    DroneRepair,
    TurretService,
    SuitPatching,
    SampleContainment,
    BloomPurging,
    FieldProcedure
};

UENUM(BlueprintType)
enum class EActivityMechanic : uint8
{
    /** Chooses a grounded default from Type. */
    Automatic,
    Timed,
    GenomeSequence,
    CableMatching,
    OrderedAssembly,
    DiagnosticSequence,
    ToolPath
};

UENUM(BlueprintType)
enum class EPlayerActivityState : uint8
{
    Idle,
    Active,
    Completed,
    Failed,
    Cancelled
};

UENUM(BlueprintType)
enum class EActivityInput : uint8
{
    Primary,
    Secondary,
    Tertiary,
    Quaternary
};

UENUM(BlueprintType)
enum class EActivityProcedurePhase : uint8
{
    Prepare,
    Diagnose,
    Repair,
    Balance,
    Verify
};

USTRUCT(BlueprintType)
struct FPlayerActivityDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    EPlayerActivityType Type = EPlayerActivityType::Scan;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    EActivityMechanic Mechanic = EActivityMechanic::Automatic;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    FText DisplayName;

    /** Time activities fill continuously. Rewire activities instead use InputSequence. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="0.1"))
    float DurationSeconds = 3.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    bool bLockMovement = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    bool bCancelWhenOutOfRange = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="50.0"))
    float MaxRange = 300.0f;

    /**
     * Sustained noise while this activity runs, on the stealth system's abstract 0..1 scale.
     * Defaults to a moderate value: shipboard work is audible but not as loud as a weapon, so
     * repairing under pressure is a real risk without being suicidal. Set to 0 for silent work
     * such as reading a terminal.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity|Stealth", meta=(ClampMin="0.0", ClampMax="1.0"))
    float WorkNoiseLoudness = 0.45f;

    /** Ordered inputs for a discrete mini-game. Empty means the activity is time based. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    TArray<EActivityInput> InputSequence;

    /** Generated puzzle length when InputSequence is empty. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="1", ClampMax="16"))
    int32 PuzzleSteps = 5;

    /** Number of incorrect selections allowed before the activity fails. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="1", ClampMax="10"))
    int32 AllowedMistakes = 3;

    /** Maximum normalized distance from a welding seam before progress pauses. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="0.05", ClampMax="1.0"))
    float ToolPathTolerance = 0.22f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity")
    bool bBloomSensitive = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="0.0", ClampMax="2.0"))
    float BloomInterferenceScale = 1.0f;

    /** Scenario-authored minimum, used when a local target is already compromised. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Activity", meta=(ClampMin="0.0", ClampMax="1.0"))
    float MinimumBloomInterference = 0.0f;
};

USTRUCT(BlueprintType)
struct FPlayerActivitySnapshot
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    EPlayerActivityState State = EPlayerActivityState::Idle;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    EPlayerActivityType Type = EPlayerActivityType::Scan;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    FText DisplayName;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float Progress = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    int32 CurrentInputIndex = 0;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    int32 TotalInputs = 0;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    EActivityInput ExpectedInput = EActivityInput::Primary;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    EActivityMechanic Mechanic = EActivityMechanic::Timed;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    int32 Mistakes = 0;

    /** Confirmed cable pairs; suitable for driving positive connection lights. */
    UPROPERTY(BlueprintReadOnly, Category="Activity")
    int32 PositiveConnections = 0;

    /** -1..1 tool displacement from the ideal welding seam. */
    UPROPERTY(BlueprintReadOnly, Category="Activity")
    FVector2D ToolOffset = FVector2D::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float ToolAccuracy = 1.0f;

    /** Normalized Bloom disruption applied to this session. */
    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float BloomInterference = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    EActivityProcedurePhase ProcedurePhase = EActivityProcedurePhase::Prepare;

    /** Shared consumable budget; interpreted as reagent for scans and repair stock for panels. */
    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float ConsumablePercent = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float ConfidencePercent = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float Voltage = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float CurrentAmps = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    float LoadPercent = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    bool bContinuityPassed = false;

    UPROPERTY(BlueprintReadOnly, Category="Activity")
    bool bOverload = false;
};
