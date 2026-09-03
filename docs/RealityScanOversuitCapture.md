# RealityScan primary-oversuit reference capture

RealityScan supplies a high-detail physical reference for folds, bulk, seams, and equipment scale.
It does not generate the designed suit from concept art, and its output is never the final rigged
game mesh. The project-owned Space Marshal working duplicates remain the topology and rigging
foundation; approved concept sheets remain the design authority.

## Physical setup

- Dress a rigid mannequin in a matte coverall or pressure-garment analogue.
- Add representative harness webbing, pouches, foam armor bucks, gloves, and boots.
- Keep the garment and mannequin completely stationary for the entire capture.
- Remove transparent visors and highly reflective parts. Scan those as separate matte mockups or
  rebuild them as clean hard-surface geometry in Unreal.
- Use diffuse, fixed lighting. Avoid direct sun, moving shadows, automatic flash, and glossy floors.
- Place non-repeating tracking markers around the base if the garment is visually uniform.

## Photo set

Capture 150–250 sharp photographs at fixed exposure, white balance, focus, and focal length:

1. One full-body ring near waist height.
2. One downward-looking ring above the shoulders.
3. One upward-looking ring around knees and boots.
4. Close detail arcs around the collar, underarms, gloves, waist, knees, boots, and equipment mounts.

Move a small distance between photographs and retain at least 60% overlap between neighboring
views. Every important surface should appear sharply in at least five photographs. Do not mix
concept renders, altered backgrounds, or photographs from different garment arrangements into the
same component.

Store the capture outside version control at:

`Intermediate/RealityScan/PrimaryOversuitCapture/Images`

## RealityScan 2.2 processing

1. Import only the physical photo set.
2. Generate AI masks and inspect the hands, boots, pouches, and silhouette before alignment.
3. Align at full image resolution and verify that all useful cameras form one component.
4. Set a tight reconstruction region around the mannequin.
5. Calculate a normal/high-detail model.
6. Remove floor, stand, marker, and background fragments.
7. Simplify a reference copy to approximately one million triangles.
8. Unwrap and texture the simplified reference.
9. Export FBX or OBJ in centimeters with textures beside the mesh.

Place processed reference exports under:

`Intermediate/RealityScan/PrimaryOversuitCapture/Export`

Import the reference only to
`/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/References/RealityScan`. Use it as a
visible sculpt/conform target alongside Manny and Quinn; do not copy its topology, skeleton, or
mannequin geometry into a wearable oversuit.

## Promotion gates

The scan may influence a class mesh only after its silhouette agrees with the approved concept
boards. A role mesh remains review-only until it is rebound to the project mannequin skeleton,
survives the common animation audit without clipping, preserves don/doff separation from the
undersuit, and passes multiplayer equipment replication tests.
