# Ginnungagap Art and Visual Style Guide

Status: working visual target for review, 28 August 2026. This is additive and does not mark the
PRD's final visual-target approval as complete.

This guide consolidates the visual language already implied by the PRD, production material tools,
ship remaster documents, clean/Bloom asset separation, and the active `Ginnungagap - UI Draft`
Figma file. It gives concept art and production assets one direction while final approval remains
open.

## Visual thesis

**Maintained expedition hardware being slowly rewritten by alien biology.**

The clean world is engineered, repairable, labelled, and physically understandable. The Bloom is
adaptive, opportunistic, and difficult to read completely. Horror comes from a trusted industrial
system behaving almost correctly after something living has learned its shape.

## Pillars

1. Physical before digital. Important navigation, repair, inventory, and ship decisions live on
   stations, tools, labels, and moving parts. The visor shows body/suit telemetry and urgent context.
2. Used, not ruined. Clean ship equipment has wear, service history, and field repair, but it remains
   maintained. Generic post-apocalyptic rust is not the baseline.
3. Bloom as semantic corruption. Purple, crystalline, organic, veined, and bioluminescent treatment
   signals infection. It must not decorate clean first-use assets.
4. Scale through repetition. Ship silhouettes and interiors communicate kilometre scale through
   repeated modules, pressure boundaries, structural ribs, distant machinery, and human-scale access.
5. Information is imperfect, not arbitrary. Visual noise, sensor uncertainty, and false readings
   should leave evidence a crew can discuss.

## Palette

### Clean expedition hardware

| Role | Direction |
| --- | --- |
| Void | Blue-black and near-black, never flat featureless black |
| Structure | Gunmetal, graphite, tungsten, dark coated steel |
| Armour | Warm off-white ceramic and desaturated light composite |
| Safety | Intact industrial orange and restrained hazard yellow |
| Telemetry | Neutral white-blue and cold cyan |
| Emergency | Amber first; red only for immediate catastrophic danger |

The Compact Rock Corer clean reference is the material precedent: off-white ceramic armour, intact
orange safety marks, gunmetal tooling, and white-blue indicators.

### Bloom

Bloom colour occupies a separate family: bruised violet, ultraviolet magenta, dead tissue grey,
calcified bone, wet near-black, and selective bioluminescent bloom. It invades seams and systems; it
does not recolour every surface uniformly. Reserve the brightest emission for active adaptation,
spores, sensory organs, and system takeover.

## Materials and surface language

- Hard surface: high roughness variation, readable coating boundaries, service wear at contact
  points, replaceable panels, fasteners, seals, and thermal discolouration where physically justified.
- Bloom: fibrous growth following cable runs and airflow, calcified barriers, translucent sacs,
  host-shaped shells, asymmetric tendrils, and rigid biological structures that imitate machinery.
- Damage: pressure, heat, impact, electrical arcing, contamination, and emergency patching should be
  distinguishable at a glance.
- Do not use purple on a clean asset unless it is explicitly contaminated or the purple is a tiny,
  clearly non-Bloom faction marking approved for that asset.

## Ships and environments

- Ship architecture follows [Ship Architecture Authority](ShipArchitectureAuthority.md). The deck
  stack and thrust axis are the same. Canonical stack proofs show bow and `+X` above, engines and
  gravity below along `-X`, and every transverse floor between its occupants and the engines. Room
  views appear upright because their geometry is authored in that same local thrust-gravity frame.
- Exteriors are structurally legible and intentionally asymmetric. Use broad calm armor fields,
  recessed functional openings, and a small number of offset masses rather than copied port and
  starboard halves.
- Drive districts use unequal, function-specific main-engine modules with parallel `X` centerlines
  and nozzle exits on one common aft plane. Keep maneuvering thrusters separate. Do not use canted
  main drives, a cloned engine wall, decorative propulsion wings, or repeated nozzle rows.
- Interiors use pressure logic: bulkheads, seals, maintenance access, life-support runs, local
  lighting, and equipment clearances define each room before set dressing.
- Interior composition is functionally asymmetric. Reusable kit pieces may repeat, but room layouts,
  equipment clusters, circulation, and service density must not read as mirrored or copy-pasted.
- Clean lighting is practical and local: work light, instrument spill, emergency strips, distant bay
  illumination. Bloom scenes preserve some readable clean light so corruption has something to oppose.
- Avoid endless dark corridors, decorative greeble without function, exterior protrusion clutter,
  pristine luxury sci-fi, and blue holograms carrying information that should exist on a physical
  control.

## Characters and threats

- Pressure suits are modular industrial life-support systems. Science, Engineering, Medical, and
  Security / Recovery roles differ through chest modules, tools, markings, and wear before colour
  alone. Crew is a collective noun, not a playable class.
- First-person gloves and held tools must remain readable against both clean and Bloom backgrounds.
- Bloom creatures retain evidence of what was taken over: crew anatomy, drone pivots, ship fixtures,
  or cable topology. Their adaptation is functional, not random spikes.
- Non-Bloom factions need their own silhouette, material, and light language; do not make every threat
  a colour-swapped Bloom enemy.

## HUD and interaction

The active Figma HUD concept establishes the baseline: sparse cyan suit telemetry at the upper left,
navigation and system state at the upper right, a minimal centre reticle, restrained scanlines, and
amber for the current objective or warning.

- Preserve the centre and lower field for the world and physical tools.
- Use monospaced, compact telemetry with plain labels and stable numeric alignment.
- Cyan means nominal information, amber means attention, red means immediate danger, and Bloom
  violet means contamination or untrusted data.
- Prompts confirm an affordance already present in the world; they do not replace labels, handles,
  moving parts, or station design.

Working file: https://www.figma.com/design/CqMu7Ojx1RQRQVTIyKWJU8/Ginnungagap-UI-Draft

## Concept-art briefs

Every concept should name its production question: silhouette, room function, material boundary,
enemy adaptation, lighting state, traversal read, or HUD readability. A beautiful image that answers
none of those is mood art, not design authority.

For environment concepts, provide clean and affected states from the same camera when possible.
For assets intended for modelling, add orthographic or controlled turntable views after the hero
concept. AI-generated rotations are visual references, not photogrammetry-ready geometry.

## Anti-goals

- Generic purple alien goo on every infected asset.
- Clean assets that already look corrupted.
- Pure darkness used to hide unresolved environment design.
- Holographic UI replacing physical ship operation.
- Decorative Nordic motifs with no in-world origin.
- Unreadable grime, chromatic aberration, film grain, or scanlines over critical telemetry.
- Proxy meshes presented as final production art without an explicit label.

## Source hierarchy

1. Product behaviour and status: `docs/PRD.md` and linked implementation ledgers.
2. This guide for cross-category visual consistency.
3. Approved asset-specific documents and clean/Bloom reference sets.
4. Figma for current interface composition.
5. Exploratory concept art, clearly labelled until approved.
# Production Reference Addendum

## Asset-first concept rule

Every new concept must identify a downstream Unreal asset or modular kit. Production sheets should prioritize consistent orthographic construction, scale, pivots, sockets, modular boundaries, material slots, clean/Bloom state compatibility, interaction points, animation requirements, and separate VFX layers over cinematic presentation.

Generated measurements, labels, names, and mechanical details are proposals until reconciled with gameplay and technical requirements. Do not treat polished generated text as canon. Preserve the approved visual language and asset intent while resolving contradictions during modeling.

## Bloom implementation

- Keep the clean hard-surface asset reusable beneath contamination states.
- Build Bloom growth, tendrils, emissive nodes, decals, and ambient particles as separately controllable layers.
- Prefer masks, modular overlays, sockets, and material instances over duplicating entire environment kits.
- Maintain cold cyan Bloom light against restrained amber human work lighting.
- Keep infected silhouettes recognizable as repurposed human tools, spaces, suits, and machines.
