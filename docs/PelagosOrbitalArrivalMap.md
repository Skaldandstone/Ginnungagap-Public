# Pelagos Orbital Arrival Map

Pelagos is a large, ship-scale space arrival map. It replaces the earlier ocean-arrival framing with an orbital station, planet, stellar lighting, debris fields, traffic corridors, docking infrastructure, and explicit jump-arrival gameplay.

## Runtime flow

`UJumpSequenceSubsystem::CompleteArrival` notifies the map-local `APelagosOrbitalArrivalDirector`. On authority, the director runs the replicated sequence:

`JumpExit -> SensorAcquisition -> IFFChallenge -> ControlHandoff -> TrafficContact -> DockRequest -> DockAssignment -> FinalApproach -> SoftCapture -> HardDock -> ServicesAvailable -> ArrivalComplete`

Departure releases the reserved dock and permits a later ship arrival. Dock availability, reservation, occupation, emergency-only state, active route, and arrival phase are authority controlled and replicated.

## Functional map content

- Four arrival routes with 16 route checkpoints
- Four sensor/IFF/control/traffic arrival gates
- Four dock approach volumes and four capture volumes
- Twenty-four traffic spawn anchors
- Ten station service anchors
- Six space-hazard and exclusion volumes
- One imported 87,364-triangle combined environment set with 11 source materials
- Stellar key and low-intensity orbital fill lighting
- Twelve color-coded navigation beacons and four cinematic coverage cameras
- Unbound orbital color-grade volume
- Nanite-enabled environment mesh using complex-as-simple ship collision

## Phase 24 gameplay systems

- `APelagosArrivalGateVolume` turns ship overlaps into authority-controlled arrival, docking, capture, and departure transitions.
- `APelagosHazardVolume` reports entry/exit contacts and applies continuous server-authoritative damage where configured.
- `APelagosTrafficController` enforces the global traffic budget and rotates through 24 authored spawn definitions.
- Six typed hazard definitions and ten typed station-service definitions are stored in the Pelagos Data Asset contract.

The generated Unreal level is `/Game/Assets/Maps/SpaceSystems/L_PelagosOrbitalArrival`.

## Rebuild pipeline

1. Export the Blender environment:

   `blender --background Art/SpaceSystems/SpaceSystems_PelagosOrbitalArrival_Level.blend --python tools/export_pelagos_for_unreal.py -- <project-root>`

2. Compile the `GinnungagapEditor` target so the Pelagos native types are available.

3. Run `tools/build_pelagos_orbital_arrival_assets.py` through Unreal Editor Python.

The asset builder is idempotent: it loads existing generated assets and uses actor tags to avoid duplicating functional anchors.

## Production ledgers

- Phase 22: `Art/SpaceSystems/PelagosImplementation_Phase22_500Steps.json`
- Phase 23: `Art/SpaceSystems/PelagosRealMap_Phase23_500Steps.json`
- Phase 24: `Art/SpaceSystems/PelagosProduction_Phase24_750Steps.json`
- Export manifest: `Art/SpaceSystems/Exports/PelagosOrbitalArrival_ExportManifest.json`

Both ledgers contain exactly 500 implementation entries and are generated from checked-in scripts.
