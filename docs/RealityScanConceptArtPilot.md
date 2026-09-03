# RealityScan concept-art pilot

The Compact Rock Corer was used to test whether a single painted concept could be expanded into a
multi-view set and reconstructed by RealityScan 2.2. The pilot is intentionally isolated from the
production Batch 03 mesh. Its purple treatment has been rejected for the base asset because it reads
as Bloom infection rather than a clean first-use state.

## Inputs

The design authority is item 41 on
`Art/Weapons/Concepts/WeaponConcepts_41-50_MiningSalvage.png`. The built-in image-generation workflow
created two six-view contact sheets and twelve individual 30-degree orbit frames. All generated
project-bound images live under:

`Art/Weapons/RealityScan/CompactRockCorer_Pilot`

The approved visual direction is in `CleanReference`: warm off-white ceramic armor, intact orange
safety markings, gunmetal and tungsten-carbide tooling, neutral white-blue indicators, and no
purple, crystalline, organic, corroded, or Bloom-infected treatment. The original purple sheets are
retained only as reconstruction and visual-direction failure evidence.

The repeated frame prompt used the contact sheets as identity references and required one
photorealistic product frame, a fixed 15-degree downward elevation, a uniform gray backdrop, fixed
lighting, identical wear and markings, and the requested orbit angle. It explicitly prohibited
geometry changes, extra parts, text, collage layouts, depth of field, and motion blur.

## Reconstruction result

RealityScan produced two alignment components:

- Largest component: 5 of 12 images
- Secondary component: 3 of 12 images

The normal-detail pass on the largest component produced 19,443 vertices and 38,878 faces with a
diffuse texture. Although the triangle count is sufficient for an Unreal review asset, the 41.7%
registration rate is not sufficient to assert coherent 360-degree geometry. Combined with the
Bloom-like purple palette, the result is rejected and must not replace the production mesh.

The source project, OBJ, material, textures, and RealityScan alignment report live under
`Art/Weapons/RealityScan/CompactRockCorer_Pilot/RealityScanOutput`.

## Unreal review

The rejected scan is imported under
`/Game/Assets/Gameplay/RealityScanPilots/CompactRockCorer`. The side-by-side comparison level is:

`/Game/Assets/Maps/ModelLibrary/L_RealityScan_CompactRockCorer_Pilot`

The imported Static Mesh has Nanite enabled, complex-as-simple review collision, provenance
metadata, and a `Rejected for first-use` promotion tag. It is not referenced by the
weapon definition, world-item catalog, district Blueprints, or shipping gameplay maps.

## Reusable gate

Run a future scan with a true photo set or consistent rendered turntable:

```powershell
.\tools\run_realityscan_unreal_pilot.ps1 `
  -InputDirectory .\Art\Weapons\RealityScan\SomeAsset\InputFrames `
  -AssetName SomeAsset
```

The script discovers RealityScan, aligns and reconstructs the source, creates a textured OBJ and
alignment report, then writes `RealityScanGate.json`. Promotion requires at least 90% of views in
the largest component and at least 10,000 output faces. Failed scans exit with code 2 and remain
quarantined from production; a conflicting visual state can be rejected independently of geometry.

## Production conclusion

RealityScan is appropriate for physical maquettes, photographed industrial parts, LiDAR, or a true
3D turntable with consistent camera overlap. AI-generated rotations from a single concept can be
useful as modeling references, but this pilot demonstrates that they should not be treated as
photogrammetrically consistent source data. For painted single views, the production path remains
Unreal Geometry Scripting and Modeling Mode, using the generated frames only as visual targets.
