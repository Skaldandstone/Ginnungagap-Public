# Corvette honeycomb refit

The plan for taking the corvette from "a stack of eleven identical decks" to one level built to
the PRD's vertical-slice criteria and the art guide's thesis (maintained expedition hardware,
physical before digital, used not ruined), using the Fab packs now in the library. Working notes,
kept current as the generator changes; the survey (`docs/CorvetteSurvey.md`) is the evidence.

## What the ship is

A thrust-gravity corvette: engines below, CIC on top, "down" toward the drive whenever the drive
burns. The crew wake with the ship dead, in zero-g, sealed in the one room that still holds air.
Everything else is behind bulkheads that must be overridden, cut, crawled past or powered.

## Layout: honeycomb, not a ladder

Each deck is a ring of cells around the trunk rather than one corridor with two rooms off it:

- **Core.** The trunk (ramps or, in zero-g, a shaft to float) with a landing ring.
- **Cells.** Six to eight rooms per deck, hexagonally packed around the core, each with two or
  three doors: to the ring, and to one or two neighbours. Room walls are the kit's 400 cm panels;
  cells are 2 x 2 or 2 x 3 panels.
- **Second ways up.** Service plenums with their own ramps join some decks; a crawl duct joins
  others; the observation deck's hull gap is a third.
- **Deck roles** (bottom to top): drive and power, engineering, casualty station (cryo, the start),
  security, marines, commons, comms (the breach), CIC, tactical, observation, sensors. Roles do not
  change; what changes is which cells are damaged and how.

## Damage that looks like damage

Procedural per run (seeded): a breach picks a hull-side cell and gets the buckled plate, torn
panels, sparking cable runs, an emergency light and a vacuum zone; a fire-damaged cell gets scorch
decals and dead lights; a flooded coolant cell gets the ruptured line barrier and fog; a powered-
down cell gets a locked door and an override panel. Every damaged cell shows its damage type at
a glance (art guide: pressure, heat, impact, arcing, contamination, patching distinguishable).

## Kits and what they are for

| Need | Pack (in the library) | Where it is |
| --- | --- | --- |
| Room shells, corridors, corners, glass walls, stairs, railings, pillars, ceilings, floors | Sci-fi Rooms and Corridors Interior Kit (Denys Rutkovskyi) | `Content/SciFiRoomsCorridors` |
| Bulkhead doors (portal + two leaves) | Sci-fi New Door (CGGame, FBX) | `Content/Fab_SciFiDoor` |
| Consoles, screens, storage, seats, cabling | Sci-Fi Computer Station Modular (Kevin Roussille) | `Content/P3_ComputerStation` (5.6 GB, high-poly: use a few pieces, not the set) |
| Machinery, panels, kit walls (current shell) | Modular SciFi Season 1 | `Content/Modular_Scifi_Mechanic_Base`, `ModSci_*` |
| Cryo pod | Sci-Fi Cryo Stasis Pod | `Content/Fab_CryoStasisPod` |
| Tools | Frontier Engineer's Toolbox | `Content/Frontier_EngineersToolbox` |
| Crouch, hit reactions, deaths, turns, emotes (UE5 Manny, no retarget) | Lyra Animation Sequences Only (FBX) | `Content/Characters/Mannequins/Anims/Lyra` via `tools/import_lyra_anims.py` |
| Prone, ladder, interaction (UE4 skeleton, retargeted) | Free Animation Library, Character Interaction Add-On | `Content/Characters/Mannequins/Anims/Retargeted` via `tools/retarget_ue4_anims.py` |
| Visor HUD art | DARK SCI-FI UI (D.F.Y.) | not yet installed |
| Medical / lab dressing for the casualty station | Medical Clinic and Laboratory, Sci-Fi Creatures Research Lab | not yet installed (older engine versions in the launcher) |

## Kit measurements (Rooms and Corridors)

Walls are 300 cm wide and 300 tall, 25 to 35 thick, origin at the floor line; corner pieces 300 x 300;
floors and ceilings 300 x 300 tiles; the kit door is 130 x 220 (too small for a bulkhead, so the Fab
portal stays); glass walls 203 and 406 wide, 243 tall; railings 300 long; pillars 24 x 50 x 300;
beds 220 x 97 x 109 (origin at the head end); tables 154 x 92 x 68; chairs 40 x 46 x 80; shelving
85 x 83 x 189 (origin at a corner); lockers 54 x 52 x 68; bins 24 x 24 x 48; light bars 44 cm. The
current shell's 400 cm panels stay: the industrial kit fits the art guide's "maintained hardware";
this kit dresses it (glass, rails, fixtures, furniture) and the seeded damage pass wrecks it.

## Order of work

1. Ground truth first: the survey walk after every change; nothing floats, nothing is a bare
   prompt without a prop, every blocked route is a blockage the crew can read.
2. Doors: every bulkhead wears the Fab portal and leaves; welded and locked states show.
3. Shell: rebuild the deck ring from the Rooms and Corridors kit (panels, corners, glass,
   ceilings, floors, stairs), keeping the generator's coordinates and tests.
4. Cells and damage: honeycomb cells with two or three doors each; seeded damage per cell.
5. Bodies: Lyra crouch for crawls, interaction clips on stations, death and hit reactions.
6. Visor: the DARK SCI-FI UI frames for the HUD panels, the seam track for welding.

## Restoring the ignored packs

`Content/SciFiRoomsCorridors`, `Content/Interaction` and `Content/Characters/Mannequins/Anims/Lyra`
are not in git (half a gigabyte of someone else's assets). On a fresh clone: add the Rooms and
Corridors kit and the Character Interaction Add-On to the project from the Epic launcher (or copy
them from another project that has them), then run `tools/import_lyra_anims.py` for the Lyra clips
and `tools/retarget_ue4_anims.py` if the retargeted clips ever need rebuilding. Without them the
generator still builds the ship (the kit dressing is skipped where a mesh is missing) and the
activities fall back to Lyra's crouch idle or nothing.
