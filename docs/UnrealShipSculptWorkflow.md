# Unreal Ship Exterior Sculpt Workflow

The capital-ship exterior shape pass now lives in Unreal Engine 5.8. The source imports and `Iteration_01` assemblies are preserved, while each sculpt map uses separate `Working/Iteration_02_Cleanup` meshes.

## Current status

Cleanup pass 01 is complete and silhouette pass 01 is underway. The cleanup assets remain preserved at `Working/Iteration_02_Cleanup`; the maps advance to non-destructive `Working/Iteration_03_Silhouette` copies. This pass separates the ships at broad-form scale: the corvette gains a compact armored center, sharper prow, hard drive shoulder, and buried command complex, while the carrier gains broader civic deck masses, a tapered navigation prow, and stronger habitat, hangar, and drive districts. Exact envelopes, rebuilt normals, UVs, tangents, and actor scale 1.0 remain mandatory.

## Sculpt maps

- Military corvette: `/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt`
- Expedition carrier: `/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt`

The corvette is locked to a 2,400 × 430 × 620 m envelope. The carrier is locked to a 6,500 × 1,400 × 1,800 m envelope. Each map includes an EVA figure, a 35 m shuttle, the relevant concept sheet, three review cameras, and neutral sculpt lighting.

## Enabled Unreal toolset

- Modeling Mode
- Geometry Script
- Scriptable Tools Editor Mode
- Static Mesh Editor Modeling
- Mesh Modeling Toolset Experimental
- Mesh Paint

Restart the editor once after the plugin change. Open the sculpt map, switch to Modeling Mode with `Shift+5`, and work only on actors named `SCULPT_WORKING_*`.

## Shape pass order

1. Work only on `Iteration_03_Silhouette`. Scale baking, coarse voxel wrapping, and tangent repair are already complete in the preserved cleanup iteration; do not repeat them before the silhouette pass.
2. Use **Deform > Sculpt** with symmetry enabled. Establish the top, side, and three-quarter silhouette before touching panel lines. Use Move, Smooth, Flatten, and Pinch as the primary brushes.
3. For the corvette, use 4,000–12,000 cm brushes for macro shaping and 800–3,000 cm brushes for secondary planes. For the carrier, use 10,000–30,000 cm brushes for macro shaping and 2,000–8,000 cm brushes for secondary planes.
4. Keep command/defense, drive/thermal, hangar/docking, and habitat/civic modules separate. Match their transitions into the hull using broad forms; do not populate the surface with generic greebles.
5. Review from the three saved cameras and against the concept board after every major silhouette change. The side view controls length and mass distribution; the three-quarter view controls character; the drive view controls stern hierarchy.
6. Only after silhouette approval, use PolyEdit and PolyGroups for armor fields, then Boolean or Project for the few large recesses visible in the concept. Reserve small seams, decals, material breakup, and damage for later passes.

## Approval gate

The shape pass is ready to advance only when all of the following are true:

- The ship reads like the concept at thumbnail size with all materials overridden to neutral gray.
- The envelope still measures exactly 2.4 km or 6.5 km as applicable.
- No single surface feature exists merely to add density.
- The bow, command mass, midship function, and drive block form a clear hierarchy.
- Tangents and normals are recomputed after remeshing, eliminating the temporary import warnings.

After approval, duplicate `Working/Iteration_02_Cleanup` to an `Approved/Shape_01` folder. Generate production UVs, bake supporting maps, add authored hull materials, configure collision, and enable Nanite on that approved copy-not on the sculpt source.

## Rebuild command

Run `tools/setup_unreal_ship_sculpt_workspace.py` through Unreal's Python commandlet to regenerate both maps, working copies, reference boards, and the scale report at `Saved/Reports/UnrealShipSculptWorkspace.json`.

Then run `tools/process_unreal_ship_sculpt_cleanup.py` to rebuild `Iteration_02_Cleanup`, followed by `tools/validate_unreal_ship_sculpt_cleanup.py` for independent fresh-load QA. Cleanup reports are written to `Saved/Reports/UnrealShipSculptCleanup01.json` and `Saved/Reports/UnrealShipSculptCleanup01_Validation.json`.

Run `tools/advance_unreal_capital_ship_silhouettes.py` to create and activate `Iteration_03_Silhouette`, then run `tools/validate_unreal_capital_ship_silhouettes.py`. The pass reports are written to `Saved/Reports/UnrealShipSculptSilhouette01.json` and `Saved/Reports/UnrealShipSculptSilhouette01_Validation.json`.
