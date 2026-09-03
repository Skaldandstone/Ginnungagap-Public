# Small Utility Escort interior plan

The four-room companionway remains the fast-loading systems test cell. It is not the room count
for the complete vessel.

The 1.4 km Small Utility Escort now has an authoritative target of **164 explorable rooms** across
12 streamed districts. Locked machinery volumes, tanks, structural voids, robotic service spaces,
and inaccessible deck sections are intentionally outside that count. This keeps the ship large
enough for a long campaign without promising hundreds of low-value, repetitive cabins.

## First production district

`L_SmallEscort_OperationsDeck` is the first ship-scale interior district. It contains 24 rooms on
decks 06–08:

- Deck 08: security checkpoint, bridge, CIC, navigation, communications, sensors, armory, and
  command companionway.
- Deck 07: duty berthing, crew commons, galley, recreation, triage, surgery, quarantine, and cryo
  watch.
- Deck 06: damage control, fabrication, life support, water reclamation, cargo staging, EVA ready
  room, drive access, and auxiliary power.

The topology has 28 logical room edges, including four vertical deck connections. All 24 horizontal
edges are now materialized as navigable, damageable corridor sections instead of placing
rooms wall-to-wall. Each corridor has a pressure bulkhead at both room thresholds, producing 48
door actors and 52 physical section edges once the corridor segments are included. Every room has
stable identity, operational state, gameplay profile, anchors, signs, dressing, lighting, and
navigation bounds. The district occupies a 77.5 × 35 × 15 m envelope and is registered at
ship-local `(-220, 0, 18) m` inside the escort.

Room dimensions are authored per room rather than inherited from one fixed module. This district
uses 13 distinct sizes across a 12–18 m length, 11–16 m width, and 4–4.6 m height range: compact
armories and companionways contrast with the larger bridge, commons, fabrication, and cargo bays.
Floors, ceilings, shell walls, sockets, hardpoints, work zones, lighting, dressing offsets,
checkpoints, and vertical apertures all derive from `size_cm`. Horizontal connectors automatically
bridge the remaining 2.5–7.5 m threshold gap and fail generation if room growth would reduce a
connector below the safe 2 m minimum. Rooms without an override retain the documented default
15 × 14 × 4.3 m module, allowing later districts to mix explicit hero spaces with standard rooms.

Every room also has two numeric identities. `room_id` is unique to the persistent room instance
(for example, `8002` is this ship's command bridge), while `room_type_id` identifies the reusable
functional recipe that procedural generation may relocate or instantiate more than once. The
default placement rule keeps matching type IDs at least three grid steps apart, counting a deck
change as two steps. Type rules can name controlled clustering sections: dormitory type `201`, for
example, may sit beside another dormitory inside `habitation`, but the same adjacency remains
invalid in command, medical, logistics, or engineering space. A seeded backtracking placer in
`tools/ship_room_placement_rules.py` evaluates these rules before actors spawn, and both the source
plan and reflected map validator reject missing, duplicate, unknown, or incorrectly spaced IDs.

Rooms and corridors carry lightweight, stable gameplay hardpoints rather than hundreds of helper
actors. The hardpoint vocabulary covers doorways, bodies, partial obstacles, Bloom growth,
activities, and damage-repair work. Each threshold door also exposes explicit room-side and
corridor-side scene handles. Encounter population, environmental storytelling, infestation, and
maintenance systems can reserve these points while respecting their clearance radius; the current
authored activity stations are placed directly on damage-repair hardpoints. Each physical corridor
also carries a neutral utility light, while room work lights and district ambient fill keep the
circulation route readable without flattening archetype-specific color cues.

One authority-owned hardpoint population director consumes a deterministic subset at runtime:
six Bloom-possessable crew bodies, ten partial crate obstacles, and eight non-blocking biomass
growths. Successful spawns reserve their exact room or corridor slots, replicate to clients, and
can be cleared as a group without touching doorway, authored activity, or remaining repair slots.

Vertical links use walkable stair geometry, reciprocal section connections, and dedicated `Up` /
`Down` room-module sockets at the ceiling and deck apertures. This keeps vertical traversal in the
same topology API as horizontal room links without reusing a cardinal socket identity.

Each of the 24 rooms now carries six scale-reviewed dressing pieces from the imported **Ice
Station** and **Sci-Fi Flying Cargo Ship** Fab packs. Consoles distinguish command and sensor
spaces; beds, tables, and chairs furnish habitation and medical rooms; crates and containers
support cargo, EVA, armory, and damage-control spaces; and generators, pipe groups, and reactor
hardware identify the engineering deck. Props stay outside a protected 3.6 m central circulation
lane, while paired functional floor zones, twin neutral work lights, restrained identity accents,
corner ribs, split side and end-wall backplates, overhead trim, and ceiling fixtures give every room
two readable work bays and clearly framed bulkhead approaches. Split panels preserve every door
approach, and props automatically relocate away from active cross-deck doors. The variable-length, 3.6 m-wide corridor
modules preserve roughly 3.3 m of clear traversal width between paired threshold bulkheads. Guard rails and posts protect
all four vertical apertures. The generator
fails fast if either source pack is unavailable, and the validator confirms all 144 pieces retain
their Fab provenance, stay inside their room envelopes, and preserve both central and side-door
circulation clearances.

The corridor kit now follows the approved Small Utility Escort spinal-companionway language:
gunmetal tread insets, twin muted-orange route stripes, dark kickplates, orange service rails,
repeated pressure ribs, exposed overhead pipe runs, cold practical fixtures, and shadow-casting
utility light. The shell uses the authored worn-steel pressure-panel texture, the deck uses the
project's scuffed non-slip plate, and recessed service fields use the dark hazard-panel atlas.
These layers are explicitly non-colliding, leaving corridor bounds, doorway
clearance, hardpoints, and the central traversal lane authoritative for gameplay.

The rooms are also gameplay-addressable rather than presentation-only. Every room owns one native
activity station selected for its function-sensor calibration on the bridge deck, medical and
decontamination work in the treatment spaces, hull/fire/fabrication tasks in damage control, and
scrubber/coolant/reactor procedures in engineering. These 24 stations use the existing interaction
and player-activity systems, carry stable per-room station IDs, and target their owning room's live
damage or operational state. Four deliberately sparse health/oxygen supplies support exploration.
A district gameplay director registers `EscortOps_RestoreOperations`, and the restoration console
in Damage Control Central resolves that objective through the existing mission subsystem. The
director's random encounter and pickup seeding is disabled because this district uses authored,
deck-correct placements. Three safe-lane checkpoint volumes-Forward Security on deck 08, Crew
Commons on deck 07, and Damage Control Central on deck 06-persist current objectives, Bloom stage,
and activity-station condition through the existing checkpoint subsystem.

## Streaming policy

Interiors stay in district maps and stream into the ship at registered local transforms. The
current exterior review assembly contains 705 visible components, so it remains separate until
the approved 18–30-module Nanite merge is complete. This avoids turning exterior review geometry
into permanent interior draw-call cost.

The district catalog and exact room graph live in
`Config/Ships/SmallUtilityEscortInterior.json`. Regenerate the first district through Unreal
Editor Python with `tools/build_small_escort_operations_district.py`, then run
`tools/validate_small_escort_operations_district.py`. The map is included in the project's cook
list but does not replace the four-room companionway as the default startup district yet.

## Scale targets

| District | Explorable rooms |
|---|---:|
| Command Citadel | 16 |
| Sensor and Navigation Complex | 12 |
| Forward Habitation | 16 |
| Aft Habitation | 16 |
| Medical, Quarantine, and Cryo | 12 |
| Galley and Crew Commons | 12 |
| Workshops and Fabrication | 12 |
| Cargo and Docking Spine | 16 |
| Life Support and Utilities | 12 |
| Power and Reactor Isolation | 12 |
| Thermal Plant and Drive District | 12 |
| Service-Craft Hangar | 16 |
| **Total** | **164** |

The target can grow when playtesting demonstrates a traversal or encounter need. New rooms must
belong to a streamed district, create a gameplay choice or memorable spatial beat, and preserve a
stable room code for saves and objectives.
