# Unreal Asset and Blueprint Pipeline

Use this guide when adding project-specific assets, Blueprint actors, widgets, data assets, materials, effects, and maps for **Ginnungagap**.

## Art direction baseline

Ginnungagap should lean into grounded industrial sci-fi survival horror: practical ships, tactile hardware, lived-in rooms, pressure suits, analog controls, and hostile alien biology. Use the tone of shows like **The Expanse** and films like **Aliens** as a high-level inspiration point for believability, utility, danger, and claustrophobia, but do **not** copy protected ships, logos, creatures, props, character designs, or screen graphics directly.

Design pillars for new assets:

- **Practical hard sci-fi:** Assets should look engineered for vacuum, low gravity, maintenance access, thermal control, radiation shielding, and emergency repair.
- **Used future:** Surfaces should have scuffs, labels, patch plates, grime, heat staining, hazard paint, worn handles, visible fasteners, and repair history.
- **Industrial readability:** Silhouettes, color accents, cables, piping, vents, and access panels should communicate function before decoration.
- **Claustrophobic survival horror:** Rooms, corridors, lighting, VFX, and audio should support tension with tight sightlines, flicker, condensation, alarms, and contaminated spaces.
- **Alien contamination:** Bloom-infected variants can use asymmetry, wet organic material, spores, tendrils, calcified growth, and intrusive shapes layered over human industrial forms.
- **Legally distinct references:** Mood references are allowed; direct replicas of recognizable IP elements are not.

Suggested palette and material language:

- Base materials: off-white composite panels, gunmetal, dark rubber, brushed steel, ceramic heat shielding, translucent polymer, dirty glass, and worn canvas.
- Accent colors: safety orange, muted red, desaturated blue, medical green, warning yellow, and low-saturation faction colors.
- Lighting: harsh utility fluorescents, emergency red, amber caution strips, cold monitor glow, helmet beams, and sparse volumetric fog.
- UI: compact, functional, high-contrast interfaces with diagnostic charts, oxygen/pressure readouts, ship schematics, and terse warning language.

## Starting content layout

New authored content should go under `Content/Assets` unless it already belongs to a more specific shipped template folder.

| Folder | Use |
| --- | --- |
| `Content/Assets/Blueprints` | Gameplay Blueprint actors, Blueprint components, Blueprint interfaces, animation Blueprints, and child Blueprints of C++ classes. |
| `Content/Assets/Data` | Data assets, data tables, curves, tuning records, and asset briefs. |
| `Content/Assets/Materials` | Master materials, material instances, functions, and material parameter collections. |
| `Content/Assets/Meshes` | Static meshes, skeletal meshes, collision meshes, sockets, and mesh-only test assets. |
| `Content/Assets/Textures` | Source textures imported into Unreal, masks, trim sheets, packed maps, and UI texture atlases. |
| `Content/Assets/UI` | Widget Blueprints, HUD assets, UI materials, icons, and menu prototypes. |
| `Content/Assets/VFX` | Niagara systems, emitters, fluids, flipbooks, and VFX-only materials. |
| `Content/Assets/Audio` | Sound waves, cues, metasounds, attenuation, and mix assets. |
| `Content/Assets/Maps` | Prototype maps, feature test maps, lighting test maps, and asset showcase maps. |

## Naming conventions

Prefer Unreal-style prefixes so assets remain searchable in the Content Browser:

- `BP_` for Blueprint actors and components.
- `BPI_` for Blueprint interfaces.
- `WBP_` for Widget Blueprints.
- `DA_` for Data Assets.
- `DT_` for Data Tables.
- `M_`, `MI_`, and `MF_` for materials, material instances, and material functions.
- `SM_` and `SK_` for static and skeletal meshes.
- `T_` for textures.
- `NS_` and `NE_` for Niagara systems and emitters.
- `S_`, `SC_`, and `MS_` for sound waves, sound cues, and metasounds.
- `L_` for maps and levels.

Example: `DA_ShipSystem_CryoPod_Brief`, `BP_ShipSystem_CryoPod`, `SM_CryoPod_Blockout`, `MI_CryoPod_Prototype`.

## Blueprint-first workflow

1. Create a planning record in `Content/Assets/Data` with **Miscellaneous > Data Asset > Ginnungagap Asset Definition**.
2. Fill out the creative brief, design pillars, theme tags, reference notes, target folder, expected primary asset, implementation notes, and acceptance checklist.
3. Build the first playable version as a Blueprint or Widget Blueprint in the matching `Content/Assets` subfolder.
4. Reference existing C++ systems when possible, especially ship systems, pickups, equipment, Bloom corruption, hazards, and UI widgets.
5. Keep placeholder meshes and materials explicitly named with `Blockout`, `Prototype`, or `Temp` until they are replaced.
6. When the asset becomes gameplay-ready, update its asset definition status and point `PrimaryAsset` at the finished Blueprint, mesh, widget, or system.

## Recommended first assets

Good first candidates for this project are:

- `BP_ShipRoom_Blockout` using modular walls, doors, lighting, hazard sockets, overhead piping, cable trays, and pressure bulkheads.
- `BP_InteractableTerminal` as a general ship-console Blueprint with diagnostic readouts, worn controls, warning lamps, and emergency override states.
- `WBP_SystemStatusCard` for showing oxygen, navigation, sensors, jump drive, pressure, radiation, and corruption state in a utilitarian interface style.
- `DA_AssetBrief_*` records for each planned creature, room kit, ship console, pickup, suit prop, equipment item, and UI panel.
- `NS_BloomSpores_Prototype` for Bloom infection mood and environmental feedback using drifting spores, condensation, and organic motes.
- `SM_ModularBulkhead_*` blockout pieces for cramped corridors, airlocks, maintenance shafts, and decompression doors.

## Definition of done for a new asset

An asset is ready to commit when:

- It is saved under the appropriate `Content/Assets` folder.
- It follows the naming prefixes above.
- It has a `DA_` asset definition if it needs design/art tracking.
- It includes theme tags and reference notes that keep it aligned with grounded industrial sci-fi survival horror.
- It opens in the editor without missing references.
- It has collision, LOD, material, input, and UI notes where applicable.
- Any required C++ or config changes compile or are documented in the PR testing notes.
