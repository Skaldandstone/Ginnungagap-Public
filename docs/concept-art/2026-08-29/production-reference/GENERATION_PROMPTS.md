# Final Image Generation Prompt Set

Built-in OpenAI image generation was used with project-local reference images. Every prompt asked
for production clarity, consistent geometry, short all-caps labels, no illegible paragraphs, and no
watermark.

## GGP-01 Companionway Modular Kit

References: the clean, damaged, damaged low-light, and Bloom corridor concepts under
`Content/Assets/ConceptArt/Corridors`.

Prompt: transform the source progression into a modular Unreal and Blender board containing a clean
assembly, front section, top plan, straight, corner, T-junction, four-way, pressure door, floor,
ceiling, service wall, obstruction socket, and clean, damaged, unpowered, depressurized, and Bloom
states. The final correction locked the module to a 6 m bay, 3.6 m traversal width, and 6.0 m
procedural height.

## GGP-01 Modular Interior Room Kit

References: CIC, bridge engineering, cryo quarters, and workshop or mess sheets from the primary
Unreal concept library.

Prompt: derive one reusable pressure-shell kit with a 6 x 6 m planning bay, 3.2 m clear occupied
height, twelve numbered construction modules, nine role-dressing examples, five room states,
material palette, and human scale.

## GGP-01 Wayfarer Exterior Master

References: Wayfarer model sheet v4, cross sections, approved escort exterior, and concept-match
beauty view.

Prompt: create a kilometer-scale master exterior board with hero, side, top, front, and rear views,
exact 1,400 x 260 x 320 m bounds, five streaming districts, clean hull, replaceable armor, docking,
defense, VFX, and Bloom layers. The final correction removed invented statistics and locked
operational decks to 24-32 and maximum complement to 1,000.

## GGP-01 Shared Pressure Suit System

References: V25 concept-lock front, profile, and rear, the role lineup, hands-free equipment, and
the corrected v2 production sheet.

Prompt: recreate the sheet directly from the V25 lock: fitted graphite textile, compact off-white
chest frame and display, circular collar, clear bubble visor, rectangular pack, exactly two short
ribbed hoses, narrow forearm modules, fitted gloves, harness and thigh loops, knee shells, and compact
boots. Include front, strict profile, rear, three-quarter, exploded parts, close-ups, materials,
deformation, skeleton, sockets, exactly one left and one right first-person arm, LODs, and export
checks. The corrected role strip is Science, Engineering, Medical, and Security.

## GGP-01 Suit Body Profile and Clearance Matrix

References: corrected shared suit v2, V25 concept-lock views, `docs/CharacterCreator.md`, and the
traversal requirements in the PRD.

Prompt: preserve the same suit across compact, medium, and tall crossed with narrow, standard, and
broad bodies. Use the documented 150-210 cm height, 34-58 cm shoulder width, 18-38 cm body depth,
45-160 kg mass, and 0.90-1.10 arm-span ratio. Map standing, crouched, crawling, vent crawl, sideways
squeeze, and damaged-door gap envelopes. Add soft-suit grading, rigid-shell fit, harness adjustment,
hose slack, first-person camera and capsule alignment, exact collision-profile rules, nine-body
minimum, morphs, physics assets, LOD parity, tool sweeps, and imported-bounds validation.

## Bloom Threat Family Production System

References: infected crew, Bloom threat lineup, Bloom robotics, and reanimated crew variants.

Prompt: produce front, side, back, and three-quarter family views for crawler, reanimated crew,
mechanized host, and brute host, plus clean-host, infection, crystal, tendril, core, VFX, growth
socket, animation, and early-to-late progression breakdowns.

## Military Corvette Critical Spaces Kit

References: primary Unreal concept-library corvette corridor, med bay, and Bloom reactor images.

Prompt: derive one heavier military-corvette construction family with twelve shared modules and
nominal, damaged, unpowered, depressurized, quarantine, and Bloom states. All room dimensions were
explicitly marked as requiring measured project input.

## GGP-01 Modular Helmet HUD

References: the in-helmet HUD concept, visor frame v2, and Bloom player-perspective HUD.

Prompt: create a sparse visor HUD board with a 16:9 safe-area grid, thirteen numbered zones,
component library, baseline, interaction, warning, critical, scan, and Bloom-warning states, plus
scale, opacity, shape, caption, reduced-motion, and safe-area guidance. One edit corrected the
BRACKETS label. The v2 correction removed the player-visible false-signal label and violet treatment,
then made fabricated Bloom telemetry visually identical to a genuine amber Bloom warning. Scan mode
retains its separate violet presentation because it is an explicit player action rather than a
truth-source disclosure.

## GGP-01 Shipboard Interface System

References: CIC workflows, first-person sensor console, CIC room sheet, and helm destination console.

Prompt: create one physical-console component language with shared grid, components, physical
control prompts, focus handoff, touch and distance guidance, sensor acquisition, contact analysis,
power routing, helm or jump commit, state matrix, input modality, and component scale sections.

## GGP-01 Pressure Suit Traversal and Performance V2

References: corrected shared suit v2, zero-g maintenance, suit-up armory, hands-free equipment, the
PRD, Character Creator, and Magnetic Suit Traversal docs.

Prompt: create twenty complete full-body actions: sealed idle, walk, sprint, crouch, vent crawl,
sideways gap squeeze, ladder climb, mantle, zero-g drift, push-off, mag-boot wall transition, left
glove anchor, dual glove pull, object pull or throw, scan, repair or rewire, weld or tool brace,
casualty carry, casualty drag, and decompression or low-O2 reaction. Add deformation and rigid zones,
IK anchors, root-motion guidance, first-person parity, role-kit clearance, exactly two hose splines,
29 animation deliverables, nine-body testing, oriented tool sweeps, and the no-tell Bloom rule.

## GGP-01 Science Pressure Suit

References: corrected shared suit v2, role lineup, V23 Scientist module previews, current role enum,
and Science skills and interactions.

Prompt: keep the V25 base unchanged and add removable sensor fairing, analysis display, scanner,
data/comms pod, paired sealed sample cases, and contamination kit. Document Science as the player
display name and `EPressureSuitRole::Scientist` as the enum, explicitly replacing Crew. Include
scan, mark, sample, stow, analyze, survey, zero-g sensor, and secured vent-crawl actions. Genuine and
false Bloom signals must be identical in every presentation channel.

## GGP-01 Engineering Pressure Suit

References: corrected shared suit v2, role lineup, V23 Technician module previews, and
`docs/PlayerSuitAssets.md`.

Prompt: keep the V25 base unchanged and add a conformal service bib, thermal backplane, paired power
cells, cable reel, folded tool-arm dock, welder, and diagnostic meter. Engineering is canonical;
Technician is an art-source alias. Include diagnose, repair, rewire, weld, breach seal, reroute
power, large-tool brace, zero-g maintenance, cable spline, oriented tool sweeps, nine-body grading,
and constrained traversal checks.

## GGP-01 Medical Pressure Suit

References: corrected shared suit v2, role lineup, V23 Medical module previews, and medical systems
in the PRD.

Prompt: keep the V25 base unchanged and add telemetry, patient monitor, injector bank, sterile pack,
paired trauma cases, rescue tether, and medical utility pouch. Include patient scan, injection,
airway stabilization, suit patch, casualty carry, casualty drag, zero-g rescue, and secured vent
crawl. Map patient and anchor IK, tether spline, sterility and contamination masks, nine-body fit,
first-person access, and constrained traversal.

## GGP-01 Security / Recovery Pressure Suit

References: corrected shared suit v2, role lineup, V23 Marine module previews, and Security / Recovery
systems in the project.

Prompt: keep the V25 base unchanged and add a conformal cuirass, paired shoulder and forearm guards,
restraint pouch, breach tool, paired recovery hardpoints, recovery tether, and drag harness. Security
is canonical; Marine is an art-source alias. Include guarded scan, restraint, breach assist, tool
brace, carry, drag, mag-boot transition, and zero-g recovery. Weapons remain separate from the suit.
Map recovery IK, tether spline, all-profile fit, first-person access, and crawl or squeeze stowage.

## Bloom Threat Family Animation, VFX, and Intensity Mapping

Reference: `bloom-threat-family-production-system-v1.png`.

Prompt: create four family rows for crawler, reanimated crew, mechanized host, and brute host, each
with idle, alert, contact, passing, attack anticipation, attack impact, hit react, and death poses.
Add rig controls, growth sockets, root-mid-tip tendril splines, notifies, collision and damage zones,
Niagara layers, infection intensity zero through three, material channels, render masks, LOD tests,
and Unreal naming. Enemy telegraphs stay readable, but a false player Bloom signal remains identical
to a genuine signal in every presentation channel.

## GGP-01 Wayfarer Spline, Streaming, and Render Mapping

Reference: `ggp01-wayfarer-exterior-master-v1.png`.

Prompt: preserve the 1,400 x 260 x 320 m ship and five streaming districts. Overlay hull guide,
armor flow, navigation light, docking approach, hangar traffic, defense arc, engine plume, utility,
and damage splines. Add pivots, module origins, sockets, HLOD and Nanite policy, collision, shadow,
materials, vertex masks, render passes, damage masks, decals, VFX, LOD silhouettes, and import naming.

## GGP-01 Companionway Spline, Socket, and Render Mapping

Reference: `ggp01-companionway-modular-kit-v1.png`.

Prompt: preserve the 3.6 m width and 6.0 m module length. Map centerline, floor service, ceiling
service, lighting, pipe and cable, decal, and Bloom splines across straight, corner, T-junction, and
four-way modules. Add obstruction and door sockets, snap planes, grid and tolerances, collision,
navmesh, occlusion, streaming, material IDs, vertex masks, trim mapping, render passes, all five
state layers, Unreal construction order, and Blender collections.

## GGP-01 Helmet HUD Data, Render, and State Mapping

Reference: `ggp01-modular-helmet-hud-v2.png`.

Prompt: create a 16:9 visor-safe-area engineering board with numbered anchors and twelve widgets.
Add data bindings, UMG hierarchy, z-order, render layers and targets, material and post-process
channels, timelines, focus states, accessibility, DPI, opacity, reduced motion, localization, and a
state matrix. Genuine and false Bloom warning examples must be identical in color, icon, copy,
pulse, sound, opacity, timing, and animation. The truth source is not exposed to presentation.

## GGP-01 Uncorrupted Robot Family Production System

References: representative RealityScan input frames for Compact Maintenance Robot, Heavy Cargo
Robot, Security Sentry Robot, and Tall Utility Robot.

Prompt: build one family board with scale lineup, front, side, back, and three-quarter views for all
four classes. Mark every dimension as requiring imported-bounds verification. Add modular chassis,
sensor, arm, tool, pelvis, leg, contact, battery, panel, and role parts, materials, rig hierarchy,
IK, tool and cargo sockets, sensor and VFX sockets, cable splines, collision and damage zones, eight
shared animation states, LOD silhouettes, render passes, vertex channels, naming, and exports. Keep
the family practical, safety-first, and completely free of Bloom corruption.

## GGP-01 Cryopod Unit Production System V2

References: Concept V4 artist, closed-fit, open, Unreal, six RealityScan turnaround views, and
`ACryoPodSystem` constants.

Prompt: preserve Concept V4 and show the closed, open, orthographic, top, assembly, component,
occupant-fit, repair, state, animation, collision, audio, VFX, Blender, and Unreal mappings. Lock the
runtime lid to 1.25 seconds and -24 degrees, repair to 4.0 seconds, and validate wake and exit against
all nine body profiles in suited and unsuited states.

## Shipboard Tool and Defense Family 01-40

References: weapon concept boards 01-10, 11-20, 21-30, and 31-40 plus current shipboard weapon code.

Prompt: preserve every numbered concept as exploration, show the shared receiver, grip, working head,
power, safety, authorization, drone, holster, effect, cable, collision, animation, render, and export
architecture. Status requires explicit gameplay mapping. Hazardous conversions are removable and
authorization-gated. Test first-person, third-person, drones, constrained traversal, and all profiles.

## Security, Salvage, and Xeno Tool Family 51-80

References: boards 51-60, 61-70, 71-80 and all checked-in ConceptMappings JSON.

Prompt: show mapped candidates 51-61 and 63, exploration-only 62 and 64-70, and quarantined xeno
concepts 71-80. Separate clean, salvaged, unsafe, biomass, crystal, contamination, and containment
layers. Include exact mapping confidence, mounts, sockets, rig, animation, splines, collision, render,
safety, and all-profile tests. Xeno concepts are not automatic player equipment.

## Pelagos Orbital Arrival Production System

References: Pelagos AAA final and artist passes, operational map, arrival documentation, Data Asset
types, native state sequence, routes, docks, services, hazards, and traffic budgets.

Prompt: build the 60 km local-operations arrival system with four routes, sixteen checkpoints, four
gates, four dock approach and capture sets, twenty-four traffic anchors, ten services, six hazards,
twelve beacons, and four cameras. Map all twelve arrival states plus Departure, authority,
replication, splines, collision, streaming, lighting, VFX, audio, render, rebuild, and QA.

## Command, Observation, and Technical Rooms

References: briefing and observation, command and observation, navigation technical, server workshop,
approved undamaged command lineage, and the explicitly rejected symmetrical CIC.

Prompt: retain source-specific architecture on the 6 m lattice with multi-bay and multi-level
exceptions. Add modules, service splines, sockets, physical consoles, reach, collision, navmesh,
sightlines, cover, constrained traversal, zero-g, casualty, repair, atmosphere, damage, Bloom,
Blender, Unreal, render, and QA. Mark the symmetrical bunker CIC as rejected and do not build it.

## Habitat, Berthing, and Life-Support Rooms

References: crew support, hygiene, operations berthing, quarters, recreation and life support, and
undamaged habitat lineage.

Prompt: build crew support, galley, berthing, quarters, hygiene, recreation, hydroponics, and
life-support archetypes on the shared lattice. Map fixtures, privacy, storage, utilities, drainage,
splines, interactions, all-profile suited clearance, atmosphere, leaks, fire, quarantine, Bloom,
collision, navmesh, audio, VFX, render, Blender, Unreal, and QA.

## Medical, Morgue, and Suit-Bay Rooms

References: medical, morgue and suit-bay, undamaged medical, cryopod support, PRD clinical actions,
and the shared room grid.

Prompt: build treatment, diagnostics, isolation, morgue, suit preparation, donning, decon, and
cryopod-support archetypes. Map patient, casualty, stretcher, morgue, suit, tether, oxygen, air,
power, data, waste, IK, constrained traversal, sterile and contaminated routes, states, materials,
audio, VFX, render, Blender, Unreal, and all-profile QA.

## Security, Brig, and Damage-Control Rooms

References: security and brig, undamaged security, server workshop, rejected symmetrical CIC, and
PRD security and damage-control actions.

Prompt: build security checkpoint, authorized storage, evidence, brig, interview, damage control,
and emergency response with asymmetric circulation and physical authorization. Map restraint,
rescue, line-of-fire, cover, sightlines, nonlethal safe zones, collision, navmesh, actions, state
layers, audio, VFX, render, Blender, Unreal, all profiles, and the no-automatic-weapon-approval rule.

## Fleet Exterior Class and Lineage System

References: verified Small Utility Escort concept-match bounds, current Medium Military Corvette and
Large Expedition Carrier direction, scale lineup, Wayfarer lineage, remasters, and sculpt reviews.

Prompt: preserve distinct class silhouettes and use 1,400 x 260 x 320 m, 2,400 x 430 x 620 m, and
6,500 x 1,400 x 1,800 m. Mark the 900 m Small remaster scale superseded. Show orthographics,
districts, pivots, sockets, splines, collision, materials, decals, VFX, audio, render, Nanite, HLOD,
World Partition, Blender, Unreal, export naming, lineage lifecycle, and imported-bounds QA.

## Local Operations Celestial and Phenomena System

References: blue-white radiation, fractured ring, gravity anomaly, operational map, radiation hero,
space-system phase lineage, and checked-in planet and nebula textures.

Prompt: separate the 60 km local-operations volume from AU-scale strategic space. Build ocean,
fractured ice, gas-band, volcanic, radiation, anomaly, debris, mission-site, beacon, traffic, route,
sensor, volume, material, VFX, audio, lighting, streaming, collision, render, Blender, Unreal, rebuild,
performance, lineage, and not-to-scale QA mappings.

## Front-End and Versus Perspective UI System

References: main-menu backdrop, antagonist perspective sheet, helmet HUD v2, and PRD front-end and
versus requirements.

Prompt: preserve the world-backed main menu and separate survival, antagonist, commander, spectator,
and respawn perspectives. Add menu states, focus, inputs, safe areas, aspect ratios, UMG hierarchy,
bindings, forbidden inputs, render targets, z-order, materials, animation, audio, accessibility,
localization, automated tests, and Unreal destinations. Genuine and false Bloom warnings remain
identical, and antagonist diagnostics never leak into the survival HUD.
