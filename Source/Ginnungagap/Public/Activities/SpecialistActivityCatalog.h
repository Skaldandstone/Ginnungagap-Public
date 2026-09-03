#pragma once

#include "CoreMinimal.h"
#include "Activities/FieldActivityCatalog.h"
#include "SpecialistActivityCatalog.generated.h"

/** One hundred specialist procedures, grouped in ten disciplines of ten. */
UENUM(BlueprintType)
enum class ESpecialistActivityPreset : uint8
{
    InjectorCleaning UMETA(DisplayName="Clean propellant injector"),
    CombustionChamberInspection UMETA(DisplayName="Inspect combustion chamber"),
    EngineNozzleAlignment UMETA(DisplayName="Align engine nozzle"),
    TurbopumpService UMETA(DisplayName="Service turbopump"),
    IgnitionCircuitTest UMETA(DisplayName="Test ignition circuit"),
    PropellantMixtureBalancing UMETA(DisplayName="Balance propellant mixture"),
    FeedPressureRegulation UMETA(DisplayName="Regulate propellant feed pressure"),
    ThrustVectorActuatorService UMETA(DisplayName="Service thrust-vector actuator"),
    ExhaustSensorCalibration UMETA(DisplayName="Calibrate exhaust sensor"),
    EngineControllerRecovery UMETA(DisplayName="Recover engine controller"),

    FrameCrackAssessment UMETA(DisplayName="Assess frame crack"),
    BulkheadBracing UMETA(DisplayName="Brace pressure bulkhead"),
    DeckPlateReplacement UMETA(DisplayName="Replace deck plate"),
    ViewportSealRepair UMETA(DisplayName="Repair viewport seal"),
    HatchHingeAlignment UMETA(DisplayName="Align hatch hinges"),
    ShockMountReplacement UMETA(DisplayName="Replace shock mount"),
    ExpansionJointService UMETA(DisplayName="Service expansion joint"),
    PressureSeamInspection UMETA(DisplayName="Inspect pressure seam"),
    ArmorBoltRetorquing UMETA(DisplayName="Retorque armor bolts"),
    StructuralUltrasoundScan UMETA(DisplayName="Run structural ultrasound"),

    OxygenGeneratorService UMETA(DisplayName="Service oxygen generator"),
    CarbonScrubberBedChange UMETA(DisplayName="Change carbon scrubber bed"),
    PotableWaterAssay UMETA(DisplayName="Assay potable water"),
    GreywaterPumpService UMETA(DisplayName="Service greywater pump"),
    HumidityCondenserCleaning UMETA(DisplayName="Clean humidity condenser"),
    ThermalLoopBalancing UMETA(DisplayName="Balance habitat thermal loop"),
    CabinPressureCalibration UMETA(DisplayName="Calibrate cabin-pressure sensor"),
    AirQualitySampling UMETA(DisplayName="Sample cabin air quality"),
    EmergencyOxygenDeployment UMETA(DisplayName="Deploy emergency oxygen"),
    WasteSeparatorService UMETA(DisplayName="Service waste separator"),

    WoundIrrigation UMETA(DisplayName="Irrigate traumatic wound"),
    BurnDressingApplication UMETA(DisplayName="Apply burn dressing"),
    RadiationMedicationDosing UMETA(DisplayName="Dose radiation medication"),
    IntravenousLinePriming UMETA(DisplayName="Prime intravenous line"),
    AirwayClearance UMETA(DisplayName="Clear patient airway"),
    VitalSensorPlacement UMETA(DisplayName="Place vital sensors"),
    QuarantineExamination UMETA(DisplayName="Perform quarantine examination"),
    ProstheticFitting UMETA(DisplayName="Fit emergency prosthetic"),
    MedicalScannerCalibration UMETA(DisplayName="Calibrate medical scanner"),
    PharmacyDispenserRepair UMETA(DisplayName="Repair pharmacy dispenser"),

    TelescopeFocusing UMETA(DisplayName="Focus observation telescope"),
    SpectrometerCalibration UMETA(DisplayName="Calibrate spectrometer"),
    CentrifugeBalancing UMETA(DisplayName="Balance laboratory centrifuge"),
    MassAnalyzerTuning UMETA(DisplayName="Tune mass analyzer"),
    GenomeSequencerPreparation UMETA(DisplayName="Prepare genome sequencer"),
    SampleFreezerRecovery UMETA(DisplayName="Recover sample freezer"),
    CleanBenchSterilization UMETA(DisplayName="Sterilize clean bench"),
    GravimeterCalibration UMETA(DisplayName="Calibrate gravimeter"),
    MagnetometerAlignment UMETA(DisplayName="Align magnetometer"),
    SeismometerDeployment UMETA(DisplayName="Deploy seismometer"),

    AccessPanelHardening UMETA(DisplayName="Harden door access panel"),
    SecurityCameraCleaning UMETA(DisplayName="Clean security-camera optics"),
    LaserTripwireAlignment UMETA(DisplayName="Align laser tripwire"),
    TurretMagazineLoading UMETA(DisplayName="Load turret magazine"),
    StunWeaponCharging UMETA(DisplayName="Charge stun weapon"),
    BrigLockInspection UMETA(DisplayName="Inspect brig lock"),
    SecureRadioPairing UMETA(DisplayName="Pair secure radio"),
    PatrolDroneProgramming UMETA(DisplayName="Program patrol drone"),
    PerimeterAlarmTesting UMETA(DisplayName="Test perimeter alarm"),
    IdentityChallengeVerification UMETA(DisplayName="Verify identity challenge"),

    PalletRestraintInspection UMETA(DisplayName="Inspect pallet restraints"),
    CraneCableService UMETA(DisplayName="Service cargo-crane cable"),
    MagneticClampCalibration UMETA(DisplayName="Calibrate magnetic cargo clamp"),
    ManifestReconciliation UMETA(DisplayName="Reconcile cargo manifest"),
    HazardousCargoLabeling UMETA(DisplayName="Label hazardous cargo"),
    CryogenicCargoCheck UMETA(DisplayName="Check cryogenic cargo"),
    LivestockPodService UMETA(DisplayName="Service livestock pod"),
    FuelContainerInspection UMETA(DisplayName="Inspect fuel container"),
    CenterOfMassCalculation UMETA(DisplayName="Calculate cargo center of mass"),
    CargoAirlockPreparation UMETA(DisplayName="Prepare cargo airlock"),

    RoverWheelReplacement UMETA(DisplayName="Replace rover wheel"),
    PortableDrillService UMETA(DisplayName="Service portable sample drill"),
    CaveBeaconDeployment UMETA(DisplayName="Deploy cave beacon"),
    ClimbingAnchorTesting UMETA(DisplayName="Test climbing anchor"),
    FieldShelterDeployment UMETA(DisplayName="Deploy field shelter"),
    WeatherStationSetup UMETA(DisplayName="Set up weather station"),
    SeismicChargeArming UMETA(DisplayName="Arm seismic survey charge"),
    RouteMarkerPlacement UMETA(DisplayName="Place route marker"),
    IceProbeOperation UMETA(DisplayName="Operate subsurface ice probe"),
    ReturnCacheSecuring UMETA(DisplayName="Secure expedition return cache"),

    AntennaPhaseMatching UMETA(DisplayName="Match antenna phase"),
    LaserCommunicatorAlignment UMETA(DisplayName="Align laser communicator"),
    RadioEncryptionLoading UMETA(DisplayName="Load radio encryption"),
    PacketRouterRecovery UMETA(DisplayName="Recover packet router"),
    RepeaterDeployment UMETA(DisplayName="Deploy signal repeater"),
    TrunkCableSplicing UMETA(DisplayName="Splice communications trunk"),
    SignalTriangulation UMETA(DisplayName="Triangulate unknown signal"),
    EmergencyChannelClearing UMETA(DisplayName="Clear emergency channel"),
    CommunicationsBuoySetup UMETA(DisplayName="Configure communications buoy"),
    TelemetryRecorderRecovery UMETA(DisplayName="Recover telemetry recorder"),

    BloomTissueClassification UMETA(DisplayName="Classify Bloom tissue"),
    SporeTrapServicing UMETA(DisplayName="Service Bloom spore trap"),
    TendrilSevering UMETA(DisplayName="Sever invasive tendril"),
    NeuralNoiseFiltering UMETA(DisplayName="Filter Bloom neural noise"),
    MimicResponseTesting UMETA(DisplayName="Test suspected mimic response"),
    CorruptionBoundaryIsolation UMETA(DisplayName="Isolate corruption boundary"),
    OrganicValveRemoval UMETA(DisplayName="Remove organic valve growth"),
    BroodSignalDetection UMETA(DisplayName="Detect brood signal"),
    PheromoneMaskPreparation UMETA(DisplayName="Prepare pheromone mask"),
    ManifestationAnchorPurge UMETA(DisplayName="Purge manifestation anchor")
};

/** Five execution contexts turn each of the 100 procedures into a distinct playable implementation. */
UENUM(BlueprintType)
enum class ESpecialistProcedureVariant : uint8
{
    Training UMETA(DisplayName="Training / assisted"),
    Nominal UMETA(DisplayName="Nominal operations"),
    Emergency UMETA(DisplayName="Time-critical emergency"),
    EVA UMETA(DisplayName="EVA / pressure-suit work"),
    BloomCompromised UMETA(DisplayName="Bloom-compromised")
};

USTRUCT(BlueprintType)
struct FSpecialistImplementationDescriptor
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    int32 ImplementationId = 0;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    ESpecialistActivityPreset Procedure = ESpecialistActivityPreset::InjectorCleaning;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    ESpecialistProcedureVariant Variant = ESpecialistProcedureVariant::Nominal;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    FText DisplayName;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    float DurationSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    int32 PuzzleSteps = 0;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    int32 AllowedMistakes = 0;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    float ToolPathTolerance = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    float BloomInterferenceScale = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category="Specialist Activity")
    float MinimumBloomInterference = 0.0f;
};

UCLASS(Blueprintable)
class GINNUNGAGAP_API ASpecialistActivityStation : public AFieldActivityStation
{
    GENERATED_BODY()

public:
    ASpecialistActivityStation();
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Specialist Activity")
    ESpecialistActivityPreset SpecialistPreset = ESpecialistActivityPreset::InjectorCleaning;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Specialist Activity")
    ESpecialistProcedureVariant ProcedureVariant = ESpecialistProcedureVariant::Nominal;

    UFUNCTION(BlueprintCallable, Category="Specialist Activity")
    void ApplySpecialistPreset();

    UFUNCTION(BlueprintPure, Category="Specialist Activity")
    int32 GetImplementationId() const;

    UFUNCTION(BlueprintPure, Category="Specialist Activity")
    FSpecialistImplementationDescriptor GetImplementationDescriptor() const;

    UFUNCTION(BlueprintPure, Category="Specialist Activity")
    static int32 GetTotalImplementationCount() { return 500; }

    UFUNCTION(BlueprintImplementableEvent, Category="Specialist Activity")
    void OnSpecialistProcedureCompleted(ESpecialistActivityPreset CompletedPreset, AActor* AffectedTarget, APawn* Player);

    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
};
