#pragma once

#include "CoreMinimal.h"
#include "Activities/ActivityStation.h"
#include "FieldActivityCatalog.generated.h"

UENUM(BlueprintType)
enum class EFieldActivityPreset : uint8
{
    TetherAnchorInstall, HullInspection, MicrometeorPatch, AntennaDeployment, SolarPanelCleaning,
    RadiatorDeployment, DebrisCutting, CargoLatch, AirlockSealTest, ThrusterPodService,
    FuseReplacement, PumpPriming, ValveAlignment, BearingLubrication, FilterBackflush,
    ConduitBracing, VibrationDamping, HeatExchangerFlush, PressureTesting, GeneratorSynchronization,
    BusDiagnostics, GroundFaultIsolation, CommsTuning, NavigationBeaconAlignment, DataCoreRecovery,
    RelayReplacement, LightingCircuitRestore, SensorMastDeployment, TransponderConfiguration, EmergencyBeaconActivation,
    SampleSwabbing, MicroscopyFocus, CultureIsolation, RadiationAssay, AtmosphericSampling,
    MineralAnalysis, ContaminationMapping, QuarantineSetup, SterilizerCycle, BloomGrowthExcision,
    HemorrhageControl, FractureSplinting, OxygenMaskFitting, AntidoteCompounding, DefibrillatorCharging,
    SuitOxygenRefill, RationPreparation, CargoInventory, SalvageDisassembly, RescueTetherAttachment,
    StarTrackerCalibration, GyroscopeAlignment, RCSThrusterPurge, FuelLineBleeding, DockingClampSynchronization,
    LandingGearInspection, FlightComputerReboot, CoursePlotVerification, RadarDishTracking, JumpCoilInspection,
    WaterRecyclerService, WasteCompactorClearing, HydroponicsNutrientMix, GrowLightRepair, GalleyHeaterService,
    BunkRestraintRepair, ShowerDrainClearing, CarbonDioxideMonitorTest, ThermalInsulationPatch, HabitatLeakSurvey,
    CratePrying, HullPanelStripping, CableHarnessHarvesting, FuelSiphoning, DataModuleExtraction,
    ReactorMaterialShielding, ArtifactCradleAssembly, WreckBeaconTagging, CargoMassBalancing, SalvageCutPlanning,
    LockBypass, SecurityCameraRestore, TurretIFFConfiguration, ArmoryInventory, AmmunitionFeedClearing,
    BarricadeBracing, MotionSensorDeployment, EvidenceBagging, RestraintApplication, SecurityLogDecryption,
    CasualtyTriage, StretcherSecuring, EmergencyLightingDeployment, AlarmCircuitRestore, EscapePodProvisioning,
    DistressPacketTransmission, FirebreakFoamApplication, RadiationShelterPreparation, EvacuationRouteMarking, BlackBoxRecovery,
    ProspectScanning, DrillAnchorSetting, DrillBitReplacement, OreGradeAssay, FractureMapping,
    MiningChargePlacement, DustSuppressionSetup, ConveyorClearing, OreHopperCalibration, GeologicalCoreSampling,
    CNCToolZeroing, PrintBedLeveling, FeedstockLoading, FurnaceCharging, MoldPreparation,
    CompositeLayup, AdhesiveCuring, FastenerTorqueAudit, DimensionalInspection, ToolSterilization,
    ActuatorCalibration, ServoReplacement, LidarAlignment, ManipulatorTeaching, RobotBatterySwap,
    FirmwareVerification, TrackTensioning, DronePropellerBalancing, CameraGimbalCalibration, AutonomyReset,
    HumidityBalancing, TemperatureSensorCalibration, PressureRegulatorService, OxygenManifoldBalancing, NitrogenPurging,
    CondensateDrainClearing, MicrobialFilterReplacement, AcousticLeakLocation, RadiationShutterTesting, EmergencyVentilationSetup,
    MissionDataUpload, ShiftHandoverVerification, CommandChecklistConfirmation, CrewIdentityEnrollment, AccessCredentialRevocation,
    TacticalMapAnnotation, HazardBriefingConfirmation, ResourceAllocationReview, EvacuationRosterVerification, IncidentReportRecovery
};

UENUM(BlueprintType)
enum class EFieldActivityOutcome : uint8
{
    RecordInspection,
    ImproveOperationalState,
    RepairHull,
    SealBreach,
    RepairElectrical,
    RestorePower,
    RestoreSuit,
    RestoreHealth,
    RestoreOxygen,
    Decontaminate,
    PurgeBloom,
    SecureTarget
};

/** One data-driven actor exposing fifty grounded field procedures. */
UCLASS(Blueprintable)
class GINNUNGAGAP_API AFieldActivityStation : public AActivityStation
{
    GENERATED_BODY()

public:
    AFieldActivityStation();
    virtual void OnConstruction(const FTransform& Transform) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Field Activity")
    EFieldActivityPreset Preset = EFieldActivityPreset::TetherAnchorInstall;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Field Activity")
    bool bUsePresetDefaults = true;

    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Field Activity|Outcome")
    TObjectPtr<AActor> TargetActor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Field Activity|Outcome")
    EFieldActivityOutcome Outcome = EFieldActivityOutcome::ImproveOperationalState;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Field Activity|Outcome", meta=(ClampMin="0.0", ClampMax="1.0"))
    float EffectStrength = 0.25f;

    UPROPERTY(ReplicatedUsing=OnRep_FieldState, BlueprintReadOnly, Category="Field Activity|Outcome")
    float OperationalValue = 0.0f;

    UPROPERTY(ReplicatedUsing=OnRep_FieldState, BlueprintReadOnly, Category="Field Activity|Outcome")
    bool bTargetSecured = false;

    UFUNCTION(BlueprintImplementableEvent, Category="Field Activity")
    void OnFieldProcedureCompleted(EFieldActivityPreset CompletedPreset, AActor* AffectedTarget, APawn* Player);

    UFUNCTION(BlueprintImplementableEvent, Category="Field Activity")
    void OnFieldStateChanged(float NewOperationalValue, bool bSecured);

    UFUNCTION(BlueprintCallable, Category="Field Activity")
    void ApplyPresetDefaults();

    virtual void OnActivityCompleted_Implementation(APawn* Player) override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

private:
    UFUNCTION()
    void OnRep_FieldState();
};
