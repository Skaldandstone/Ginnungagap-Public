# Ship Production Vertical Slice

The Small Utility Escort exterior Unreal production review is tracked in
[`SmallEscortExteriorProductionReview.md`](SmallEscortExteriorProductionReview.md). The imported review assembly is scale-approved; its material-preserving Nanite merge and tangent cleanup remain the shipping optimization gate.

This vertical slice converts the approved ship concepts into reusable Unreal content rather than one-off level geometry.

## Generated content

Run `tools/build_ship_production_assets.py` through Unreal Editor Python. It creates:

- 14 reusable static meshes under `/Game/Assets/Ships/Production/Meshes`.
- 7 physically based prototype materials under `/Game/Assets/Ships/Production/Materials`.
- `L_Small_Companionway_Showcase` under `/Game/Assets/Maps/ShipProduction`.
- `L_Medium_ExpressSpine_Showcase` under `/Game/Assets/Maps/ShipProduction`.
- `L_Large_CarrierConcourse_Showcase` under `/Game/Assets/Maps/ShipProduction`.

The kit includes floor, ceiling, wall, pressure-bulkhead, and structural-rib modules plus terminals, cargo crates, oxygen bottles, crash seats, lockers, life-support scrubbers, power junctions, pipes, and light fixtures.

## Scale and grid

- Unreal unit: 1 cm.
- Base construction grid: 400 cm.
- Small representative corridor: 12 m wide, 52 m long, 4.3 m high.
- Medium representative express spine: 32 m wide, 72 m long, 7.6 m high.
- Large representative concourse: 48 m wide, 92 m long, 12 m high.

These maps validate modular scale and lighting. They are room-scale vertical slices inside the much larger 1.4 km, 2.4 km, and 6.5 km ships; production levels should be streamed as isolated districts rather than rendered as a single contiguous interior.

## Next production passes

1. Replace prototype geometry with authored Nanite meshes and trim-sheet UVs.
2. Add Blueprint variants for doors, terminals, lights, vents, and Bloom-corruptible machinery.
3. Add Lumen lighting, audio zones, decals, fog, VFX, and damage-state variants.
4. Assemble playable district maps with World Partition or level instances.
5. Add navigation, encounters, pressure simulation, loot, objectives, and performance budgets.

## Interactive fixture pass

`tools/build_ship_interactive_assets.py` creates six reusable Blueprint actors under
`/Game/Assets/Ships/Production/Blueprints` and places a validation set in every showcase map:

- Animated production pressure bulkhead using the existing pressure-transfer behavior.
- Toggleable wall terminal.
- Emergency light.
- Ventilation control.
- Purge station.
- Bloom-corruptible machinery fixture.

All fixtures participate in ship power and Bloom corruption state. Their native components,
events, materials, collision, status lighting, and interaction behavior are exposed to Blueprint.

## Damage, atmosphere, and Bloom pass

`tools/build_ship_environment_assets.py` creates an environment-state controller, eight
authored presets, and a live runtime Blueprint. The live controller subscribes to the global
Bloom stage and the containing ship section's damage state, driving growth visibility, alarms,
lighting, fog, post-processing, decals, and spatial ambience without replacing the art presets.

`tools/validate_ship_playable_maps.py` performs a fail-fast content check across all three
districts, including gameplay anchors, interactive fixtures, and live environment bindings.
Blueprint presets: Clean, Alert, Damaged, Colony, Swarm, Puppeteer, Infector, and Manifestation.
Each preset drives movable state lights, volumetric fog, post-processing, spatial ambience,
damage decals, and escalating Bloom growth meshes. Three synthetic looping source ambiences are
imported as native SoundWave assets for ship hum, alarms, and Bloom presence. Lumen GI,
Lumen reflections, virtual shadow maps, mesh distance fields, and DX12 are enabled project-wide.

## Playable district pass

`tools/build_ship_playable_districts.py` turns each showcase into a gameplay-ready district. It
adds a scale-specific gameplay director, deterministic enemy and pickup seeding, a registered
mission objective, an interactive completion console, checkpoint trigger, pressure/contamination
section, player navigation bounds, and scale-specific performance-budget Data Assets.

District checkpoints persist the map, respawn transform, completed objective IDs, and Bloom
stage in `GinnungagapShipCheckpoint`. On district load the gameplay director restores the player
and world state; after death the survival character revives at the saved checkpoint without
paying objective rewards twice. A missing or mismatched checkpoint falls back to the original
player spawn transform.

The packaged build starts directly in the Small Utility Escort district. Each map contains an
interactive transit console that unlocks when required objectives are resolved and cycles to the
next ship class: Small Utility Escort → Medium Military Corvette → Large Expedition Carrier →
Small Utility Escort. Checkpoint data remains intact across travel and only restores when its
district is active.

The Small Utility Escort is the canonical playable demo. Its district director also spawns life
support, collector/resource, sensor, helm, jump-console, cryo, escape-pod, and self-destruct
stations inside the authored companionway. The demo jump console uses an opt-in native fallback
that selects the first generated destination because a full destination-picker UI is not yet
authored. Production maps suppress `AProceduralShipBuilder`, preventing the procedural corvette
from overlapping the production environment.

Budgets deliberately apply per streamed district rather than per kilometer-scale ship. Full ships
must be assembled from isolated level instances or World Partition cells so only nearby districts
are resident and simulated.

## Fitted modular-room pass

`tools/fit_modular_rooms_to_ship_levels.py` partitions the three production districts into fitted
`AModularShipRoom` actors while preserving the original showcase kit, lighting, fixtures, and
district-wide environment controller. Generated actors use the `ModularFit_` label prefix so the
pass is deterministic and safe to rerun.

- Small Utility Escort: 4 rooms across the 52 m companionway.
- Medium Military Corvette: 6 rooms across the 72 m express spine.
- Large Expedition Carrier: 8 rooms across the 92 m concourse.

The pass installs production pressure bulkheads and tiled pressure-wall partitions, assigns stable
room codes and functional archetypes, authors reciprocal navigation/atmosphere links, and disables
navigation registration on the legacy aggregate pressure section. The aggregate actor remains in
the map for backward-compatible environment and district references.

## Cook validation

The three playable maps are listed explicitly in `Config/DefaultGame.ini` packaging settings.
Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/cook_ship_districts.ps1`
to perform a focused Windows cook with local shader compilation. The process-scoped bypass is
needed on machines that disable direct PowerShell scripts; it does not change system policy. The
script avoids distributed-XGE fallback deadlocks and writes its complete result to
`Saved/Logs/ShipDistrictCook.log`.

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/package_ship_districts.ps1`
to build, cook, stage, IoStore-package, compress, and archive a standalone Windows Development
build. Pass `-Configuration Shipping` for a release package. Output defaults to
`Builds/ShipDistricts-Windows-<Configuration>` and includes all three playable districts.

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
tools/smoke_test_packaged_ship_districts.ps1` after packaging. It launches the archived executable
headlessly against each district, requires a successful map-load confirmation, rejects runtime
error/fatal log entries, and writes per-map logs beside the package.
