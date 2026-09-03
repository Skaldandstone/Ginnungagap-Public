# Production Tool Recommendation

## Decision

Use **Blender 5.2 LTS for hero modeling and look development, Houdini 22.0.423 for approved procedural ship and room generators, and Unreal Engine 5.8 PCG for assembly, streaming, lighting, interaction, and final validation**.

Start with **GGP-S01 Small Utility Escort**.

This preserves the fastest route to visible quality while preparing the higher-ceiling procedural workflow requested for the fleet. Existing Blender builders can produce and refine the first approved modules immediately. Houdini should then own repeated structural generation, validation, and data mapping. Unreal remains the authority for final assembly and runtime proof.

## Evidence

- Installed Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`, verified as Blender 5.2.0 LTS.
- Installed Unreal: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe`.
- Project engine association: Unreal Engine 5.8.
- Project PCG plugin: enabled in `Ginnungagap.uproject`.
- Existing ship code: `tools/build_small_escort_concept_match.py`, `tools/import_small_escort_unreal.py`, `tools/build_small_escort_operations_district.py`, and multiple Blender room builders.
- The official Houdini Engine for Unreal source is installed project-locally and enabled for Unreal 5.8. It is pinned to Houdini 22.0.423.
- The matching SideFX authoring runtime is not yet installed because the official CLI requires a SideFX-authenticated settings file and explicit EULA acceptance.

## Option comparison

| Option | First playable ship | Procedural fleet ceiling | Current project fit | Decision |
| --- | --- | --- | --- | --- |
| Blender 5.2 LTS + Unreal 5.8 PCG | Fastest | High | Excellent | Use for hero art now |
| Houdini 22.0.423 + Houdini Engine | Moderate setup | Highest | Plugin installed, runtime gated | Use for approved generators |
| Unreal Modeling Mode + PCG only | Fast graybox, slower hero finish | Medium | Good | Use for in-engine adjustment, not source modeling |
| Manual Blender kitbash only | Fast first screenshots | Low | Good | Avoid as the fleet architecture |

## Why this pairing fits the ship architecture

Blender Geometry Nodes can create reusable modifiers over meshes, curves, instances, and point clouds. That maps directly to transverse frame arrays, hull section lofts, room-kit placement, spline-routed utilities, and bounded asymmetry. Blender instances avoid duplicating source geometry while still allowing controlled variation. Asset libraries can hold approved hull, room, engine, prop, and damage modules.

Unreal PCG is designed for iterative procedural content and integrates with World Partition, Data Layers, and HLOD. That maps directly to the seven longitudinal streaming cells, room population, damage variants, Bloom overlays, collision variants, and scalable set dressing defined in the production JSON.

Official references:

- [Blender 5.2 Geometry Nodes introduction](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/introduction.html)
- [Blender 5.2 instance-on-points behavior](https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/instances/instance_on_points.html)
- [Blender 5.2 Asset Libraries](https://docs.blender.org/manual/en/latest/files/asset_libraries/index.html)
- [Unreal Engine 5.8 PCG Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-in-unreal-engine)
- [Unreal Engine 5.8 PCG and World Partition overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-overview)
- [Unreal Engine 5.8 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes)

## GGP-S01 vertical-slice build order

### 1. Measured Blender master

- Adapt `tools/build_small_escort_concept_match.py` to the new production manifest instead of rebuilding from a blank file.
- Move the ship root to the aft engine-base center.
- Preserve +X bow, -X gravity, +Z display-up, and YZ floor planes without export rotation.
- Replace the old symmetric drive layout with the five unequal engine modules in the production JSON.
- Split the ship into seven longitudinal streaming cells aligned to transverse YZ frames.
- Keep broad armor masses and cap exterior greeble coverage at 18 percent.

### 2. Hero interior district

Build one contiguous playable route across three adjacent transverse slabs:

1. Watch CIC
2. Damage Control
3. Cargo Lock

Include one maintenance bypass that uses crawl, vent, and squeeze-gap clearances. Use the remaining Cryo Refuge and Crew Commons as visible but initially inaccessible depth.

### 3. Modular quality pass

- Hero-build the five room silhouettes rather than producing mirrored variants.
- Author three unique landmarks per room before general set dressing.
- Use reusable structural, door, trim, utility, and prop kits with per-room seed exclusions.
- Route power, fluid, data, ventilation, and hidden Bloom paths through named frame sockets.
- Author clean, light-damage, heavy-damage, and Bloom overlays as separate collections.

### 4. Unreal assembly

- Import one static mesh set per streaming cell with separate collision proxies.
- Assemble the ship under `BP_GGP_S01_ShipRoot`.
- Use `PCG_GGP_S01_HullAssembly` for deterministic module placement.
- Use `PCG_GGP_S01_RoomPopulation` for bounded, seeded dressing that excludes duplicate landmark arrangements.
- Use `PCG_GGP_S01_DamageOverlay` for damage and Bloom layers without changing the clean base mesh.
- Assign Exterior, Interior, Damage, Bloom, and VFX Data Layers.
- Build HLODs by selected region and enable Nanite only on eligible opaque static modules.

### 5. Demo acceptance gate

The first ship is demo-ready only after all of these pass in Unreal:

- Player boots visibly land on YZ floor slabs and gravity acceleration is -X.
- Walk, crouch, crawl, vent, and squeeze-gap routes pass with every supported suit profile.
- No room is a mirrored or copy-pasted version of another room.
- Aft engine silhouette remains recognizably asymmetric at near, fleet, and thumbnail distances.
- Three adjacent streaming cells transition without visible holes, duplicate actors, or cross-cell ownership warnings.
- Nanite, collision, HLOD, lighting, memory, and frame-time measurements meet the chosen demo hardware budget.
- Damage and Bloom layers can be enabled independently.
- A Bloom false signal remains visually indistinguishable from a valid clean signal until gameplay reveals it.
- Final editor and packaged-build captures pass visual review. Static validation alone does not satisfy this gate.

## Houdini adoption gate

Houdini Engine is the stronger long-term choice for a generalized ship generator spanning dozens of hulls. Current official SideFX support includes Unreal 5.8, HDAs, Session Sync, Node Sync, PCG integration, static meshes, instancers, splines, collisions, data tables, and baked Unreal outputs. Authoring HDAs still requires an appropriate Houdini authoring product and procedural design ownership.

Begin the first HDA only after the revised GGP-S01 concepts and production packet are approved. The first scope is hull partition lofting, transverse frame generation, collision, sockets, room envelopes, and utility spline routing. Keep room art direction, hero modeling, material look development, and final Unreal assembly in Blender and Unreal unless Houdini demonstrates a measured iteration benefit.

See `docs/HoudiniEngineSetup.md` for the verified installation state, account-safe CLI handoff, and first-session validation.

- [Houdini Engine for Unreal introduction and UE 5.8 compatibility](https://www.sidefx.com/docs/houdini/unreal/intro.html)
- [Houdini Engine for Unreal and Unity licensing](https://www.sidefx.com/products/houdini-engine/)
