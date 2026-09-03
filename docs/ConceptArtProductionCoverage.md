# Concept Art Production Coverage

## Verified coverage

The production-reference inventory currently links 341 of 429 configured visual sources to at
least one machine-readable production packet. The remaining 88 visuals require classification or
packet linkage before full coverage is restored.

| Metric | Verified value |
| --- | ---: |
| Inventoried visual files | 429 |
| Linked visual files | 341 |
| Unlinked visual files | 88 |
| Coverage | 79.5 percent |
| Production-reference packets | 51 |
| Active packets | 47 |
| Superseded packets | 4 |
| Production-ready packets | 0 |

Inventory linkage records explicit production lineage. It does not mean that a concept is approved,
dimensionally reconciled, modeled, rigged, imported, performant, or ready to ship. Current unlinked
visuals remain outside complete production-reference coverage.

## Source collections

The primary concept source is `Content/Assets/ConceptArt`. Supporting collections include:

- `docs/concept-art` design references and approved or rejected visual documentation;
- `Art/Weapons/Concepts` and clean first-use tool references;
- cryopod production iterations and RealityScan turnaround inputs;
- ship concept-match, remaster, and Unreal sculpt-review lineages;
- player-suit concept lock and module references;
- complete space-system production and texture lineage;
- Bloom progression, robot, UI, and review imagery.

Recursive `concept_source_sets` in a production JSON packet link a complete lineage root to exact
per-file inventory records. The source set records its role and lifecycle, such as current
direction, design reference, superseded, review only, or production reference.

## Production systems

The active packets cover:

- companionways, room shell, command, observation, technical, habitat, berthing, life support,
  medical, morgue, suit bay, security, brig, damage control, cryo bay, and the individual cryopod;
- the Small Utility Escort, Medium Military Corvette, Large Expedition Carrier, Wayfarer exterior,
  fleet-class lineage, streaming, sockets, splines, collision, damage, HLOD, and render mapping;
- the shared V25 pressure suit, nine body profiles, traversal and performance, and the canonical
  Science, Engineering, Medical, and Security / Recovery role kits;
- Bloom threat families, the mechanized-host V2 production system and implementation companion,
  corruption progression, combat and zero-g references, animation, tendril splines, VFX intensity,
  damage, LOD, and render layers;
- uncorrupted robot classes, shipboard tools 01 through 40, mapped security and salvage tools 51
  through 80, EVA salvage tools, clean first-use references, unsafe conversions, and xeno quarantine;
- Pelagos orbital arrival plus broader local-operations celestial bodies, phenomena, routes, POIs,
  sensors, volumes, materials, lighting, streaming, and render passes;
- helmet HUD, data and state mapping, shipboard interfaces, main menu, front-end states, antagonist
  versus perspectives, commander, spectator, respawn, accessibility, input, and render isolation.

## Lifecycle rules

Every visual belongs to a packet, but its lifecycle controls how it may be used:

1. Verified runtime configuration and measured imported bounds.
2. Approved current production direction.
3. Current technical review and concept-match evidence.
4. Supporting design reference.
5. Superseded or rejected lineage.
6. Exploration only.

Rejected concepts remain inventoried for provenance. The symmetrical CIC is explicitly marked
`REJECTED, DO NOT BUILD`. V01 and V02 ship remasters and intermediate sculpt-review renders remain
lineage, not final art. Weapon exploration boards do not automatically approve player equipment.
Xeno-hybrid tools 71 through 80 remain quarantined pending narrative and gameplay approval.

## Current authority corrections

- The Small Utility Escort production contract is 1,400 x 260 x 320 m. The 900 x 125 x 250 m
  remaster scale is superseded. `Config/ShipLayout.json` and older approximately 1,150 m text still
  require reconciliation before final promotion.
- The Medium Military Corvette is 2,400 x 430 x 620 m.
- The Large Expedition Carrier is 6,500 x 1,400 x 1,800 m.
- The canonical playable role list is Science, Engineering, Medical, and Security / Recovery.
  Crew is not a class. Technician and Marine remain legacy art aliases for Engineering and
  Security.
- Genuine and false Bloom signals must remain identical in color, icon, copy, severity, pulse,
  sound, opacity, timing, animation, and motion. Normal UI cannot access hidden truth.

## Production readiness

No packet is currently marked production ready. The sheets and JSON define build intent and gates,
not finished artist-level Unreal or Blender assets. Common remaining gates include:

- imported-bounds, scale, pivot, socket, and collision capture;
- graybox and all-nine-body-profile traversal validation;
- first-person, third-person, IK, root-motion, and multiplayer replication tests;
- material, LOD or Nanite, HLOD, World Partition, render, audio, VFX, and performance validation;
- gameplay mapping and explicit approval for exploration, unsafe, xeno, or rejected sources;
- automated UI accessibility and hidden-truth isolation tests.

## Machine-readable outputs

- `docs/concept-art/production-reference/catalog.json`
- `docs/concept-art/production-reference/UnrealProductionReferences.csv`
- `docs/concept-art/production-reference/concept-art-inventory.json`

Run from `C:\Users\James\Documents\Unreal Projects\Ginnungagap`:

```powershell
python tools\production_reference_pipeline.py all
```

The validator checks packet schema, source-sheet hashes and dimensions, required individual sources,
required recursive source sets, expanded implementation maps, duplicate acceptance IDs, catalog
supersession, and exact inventory linkage.
