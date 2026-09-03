# Shared Pressure Suit V25 Implementation

The production-reference sheets dated 2026-08-29 are the visual and technical authority. Earlier monolithic player-suit meshes are retained only as historical rollback sources.

## Build order

1. Author the Medium/Standard shared soft suit and rigid modules against the UE5 MetaHuman-compatible fit source.
2. Keep Science, Engineering, Medical, and Security/Recovery equipment as removable role kits. Role selection must not alter the shared base silhouette.
3. Grade the approved MS source to CN, CS, CB, MN, MB, TN, TS, and TB. Each profile requires at least 2.5 cm module clearance.
4. Validate shoulder, elbow, chest-side, inner-thigh, knee, and glove deformation before generating LODs.
5. Import into Unreal only after neutral, crouch, vent crawl, sideways squeeze, ladder, zero-g, and damaged-door clearance passes.

## Asset boundaries

- `SHARED_SOFT_SUIT` deforms with the character skeleton.
- `SHARED_RIGID` contains collar, helmet, chest frame, backpack, forearm modules, knee shells, cuffs, boots, and harness hardware.
- `SHARED_HOSES_EXACTLY_TWO` contains the two collar-to-pack hose splines.
- `ROLE_*` collections contain removable role equipment only.
- `SOCKETS` contains role-neutral attachment points.

Rigid modules must not be weight-painted as soft garment. The clear helmet is a shared pressure enclosure, not a role helmet. The character head remains a separate MetaHuman character-creator component.

## Current acceptance state

The first MS authoring source is a production block-in for proportion, modularity, materials, fit, and role-kit review. It is not runtime-ready until nine-profile grading, deformation QA, LOD generation, and Unreal import validation pass.
