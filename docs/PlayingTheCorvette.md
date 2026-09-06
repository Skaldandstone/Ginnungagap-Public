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
| L | Wrist lamp on the suit's left forearm (comes on with the suit; suit only) |
| F | Cycle the approach at an obstruction (cut or squeeze) |
| Tab (right stick click) | First or third person |
| H (D-pad down) | Use a carried supply: the first one that would do anything (oxygen when low, a kit when hurt) |
| Enter | Restart the ship |

The HUD shows these for the first thirty seconds.

## The camera

You wake in third person, standing in the tube behind its glass, in the cryo bodysuit and not
the pressure suit. The tube stays on the deck: only the glass and its cap lift. You step out,
and the view hands over to first person with the visor HUD. Squeezing through a gap (an
obstruction's squeeze, and any crawl space to come) is watched in third person for its duration
and returns to first person after. Cutting with the tool stays first person. Tab toggles at will.

## Light

Dead ship, dead lights. The casualty station has the cryo tubes' blue glow and nothing else; the
suit's wrist lamp (L) is the crew's light from the rack on. Restoring power at the drive brings the
emergency bus up: every fixture and practical aboard, dull red-amber, flickering, with dropouts and
a slow beacon pulse. The mission director runs that (`BringUpEmergencyLighting`), live from the
power station and again on a checkpoint restore.

## The chain

1. **Casualty station (deck 3).** The ship is dead: no drive, no gravity. You wake inside the
   tube, in third person; when it comes awake, press E to release it and float out. Suit up at
   the rack on the port wall (the Space Marshal hangs on a rail by each locker; the cryo bodysuit
   is not pressure-rated), then M toggles the suit's magnetic boots so you can walk the deck and L
   the wrist lamp. The ship is dark: the pods' blue glow is the bay's only light until you carry
   your own, and nothing else aboard lights until the bus is back. The room's door is locked against the vacuum in the
   corridor beyond; the override panel by the door refuses anyone not sealed in a suit.
2. **Engineering control (deck 2).** Down the trunk (floating, or on the boots). The room's door
   lost its bus with the main power: the override panel in the corridor winds it open. The
   workshop bench hands over the tool.
3. **Power and distribution (deck 1).** Down again: restore the main bus at the floor console.
   The bus feeds the drive: the ship goes back under thrust and the deck is down again.
4. **Security center (deck 4).** Climbing back, the trunk's ramp head is blocked by a collapsed
   ceiling frame: cut through with the tool, or squeeze past.
5. **Crew commons (deck 6).** A conduit bundle is down across the ramp head from the marine deck.
   No way past it but the tool.
6. **Comms (deck 7).** The room was welded shut when it lost pressure. Cutting the weld is a tool
   path: the seam wanders and the torch has to be kept on it (look up and down; the visor shows
   the seam and the torch on one track). Inside, patch the hull rupture at the breach station.
7. **Armored CIC (deck 8).** The door is locked; the access panel in the corridor overrides it. The
   tactical console ends the chain, and the game cuts to the start screen.

Past the chain, the observation deck's ramp head is crossed by a ruptured coolant line: squeeze
past it, and it may catch you. Decks 2-3, 6-7 and 9-10 are also joined by a ramp through their
service plenums, so a blocked trunk is not always the only way up.

## Off the chain

Every deck has something to do besides: a side station on a room wall (battery recovery, armory
override, turret service, suit patching, scrubber service, plotter core, decontamination, sensor
calibration), field supplies in the aft corners of each main room and loose oxygen in some
corridors, a fallen duct across the tactical corridor, a collapsed duct run in the marine deck's
plenum doorway that can only be crawled through, and the observation deck's secondary room welded
shut, cut free with the tool. The observation deck's glass looks out on stars. Rails guard the
ramps and the landing edges; the trunk signs say which deck each ramp leads to.

## Dressing and damage

The generator furnishes each deck for what it is (bunks in the marine ready room, a mess in the
commons, plotting tables in tactical, shelving and lockers elsewhere, pillars at the partitions,
light fixtures at the practicals) and wrecks one room in some decks with seeded damage: arcing (a
torn-open electrical box, a dropped cable run, a red flicker) or impact (a toppled barrel, a
fallen duct section). Change `BUILD_SEED` in `tools/build_corvette_thrust_stack.py` and regenerate
for a different ship. The chain's authored damage (the Comms rupture, the welded door, the locked
bulkheads) does not vary.

## Co-op

The menu's Co-op mode hosts the corvette as a listen server. From the command line, the packaged
game hosts with `Ginnungagap.exe /Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack?listen`
and a second copy joins with `Ginnungagap.exe <host-ip>:7777`. Both loading the ship and the
join hand-shake are verified, and a joining player receives the objective chain: the director
replicates the completed list, so the client's HUD and beacons show the same active objective as
the host's. Every player wakes in a cryo pod of their own: the server gives each arriving crew
member a pod and drives the lid, the climb out and the stand, and each machine plays the camera,
blackout and HUD beats for its own player on the server's clock. Someone who joins late wakes on
their own timeline while the others watch them climb out. Two players finishing the chain
together end to end has not been played through yet.

## What the tests prove

`Ginnungagap.Smoke.CorvetteRoutesReachable` proves the trunk barrier cuts the climb and, past it
(with welds cut and locks overridden as the crew would), every station is reachable on the navmesh
and each plenum ramp is the path between its plenums. `Ginnungagap.Smoke.PlayerPlaysEveryStation`
plays the chain, every barrier, every side station, a supply and the welded doors through the real
input handlers, steering the torch along the seam. `Ginnungagap.Survey.CorvetteWalkthrough` drives
the character on foot up the chain, back down and out to every side station and writes
`docs/CorvetteSurvey.md`: where everything is, every snag, floor gap, penetration and blocked door
met on the way, every prop hanging in the air, every figure aboard, and what each interactable is
made of. Run it after any change to the ship; it is where the next list of work comes from.
`Ginnungagap.Look.RoomTour` and `OpeningShots` are stills for a visual check, not deliverables.
