# Playing the corvette

The playable ship is `L_Corvette_ThrustStack`, the GGP-M01 corvette: eleven one-storey decks
stacked along the drive axis, joined by a ramped access trunk. The drive is lit, so "down" is
toward the engines.

## Starting it

- From the editor: `powershell -ExecutionPolicy Bypass -File tools/play_corvette.ps1` launches a
  windowed game straight into the ship (add `-Menu` for the front end; all three play modes open
  the corvette).
- Standalone: `tools/package_corvette.ps1` builds `Builds/Corvette-Windows-Development/Windows/
  Ginnungagap.exe`. Run it alone; it takes twenty minutes the first time and under a minute after.
- A fresh start needs no `Saved/SaveGames/GinnungagapShipCheckpoint.sav`: the mission director
  restores it on play. The automation runs delete theirs; a manual play leaves one behind.

## Keys

| Key | Does |
| --- | --- |
| W A S D, mouse | Move, look |
| E | Interact: stations, doors, pickups, the pod |
| F | Cycle the approach at an obstruction (cut or squeeze) |
| Tab (right stick click) | First or third person |
| Enter | Restart the ship |

The HUD shows these for the first thirty seconds.

## The chain

1. **Casualty station (deck 3).** Wake in the pod, suit up at the rack on the port wall.
2. **Engineering control (deck 2).** Down the ramp: the workshop bench hands over the tool.
3. **Power and distribution (deck 1).** Down again: restore the main bus at the floor console.
4. **Security center (deck 4).** Climbing back, the trunk's ramp head is blocked by a collapsed
   ceiling frame: cut through with the tool, or squeeze past.
5. **Comms (deck 7).** Patch the hull rupture at the breach station.
6. **Armored CIC (deck 8).** The door is locked; the access panel in the corridor overrides it. The
   tactical console ends the chain, and the game cuts to the start screen.

## Off the chain

Every deck has something to do besides: a side station on a room wall (battery recovery, armory
override, turret service, suit patching, scrubber service, plotter core, decontamination, sensor
calibration), field supplies in the aft corners of each main room and loose oxygen in some
corridors, a fallen duct across the tactical corridor, and the observation deck's secondary room
welded shut, cut free with the tool. The observation deck's glass looks out on stars.

## What the tests prove

`Ginnungagap.Smoke.CorvetteRoutesReachable` proves the trunk barrier cuts the climb and, past it,
every station is reachable on the navmesh. `Ginnungagap.Smoke.PlayerPlaysEveryStation` plays the
chain, both barriers, every side station, a supply and the welded door through the real input
handlers, twenty steps in about two minutes. `Ginnungagap.Look.RoomTour` and `OpeningShots` are
stills for a visual check, not deliverables.
