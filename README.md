# Ginnungagap

A co-operative survival-horror first-person game set aboard a derelict starship, built in
Unreal Engine 5.8 by a solo developer at Skald and Stone. This repository is the evaluation
snapshot of the project: the complete C++ source, the Python tooling that generates and dresses the
ship, the design documentation and concept art, the project's own game assets, and the
evidence-based project record. It is refreshed from the private working repository by
`tools/export_public_repo.py`; this snapshot is from 2026-09-04.

## The demo

The current vertical slice is a four-deck derelict (`Content/Assets/Maps/ShipProduction/
L_QuickDemo_FourDeck`). A crew member wakes from cryo after the ship is struck, seals a pressure
suit, engages magnetic boots, cuts out of the cryo bay, draws equipment in the workshop, descends
to deck 2 through the damaged corridor to restore the main bus -- which brings the ship up on
emergency red and wakes something very large in the breach room -- then returns to deck 3 to patch
the hull rupture, overrides the CIC door and boots the tactical console, at which point the game
cuts to its title screen.

Every step of that chain is walked by the real player character under path following in an
automated PIE test (`Source/Ginnungagap/Private/Tests/CryoExitWalkthroughPieTests.cpp`), with
each station's real completion trigger fired in sequence and the player's own view captured at
every stop. The suite it belongs to has 116 automation tests and runs headlessly. The same walk, run under a
windowed editor with `tools/record_demo_walk.ps1`, records one frame per fixed 30 Hz step of the
player's own view and `tools/assemble_demo_video.py` cuts it into the demo video, laying the
in-game sound cues back in on the same timeline.

## What is here

| Path | What it is |
| --- | --- |
| `Source/Ginnungagap/` | All gameplay code: character and survival model, pressure suits and magnetic traversal, ship rooms and systems, Bloom hosts and the epidemiology model, activities and stations, mission objectives, the threat director, UI, versus mode, and the automation tests. |
| `tools/` | The Unreal Python and plain-Python tooling: the ship generator, the dressing passes, the doorway and navmesh audits, hero-shot capture, the title-plate baker, the demo recording pipeline, asset synthesis. `tools/archive/` holds one-shot scripts kept for history. |
| `docs/` | Design documentation, the product requirements, the module storyboard, and `docs/concept-art/` -- the consolidated concept-art reference by subject, plus dated, schema-validated production-reference packets that map each concept to implementation facts. |
| `Content/Assets/` | Project-authored Unreal content: maps, models, materials, textures, ships, rooms, gameplay data, audio, UI, VFX. |
| `Content/UI/` | The front end: widgets and the baked title plate. |
| `.game-guide/project.json` | The project record: concept brief, feasibility register, checkpoints with evidence, guidance sources, and decisions -- kept separately from git so implementation, testing and human acceptance stay distinct claims. |

## What is not here

The project depends on licensed asset packs from Fab that cannot be redistributed. They are not in
this repository, so opening the map here shows their meshes as missing. To build a complete
working copy, a licensed copy of each pack is installed to `Content/<PackName>/`:

- `Abandonned_Brutalist`
- `Alien_Biomass`
- `Alien_Cave_biome`
- `Alien_planet`
- `Dam_city`
- `DeadBodies_Poses_nikoff`
- `FreeAnimationLibrary`
- `HorrorAmbientSFX`
- `Ice_Station`
- `MagmaSciFiPistol`
- `ModSci_EngiProps`
- `ModSci_Engineer`
- `Modular_Scifi_Mechanic_Base`
- `SF_Brutalist_city`
- `SF_White_desert`
- `Sci-Fi_Flying_Cargo_Ship`
- `SciFiUISFX`
- `SciFiWorld`
- `SciFi_ToiletMech`
- `Sci_Fi_city`
- `Scifi_Hideout`
- `kb3d_missiontominerva`
- `Frontier_EngineersToolbox`
- `Fab_CryoStasisPod`

Source art scenes (`Art/`, 5 GB of Blender files and capture packets) and `Content/Characters` are
also excluded for size and licensing. Files over 95 MB are skipped by the export:

- none

## Building

Unreal Engine 5.8, Visual Studio 2022 build tools, Windows. Generate project files from the
`.uproject`, build the `GinnungagapEditor` target, and open the editor. The automation suite runs
headlessly with:

```
UnrealEditor-Cmd.exe Ginnungagap.uproject -ExecCmds="Automation RunTests Ginnungagap; Quit" -unattended -nopause -nullrhi -TESTEXIT="Automation Test Queue Empty"
```

Binary assets in this repository are tracked with Git LFS.

## License

All rights reserved; see `LICENSE`. Published for evaluation, not for reuse.
