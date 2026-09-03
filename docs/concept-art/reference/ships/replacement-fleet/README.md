# Replacement Thrust-Tower Fleet

This batch replaces conventional horizontal-deck, mirrored-engine, and copy-pasted room interpretations with the canonical thrust-gravity architecture in `docs/ShipArchitectureAuthority.md`.

## Canonical frame

- +X: bow, floor normal, and away from engines
- -X: aft engine base and gravity-down
- Y: port and starboard
- Z: lateral cross-stack direction, never gravity-down
- Every habitable floor is a transverse YZ slab.
- Canonical stack proofs show +X bow/up-stack above and -X engines/gravity below. Floors sit between occupants and engines.
- Every main-engine centerline is parallel to X and every main nozzle exits on one common aft plane. Main engines cannot cant, splay, or gimbal.
- Room views are locally upright because the floor, fixtures, occupants, and structural load path are authored in the correct thrust-gravity frame.
- Interiors use unique silhouettes, offset doors, unequal alcoves, varied landmarks, and no mirrored room reuse.

## Production set

| Ship | Exterior baseline | Vertical-stack overview | Enlarged room and traversal sheet | Production JSON |
| --- | --- | --- | --- | --- |
| GGP-S01 Small Utility Escort | [Exterior v1](concepts/ggp-s01-small-utility-escort-replacement-concept-v1.png) | [Overview v2](../production-reference/ggp-s01-small-utility-escort-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-s01-small-utility-escort-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-s01-small-utility-escort-thrust-tower-production-v1.production.json) |
| GGP-S02 Small Deep Survey Cutter | [Exterior v2](concepts/ggp-s02-small-deep-survey-cutter-replacement-concept-v2.png) | [Overview v2](../production-reference/ggp-s02-small-deep-survey-cutter-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-s02-small-deep-survey-cutter-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-s02-small-deep-survey-cutter-thrust-tower-production-v1.production.json) |
| GGP-S03 Small Salvage Recovery Tender | [Exterior v2](concepts/ggp-s03-small-salvage-recovery-tender-replacement-concept-v2.png) | [Overview v2](../production-reference/ggp-s03-small-salvage-recovery-tender-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-s03-small-salvage-recovery-tender-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-s03-small-salvage-recovery-tender-thrust-tower-production-v1.production.json) |
| GGP-M01 Medium Military Corvette | [Exterior v1](concepts/ggp-m01-medium-military-corvette-replacement-exterior-v1.png) | [Overview v2](../production-reference/ggp-m01-medium-military-corvette-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-m01-medium-military-corvette-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-m01-medium-military-corvette-thrust-tower-production-v1.production.json) |
| GGP-M02 Medium Research Cruiser | [Exterior v1](concepts/ggp-m02-medium-research-cruiser-replacement-exterior-v1.png) | [Overview v2](../production-reference/ggp-m02-medium-research-cruiser-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-m02-medium-research-cruiser-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-m02-medium-research-cruiser-thrust-tower-production-v1.production.json) |
| GGP-M03 Medium Medical Quarantine Cruiser | [Exterior v2](concepts/ggp-m03-medium-medical-quarantine-cruiser-replacement-exterior-v2.png) | [Overview v2](../production-reference/ggp-m03-medium-medical-quarantine-cruiser-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-m03-medium-medical-quarantine-cruiser-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-m03-medium-medical-quarantine-cruiser-thrust-tower-production-v1.production.json) |
| GGP-L01 Large Expedition Carrier | [Exterior v1](concepts/ggp-l01-large-expedition-carrier-replacement-exterior-v1.png) | [Overview v2](../production-reference/ggp-l01-large-expedition-carrier-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-l01-large-expedition-carrier-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-l01-large-expedition-carrier-thrust-tower-production-v1.production.json) |
| GGP-L02 Large Colony Habitat Ark | [Exterior v1](concepts/ggp-l02-large-colony-habitat-ark-replacement-exterior-v1.png) | [Overview v2](../production-reference/ggp-l02-large-colony-habitat-ark-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-l02-large-colony-habitat-ark-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-l02-large-colony-habitat-ark-thrust-tower-production-v1.production.json) |
| GGP-L03 Large Fleet Logistics Carrier | [Exterior v1](concepts/ggp-l03-large-fleet-logistics-carrier-replacement-exterior-v1.png) | [Overview v2](../production-reference/ggp-l03-large-fleet-logistics-carrier-vertical-stack-room-production-v2.png) | [Expanded v1](../production-reference/ggp-l03-large-fleet-logistics-carrier-enlarged-room-traversal-splines-v1.png) | [JSON v1](../production-reference/ggp-l03-large-fleet-logistics-carrier-thrust-tower-production-v1.production.json) |

Superseded horizontal-hull and v1 overview images remain in place for traceability, but they are not canonical. The production JSON points to the enlarged traversal sheet for room and route data, the v2 overview for engine-bearing production panels, and the dedicated orthographic engine sheet for main-drive geometry.

[Main-engine orthographic geometry authority](../production-reference/ggp-main-engine-orthographic-alignment-authority-v1.png)

## Validation

Run from the canonical Unreal project root in PowerShell:

```powershell
python tools\production_reference_pipeline.py all
python tools\validate_thrust_tower_packets.py
```

The packets remain `ready-for-graybox`, not `production-ready`, until their measured Blender assets and Unreal runtime acceptance checks pass.
