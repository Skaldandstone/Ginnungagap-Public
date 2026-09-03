# Player activities

The activity framework turns an `IInteractable` press into a cancellable, server-authoritative
gameplay session. `UPlayerActivityComponent` lives on `ACoopSurvivalCharacter` and exposes a
replicated `FPlayerActivitySnapshot` for HUDs and Blueprint presentation.

## Quick prototype

1. Place an `ActivityStation` (or a Blueprint subclass) in a map and give its mesh Visibility
   collision.
2. Choose `Scan`, `Repair`, `Build`, `Rewire`, or `Welding`, set its display name and maximum range.
3. `Automatic` selects the grounded default: genome alignment for Scan, cable matching for Rewire,
   seam tracking for Welding, and timed physical work for Repair/Build. An explicit mechanic can
   override this on specialized stations.
4. Implement `ReceiveActivityCompleted` in the Blueprint to apply the world result: reveal scan
   data, call a `ShipDamageComponent` repair function, spawn/finish construction, or change a
   power node.

During play, `E` starts an activity and supplies input 1, while `F`, `3`, and `4` supply inputs 2–4;
`X` cancels. Mouse/controller look steers a welding tool across its seam. The native survival HUD
displays progress, welding accuracy, matched connections, mistakes, and the expected input. Moving the station
out of range cancels by default, and locked movement is restored to its previous movement mode
after every terminal state.

For bespoke actors, implement both `IInteractable` and `IPlayerActivitySource`. The source owns the
definition and validates whether work can begin; the component owns session state and invokes
`OnActivityCompleted` only on the authority. This preserves `IInteractable` as the single entry
path while allowing each ship system to own its actual gameplay consequence.

## Grounded abstractions

- **Welding:** the seam moves under the tool; progress is proportional to alignment accuracy and
  pauses outside the tolerance. `AWeldableBulkheadDoor` closes first, requires a successful seam,
  then becomes impassable until `CutEmergencyWeld` is called.
- **Bio-scanning:** four inputs stand in for nucleotide/base symbols. Correct alignment advances a
  short generated genome sample; mistakes represent rejected base calls.
- **Rewiring:** the same four-channel language represents labeled cable colors/endpoints. Each
  correct pair increments `PositiveConnections`, intended to drive green panel indicators.
- **Bloom:** its global stage becomes normalized session interference. Higher tiers add puzzle
  steps, introduce seam drift, and at Puppeteer tier or above can break the most recent unconfirmed
  sequence/cable match after an error. The HUD exposes the interference instead of hiding it.

## Maintenance station presets

Ten placeable subclasses provide tuned starting points and apply authoritative outcomes to their
configured `TargetActor`:

| Station | Simplified physical task | Runtime outcome |
|---|---|---|
| `HullPatchingStation` | Keep sealant/tooling aligned across a patch edge | Restores hull integrity |
| `FireSuppressionStation` | Sweep suppressant across the fire base | Reduces fire intensity |
| `PipeSealingStation` | Seat and tighten an emergency pipe clamp | Reduces breach severity |
| `ComponentReplacementStation` | Match replacement connectors | Repairs electrical/component damage |
| `FabricationStation` | Fit recipe parts in order | Produces an inventory item or actor |
| `SensorCalibrationStation` | Hold a waveform on its reference line | Restores sensor signal-path integrity |
| `DecontaminationStation` | Remain through a complete chamber cycle | Purges pathogen load |
| `MedicalStabilizationStation` | Apply a short ordered triage protocol | Restores health and some oxygen |
| `BreakerReroutingStation` | Match cable endpoints and verify continuity | Brings a power node online and repairs it |
| `MechanicalOverrideStation` | Maintain manual crank effort | Toggles a bulkhead mechanically |

Stations optionally require and consume inventory items only after successful completion. This
allows repair compounds, clamps, replacement modules, medical supplies, and fabrication feedstock
to be introduced without changing the activity session code.

## Operations station presets

The second set covers ship operation, field equipment, and containment:

| Station | Compressed procedure | Runtime outcome |
|---|---|---|
| `AirlockRepressurizationStation` | Confirm valve/interlock channels in order | Seals the door and breach |
| `OxygenScrubberServiceStation` | Remove and seat filter-media stages | Restores power and clears corruption |
| `CoolantBalancingStation` | Hold flow against a moving reference | Improves cooling/power-system condition |
| `BatteryRecoveryStation` | Match charging and balancing leads | Recharges and reconnects storage |
| `ReactorStartupStation` | Complete a strict startup checklist | Repairs and starts its generator node |
| `DroneRepairStation` | Restore cable and actuator continuity | Recalls the drone to a docked state |
| `TurretServiceStation` | Service feed components in order | Restores its operational/power state |
| `SuitPatchingStation` | Keep a pressure patch aligned over the tear | Restores suit integrity |
| `SampleContainmentStation` | Follow isolation and seal verification | Marks the sample secured |
| `BloomPurgingStation` | Isolate the organism's active signature | Purges the target and informs BloomDirector |

`OperationalValue` and `bOperationSecured` are replicated fallback state for machinery whose full
simulation has not been authored yet. `OnOperationStateChanged` lets Blueprint visuals, indicator
lights, audio, objectives, and hazards respond immediately without inventing a parallel system.

## One-hundred-and-fifty-procedure field catalog

`AFieldActivityStation` adds one hundred and fifty selectable presets without creating copy-pasted actor
classes. The first fifty cover EVA, engineering, electrical/comms, science/containment, and
medical/logistics. The next fifty add flight/navigation, habitat upkeep, salvage, security, and
emergency response. Each entry supplies its own label, mechanic, duration, sequence length, tool
tolerance, mistake budget, Bloom sensitivity, and completion outcome.

The third fifty add mining/resource extraction, manufacturing, robotics, environmental control,
and command/crew operations. They cover prospecting, drilling and ore handling; CNC/additive,
casting and composite work; actuator, sensor and autonomy maintenance; atmospheric balancing and
leak control; and authenticated mission, shift, access, hazard, resource and evacuation procedures.

The catalog includes tether installation, hull inspection, puncture patching, external deployment
and cleaning, debris cutting, cargo restraint, seal testing, thruster servicing, fuse/relay work,
pump and valve operations, bearing and filter service, conduit/damper/exchanger work, pressure
testing, generator synchronization, bus/fault diagnostics, communications/navigation equipment,
data recovery, lighting and beacons, sample collection and analysis, quarantine and sterilization,
Bloom excision, trauma care, oxygen support, antidote preparation, suit refilling, inventory,
salvage, and rescue tethering.

The second set includes flight instrumentation, RCS/fuel/docking work, jump-coil inspection,
water/waste/hydroponics and habitat upkeep, structured salvage recovery, locks/cameras/IFF and
other security procedures, casualty movement, escape-pod provisioning, distress transmission,
firebreaks, radiation sheltering, evacuation marking, and flight-recorder recovery.

Existing ship components receive direct authoritative changes. Procedures awaiting a dedicated
simulation use replicated `OperationalValue`/`bTargetSecured` state and the typed
`OnFieldProcedureCompleted` Blueprint event. A compile-time assertion keeps the preset table at
exactly one hundred and fifty entries.

## One-hundred-procedure specialist catalog

`ASpecialistActivityStation` adds a second catalog with one hundred named procedures across ten
disciplines: propulsion, structural maintenance, life support, clinical medicine, laboratory
science, security, cargo handling, planetary exploration, communications, and advanced Bloom
response. Together with `AFieldActivityStation`, the project now exposes 250 activity presets.

The specialist actor derives its authoritative completion behavior from the existing field actor,
but owns a separate enum so neither Blueprint selector approaches Unreal's `uint8` enum limit.
Every procedure has a human-readable editor name. Discipline and per-entry position determine its
mechanic, duration, complexity, tolerance, failure budget, effect strength, and outcome. Advanced
Bloom procedures receive amplified interference and route into purge/decontamination outcomes.

`OnSpecialistProcedureCompleted` provides a typed Blueprint hook for procedure-specific animation,
audio, rewards, objectives, and machinery state beyond the common replicated outcome.

## Five-hundred specialist implementations

Every specialist procedure supports five execution variants, producing an exact 100 × 5 matrix:

| Variant | Gameplay interpretation |
|---|---|
| Training | Assisted pace, fewer steps, larger tolerances, five allowed errors, no Bloom noise |
| Nominal | Baseline professional procedure |
| Emergency | Faster target pace, extra verification, tighter tolerance, stronger outcome |
| EVA | Slower suited work, reduced reach, tighter handling, movement locked at the worksite |
| Bloom-compromised | Two extra steps, one allowed error, severe tool drift and forced local interference |

Each configuration has a stable `ImplementationId` (`ProcedureIndex * 5 + VariantIndex`) from 0 to
499. `GetImplementationDescriptor` exposes the resolved label, duration, puzzle size, errors,
tolerance, and interference to Blueprint UI, mission generation, telemetry, and automated tests.
The compromised variant uses `MinimumBloomInterference`, so a locally infected machine remains
hostile even when the global Bloom stage is low.
