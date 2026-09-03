# Concept Ship Remaster V02

V02 replaces the rejected virtual-photogrammetry approach with clean hard-surface authoring driven directly by the exterior concept boards. RealityScan output remains quarantined in its existing review namespace and is not used by these assets.

## Fleet

| Ship | Concept dimensions | Authored objects | Signature features |
|---|---:|---:|---|
| Small Utility / Escort | 900 × 125 × 250 m | 159 | recessed service hangar, docking spine, six-engine drive district |
| Medium Military Corvette | 2,400 × 430 × 620 m | 379 | dual recessed hangars, armored citadel, mounted defense terraces, 4×4 drive face |
| Large Expedition Carrier | 6,500 × 1,400 × 1,800 m | 659 | carrier concourse, protected longitudinal habitat drums, command city, twelve-engine drive face |

## Source and validation

- Builder: `tools/build_concept_ship_remaster_v02.py`
- Blender, GLB, manifests, and four-view renders: `Art/Ships/Exterior/ConceptRemasterV02/<Ship>/`
- Unreal importer: `tools/import_concept_ship_remaster_v02.py`
- Unreal meshes: `/Game/Assets/Ships/Exterior/ConceptRemasterV02/<Ship>/`
- Unreal review maps: `/Game/Assets/Maps/ShipExterior/ConceptRemasterV02/`
- Unreal import report: `Saved/Reports/ConceptShipRemasterV02Import.json`

The GLBs have valid `glTF` headers and the generated manifests report exact concept dimensions. Promotion remains review-gated; V02 does not overwrite the production fleet or the older RealityScan candidates.
