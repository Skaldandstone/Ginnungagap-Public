# Ginnungagap Production Reference Manifest

These sheets are inputs for Unreal asset planning. They establish visual and modular intent, not automatically approved dimensions, lore, performance budgets, or final naming.

| Sheet | Intended asset | Authoritative for | Validate before production lock |
| --- | --- | --- | --- |
| `small-utility-escort-production-sheet-v1.png` | Possible shuttle exploration or superseded escort study | Surface grammar, clean/Bloom pairing, detachable-module ideas | Asset identity, canonical 1,400 m escort scale, docking standard, collision, flight pivots |
| `cryo-bay-modular-kit-v1.png` | Modular environment kit | Tile family, cryo-pod variants, snap/pivot intent, state compatibility | Unreal grid, player metrics, trim-sheet plan, kit coverage |
| `pressure-suit-salvage-specialist-v1.png` | Skeletal character plus equipment | Suit silhouette, equipment groups, materials, deformation zones | Character identity, skeleton, gameplay sockets, helmet visibility |
| `bloom-reanimated-crew-v1.png` | Skeletal enemy plus modular growth/VFX | Recognizable suit base, growth zones, animation intent, emissive separation | Enemy behaviors, collision, tendril simulation budget, gore limits |
| `helm-destination-console-v1.png` | Interactive console blueprint and meshes | Tactile control layout, modular units, visual states | Reach envelopes, interaction mapping, screen/UI requirements |
| `eva-salvage-tool-kit-v1.png` | Six first/third-person prop assets | Shared prop grammar, grips, sockets, moving parts, emissive intent | Tool mechanics, hand poses, dimensions, first-person readability |

## Acceptance checklist

- Orthographic views reconcile to one model and one scale.
- Pivots, sockets, collision intent, modular seams, and material slots are documented.
- Clean and Bloom states reuse base construction wherever possible.
- Organic geometry, emissive materials, decals, and VFX can be toggled independently.
- Interaction props include hand pose, reach, holster, and moving-part requirements.
- Environment modules are proven in a small playable graybox before the full kit is authored.
- Character and enemy sheets produce neutral turntables plus representative animation tests.
- Any concept-generated label, dimension, or lore statement is reviewed before entering source-of-truth data.

Generated with OpenAI image generation on 2026-08-28 using the current HUD, companionway, and mechanized-host references. Prompts requested consistent orthographic construction, modular breakdowns, material separation, rig or interaction notes, and clean/Bloom state reuse.

## Machine-readable packets

Each sheet now has a sibling `.production.json` packet validated against
`production-reference.schema.json`. The global `catalog.json`, `UnrealProductionReferences.csv`,
and `concept-art-inventory.json` under `docs/concept-art/production-reference/` provide the current
cross-batch status, handoff index, hashes, dimensions, and packet links. The primary existing
library is `Content/Assets/ConceptArt`.

Run the pipeline from `C:\Users\James\Documents\Unreal Projects\Ginnungagap`:

```powershell
python tools\production_reference_pipeline.py all
```

This historical dated batch:

- 6 visual sheets and 6 production packets

Current global registry after the 2026-08-29 batch:

- 14 production packets
- 282 inventoried concept and production-reference visuals
- 63 visuals in the primary Unreal concept library, with 21 currently linked to packets
- 47 packet-linked visuals overall
- 0 packets marked production-ready
- 7 packets with explicit blocking conflicts

See `docs/ProductionReferencePipeline.md` for Blender and Unreal handoff commands and promotion
rules.
