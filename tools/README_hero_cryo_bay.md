# L_Hero_CryoBay — status as of tonight, stopped mid-lighting

## What's correct and settled

`build_hero_cryo_bay.py` assembles the room from the project's own canonical, approved assets —
`SM_Room_CryoShell` and `SM_Room_CryoMachinery` — placed at the exact transform already shipped in
`Source/Ginnungagap/Public/LevelSetup/ProceduralShipBuilder.cpp::AddAuthoredCryoRoom` (ArtOrigin
(0,0,-300), yaw 90°). Four real `ACryoPodSystem` actors at their real shipped world positions
(X=156.2, Y in {-384.3,-136.6,112.2,359.9}), one lid open. This is not an improvised Fab kit — it's
the same hand-authored Blender room the real ship uses, sourced from the production reference packet
at `docs/concept-art/2026-08-28/production-reference/cryo-bay-modular-kit-v1.production.json`.

The palette target is measured, not guessed: Sheet 11's cryo bay reads mean RGB (0.175,0.174,0.184),
blue-minus-red +0.009, mean saturation 0.209 — see `compare_cryo_palette.py`. Every light in this
room uses `set_light_color` with a `LinearColor`, never `unreal.Color` positionally, so the
channel-order bug that turned the *other* cryo bay blue cannot recur here.

## What's not converged: lighting and camera

Ten-plus iterations tonight hit a distinct real cause each time — lamp mesh blocking the lens, a
wall's structural rib on-axis, a pod's bounding box clipping the camera, `AEM_MANUAL` silently
ignoring exposure settings, wrong bias direction — and the last state (4 lights at 2600 intensity,
1100 radius, bias +1.5) still renders mostly black with no clear signal that more parameter pushing
would fix it. That's the point past which blind headless guessing stops being worth its cost: each
cycle is a full rebuild + grade + capture, 3-5 minutes.

**This needs eyes, not more automation.** Open `L_Hero_CryoBay` in the actual editor, drop into the
level viewport, and place/adjust lights and camera by eye. The hard part — right assets, right
transforms, right palette target — is done; what's left is the part a person does faster than a
script guessing blind.

## Files

- `build_hero_cryo_bay.py` — rebuilds the room from scratch (destructive: calls `new_level`)
- `grade_hero_cryo_bay.py` — applies/reapplies the post-process volume; current constants are the
  last (unsuccessful) attempt, not a recommendation — expect to retune by eye
- `capture_hero_cryo_bay.py` — the capture rig, camera position is provisional
- `compare_cryo_palette.py` — measures a render against Sheet 11 numerically
- `measure_canonical_cryo_shell.py`, `debug_hero_cryo_bay_topdown.py` — diagnostics, not part of the
  build

## Until this is finished

Use the four already-validated shots from the four-deck demo for anything that needs a hero image
now: `Saved/HeroShots/Hero_04_CIC.png`, `Hero_05_BloomBreach.png`, `Hero_07_Workshop.png`,
`Hero_08_PowerControl.png`. Measured, graded, and confirmed good earlier this session.
