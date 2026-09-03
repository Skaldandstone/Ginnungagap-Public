# RealityScan ship fleet

Three exterior concepts now have isolated RealityScan 2.2 review candidates in Unreal. This pass
uses the concept-matched Blender hulls as coherent virtual maquettes, renders overlapping locked-
camera turntables, reconstructs those frames in RealityScan, and imports only candidates that pass
the registration and mesh gates. Painted orthographic boards are design authority, but are not fed
directly to photogrammetry because their views are not guaranteed to be camera-consistent.

## Results

| Ship | Design authority | Registered views | Reconstructed mesh | Review dimensions |
| --- | --- | ---: | ---: | ---: |
| Small Utility Escort | `small-utility-escort-exterior.png` | 36/36 | 7,118 vertices / 14,232 faces | 1,400 x 260 x 320 m |
| Military Corvette | `medium-military-corvette-exterior.png` | 24/24 | 6,305 vertices / 12,606 faces | 2,400 x 430 x 620 m |
| Expedition Carrier | `large-expedition-carrier-exterior.png` | 24/24 | 8,503 vertices / 17,002 faces | 6,500 x 1,400 x 1,800 m |

Each scan formed one component with 100% of its input views registered. The gate JSON, alignment
report, RealityScan project, textured OBJ, material, and textures are under
`Art/Ships/Exterior/RealityScan/<Ship>/RealityScanOutput`.

## Unreal assets

The Nanite-enabled meshes, diffuse textures, and materials are isolated under:

`/Game/Assets/Ships/Exterior/RealityScan/<Ship>`

The exact-dimension review maps are:

- `/Game/Assets/Maps/ShipExterior/RealityScan/L_SmallUtilityEscort_RealityScan`
- `/Game/Assets/Maps/ShipExterior/RealityScan/L_MilitaryCorvette_RealityScan`
- `/Game/Assets/Maps/ShipExterior/RealityScan/L_ExpeditionCarrier_RealityScan`

These are review candidates. They do not replace production exterior meshes or gameplay
references without visual approval. Their nonuniform level scale enforces the approved target
dimensions while preserving the raw scan packages for provenance.

## Visual QA

Unreal offscreen renders were captured from all three review maps under
`Saved/Reports/RealityScanShipFleet`. The scans preserve distinct escort, corvette, and carrier
silhouettes and remain continuous enough for scale/composition comparisons. Fine hull features are
scan-soft, however, and the current diffuse textures clip bright upper surfaces while losing detail
on the undersides. Geometry promotion gates therefore pass, but production visual promotion remains
pending a material/exposure pass and hand-authored hard-surface refinement.

## Rebuild

Run these commands from the canonical Unreal project root:

```powershell
& '<Blender executable>' --background --python .\tools\prepare_realityscan_ship_turntables.py
python .\tools\write_realityscan_ship_xmp.py
```

Then reconstruct each ship with `tools/run_realityscan_unreal_pilot.ps1`, passing its `InputFrames`
directory and `<Ship>_RS` as the asset name. Finally run Unreal headlessly with
`tools/import_realityscan_ship_fleet.py`. The consolidated import and exact-bounds evidence is
written to `Saved/Reports/RealityScanShipFleetImport.json`.

`GINNUNGAGAP_RS_SHIPS` can limit turntable preparation to a comma-separated set of ship keys, for
example `SmallUtilityEscort,MilitaryCorvette`.
