# GGP-01 Wayfarer Interior Maps

The ship-agnostic canonical list of established and approved interior spaces is maintained in [Ship Room Type Catalog](RoomTypeCatalog.md). This document selects and arranges room types for the Wayfarer; it is not the master catalog.

## Whole-ship scale

The Wayfarer is a capital-scale vessel with **24 primary decks**, plus crawlspaces, pressure trunks, tank volumes, and machinery voids that do not count as decks. The present procedural prototype becomes a deliberately bounded four-deck damage-control sector-Decks 09 through 12-rather than the entire ship.

The current Small Utility Escort envelope is **1,400 m long, 260 m wide, and 320 m high**, including
the aft engine base and forward command crown. Authored gravity down points aft along the ship's
long axis. Floors are transverse to that axis and face the engines. Deck numbers rise from aft to
fore, away from the engines. See
[Ship Architecture Authority](ShipArchitectureAuthority.md).

| Decks | Major band | Principal spaces |
| --- | --- | --- |
| 21–24 | Command crown | bridge, flag CIC, navigation, strategic sensors, secure command, observation |
| 17–20 | Crew habitat | cabins, galley, medical, recreation, hydroponics, life support |
| 13–16 | Mission operations | hangars, drones, laboratories, workshops, cargo exchange, auxiliary CICs |
| 09–12 | Damage-control sector **(current playable slice)** | local cryo refuge, field workshop, engineering distribution, emergency CIC |
| 05–08 | Main engineering | reactors, jump machinery, drive control, coolant, power conversion |
| 01–04 | Keel and stores | tankage, bulk cargo, fabrication feedstock, waste and water recovery |

The ship is divided longitudinally into seven pressure zones. Lifts handle normal vertical circulation, while armored stairs, maintenance ladders, and emergency trunks preserve traversal after power loss. Large machinery spaces can span two to four deck heights.

## Hangar connection - Decks 13–16

The major side opening connects to one dominant offset hangar complex amidships. Smaller service
locks and recovery pockets occupy the opposite side. These are real traversable spaces, not shallow
facade recesses, and the port and starboard arrangements must not be copied.

- The dominant hangar spans four deck levels and approximately two pressure-zone bays longitudinally.
- Deck 13 contains recovery machinery, magazines isolated behind armored transfer locks, and maintenance pits.
- Deck 14 is the primary launch/recovery floor, continuous with the visible exterior threshold.
- Deck 15 contains ready rooms, flight control, workshops, and service galleries overlooking the bay.
- Deck 16 carries overhead cranes, fuel-safe utility runs, drone storage, and retractable blast-door machinery.
- An armored logistics tunnel links the dominant hangar to the smaller recovery and service locks
  without leaving a direct shot through the hull.
- Segmented exterior doors retract into protected pockets. An internal pressure curtain and secondary blast wall allow limited launch operations without venting the whole complex.
- The normal open-bay state uses a transparent atmospheric containment shield seated in the mouth frame. It retains atmosphere while permitting controlled craft passage; retractable physical doors remain the pressure-safe fallback.
- Hangar lighting is warm-white and localized inside the opening; it should not spill across the surrounding hull like decorative illumination.

### Containment-shield presentation

- Idle appearance: nearly invisible center, thin cyan perimeter glimmer, subtle refraction, very faint micro-hex structure, and slow pearlescent interference bands.
- Crossing response: a localized circular ripple follows the intersecting object and decays in under one second; do not flash the entire opening.
- Impact response: a sharper branching ripple propagates from the contact point toward frame emitters, with intensity proportional to impulse.
- Power loss: brief uneven flicker, interference bands slow and break apart, then the plane collapses inward toward the frame; physical blast doors begin closing immediately.
- Gameplay readability: the interior and silhouettes behind the membrane must remain visible. Shield opacity should never make the hangar resemble a solid blue door.

### Unreal implementation

- `M_HangarContainment`: translucent unlit material with depth-aware refraction, Fresnel-weighted edge emission, low-contrast animated interference noise, and optional micro-hex normal modulation.
- `BP_HangarShield`: owns the shield plane, frame emitters, power state, crossing events, and material parameters.
- `NS_ShieldRipple`: short-lived local ripple spawned at intersection/impact position; use a parameterized projected ring instead of increasing whole-plane brightness.
- Recommended parameters: `ShieldPower`, `EdgeIntensity`, `RefractionStrength`, `InterferenceSpeed`, `RippleOrigin`, `RippleRadius`, and `ImpactStrength`.
- Collision and atmosphere simulation remain separate from the visible material so graphics scalability cannot affect gameplay sealing.

## Exterior airlock ports

Airlocks are deliberate navigation landmarks distributed across pressure zones rather than attached to every compartment.

- Standard visual kit: chamfered or hexagonal collar, amber hazard surround, two short cyan approach bars, external handholds, a central docking target, and two visibly separate pressure-door planes.
- Personnel lock: 2.5–3 m collar, short vestibule, suit/service niche, and four-person cycle capacity.
- Cargo lock: 6–8 m collar, reinforced guide rails, overhead handling beam, and connection to cargo corridors rather than habitation rooms.
- Emergency/EVA lock: compact collar with red manual-release hardware and an exterior tether rail.
- Map iconography and HUD scanner silhouettes must match the exterior collar shape so players recognize an airlock before reading text.
- Hangar mouths never substitute for airlocks; personnel access beside a hangar uses its own small standardized collar.

## Map grammar

The current playable sector retains the generator's footprint: four decks, twelve longitudinal columns, port and starboard room bands, and a central corridor. One column is a 6 m bay; a normal room is approximately 6 m × 6 m, the corridor is 2.6 m wide, deck spacing is 4.3 m, and clear room height is 3.2 m. This 72 m-long grid represents one isolated sector in the wider hull, not a bow-to-stern plan.

Coordinates run **aft to fore** from column 01 to 12. `P` and `S` identify port and starboard room bands. The plan overview is stored at `Content/ConceptArt/Ships/GGP01_Wayfarer_InteriorDeckPlans.svg`.

## Deck identities

### Deck 12 - Emergency command and mission

The upper level of the playable sector. It contains a local emergency CIC, sensor analysis, briefing, secure records, and redundant flight-control equipment. The primary bridge remains far above on Decks 23–24.

- Landmark: forward observation blister and a tall, damaged sensor plot.
- Gameplay character: long sightlines interrupted by security shutters and glass partitions.
- Vertical links: one midship route at columns 04–07 and one forward route at columns 09–11.
- Procedural pool: officer cabins, chart rooms, encrypted archives, comms repair, drone control, and secure storage.

The primary bridge on Decks 23–24 is a multi-level panoramic command space inside the forward dorsal viewport complex. It uses broad exterior viewing panels rather than an armored bunker layout. The Deck 12 emergency CIC is internal and screen-driven; it is a redundant local control room, not the visually prominent bridge.

### Primary bridge concept - Decks 23–24

- Two-story amphitheater with navigation and helm forward, tactical stations on the lower ring, and command/flag positions on the raised aft tier.
- Panoramic dark structural-glass viewports wrap the forward and side faces, broken by heavy mullions aligned with exterior armor ribs.
- A narrow overhead window band provides dorsal visibility without turning the ceiling into glass.
- Physical plotting table and retractable display layers supplement the exterior view; the windows remain readable and unobstructed during normal operation.
- Emergency protection comes from localized pressure curtains, redundant transparent layers, and deployable internal blast partitions between bridge zones-not permanent exterior armor shutters.
- Direct access connects to navigation, secure comms, flag briefing, and two independent lift/stair trunks.

### Deck 11 - Habitation, medical, and emergency-CIC access

This is the player's onboarding and primary narrative deck. Cryo remains fixed at aft-port column 01, the workshop remains at aft-port columns 02–03, and CIC remains in one of the forward column-12 rooms. The impact breach occupies the opposite forward band.

- Landmark: the cryo bay's red emergency light and the breached forward hull.
- Critical path: cryo → workshop → midship descent → Deck 02 power → forward ascent → CIC.
- Loop: the port and starboard bands provide parallel routes around blocked compartments.
- Procedural pool: galley, medbay, washroom, bunks, commons, hydroponics, stores, and life-support access.

### Deck 10 - Distribution engineering and power

Heavy machinery, short sightlines, heat haze, coolant vapor, and loud structure-borne sound. The main engine room remains aft-port column 01. Power control occupies aft-starboard column 01 or 02, forcing the player to descend forward of cryo and backtrack aft.

- Landmark: a reactor-transfer trunk visible through several bays.
- Critical interaction: restore the main distribution bus at Power Control.
- Vertical links: two routes to Deck 03 at columns 05–06 and 09–10; two routes to Deck 01 at columns 03–06 and 09–11.
- Procedural pool: coolant pumps, converters, fuel conditioning, machine shop, battery rooms, damage control, and engine access.

### Deck 09 - Service, cargo, and utilities

The most industrial and least inhabited deck. Cargo rails and pipe trunks create alternate traversal shapes while preserving the same grid. It acts as a dangerous bypass when upper-deck routes are locked or exposed.

- Landmark: a long cargo handling rail along the central spine.
- Gameplay character: low light, open maintenance pits, movable cargo, and frequent zero-g traversal opportunities.
- Procedural pool: cargo holds, water recovery, waste processing, fabrication feedstock, stores, landing/handling equipment, and utility junctions.

## Shared zoning rules

- Columns 01–03 are the sector's **aft machinery/support** end.
- Columns 04–08 are the sector's **central living/logistics** span.
- Columns 09–12 are the sector's **forward mission/escape** end.
- Each deck receives one airlock site in columns 04–05 and another in columns 10–11, matching the generator.
- Escape pods remain restricted to columns 10–12 and appear on exterior-facing walls only.
- Vertical-route windows remain seeded within their existing ranges; surrounding rooms should advertise them with ladders, yellow framing, cable trunks, and repeated deck-number markings.
- Every generated critical path must have at least one unblocked route; blockers should create detours, not seed-dependent dead ends.

## Variable room and corridor rules

- The 6 m lattice is a placement substrate, not a one-room-per-cell mandate. Most occupied spaces merge several slots or span multiple deck heights.
- Human-scale rooms should cluster around habitat and command nodes; they must not tile the entire hull.
- Large machinery, hangars, cargo holds, tankage, lift trunks, framing, armor depth, and inaccessible reserves consume most ship volume.
- Corridors form a seeded graph of offset spines, doglegs, cross-links, machinery rings, service spurs, and maintenance bypasses.
- Each deck needs at least one navigable loop. Adjacent decks need at least two separated vertical connections so damage can force a detour without making the seed unsolvable.
- Straight sightlines longer than four room slots should terminate at a bend, pressure door, landmark, overlook, or major-volume threshold.
- Dead ends are allowed only for optional service, loot, observation, or narrative spaces-never on the sole critical route.

## Environmental navigation language

| Deck | Base color | Secondary cue | Ambient sound |
| --- | --- | --- | --- |
| 04 Command | desaturated blue | white pin lights and glass | electronics, distant relay clicks |
| 03 Habitation | faded teal | warm personal lights; red emergency state | ventilation, loose personal objects |
| 02 Engineering | oxidized amber | cyan coolant and electrical arcs | pumps, turbines, hull knocks |
| 01 Service | neutral gray | yellow handling stripes | cargo rail, pipe resonance |

Room signs should always include deck, pressure zone, side, and bay-for example `D11-Z4-P-07`-so navigation survives procedural room-name changes.

## Generator changes implied by the design

1. Add a semantic zone or room-archetype field to `FShipRoomData` rather than naming every ordinary room `COMPARTMENT`.
2. Seed room archetypes from a per-deck weighted pool while reserving all current special rooms.
3. Validate graph connectivity after placing blockers, guaranteeing the cryo–workshop–power–CIC critical path.
4. Expose the generated room and hatch data to a map widget so the player's deck plan matches the actual seed.
5. Add landmark modules at aft, midship, and forward positions to prevent the repeated 6 m bays from becoming visually indistinguishable.
6. Remap prototype deck indices 1–4 to ship-facing deck numbers 09–12 in labels and UI while retaining compact internal array indices.
7. Replace the fixed central corridor with a seeded, validated corridor graph and allow room footprints to claim multiple contiguous slots.
