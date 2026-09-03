# Ship interior concept sheets — August 2026

Seventeen 2×2 concept sheets of ship interiors, generated 2026-08-21 and filed 2026-08-28. Each
sheet holds four rooms. Source: `~/.codex/generated_images/01a027fd-3c60-7a80-b7c5-c4b164a0d6f4`.

Filenames are `GGP01_Interior_<Theme>_Sheet<NN>`, where `NN` is the generation order by timestamp —
so the numbering is stable and the theme is descriptive. Every room below was identified by opening
the sheet and looking at it, not inferred from a filename or from the order they arrived in.

Quadrants read clockwise from top-left.

| # | Theme | Top-left | Top-right | Bottom-right | Bottom-left |
|---|-------|----------|-----------|--------------|-------------|
| 01 | BridgeCommand | Bridge, forward viewport over a planet | Circular holo command table | Ops console row, star-chart windows | Conference room, plain table |
| 02 | BriefingObservation | Ops room, planet hologram in a cylinder | Observation lounge, couches under viewports | Tactical planning room, lit map table | Briefing theatre, tiered seating |
| 03 | NavTechnical | Ops room, console banks | Electronics workbench run | Cold-storage locker corridor, terminal | Navigation chart room, plot table and globe |
| 04 | BridgeEngineering | Bridge, raked viewport | Tactical plot table with server racks | Ops console corridor | Engineering control, heavy pipework |
| 05 | CIC | Helm, viewport and console row | CIC with plot table | Sensor station, large wall screens | Wardroom, map table |
| 06 | CommandObservation | Holo plot room | Captain's day cabin over a planet | Astro planning room, galaxy table | Briefing theatre, star map |
| 07 | ServerWorkshop | Server room, racks and console | Tool workshop, pegboard and cart | Records store, lockers and cart | Plot room, map table and radar |
| 08 | OpsBerthing | Server corridor, terminal | Weapons ops, console seats, weapon on bench | Single crew cabin, bunk and desk | Cockpit / secondary bridge |
| 09 | Quarters | Bunk room, stacked berths | Secure storage cage | Senior officer's suite, table and bunk | Officer's cabin, viewport and desk |
| 10 | SecurityBrig | Security control, CCTV wall | Brig, barred cells | Ordnance workroom, cold cabinet | Armoury, weapon racks and bench |
| 11 | CryoQuarters | **Cryo bay, four pods, EVA suits in wall niches** | Cryo support, single pod and stores | Shared quarters, bunks and table | Crew cabin, bunks and desk |
| 12 | CrewSupport | Galley / kitchen | Medbay ward, curtain and surgical arm | Mess hall, booths and tables | Washroom, sinks and stalls |
| 13 | RecLifeSupport | Rec room, foosball and gym gear | Hydroponics, lit grow racks | General stores, shelving corridor | Life support plant, tanks and pipework |
| 14 | WorkshopMess | **Machine workshop, central bench and tool wall** | Repair nook, bench and field gear | Canteen, servery line | Crew mess, tables and galley counter |
| 15 | Hygiene | Shower block | Locker room | Gym | Laundry |
| 16 | Medical | Operating theatre, surgical lights | Isolation ward, glass-fronted berths | Pharmacy / dispensary | Quarantine airlock, green-lit chamber |
| 17 | MorgueSuitBay | Morgue, body drawers and slabs | Pathology lab, fume hood | **EVA suit maintenance bay, exosuit on a rack** | Decon shower and utility |

## What these are for

Reference, not assets — they are 2D sheets and the demo is greyboxed from Fab kits. Three uses:

**Rooms the demo does not have.** The four-deck map dresses six. These cover medbay, galley, mess,
brig, armoury, morgue, pathology, laundry, gym, hydroponics, life support, observation and a suit
bay, which is most of a ship's worth of spaces the mission chain currently walks past.

**Direct references for rooms it does have.** Sheet 11 is a cryo bay with horizontal pods and suits
racked in wall niches, which is the demo's opening room. Sheet 14 top-left is a machine workshop,
which is the room whose lighting was just rebuilt. Sheet 04 bottom-left is an engineering control
space close to the demo's engine room.

**A lighting target.** Nearly every sheet does what the depth-light pass arrived at the hard way: a
practical in the mid-ground carrying the subject, ceilings left dark, warm pools against a cold
fill. Worth comparing a hero shot against the matching sheet directly rather than iterating blind.

Note the palette gap: these sheets are lit but *desaturated and cold*, where the demo's dressing
pass assigns each room a saturated identity colour. Sheet 11 is a useful case — the cryo bay reads
as steel and white with cold accents, not the near-pure blue the demo's cryo shot currently gives.
