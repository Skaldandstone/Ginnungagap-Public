# Exterior Jump-Arrival Animation

## Direction

Treat the jump as space releasing the ship, not as a craft flying through a circular portal. The vessel moves only a modest distance in world space; lensing, a collapsing wake, exposure, and particles sell the impossible speed. This keeps a capital-scale ship feeling massive.

## Six-second shot

| Time | Picture | Implementation |
| --- | --- | --- |
| 0.00–0.75 s | Quiet system establishing shot; stars subtly bow toward an empty point | Sequencer camera; material-parameter collection ramps localized lens distortion from 0 to 0.2 |
| 0.75–1.10 s | A razor-thin blue-white caustic forms, with stars stretched along the travel axis | Niagara ribbon/sprite system plus post-process radial distortion; no ship yet |
| 1.10–1.35 s | Prow resolves first; the rest of the hull unwraps from compressed space | Reveal ship with a moving world-position mask or segmented dither; animate wake boundary aft along the hull |
| 1.35–1.65 s | Full hull arrives; curved shock sheet snaps outward | Niagara mesh/ribbon shock front, one-frame exposure peak, chromatic fringe, and camera impulse |
| 1.65–3.00 s | Wake tears into long filaments and curls behind the engine block | GPU Niagara ribbons advected backward; reduce distortion rapidly, then decay slowly |
| 3.00–6.00 s | Engines stabilize; warm system light takes over; residual sparks fade | Engine emissive settles from white to cyan; exposure and bloom return to baseline |

## Unreal asset plan

- `BP_JumpArrival`: owns timing, ship reference, Niagara systems, audio cues, post-process blend, and a `PlayArrival` event.
- `NS_JumpCaustic`: thin pre-arrival line and axial star-streak impression.
- `NS_JumpWake`: GPU ribbons emitted from sockets distributed over the aft third of the hull.
- `NS_JumpShock`: expanding curved sheet with depth fade and camera-facing breakup particles.
- `M_JumpReveal`: world-position reveal boundary with dithered opacity; use only during the 0.25-second emergence.
- `MPC_JumpArrival`: `ArrivalOrigin`, `ArrivalAxis`, `Compression`, `Fringe`, and `ExposureKick` shared by VFX and post process.
- `LS_JumpArrival`: Level Sequence for the first hero shot; gameplay arrivals can drive the same parameters from C++ or Blueprint.

## Motion and camera rules

- Move the ship roughly 5–10% of its own length during emergence, then ease heavily into a slow drift.
- Keep rotation below one degree during the effect; a capital ship should not twitch.
- Put the camera three-quarter aft and slightly below so the engine cluster and collapsing wake read together.
- Use a short, low-amplitude translational impulse after the shock front, not handheld noise throughout.
- Let the destination star provide warm rim light opposite the cold jump wake.

## Audio layers

Even for an exterior shot, use subjective cinematic sound: sub-bass pressure rise, a brief high-frequency vacuum cut at emergence, a wide impact transient, then stressed-metal settling and engine harmonics. For strict in-world EVA presentation, route the impact through suit contact or structure-borne vibration instead.

## First playable milestone

Build the effect with the ship blockout, one Niagara ribbon system, one shock mesh, and exposure animation before detailed modeling. Success criteria: the direction of travel is readable with the sound muted, the ship feels massive, and the effect still reads at medium distance without relying on bloom.

