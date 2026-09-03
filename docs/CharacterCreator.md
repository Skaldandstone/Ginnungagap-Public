# Character creator: body and MetaHuman contract

The character creator opens before the initial cryopod revival. The body page owns physical measurements only; identity, background/world integration, and gameplay attributes remain separate sections.

## Supported body controls

| Control | Range | Simulation consumers |
| --- | ---: | --- |
| Height | 150–210 cm | capsule height, camera height, standing/crouched clearance, overhead reach |
| Shoulder width | 34–58 cm | capsule radius and lateral gap clearance |
| Body depth | 18–38 cm | capsule radius and crawl clearance |
| Body mass | 45–160 kg | Character Movement mass, structural load, inertia, applied-force response |
| Arm span | 0.90–1.10 × height | functional reach only; it does not imply strength |

`FCharacterBodyProfile` is the authoritative simulation record. It exposes standing, crouched, and crawling envelopes and validates `FTraversalRequirement` records. Generated gaps, damaged doors, crawlspaces, ladders, and fragile surfaces should store those requirements on navigation-graph edges.

Every supported profile must retain at least one route to every mandatory objective. Morphology may change shortcuts, risks, or traversal methods, but it may not create a critical-path soft lock.

## Consequence presentation

The creator updates a combined Physical Consequences panel as sliders move. It reports advantages, tradeoffs, and exact simulation values. Consequences describe physical behavior without inferring strength, health, stamina, intelligence, or carrying capacity from appearance.

Threshold language currently uses these bands:

- Compact/tall stature: at or below 162 cm / at or above 190 cm.
- Narrow/broad frame: at or below 40 cm / at or above 51 cm shoulder width.
- Low/high crawl profile: at or below 22 cm / at or above 32 cm body depth.
- Light/heavy mass: at or below 62 kg / at or above 110 kg.
- Reduced/extended arm span: at or below 0.95 / at or above 1.05 height ratio.

The exact pass/fail decision never uses these labels. It compares centimeter and kilogram values directly.

## MetaHuman workflow

MetaHuman Creator is enabled in `Ginnungagap.uproject`. Use its parametric Body Params tool to author visual bodies, record their diagnostics, then assemble game-facing versions with the UE Optimized pipeline.

MetaHuman body fitting is an editor authoring operation. Runtime code must not call editor-only fitting or conform APIs. Instead:

1. Author a representative lattice of body variants in MetaHuman Creator.
2. Record each body's physical measurements in a `UMetaHumanAppearanceCatalog` data asset.
3. Assign its assembled Blueprint (or actor backed by a cooked MetaHuman Instance) to the catalog entry.
4. Assign the catalog to the player character defaults.
5. At runtime, select the closest authored visual body while retaining the player's exact `FCharacterBodyProfile` for collision and simulation.

UE 5.8 MetaHuman Collections and Instances may be used for runtime hair, clothing, accessories, and material overrides. Collections are experimental in 5.8, so they should remain behind the catalog/actor boundary and must never become a dependency of traversal validation or saved physical measurements.

The current fallback primitive body remains active during the cryopod animation until MetaHuman-compatible wake, suit-up, crouch, crawl, and squeeze animation assets are retargeted. The MetaHuman visual is hidden during that sequence to prevent an unanimated body from overlapping the pose rig.

The creator reports both the closest authored fit and the closest assembled runtime body. While the optimized-body batch is incomplete, gameplay uses the nearest available assembled body instead of spawning an empty visual. Collision, gap clearance, load checks, and saved measurements always use the exact selected profile rather than the visual fallback.

## Authoring the first catalog

Create `/Game/Characters/MetaHumans/DA_PlayerMetaHumanCatalog` as a `MetaHumanAppearanceCatalog` data asset. Begin with at least nine bodies covering compact/medium/tall stature crossed with narrow/standard/broad frame. Add light and heavy mass/composition variants where the same geometry cannot represent the selected mass honestly.

Each entry needs a stable `VariantId`, player-facing name, recorded measurements, source MetaHuman Character ID, Body Params preset ID, assembled actor class, and optional portrait. Catalog selection is measurement-based and therefore independent of player-facing labels.

For automated captures or direct gameplay testing, launch with `-SkipCharacterCreator` to use the default profile.
