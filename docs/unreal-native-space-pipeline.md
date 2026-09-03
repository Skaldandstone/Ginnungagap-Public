# Unreal-Native Space Pipeline

Ginnungagap targets Unreal Engine 5.8. Local system visuals are generated around the existing
`AProceduralStarSystemMap`; strategic galaxy placement remains a separate playthrough-level concern.

## Responsibilities

- `CelestialVault`: deep-sky sphere and data-driven fictional star catalog.
- `AProceduralStarSystemMap`: stable system identity, gameplay volumes, bodies, hazards, resources,
  and the root deterministic seed.
- `PCG`: asteroid and large debris placement.
- `Niagara`: radiation, dust, sparse stars, and other particle-scale phenomena.
- `Volumetrics` / volume materials: localized nebula fields.
- Blender: optional source for unique hero meshes only. It does not compose the system scene.
- Twinmotion: optional look-development and hero-environment staging tool. Export approved geometry
  through Datasmith; it does not own procedural system layout or runtime generation.

## Twinmotion bridge

Twinmotion 2026.1 is available locally. The project enables Unreal's `DatasmithImporter`, allowing
Twinmotion scenes to be exported as `.udatasmith` and imported into an isolated staging folder.

- Export into `/Game/Assets/SpaceSystems/TwinmotionStaging/<SceneName>`.
- Prefer Standard export while assets are being iterated; use Optimized only for a locked scene.
- Migrate approved static meshes, textures, and material instances out of staging before runtime use.
- Do not import Twinmotion sky, sun, weather, landscape, cameras, or scene-wide post processing into
  generated system maps. Celestial Vault, Niagara, PCG, and the system visual actor remain authoritative.
- Do not place a complete Datasmith scene actor in a procedural map. Reference approved individual
  assets from PCG graphs or system-specific landmark Blueprints instead.

## Seed contract

After `BuildSystem`, bind a Blueprint visual director to `OnSystemVisualSeedReady`. Use
`GetVisualLayerSeed` with stable names such as `DeepSky`, `CelestialBodies`, `Asteroids`,
`RadiationDust`, and `NebulaVolumes`. Changing one visual layer does not perturb the others.

The system seed derives from persistent system identity. Galaxy coordinates are intentionally not
part of this seed, so a system can move between playthroughs without changing its contents.

`AProceduralStarSystemMap` now owns three reusable native attachment points:

- `AsteroidPCG`: an on-demand PCG component seeded with `Asteroids`.
- `RadiationDustFX`: a Niagara component seeded with `RadiationDust`.
- `NebulaFX`: a Niagara component seeded with `NebulaVolumes`.

Niagara systems receive `User.SystemSeed`, `User.SystemPhenomenon`, and `User.SystemRadiusCm`.
They also receive `User.QualityScale` and `User.ExclusionRadiusCm`.
Assign production PCG/Niagara assets on a Blueprint subclass; `BuildSystem` automatically calls
`RefreshUnrealNativeVisuals`. Unassigned layers remain inactive, making partial authoring safe.

## Ginnos proof setup

1. Place or spawn `AProceduralStarSystemMap` through the existing jump-arrival flow.
2. Add a Celestial Vault actor to the system level and assign a fictional-star Data Table.
3. Create a Blueprint subclass of `AProceduralStarSystemMap` for visual asset assignments.
4. Assign the reusable asteroid graph to `AsteroidPCG`.
5. Assign radiation/dust and nebula systems to their Niagara components.
6. Select nebula material instances by `DominantPhenomenon`; seed their noise offsets with
   `GetVisualLayerSeed("NebulaVolumes")`.
7. Bind optional system-specific landmark logic to `OnSystemVisualSeedReady`.
8. Keep `bUseLegacyCosmicSky` disabled.

The machine-readable profile is `Config/SpaceSystems/Ginnos_UnrealNativePipeline.json`.

## Quality and safety

`VisualQualityTier` supports Low, Medium, High, and Cinematic. Lower tiers consume a stable prefix
of the same deterministic debris sequence, so lowering quality does not reshuffle visible objects.
Low disables the heavier PCG asteroid layer. Niagara receives a quality multiplier for emitter
budgets. Generated debris resamples away from arrival and every hazard/resource/phenomenon point;
`VisualExclusionRadiusCm` defaults to 1.2 km.

The first fictional deep-sky catalog is generated from
`Config/SpaceSystems/GinnungagapFictionalStars.csv`. The Ginnos proof level is
`/Game/Assets/Maps/SpaceSystems/L_Ginnos_UnrealNativeProof`.

## Fab landmark pool

Fab packs feed an optional `Landmarks` seed layer. Each system deterministically selects either no
landmark or one exterior landmark; these assets never influence hazards, resources, or system
identity. The initial pool contains the Alien Portal Blueprint, three Alien Biomass anomaly meshes,
and the complete Sci-Fi Flying Cargo Ship exterior. Spawned landmarks receive a point of interest
and maintain the same safety clearance used by procedural debris.

Ice Station remains staged and is not in the runtime pool because research-habitat interiors are
deferred. `MaterialsScifi` remains a donor library. The machine-readable selection is
`Config/SpaceSystems/FabLandmarkPool.json`.
