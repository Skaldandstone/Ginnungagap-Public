# Production Reference Pipeline

This pipeline turns concept art into explicit build contracts for Blender and Unreal. It does not
make generated measurements, labels, or mechanical details canonical by itself.

## Source of truth

The primary existing art library is `Content/Assets/ConceptArt`. It must be checked before a new
sheet is generated or a production packet is approved. Supporting sources under `docs/concept-art`,
`Art`, and `Build/RealityScan` preserve design history, production iterations, captures, and
technical reviews. Generated production sheets supplement those sources and do not replace them.

Production reference data uses three authority levels:

1. `approved`: verified project facts that tools may consume.
2. `provisional`: useful design intent that an artist may explore, but automation must not treat as
   locked.
3. `conflicts`: contradictions that must be resolved before the affected build stage can pass.

Every production packet lives beside its visual sheet in a dated
`docs/concept-art/YYYY-MM-DD/production-reference/` batch and uses the suffix `.production.json`.
The shared JSON schema currently lives in
`docs/concept-art/2026-08-28/production-reference/production-reference.schema.json`.

## Packet contents

A full packet records:

- visual sources and SHA-256 hashes;
- asset category, owner, status, and production readiness;
- approved facts, provisional art suggestions, and blocking conflicts;
- units, axes, bounds, pivots, modular parts, materials, sockets, and state variants;
- Blender collection, naming, source, export, and guide information;
- Unreal asset type, destination, source files, existing assets, and import policy;
- acceptance checks and unresolved production questions.

Packets use one of two implementation profiles:

- `core` records the master construction contract.
- `expanded` is a companion or full implementation contract. It must include `metadata` plus
  explicit `rig`, `animation`, `vfx`, `spline_mapping`, `render_mapping`, and `implementation`
  objects. A domain that does not apply still records an explicit reason.

The JSON sidecar is authoritative for exact names, values, mappings, state contracts, and
requirements. The PNG is the visual communication layer and must not be parsed as the engine data
source.

The first normalized batch covers the six existing production sheets. It is a metadata baseline,
not a claim that all six assets are ready for final modeling.

The ordered next-wave list is in `docs/ProductionReferenceBacklog.md`.

## Commands

Working directory for every command below:

`C:\Users\James\Documents\Unreal Projects\Ginnungagap`

Validate packets and their referenced files:

```powershell
python tools\production_reference_pipeline.py validate
```

Regenerate the searchable packet index and Unreal-friendly CSV:

```powershell
python tools\production_reference_pipeline.py index
```

Regenerate the broader concept-art inventory with collection identity, file format, dimensions,
hashes, and production-packet links:

```powershell
python tools\production_reference_pipeline.py inventory
```

Run all three operations:

```powershell
python tools\production_reference_pipeline.py all
```

Generated global outputs:

- `docs/concept-art/production-reference/catalog.json`
- `docs/concept-art/production-reference/UnrealProductionReferences.csv`
- `docs/concept-art/production-reference/concept-art-inventory.json`

The inventory includes PNG, JPEG, WebP, TIFF, GIF, and SVG visual sources. Its
`packet_linked_visual_count` and `unlinked_visual_count` fields distinguish files already cited by
a production packet from files that still need classification or normalization. Collection-level
coverage is summarized in `docs/ConceptArtProductionCoverage.md`.

## Blender handoff

The Blender adapter creates collection structure, a bounds guide, and socket empties from one
packet. It deliberately does not generate final geometry.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python tools\blender\bootstrap_from_production_reference.py -- docs\concept-art\2026-08-28\production-reference\cryo-bay-modular-kit-v1.production.json
```

Use the Blender version installed on the workstation if that path differs. Add a `.blend` output
path after the manifest to save the bootstrapped scene.

## Unreal handoff

`tools/unreal/apply_production_reference_metadata.py` attaches approved packet identity, source
hash, status, and manifest path to existing Unreal assets listed in a packet. It does not import or
replace meshes. Run it through Unreal's Python environment after reviewing the packet:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' Ginnungagap.uproject -run=pythonscript -script="tools/unreal/apply_production_reference_metadata.py docs/concept-art/2026-08-28/production-reference/cryo-bay-modular-kit-v1.production.json"
```

Packets with `production_ready: false` may still be tagged for traceability. The adapter never
changes geometry, collision, materials, import settings, or gameplay classes.

## Promotion gate

An asset can move to production-ready only when:

- all blocking conflicts are resolved;
- scale and coordinate rules are approved;
- orthographic views reconcile to one buildable object or modular kit;
- pivot, socket, collision, material, and state boundaries are explicit;
- the Blender or Unreal graybox has been measured;
- acceptance checks required for the current stage pass.

Generated visual polish is not evidence that this gate passed.
