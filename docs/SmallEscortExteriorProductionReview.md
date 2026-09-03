# Small Utility Escort - Exterior Production Review

## Decision

The concept-matched escort is approved as the fleet's scale and visual-language reference, with a conditional performance gate. Its Unreal actor-space bounds are **1,399.9916 × 260 × 320 m**, which passes the approved **1,400 × 260 × 320 m** contract within imported floating-point precision.

## Completed production checks

- 736 static meshes imported from the authored GLB; 705 are visible exterior components.
- 28 operational-deck reference meshes and three UCX meshes are excluded from rendering in the EVA map.
- Nanite was requested on every imported static mesh and UV channel 1 was selected for lightmaps.
- The EVA validation map includes 1.8 m technician, 8 m cargo tug, 22 m service shuttle, and 80 m traversal-route references.
- Pristine, scorched, and breached-edge production material instances are available.
- The reusable exterior kit contains RCS, antenna, armor, lifeboat, EVA rail, hatch, heat exchanger, defense, sensor, clamp, and thermal-shield modules.
- Bow, midship, and drive HLOD zones are the approved streaming split; the recommended World Partition cell size is 256 m.

## Conditional performance gate

The 705 visible components preserve editability and provide the correct high-detail review assembly, but they are not the shipping draw-call layout. Before gameplay integration, merge them into approximately 18–30 material-preserving Nanite modules divided across bow, midship, hangar/docking, command/sensor, and drive districts. Keep damage-replaceable panels, animated docking hardware, defense mounts, and VFX emitters separate.

The Unreal import also reported degenerate tangent bases on a small subset of thin armor plates and near-zero tangents on the hull-ID decal. These pieces require a Blender custom-normal/tangent cleanup or a material/decal conversion before the final shipping gate. They do not alter silhouette or scale.

## Acceptance criteria for the optimized assembly

- Exact aggregate dimensions remain within 0.1% of the approved contract.
- No visible seam or material-ID regression at EVA distance.
- No more than 30 static exterior modules in the undamaged baseline assembly.
- Separate interaction, damage, docking, weapon, and VFX components retain stable sockets.
- No degenerate tangent warnings on shipping geometry.
- Fleet-distance silhouette remains equivalent to the concept-match beauty and fleet renders.

