# Magnetic suit traversal

The pressure suit supports magnetic boot traversal, independent left/right glove anchors, and a rotation thruster.

## Controls

- `M` / D-pad Down: toggle magnetic boots.
- Left Shift / Left Shoulder: left glove grip.
- Right Shift / Right Trigger: right glove grip.
- `R` / Right Shoulder: rotate feet toward the targeted surface.
- `Q` / gamepad Face Left: throw the held physics object.

World-static ship geometry is magnetic by default. Movable physics components must carry a `Metal` or `Metallic` component or actor tag. The server validates glove reach, target validity, and tags before accepting a grip, and owns pull/throw forces.

## Visual and audio authoring

Boot and glove materials receive `MagnetGlowColor` and `MagnetGlowStrength`. Author the master suit material with separate boot-sole and glove-pad masks feeding those parameters; the attached red point lights remain a runtime fallback. Assign `MagnetEngageSound`, `MagnetReleaseSound`, `ThrusterLoopSound`, and `ThrusterParticle` on suit Blueprint defaults for production feedback.

Thruster fuel drains while rotating, recharges while idle, and locks out at empty until the restart threshold is reached. Death, total suit-integrity loss, and respawn release all magnetic anchors.
