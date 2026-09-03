# Production Reference Backlog

This order follows the playable-demo gaps in `docs/PRD.md` and the current Linear pointers in
`docs/QueuedWork.md`. A reference packet is complete only when it identifies a buildable Unreal
asset or cohesive modular kit.

## P0: playable demo art

| Order | Asset family | Existing packet | Next reference deliverable | Dependency |
| --- | --- | --- | --- | --- |
| 1 | Helm and destination console | `helm-destination-console-v1.production.json` | Measured graybox, seated and standing reach overlay, control animation map | None |
| 2 | Bloom reanimated crew encounter | `bloom-reanimated-crew-v1.production.json` | Topology zones, exact growth sockets, LOD plan, animation silhouettes, VFX budget sheet | Enemy-count and performance target |
| 3 | Cryo bay and wake area | `cryo-bay-modular-kit-v1.production.json` | Reconciled 6 m grid kit fitted to current shell bounds | Resolve replacement versus dressing kit |
| 4 | Demo companionway and corridor kit | Master plus `ggp01-companionway-spline-socket-render-mapping-v1.production.json` | Measured graybox assembly and runtime spline, snap, navmesh, door, and atmosphere validation | TRO-239 and TRO-243 |
| 5 | Core player pressure suit | V2 master plus body-profile matrix, V2 traversal/performance packet, and Science, Engineering, Medical, and Security / Recovery class packets | Import the V25 base, build all role modules, retarget 29 deliverables across nine profiles, and validate first-person, crawl, squeeze, zero-g, tools, and casualty handling | Final runtime body and skeleton matrix |
| 6 | Captive-bolt and repair activity tools | EVA kit is only partial | One packet per canonical tool with dimensions, grips, clearance, moving parts, VFX and audio sockets | Approve EVA tool ID mapping |
| 7 | Demo room dressing set | `ggp01-modular-interior-room-kit-v1.production.json` | Reusable props, trim sheet, decals, lighting, damage overlays, and placement rules | TRO-244 |
| 8 | Modular helmet HUD | Master plus `ggp01-helmet-hud-data-render-state-mapping-v1.production.json` | UMG build and automated binding, safe-area, accessibility, and false-signal truth-isolation validation | Atmosphere data source for pressure and CO2 |
| 9 | Shipboard and CIC interfaces | `ggp01-shipboard-interface-system-v1.production.json` | Shared UMG component library and measured physical-console reach test | Approved display sizes and viewing distances |

The generated small-utility-escort sheet is not a P0 implementation input until its 18.6 m design
is either reclassified as a shuttle or regenerated for the canonical 1,400 m escort. The older
900 m remaster is also superseded by the current 1,400 x 260 x 320 m production contract.

## P1: reusable production families

1. Bridge and CIC modular station family based on the existing 17 interior sheets.
2. Medical, workshop, engineering, security, habitat, hygiene, and life-support room kits.
3. Uncorrupted maintenance, cargo, security, and utility robot family runtime validation from `ggp01-uncorrupted-robot-family-production-system-v1.production.json`, starting with authoritative imported bounds.
4. Bloom crawler, puppeteer, infested drone, growth, barricade, spore, and hive-node families.
5. Clean ship exterior module and trim-sheet family for all three canonical hull scales.
6. Remaining weapon and shipboard-tool families, split by canonical gameplay definition.
7. Non-Bloom pirate, rebel, and alien faction silhouettes, equipment, materials, and encounter kits.
8. Pelagos docking, service, traffic, and mission-site hero kits.

## Required sheet set by category

### Static prop or tool

- front, side, rear, top, and controlled perspective;
- dimensions and human or glove scale;
- exploded parts, moving parts, pivots, grips, sockets, collision, and holster envelope;
- material slots, emissive and damage states;
- first-person and third-person readability frames.

### Character or enemy

- neutral front, side, back, and perspective;
- exact approved body and skeleton target;
- removable layers, material zones, deformation zones, sockets, and physics elements;
- representative locomotion, interaction, attack, damage, and death silhouettes;
- VFX and secondary-motion layers separated from the base rig.

### Environment or modular room kit

- plan, section, front, side, and human-scale view;
- gameplay grid, art snap increment, pivots, seams, door and traversal clearances;
- modular pieces, trim sheet, material slots, decals, clutter, lighting, and collision;
- clean, damaged, emergency, depressurized, and Bloom compatibility where applicable;
- one measured playable assembly before full kit production.

### Ship or large structure

- reconciled front, side, top, rear, and perspective views at canonical scale;
- streamed module boundaries, pivots, docking interfaces, propulsion, collision, and damage zones;
- close-range surface and far-range silhouette plans;
- clean construction beneath separately controlled Bloom and damage layers;
- Unreal streaming, Nanite, HLOD, lighting, and collision budgets.

## Promotion rule

Mood art may support a packet, but it cannot replace measured orthographics, approved scale, exact
runtime targets, or a validated graybox. A packet stays non-production-ready while any required
field is provisional or any blocker remains open.
