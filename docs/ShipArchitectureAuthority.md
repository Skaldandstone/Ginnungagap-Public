# Ship Architecture Authority

This document is the visual and spatial authority for new ship concepts, room concepts, production reference sheets, and ship-kit construction. A ship is a true thrust-gravity vertical stack. It is built like a multi-story building along the thrust axis, with its main engines directly below the occupied decks. Exterior beauty views may use perspective, but every production proof must preserve this physical stack rather than reinterpret the ship as an airplane, naval vessel, or conventional axial corridor.

## Coordinate and gravity frame

- `+X` is bow, tower up, and away from the primary engines.
- `-X` is aft, gravity down, and toward the primary engine base.
- `+Y` is starboard.
- `-Y` is port.
- `+Z` and `-Z` are lateral cross-stack directions. Neither is gravity-down.
- Habitable floor surfaces are transverse to `X` on the engine-facing side of every room. Their surface normal points toward `+X`, away from the engines.
- Deck numbering increases from aft to fore, away from the engine base. Engineering, tankage, and structural stores occupy the lowest aft deck bands. Command, sensors, and observation occupy the highest forward deck bands.
- The long hull axis is the deck-stack and thrust axis. A ship is a skyscraper-like stack, not a naval vessel with one long floor running bow to stern.
- Local zero-G, failed pseudo-gravity, magnetic traversal, shafts, and rotating machinery can interrupt the player experience, but they do not change the authored floor frame.

## Exterior construction rules

- The primary engines form a protected aft base aligned with gravity down. They are not a copied row or mirrored engine wall.
- Every main-engine centerline is parallel to ship `X`, every main nozzle exits on one common aft plane, and main engines do not cant, splay, or gimbal. Asymmetry comes from unequal diameter, YZ placement, housing, service access, and role, not diagonal thrust axes.
- Attitude, translation, docking, and trim thrusters are separate maneuvering systems. They may point away from `X`, but they must never be visually or semantically grouped with the main drive.
- Major massing must be intentionally asymmetric. Use one dominant hull mass, one subordinate counter-mass, and a small number of offset operational features.
- Port and starboard sides must not be copied. Recessed bays, radiator fields, sensor apertures, docking scars, armor replacement, and command volumes should respond to role and internal zoning.
- Exterior systems are flush, recessed, shuttered, or protected whenever possible. Prefer broad calm armor fields and a few legible breaks over dense surface protrusions.
- Every visible break needs a function: access, heat rejection, sensing, launch, docking, pressure isolation, structural load transfer, or repair.
- Prohibit decorative greeble fields, repeated pod stacks, exposed pipe forests, antenna hedges, mirrored winglets, and evenly cloned engine bells.
- Preserve the approved material language: worn off-white composite armor, gunmetal structure, ceramic-black thermal surfaces, muted safety-orange identification, and localized operational light.

## Interior construction rules

- Every room concept must show gravity down along `-X` toward the aft engine base. Floors, drainage, bunks, consoles, handrails, loose-object capture, doors, and maintenance access must agree with that direction.
- Normal rooms are rectilinear pressure volumes stacked in deck bands. Large machinery, hangars, tanks, cargo voids, and vertical circulation may span several decks.
- Lifts, armored stairs, ladders, and emergency trunks connect decks along `X`. Corridors and logistics routes within one deck run across `Y` and `Z`. Any spine that runs along `X` behaves as a vertical shaft, lift bank, or ladder tower under thrust gravity.
- Hangars and cargo mouths are role-driven and offset. A ship can have one dominant bay and smaller service locks instead of mirrored port and starboard complexes.
- Interiors use calm structural surfaces with localized service density. Pipes, cable trays, controls, labels, and access panels cluster where systems are maintained rather than covering every wall.
- Interior rooms are not bilaterally mirrored compositions. Use offset doors, unequal alcoves, one dominant operational focus, one subordinate support zone, and service runs that follow actual equipment needs.
- Do not fill space with copied wall bays, paired console banks, repeated bunks, evenly spaced cabinets, or identical ceiling modules. Standard parts may repeat, but their placement must respond to circulation, maintenance clearance, pressure zoning, damage routes, and room function.
- Every interior concept sheet must prove a multi-story stack and one complete room story. The room story, from engineward to bowward, is structural transverse floor slab, utility plenum, finished floor, occupied room volume, overhead plenum, ceiling, and the next deck slab.
- Canonical side-axis stack diagrams place `+X` bow/up-stack toward page top and `-X` engines/gravity toward page bottom. Every `YZ` floor is visibly between the occupant and the engines. Main-engine guide lines must be straight, parallel to `X`, and terminate at one common aft plane.
- Every engine-bearing Houdini, Blender, Unreal, PCG, stack-preview, story-construction, and room-section panel must use flat orthographic engine geometry. Perspective and isometric engine depictions are non-authoritative and may not appear in acceptance-proof panels.
- Room perspectives may appear conventionally upright only because the room geometry is correctly authored in local thrust gravity. The occupant, fixtures, drains, loose-object capture, and structural loads must all bear on the engine-facing floor. Do not paste an upright person into a room whose geometry still uses a different gravity direction.
- A production sheet must include a large YZ room plan, an X section, named traversal splines, boundary sockets, clearance envelopes, utility routes, volume overlays, and a stack-location or story-construction proof. A perspective room view alone is insufficient.
- Diagonal or canted main engines, floors outside the occupant-to-engine load path, conventional axial corridors masquerading as room stories, page-bottom `Y` gravity, page-bottom `Z` gravity, and unlabelled frame changes are invalid.
- Signature rooms within one ship need different spatial silhouettes. Vary ceiling height, plan depth, thresholds, overlooks, pits, raised service zones, equipment islands, and multi-deck voids where function permits.
- Room variants must preserve the same module sockets, pressure boundaries, gravity frame, and gameplay clearances across clean, damaged, and Bloom-contaminated states.

## Player circulation authority

- Within one deck, player movement is planned in `YZ`. Between decks, player movement is planned along `+/-X`. A long passage parallel to ship `X` is a shaft or vertical circulation system under thrust, never an ordinary hallway.
- Each occupied deck band must expose at least two viable interdeck methods. One may be maintenance-only or emergency-only, but a disabled lift cannot isolate an otherwise habitable deck.
- Primary pressure lifts are off-center and may skip large voids or hazardous work bands. Every stop uses a short local dogleg so a lift door does not create one centered sightline through the ship.
- Pressure stairs connect only feasible adjacent deck bands. Service ladders and emergency trunks occupy different `YZ` offsets and serve different deck subsets so they do not form one copied central core.
- Large multi-story volumes use perimeter catwalks, landings, ladders, and maintenance routes. Do not draw a normal transverse floor through a cargo, hangar, reactor, or machinery void merely to simplify navigation.
- Corridors wrap around room footprints, equipment islands, pressure zones, and structural obstructions. They do not cross room centers by default. Each floor uses a distinct topology and may include an offset perimeter route, dogleg, broken loop, notched ring, overlook, or purposeful gameplay spur.
- A route may end only at a named gameplay function such as loot, repair, observation, sabotage, or hazard bypass. Purposeless dead ends are prohibited.
- Every pressure-boundary crossing receives a named socket. Door, stair, lift, ladder, trunk, vent, and breach sockets preserve route direction and deck ownership through Houdini, Blender, and Unreal export.
- Canonical horizontal route splines are `SPL_WALK_PRIMARY`, `SPL_CROUCH_ALTERNATE`, `SPL_CRAWL_SERVICE`, `SPL_VENT_BYPASS`, and `SPL_SQUEEZE_EMERGENCY`.
- Canonical interdeck route splines are `SPL_LIFT_PRIMARY`, `SPL_STAIR_PRESSURE`, `SPL_LADDER_SERVICE`, and `SPL_TRUNK_EMERGENCY`.
- Route state data must cover nominal, lift-disabled, depressurized, fire-obstructed, locked-door, damage-breach, and Bloom false-signal conditions. A Bloom false signal uses the same normal signal presentation as a real signal, with no visible player-facing tell.
- Unreal implementation uses spline components for route identity, navigation modifier volumes for clearances, smart links for stairs, ladders, vents, and squeeze gaps, and dedicated stateful actors for pressure lifts, stairs, service ladders, and emergency trunks. Streaming ownership remains with the local deck band.

## Replacement concept cohort

All nine ships use the established size-class envelope so scale comparisons remain stable. Shape, room program, bay placement, deck allocation, and engine architecture distinguish the roles.

| ID | Size | Type | Envelope | Signature spaces |
| --- | --- | --- | --- | --- |
| `GGP-S01` | Small | Utility Escort | 1,400 x 260 x 320 m | watch CIC, damage control, cargo lock, cryo refuge, crew commons |
| `GGP-S02` | Small | Deep Survey Cutter | 1,400 x 260 x 320 m | sensor chart, sample lab, contamination airlock, cold store, observation room |
| `GGP-S03` | Small | Salvage Recovery Tender | 1,400 x 260 x 320 m | salvage control, tool lock, dirty decon, parts sorting, fabrication bay |
| `GGP-M01` | Medium | Military Corvette | 2,400 x 430 x 620 m | armored CIC, tactical plotting, security center, casualty station, offset marine ready room |
| `GGP-M02` | Medium | Research Cruiser | 2,400 x 430 x 620 m | wet lab, xenobiology containment, sensor theater, specimen cold archive, fabrication lab |
| `GGP-M03` | Medium | Medical Quarantine Cruiser | 2,400 x 430 x 620 m | triage, surgery, isolation ward, decon lock, medical logistics |
| `GGP-L01` | Large | Expedition Carrier | 6,500 x 1,400 x 1,800 m | flight operations, carrier concourse, strategic command, habitat district, reactor refinery |
| `GGP-L02` | Large | Colony Habitat Ark | 6,500 x 1,400 x 1,800 m | habitat neighborhoods, hydroponics, civic commons, hospital, colony fabrication |
| `GGP-L03` | Large | Fleet Logistics Carrier | 6,500 x 1,400 x 1,800 m | cargo interchange, fabrication district, refinery, repair dock, logistics command |

## Concept and production deliverables

Each ship receives an exterior baseline, canonical integration and circulation raster sheets, and one machine-readable manifest:

1. Replacement exterior baseline: approved role and hull identity retained as source context.
2. Vertical-stack room production overview: full stack cutaway, straight main-engine alignment, five role-specific rooms, transverse plans and sections, story construction, and asymmetric room language.
3. Enlarged room and traversal spline reference: large room cutaways, YZ plans, X sections, named traversal and utility splines, sockets, clearances, suit envelopes, volumes, render overlays, and Houdini to Blender to Unreal mapping.
4. Production JSON: provenance, dimensions, coordinate frame, story layers, room-kit modules, straight main-engine constraints, traversal and utility splines, pivots, sockets, suit clearances, volumes, render layers, collision, animation, VFX, budgets, asymmetry checks, gravity checks, and verification state.
5. Exterior and deck asymmetry integration reference: maps unequal deck footprints, partial floors, voids, offset structural spines, room centroids, and functional hull openings back into the approved exterior identity.
6. Player circulation and deck connectivity reference: maps distinct per-floor `YZ` corridor networks plus lifts, pressure stairs, ladders, emergency trunks, vents, crawl routes, pressure boundaries, fallback routes, and engine integration data.

Generated labels, measurements, and mechanical details remain proposals until reconciled with the JSON and project documents. The JSON and this document control implementation where a generated raster label is ambiguous.

## Demo priority

`GGP-S01` remains the first demo-production candidate because the PRD already names the Small Utility Escort as the canonical vertical slice and its gameplay loop, district code, and room catalog are the most mature. Replacement art must preserve those gameplay requirements while changing the hull and room architecture to this gravity frame.
