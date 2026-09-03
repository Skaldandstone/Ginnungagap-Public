# Concept art

Two kinds of thing live here, kept apart on purpose.

## `reference/` — the art, by subject

Every loose concept image the project has produced, in one tree. These are reference: they set
tone, palette and silhouette, and a production-reference packet (below) decides what of each is
approved for implementation.

| Folder | Subject |
| --- | --- |
| `reference/bloom/` | The Bloom threat family: hero concepts of the mechanized host (and its iteration history in `mechanized-host-iterations/`), reanimated crew variants, infested drones and robots, corridor and zero-g combat, the uncorrupted baselines they are built from. |
| `reference/ships/` | Exterior ship classes, the replacement fleet lineage, thrust-tower studies. |
| `reference/rooms/` | Interior rooms: cryo bay, companionways, command, engineering, medical. |
| `reference/suits/` | Pressure suits by class, the cryo bodysuit, helmet and HUD studies. |
| `reference/space/` | Star systems, orbital arrival, celestial phenomena. |
| `reference/ui/` | The in-helmet HUD and front-end studies. |
| `reference/cic/` | Combat Information Center interactions. |
| `reference/versus/` | The asymmetric versus mode's perspective and UI. |

Concept images that are also in-engine textures (used on screens and plates in the maps) live
beside their `.uasset` under `Content/Assets/ConceptArt/` and are referenced from packets by that
path; they are not duplicated here.

## `<date>/production-reference/` — the packets

Schema-validated JSON (`production-reference/production-reference.schema.json`) that maps a
concept to implementation facts: which runtime class, which meshes, what is approved, what is
provisional, what conflicts remain, and the acceptance checks. Each packet points at its own
production sheet (a `.png` beside it) and at the reference images above. They stay in their dated
folders because the schema, the inventory (`concept-art-inventory.json`) and the manifest refer to
them there.

Validate everything with:

```
python tools/validate_production_references.py
```

`tools/consolidate_concept_art.py` is how the `reference/` tree was made, and rewrites every path
that pointed at the old locations; it is idempotent and safe to re-run after adding a folder.
