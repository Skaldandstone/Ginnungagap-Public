# Ginnungagap - Product Requirements Document

**Status as of:** 2026-08-24 (front-end/multiplayer, character system, and Small Escort interior
sections refreshed against the current `main`; the rest of this document has not been re-audited
line by line - see the note at the end of §11)

**Engine:** Unreal Engine 5.8

**Runtime module:** `Ginnungagap` (`GINNUNGAGAP_API`)

**Current milestone:** playable production vertical slice and multiplayer foundation

**Canonical startup map:** `/Game/UI/MainMenu`

**Canonical playable demo:** `/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck` - this is what
`UMenuManagerSubsystem::GameModeLevelMap` actually loads for Single Player, Co-op, and Versus from
the Start Game flow. `L_Small_Companionway_Showcase` (the fitted four-room pass described in
[Ship Production Vertical Slice](ShipProductionVerticalSlice.md)) still exists and is still asset-
validated, but is no longer what a player reaches by starting a game from the menu.

This document is the product-level source of truth for what exists, what is only partially complete,
and what remains before the project is demo-ready and production-ready. Detailed implementation
ledgers remain in the linked documents and are not duplicated here.

---

## 1. Product Vision

Ginnungagap is a first-person co-op survival-horror game about keeping a damaged interstellar ship
and its crew alive while an adaptive xenobiological antagonist, the Bloom, learns from the crew's
behavior. The player experience combines physical ship operation, imperfect navigation, EVA,
resource recovery, damage control, clinical survival, and escalating mistrust.

The intended expedition rhythm is:

1. Arrive in a system with incomplete or corrupted information.
2. Survey hazards, resources, routes, and mission opportunities.
3. Operate, repair, and defend the ship while gathering what is needed for the next jump.
4. Select one of no more than six candidate destinations.
5. Return to functioning cryogenic protection during the jump warning.
6. Resolve jump consequences and the Bloom's hidden adaptation.
7. Discover what changed only after arrival and repeat until victory, loss, or self-destruction.

### Product pillars

- **Cryo-or-suffer tension:** missing a jump's cryo window causes lasting but normally nonfatal
  consequences; remaining outside the ship can be fatal.
- **Hidden adaptation:** the Bloom evolves during jumps from prior hazards and player actions. The
  game communicates symptoms and consequences, never its complete internal state.
- **Imperfect foreknowledge:** sensor quality, astrophysics, and Bloom corruption determine how much
  the crew can trust destination and contact data.
- **Physical ship operation:** navigation, repairs, inventory, configuration, and mission work live
  on physical stations; the helmet HUD is reserved for body/suit telemetry and urgent context.
- **Resource-gated survival:** internal reactivation, EVA retrieval, and drone dispatch produce the
  materials needed to repair, upgrade, and continue.
- **Grounded co-op roles:** crew members specialize through equipment, suit role, skills, procedures,
  and shared ship responsibilities.
- **Overlapping threats:** Bloom, pirates, rebels, alien creatures, environmental hazards, and human
  error may coexist instead of being mutually exclusive encounter modes.

---

## 2. Scope and Delivery Definitions

Status in this document means:

| Status | Meaning |
| --- | --- |
| **Implemented** | Runtime code/content exists and is wired into an accessible path. |
| **Foundation** | Core data model or runtime path exists, but production content, UX, networking, or tuning remains. |
| **Validated** | Relevant compile, automation, map validation, cook, smoke test, or documented visual QA has passed. |
| **Blocked** | A known issue prevents the affected content from being considered healthy or shippable. |
| **Planned** | Required product work has not been implemented. |

An automation test passing does not replace multiplayer, PIE, usability, balance, performance, or
content QA. Likewise, a generated asset existing does not mean it is final production art.

### Current repository baseline

- 164 C++ implementation files and 176 headers in the runtime module.
- 956 `.uasset` packages and 11 maps under `Content/`.
- Native automation coverage across gameplay foundations, input, menus, demo defaults, modular
  rooms, player suits, status effects, weapons, threats, Pelagos, sensors, and versus rules.
- Reproducible Blender/Unreal Python pipelines for ships, fitted rooms, player suits, weapons,
  space systems, Pelagos, menus, model libraries, captures, validation, cooking, and packaging.
- Windows Development package and map smoke logs exist for the main menu and all three ship
  districts.

---

## 3. Current Player Experience

### 3.1 Front end and launch flow - Implemented, partially validated

- The project starts in `/Game/UI/MainMenu` using `AMainMenuGameMode` and
  `AGameInitializerController`.
- Native fallback widgets provide title, mode selection, expedition customization, first-launch
  character creation, co-op/versus host setup, settings, and in-game pause/progression surfaces.
- New Game, Continue, save-backed expedition configuration, call-sign validation, pressure-suit
  role selection, and destination-map validation are implemented.
- Display settings persist through `UGameUserSettings`, including quality, render scale, window
  mode, VSync, frame cap, defaults, and timed confirmation/revert.
- The title backdrop and restrained native motion treatment are implemented with a reduced-motion
  option.
- Single-player survival, co-op survival, and versus are exposed by the menu flow.
- A boot/title gate (`ShowBootSplash`/`OnTitleGateFinished`), replicated crew lobby
  (`ALobbyGameState`/`ALobbyPlayerState`), and `UMultiplayerSessionSubsystem`-backed crew
  matchmaking (host, find/join, leave, reconnect-on-failure messaging) are now implemented and wired
  into `UMenuManagerSubsystem`, superseding the older "Host Lobby only" prototype path.
- **Remaining:** public matchmaking and platform friend invitations are explicitly disabled and
  unimplemented; the crew lobby/matchmaking flow above is implemented but not yet PIE-validated with
  a second client (tracked as TRO-54); controller focus, resolution coverage, accessibility, and
  every back/continue path still require a complete interactive QA pass.

### 3.2 Player, survival, interaction, and traversal - Implemented foundation

- `ACoopSurvivalCharacter` owns replicated health, oxygen, radiation, suit integrity, stability,
  inventory, equipment, activities, status effects, psychosis, pathogen load, interaction, weapon,
  and zero-G/magnetic traversal components.
- First-person helmet view is the default. Contextual third person is available for authored
  traversal and readability-sensitive actions.
- Keyboard and gamepad mappings cover movement, look, interaction, activities, jump/push-off,
  weapon fire/mode, magnetic boots, independent glove grips, thruster rotation, object throw,
  psychosis reality check, and menus.
- `IInteractable` plus `UInteractionComponent` remains the single interaction route.
- Zero-G movement, pseudo-gravity, gravity-aligned camera roll, push-off, magnetic boots, independent
  glove anchors, held-object pull/throw, and rotation-thruster fuel are implemented with server
  validation where authoritative interaction is required.
- The native visor HUD presents vitals, contamination, active conditions, interaction prompts,
  jump/life-support/self-destruct warnings, activity state, and tracked navigation cues.
- **Remaining:** end-to-end PIE/network tuning for zero-G, magnetic traversal, camera transitions,
  collision edge cases, input conflicts, animation readability, and production audio/VFX.

### 3.3 Pressure suits and character presentation - Implemented, production validation ongoing

- Four playable pressure-suit roles exist: Science, Engineering, Medical, and Security / Recovery.
  `EPressureSuitRole::Scientist` retains enum index 0 for save compatibility and replaces the
  obsolete Standard Crew role. Technician remains an art-source alias for Engineering.
- The modular suit uses UE Manny animation, role-specific chest modules, PBR material sets, dynamic
  damage/grime/Bloom contamination, first-person visibility rules, replicated role selection, and a
  live character-creation preview.
- Suit regeneration, showcase, fixed-pose audit, PBR generation, attachment validation, and
  multiplayer asset-resolution tests are documented and scripted.
- Source art includes production-v2 through production-v6 Blender passes, deformation/close-up QA,
  concept crops, renders, and import tooling.
- The 32 previously zero-filled packages under
  `Content/Characters/Player/Suit/PackagedCombined` have been regenerated from the checked-in
  Unreal export package. The repaired set includes 20 textures, four materials, four combined role
  meshes, two equipment meshes, and two skeletal-prototype packages; clean asset-registry and model
  validation now pass without `PACKAGE_FILE_TAG` errors.
- **Remaining:** final hero-quality face/hair/body art, final deformation and clipping approval,
  production material masks for magnetic feedback, authored traversal animations, and complete
  first-/third-person visual QA.
- **Known issue:** two independently-built character-appearance systems currently coexist on
  `ACoopSurvivalCharacter`/`FCharacterProfile` - a MetaHuman-preset-ID system
  (`FirstLaunchCharacterCreationWidget`) and a body/face/skin/hair/voice-preset-enum system
  (`CharacterCreatorWidget`) with its own role-based primary-oversuit swapping. Both compile and are
  wired into the menu flow as a merge stopgap; one needs to become canonical (tracked as TRO-215)
  before further character-creation UI work builds on top of either.

### 3.4 Clinical survival and psychological horror - Implemented foundation

- `UPlayerStatusEffectComponent` provides replicated, server-authoritative conditions with severity,
  duration, source category, triage priority, and treatment guidance.
- The current catalog covers hypoxia, jump psychosis, radiation sickness, decompression trauma,
  hypothermia, heat stress, space-motion sickness, CO2 toxicity, acute stress, hemorrhage, fracture,
  and burn trauma.
- Hazards, collisions, life support, cryo, medical stabilization, field procedures, respawn, scanner
  diagnostics, and visor display are integrated.
- `UPlayerPsychosisComponent` produces owner-only apparitions, false telemetry, spatial audio events,
  contradictory voices, escalation phases, grounding, and reality checks without altering
  authoritative world state.
- **Remaining:** production hallucination art/audio/performance, medication and grounding content,
  multiplayer privacy/usability tests, clinical balance, accessibility options, and narrative review.

---

## 4. Ship, Expedition, and World Systems

### 4.1 Authored production districts - Implemented and smoke-tested

- The canonical ship frame is defined in [Ship Architecture Authority](ShipArchitectureAuthority.md):
  the long hull, thrust axis, and tower-like deck stack are aligned; authored gravity down points
  aft toward the engine base; floors are transverse to the hull and face aft; and deck numbering
  rises toward the bow. Replacement ships and
  rooms must be intentionally asymmetric, low in exterior protrusion clutter, and free of copied
  engine walls.
- Three production districts exist:
  - Small Utility Escort companionway: 12 m × 52 m × 4.3 m.
  - Medium Military Corvette express spine: 32 m × 72 m × 7.6 m.
  - Large Expedition Carrier concourse: 48 m × 92 m × 12 m.
- The Small Utility Escort is the canonical demo and contains the complete resource/sensor/helm/
  jump/cryo loop plus objectives, encounters, pickups, checkpoints, and transit.
- Production maps suppress the legacy procedural builder to prevent overlapping ships.
- Transit consoles cycle Small → Medium → Large → Small while preserving district checkpoints.
- Packaging config explicitly cooks the main menu and all three districts. Windows cook/package/
  smoke-test scripts are checked in; existing packaged smoke logs show all three districts and the
  main menu loading and exiting successfully.
- **Remaining:** replace prototype kit pieces with final Nanite/trim-sheet art, finish Lumen/audio/
  decals/VFX/damage states, define streaming strategy for kilometer-scale full ships, and validate
  target-platform performance budgets.

### 4.2 Modular rooms and fitted production pass - Implemented and validated

- `AModularShipRoom` extends ship sections with stable room codes, player-facing names, archetypes,
  dimensions, eight socket positions, reciprocal topology, atmosphere coefficients, gameplay
  profiles, typed anchors, replicated operational state, readiness, habitability, quarantine,
  power, damage, contamination, signage, and identity-light bindings.
- The procedural ship catalog uses explicit room-to-room edges rather than index inference.
- The fitted pass creates 18 gameplay-addressable rooms, 15 pressure bulkheads, and 198 deterministic
  dressing pieces across the three production districts. The Small Utility Escort's first production
  district (`L_SmallEscort_OperationsDeck`) has since been substantially expanded beyond this
  baseline - see [Small Escort Interior Plan](SmallEscortInteriorPlan.md) for the current 24-room,
  corridor-materialized, per-room-sized, hardpoint-driven version of that district; the room/dressing
  counts above are stale for that district specifically and have not yet been re-tallied here.
- Generated actors are idempotent and isolated by stable `ModularFit_` labels.
- Validation covers dimensions, identity, topology, reachability, socket conflicts, profiles,
  bindings, actor budgets, and generated dressing.
- **Remaining:** convert more authored districts to reusable room Level Instances/World Partition
  cells, add final art variants and traversal nav, exercise replicated room state in multi-client
  destructive scenarios, and reconcile [Room Systems Ledger](RoomSystemsImplementationLedger.md)'s
  action-161–660 baseline with the Operations Deck expansion above.

### 4.3 Ship systems, power, atmosphere, damage, and quarantine - Foundation

- Ship sections, navigation/pathfinding, doors, power nodes/grid, damage state, pressure transfer,
  quarantine, environment presets, Bloom corruption, life support, sensors, helm, cryo, escape pod,
  self-destruct, armor plating, collector, and interactive fixtures exist.
- Production bulkheads, terminals, emergency lights, ventilation controls, purge stations, and
  corruptible machinery are reusable Blueprint-facing actors.
- Clean, Alert, Damaged, Colony, Swarm, Puppeteer, Infector, and Manifestation environment presets
  drive lighting, fog, post-processing, decals, ambience, and growth presentation.
- `UShipDamageComponent` models hull, breaches, fire, electrical faults, local atmosphere, repair,
  sealing, suppression, and repressurization. `UShipPowerGridSubsystem` allocates generation/storage
  to consumers by bus and priority.
- `AArmorPlatingSystem` consumes structural alloy for repair and mitigates thermal/pressure hazards.
- `ACryoPodSystem` now combines a multi-part procedural visual (bed/detail/hinge/restraints/status
  lights/lid frame/glass, assembled in `OnConstruction` from the GeneratedV3 mesh set) with
  curve/duration-based lid animation and replicated `bLidOpen` - merged from two independently-built
  implementations and not yet confirmed in PIE (tracked as TRO-216).
- **Remaining:** generator/storage content and fuel economy; tuned demand/load shedding; universal
  enforcement of power/operational gates; door/vent atmosphere simulation; gameplay damage sources;
  breach/fire actors and VFX; repair costs/tools; system-specific failure consequences; full
  multiplayer authority and tuning.

### 4.4 Activities, maintenance, and field work - Implemented foundation

- `UPlayerActivityComponent` turns interaction into cancellable, server-authoritative sessions with
  replicated snapshots and native HUD/minigame presentation.
- Scan, repair, build, rewire, and welding mechanics exist, including Bloom interference and the
  weldable emergency bulkhead.
- Twenty dedicated maintenance/operations station presets apply authoritative outcomes to ship,
  suit, medical, power, drone, containment, and Bloom targets.
- A field catalog provides 150 procedures. A specialist catalog adds 100 procedures, each with five
  variants, for an exact 500-implementation matrix.
- Procedural records and typed completion hooks support mission generation, checkpoints, telemetry,
  Blueprint presentation, and future streaming regeneration.
- **Remaining:** authored station animations/audio/tool models, richer failure consequences, final
  input/minigame UX, item/equipment consumption across the complete catalog, procedural placement
  rules, mission rewards, co-op contention/assistance, and balance.

### 4.5 Inventory, equipment, progression, objectives, and persistence - Mixed foundation

- Replicated inventory supports capacity, mass, stacking, splitting, transfer, tags, and item Data
  Assets. Mission objectives support prerequisites, hidden/required/optional state, progress, jump
  gating, persistence, and currency rewards.
- Character profile, expedition run, district checkpoint, run outcome, and banked-currency save
  types exist.
- The skill tree is role-based, keyed to `EPressureSuitRole` (Scientist, Engineering, Medical,
  Security) so a player's tree matches the oversuit they wear. Skills split into permanent
  passives and a three-slot payload of triggered actives with cooldowns, durations and optional
  per-run charges; both ranks up. Every skill carries a named effect ID with a live consumer.
  Purchase rules, prerequisites and pricing live in the catalogue rather than the UI.
- Native widgets exist for the tree, the pre-run payload picker, and the in-run ability bar.
- Win, hard loss, escape/self-destruct, jump-count, Bloom-eradication, player-survival, and currency
  outcomes are implemented.
- Equipment has five slots, durability, resistance/stat data, role visuals, and pickups.
- Equipment bonuses apply. Radiation resistance, suit integrity and movement are wired; protection
  scales continuously with remaining durability rather than switching off at zero. Thermal,
  pressure-threshold and dust resistances remain unwired because no hazard consumes them yet.
- **Remaining:** inventory lacks secure request RPCs, item use, quick slots, world drop/containers,
  death/disconnect policy, save serialization, encumbrance, fabrication integration, production
  items, and full UI. Skill unlocks, equipment purchases, and banked-currency spending need one
  coherent meta-progression loop. Skill magnitudes are reasoned rather than playtested, and solo
  vs co-op balance has had no play pass.
- **Remaining:** timed/procedural missions, failure consequences, objective-specific listeners,
  primary/side-objective UI, reward balance, replicated objective authority, and an authored
  end-to-end mission campaign.

---

## 5. Navigation, Jump, Resources, and Space

### 5.1 Sensor, helm, and ship-relative travel - Implemented foundation

- Sensors generate up to six jump candidates with hazard/resource uncertainty and possible
  falsification. Short-/long-range upgrades and Bloom corruption alter range and classification.
- Live contacts expose identity, type, world position, range, bearing, and tracking. Unknown contacts
  do not leak ground truth.
- The sensor console provides selectable contact rows, resource-operation state, and drone dispatch.
- Helm solutions include desired direction, heading error, ETA, hazard-route intersection, clearance,
  stopping distance, detours, arrival burn, arrival tolerance, and operations targets.
- Ship-relative propulsion keeps the multi-actor interior stationary while generated exterior
  actors and POIs translate consistently.
- **Remaining:** final physical console UI, co-op replication/usability, pilot controls, authored
  travel feedback, autopilot policy, docking integration between general navigation and Pelagos,
  route/performance stress testing, and production balance.

### 5.2 Jump loop and arrival refresh - Implemented, requires end-to-end QA

- `UJumpSequenceSubsystem` owns candidate generation, selection, warning, fate resolution, jump,
  Bloom adaptation/sabotage, system replacement, arrival, final-destination evaluation, and counters.
- Cryo protects the player when functioning; missing cryo applies jump consequences; EVA fate uses
  the canonical outside-ship test.
- Arrival despawns only content owned by the jump subsystem and deterministically spawns new hazard
  zones, resource nodes, collectors, and a procedural star-system map.
- Internal reactivation resources stay in ship coordinates; EVA/drone targets move with exterior
  system travel.
- **Corrected 2026-08-24:** this section previously said the demo used an opt-in first-destination
  fallback "because the final destination-picker presentation is not yet authored." That is stale.
  `AJumpConsoleSystem` builds `UJumpDestinationWidget` on interaction, populates one selectable
  `UJumpDestinationRowWidget` per candidate, and confirms the choice through
  `ConfirmJumpSelection()`. `bAutoSelectFirstCandidate` defaults to **false** and is only reachable
  if widget creation fails, so it is a safety net rather than the demo path.
- **Remaining:** authored visual treatment for the destination console (it builds its own native
  layout today); save/rejoin behavior during every phase; multi-client authority; failure recovery;
  repeated multi-system soak testing; falsification readability; and tuning for countdowns, fate
  probabilities, destination counts, costs, hazards, resources, and Bloom evolution.

### 5.3 Procedural star systems - Implemented foundation

- Strategic system maps operate at astronomical scale in AU and contain the star, 4–8 major bodies,
  orbital ordering, belts, jump boundaries, uncertainty, and selectable points of interest.
- Selecting a point of interest streams a separate kilometer-scale local operations volume. The
  existing generated exterior is a 60 km-diameter encounter bubble containing nearby celestial
  presentation, debris, hazards, resources, contacts, and mission geometry; it is not the solar
  system itself.
- Phenomena include gold giant, blue-white star, binary stars, violet dwarf, ion nebula, gravity
  anomaly, and fractured world; planet families include ocean, volcanic, ice, and gas giant.
- Visual cause, hazard placement, sensor representation, tracking, route safety, and operations
  targets share the same POI model.
- A large Blender asset library and modular catalog cover destinations, economy/logistics, hazards,
  mission sites, traffic craft, navigation assets, installations, cameras, and production budgets.
- **Remaining:** biome/content variety beyond generated prototypes, mission hooks per POI, streaming/
  LOD/Nanite/performance validation at scale, traversal boundaries, final sky/planet materials,
  multiplayer determinism, and long-run regeneration tests.

### 5.4 Pelagos orbital arrival - Implemented production map foundation

- `/Game/Assets/Maps/SpaceSystems/L_PelagosOrbitalArrival` contains an 87,364-triangle imported
  environment, four routes, 16 checkpoints, four gate sets, four dock approaches/captures, 24
  traffic anchors, ten service anchors, six hazard/exclusion volumes, beacons, lighting, cameras,
  and color grading.
- `APelagosOrbitalArrivalDirector` replicates the authority-controlled sequence from Jump Exit
  through Arrival Complete, including IFF, traffic control, dock reservation, soft/hard capture,
  service availability, departure, and reuse.
- Gate volumes, typed hazards, service definitions, traffic budgets, continuous hazard damage, Data
  Asset contracts, rebuild scripts, validation, and Phase 22–24 production ledgers exist.
- **Remaining:** connect Pelagos to the normal campaign destination pool and save flow; supply final
  docking UI/comms/audio/VFX; ship flight/collision response; service transactions; AI traffic
  behavior; multi-ship contention; network soak; performance/cook gate; and player-facing mission
  content within the station environment.

---

## 6. Threats, Combat, Bloom, and Versus

### 6.1 The Bloom - Implemented foundation

- `UBloomDirector` owns Latent → Colony → Swarm → Puppeteer → Infector → Manifestation progression,
  hazard resistance, exposure/action memory, host infection, system corruption, jump-time evolution,
  sabotage, self-destruct counterplay, and eradication state.
- Pathogen load, epidemiological diffusion/decay/shedding, corruptible systems, contaminated sections,
  hazard purging, corpse possession, and environment presentation are implemented.
- **Remaining:** production Bloom enemy/growth skeletal meshes, rigs, animation, behavior, audio, VFX,
  encounter direction, infection/corruption counterplay, late-stage content, balance, scale profiling,
  and full multi-client/end-to-end testing. Existing Bloom creature meshes are proxies.

### 6.2 Non-Bloom threats - Implemented foundation

- `AShipThreatDirector` supports pirate boarding, rebel takeover, alien hunting pack, alien brood,
  mixed alien incursion, and custom encounters independently of the Bloom.
- Encounters support seeded ship-section spawning, explicit anchors, Bloom requirements/overlap,
  primary-antagonist objectives, and jump blocking.
- Team-affiliation rules are shared by player weapons and threat AI to prevent allied damage and
  preserve hostility between distinct antagonist factions.
- **Remaining:** final faction art/animation/audio, ranged/tactical behavior, encounter pacing,
  spawn presentation, loot/rewards, mission authoring, navigation/cover, difficulty scaling,
  co-op threat selection, and performance/network tests.

### 6.3 Shipboard weapons - First playable slice implemented

- `AShipboardWeapon`, `UWeaponMountComponent`, definition Data Assets, operator compatibility,
  persistent modification state, safe/unsafe profiles, recoil, hull risk, and oriented traversal
  envelopes form the shared weapon foundation.
- The captive-bolt driver is mounted on the player by default and performs server-authoritative
  traces, biological damage, impulse, recoil, and ship damage, with multicast cosmetic hooks.
- Clearance volumes and oriented sweeps prevent players or drones from carrying oversized tools
  through apertures while preserving retreat and slide-out behavior.
- Weapon concept sheets, collision kit, mounts, production batches, and exported models exist.
- **Remaining:** replace temporary captive-bolt visuals in the runtime actor with the dedicated
  asset; author cosmetics; implement additional weapon subclasses; connect aerial/robotic drone AI;
  add projectiles, tethers, foam, thermal simulation, ammo/energy, modifications, inventory/equipment
  UX, target doctrine, damage balance, and network/PIE tests.

### 6.4 Asymmetric versus - Network-aware foundation, not feature-complete

- `AVersusGameMode`, GameState, PlayerState, settings, 8v4 roster limits, team assignment, URL
  options, spectator fallback, faction identity, relationship rules, controllable antagonist pawn,
  primary attack, and skill trees exist.
- Antagonist factions are Bloom, pirates, rebels, and alien. Optional independent AI factions can
  pursue their own agendas and remain hostile to other factions.
- Server-authoritative antagonist activities award shared skill/command resources and call typed
  world-effect hooks.
- Commander role, claim/release, command economy, prioritized orders, faction permissions, and
  same-faction AI order consumption are implemented.
- Native automation tests for settings, hostility, skill trees, activities, and commander rules are
  present and the latest versus run completed successfully.
- **Remaining:** faction-specific pawns, active skill effects, robust combat, overhead commander
  camera, tactical map/cursor, summon/build menus, voting/mutiny, lobby/session UX, reconnect/
  migration, balance, anti-cheat/server hardening, replication/latency tests, and complete versus
  objectives/maps.

### 6.5 Art, model libraries, cinematics, and production tooling - Broad foundation

- Reproducible model libraries cover handheld tools/weapons, pickups, drones, large ship systems,
  EVA fixtures, room machinery, damage-control states, mission items, space-system objects, player
  wearables, Bloom rig-prep modules, and expanded Bloom encounter proxies.
- Full-scale exterior silhouettes exist for the 1.4 km utility escort, 2.4 km military corvette,
  and 6.5 km expedition carrier, with reusable exterior-detail modules and a fleet scale-comparison
  map.
- Shared hard-surface and Bloom material masters plus category instances provide a consistent
  prototype production language across ships, props, equipment, pickups, drones, and creatures.
- Gameplay and complete-asset review maps, critical-reference validation, minimum mesh-count checks,
  Blender sources, GLB/FBX exports, Unreal Python importers, still-capture tools, and visual QA
  reports are checked in.
- A 40-slide gameplay concept storyboard and native CGI-trailer director/build/capture tooling exist
  as preproduction and presentation assets.
- **Remaining:** approve a definitive visual target; connect unhooked library models to runtime
  actors; replace proxies; add skeletal rigs/animations, authored LODs/Nanite, sockets, destructible
  parts, final collision, trim sheets, texture budgets, VFX/audio, and platform performance QA;
  rationalize duplicate/intermediate assets and enforce a clean source/runtime/generated boundary.

---

## 7. Verification and Known Technical Debt

### 7.1 Verified evidence currently present

- Latest logged versus suite: five tests passed.
- Latest logged weapons suite: captive-bolt profiles, collision-envelope aperture, and safe defaults
  passed.
- Latest logged desktop/gamepad input mapping test passed.
- Player-suit documentation records successful editor builds, visual captures, and suit replication
  tests before the current package-corruption state.
- Fitted-room documentation records successful regeneration and zero-error playable-map validation.
- Packaged Development smoke logs show the main menu and all three production districts loading.

### 7.2 Required release gates not yet satisfied

1. Restore/regenerate all 32 zero-filled player-suit packages and prove a clean asset-registry scan.
2. Perform a clean editor build and full `Ginnungagap` automation run from the current checkout.
3. Re-run production-map validators after asset restoration.
4. Complete a clean cook/package with no unloadable-package, missing-reference, fatal, or cook errors.
5. Smoke-test main menu, Small, Medium, Large, and Pelagos from the new package.
6. Run manual PIE matrices for jump/cryo/EVA, Bloom possession, zero-G/magnets, activities,
   checkpoints/death, status effects, weapons/hull damage, self-destruct, and every menu path.
7. Run listen-server plus remote-client tests for survival and versus, including late join, death,
   travel, reconnect, ownership, and authority rejection.
8. Profile CPU, GPU, memory, network, actor counts, navigation, epidemiology, and streaming on target
   hardware.

### 7.3 Known code/content debt

- `UEquipmentComponent::ApplyEquipmentBonuses` and `RemoveEquipmentBonuses` are placeholders.
- `ALevelSetupManager::SpawnEquipment` and `SpawnPlayerStarts` remain deferred stubs; production maps
  use their authored directors, and the legacy procedural path uses `AProceduralShipBuilder`.
- `UBTService_UpdatePatrolPoint` still contains a TODO; native controller logic is the current
  fallback when no Behavior Tree is assigned.
- Stock Combat, Side Scrolling, and Platforming template variants remain in the module and contain
  unrelated template stubs. They should be removed or isolated before production hardening.
- Public matchmaking and friend invites have explicit TODOs.
- The repository has both generated/runtime content and large source-art/preview/ledger collections;
  storage ownership, LFS policy, reproducibility, and CI artifact boundaries need formalization.

---

## 8. Prioritized Remaining Work

### P0 - Restore a trustworthy demo baseline

1. Recover the 32 invalid suit packages, run asset validation, and confirm the default pawn resolves
   every role asset.
2. Run the complete build/automation/map-validation/cook/package/smoke pipeline from the current
   revision and capture one consolidated report.
3. Manually play the canonical Small district from menu to objective completion, resource operation,
   sensor selection, helm transit, jump warning, cryo outcome, arrival refresh, death/checkpoint,
   and run resolution.
4. Fix any blockers found in zero-G/magnetic traversal, interaction, activities, navigation, jump,
   status, Bloom, weapon traversal, and save/load.
5. Decide whether the next external demo promises single-player only, listen-host co-op, or versus;
   the promise determines the mandatory network gate.

### P1 - Finish the vertical slice

1. Author the final destination-selection and physical sensor/helm console UX.
2. Finish one complete mission chain with primary/side objectives, timed failure, rewards, threat
   encounter, resource choice, repair consequence, and final outcome.
3. Complete one production Bloom encounter and one non-Bloom encounter with final-enough art,
   animation, audio, VFX, rewards, and difficulty tuning.
4. Finish the captive-bolt driver presentation and at least one repair/tool activity with production
   feedback and item consumption.
5. Finish a coherent equipment/inventory/skill/currency loop, and balance skill magnitudes in play.
6. Integrate Pelagos as a reachable destination with docking, services, and departure.
7. Complete usability, accessibility, controller, save/load, crash recovery, and performance passes.

### P2 - Make co-op and versus production-capable

1. Audit and implement authority/replication for all remaining ship, jump, Bloom, objective,
   inventory, equipment, activity, travel, and save paths.
2. Add online sessions, discovery/matchmaking, invitations, lobby readiness, reconnect, host migration
   policy, server travel, and failure UX.
3. Build multi-client automation and soak suites for survival and versus.
4. Finish faction pawns, active abilities, commander UX, tactical ordering, objectives, balance, and
   anti-exploit validation.

### P3 - Content scale and production hardening

1. Replace remaining proxy art for Bloom, aliens, human factions, ship modules, tools, and weapons.
2. Build streamed ship districts and destination/mission content from the reusable room and POI kits.
3. Expand narrative, VO, audio, cinematics, onboarding, tutorials, accessibility, localization, and
   telemetry.
4. Establish target platforms, scalability tiers, performance budgets, CI/DDC/cook automation,
   crash reporting, release packaging, store/platform services, and save migration.
5. Perform legal/IP, security/privacy, content-rating, and distribution readiness reviews.

---

## 9. Open Product Decisions

1. **Demo networking promise:** single-player, listen-host co-op, or fully remote co-op/versus?
2. **Vertical-slice ending:** destination victory, Pelagos docking, self-destruct escape, or a curated
   combination?
3. **Meta progression:** how should banked currency divide between permanent class skills, equipment,
   ship unlocks, cosmetics, and run-start advantages?
4. **Failure philosophy:** which deaths/failures are recoverable at checkpoints, which cost run
   resources, and which end the expedition?
5. **Sensor deception limits:** what information may be falsified without making planning feel
   arbitrary or unfair?
6. **Versus priority:** is asymmetric versus part of the next milestone or a later mode built after
   co-op survival is stable?
7. **Pelagos role:** recurring hub, optional destination, final destination, tutorial arrival, or
   standalone showcase?
8. **Content quality bar:** which proxy assets are acceptable for the next demo, and which must be
   replaced before external viewing?
9. **Target platforms and minimum hardware:** required before meaningful final performance budgets,
   input certification, online-service selection, and packaging decisions.

---

## 10. Acceptance Criteria

### Playable vertical slice

- Starts from the main menu and supports New Game, Continue, settings, character creation, and
  controller navigation.
- Loads the Small Utility Escort with the correct pawn, HUD, objectives, encounters, checkpoint,
  and ship systems without asset-registry errors.
- Lets the player survey and track contacts, operate resources, repair at least one meaningful ship
  failure, and complete at least one authored mission objective.
- Executes a complete jump with visible warning, cryo/no-cryo/EVA consequences, hidden Bloom
  adaptation, old-content cleanup, new-system spawn, and continued play.
- Supports death/respawn and one complete victory/loss/self-destruct outcome with correct persistence.
- Produces a clean Windows Development build whose required maps smoke-test successfully.

### Co-op milestone

- Two or more remote clients can join, complete the vertical-slice loop, travel, die/respawn, and
  reconnect without divergent authoritative state.
- All player-requested inventory, equipment, activity, weapon, door, ship-system, objective, jump,
  and versus actions are server validated.
- Player-private psychosis remains private; shared hazards, objectives, enemies, and ship state remain
  consistent.

### Production readiness

- No zero-filled, unloadable, missing, or redirector-broken runtime packages.
- Full automated, map-validation, cook, package, smoke, multiplayer, soak, and performance gates pass
  on supported targets.
- Required gameplay content uses production-quality art/audio/VFX or an explicitly approved demo
  proxy, with accessibility, localization, save migration, crash handling, and platform services
  complete for the release scope.

---

## 11. Detailed References

- [Module Storyboard](ModuleStoryboard.md) - player-facing module coverage and dependencies.
- [High-Priority Gameplay Foundations](HighPriorityGameplayFoundations.md) - mission, inventory,
  power, and damage-control foundations.
- [Ship Production Vertical Slice](ShipProductionVerticalSlice.md) - authored districts, generation,
  cook, package, and smoke workflows.
- [Modular Ship Rooms](ModularShipRooms.md) and [Room Systems Ledger](RoomSystemsImplementationLedger.md)
  - topology, room profiles, bindings, and validation.
- [Fitted Room Production Pass](FittedRoomProductionPass.md) - the 18-room dressing pass.
- [Player Activities](PlayerActivities.md) - activities, stations, and 500 specialist variants.
- [Player Suit Assets](PlayerSuitAssets.md) and [Magnetic Suit Traversal](MagneticSuitTraversal.md).
- [Player Status Effects](PlayerStatusEffects.md) - clinical state and psychosis perception.
- [Shipboard Weapons](ShipboardWeapons.md) and [Mission Threat Encounters](MissionThreatEncounters.md).
- [Pelagos Orbital Arrival Map](PelagosOrbitalArrivalMap.md).
- [Asymmetric Versus Mode](VersusMode.md).
- [Unreal Asset Pipeline](UnrealAssetPipeline.md) and [Gameplay Model Library](GameplayModelLibrary.md).
- [Complete Asset Catalog](CompleteAssetCatalog.md), [Ship Exterior Models](ShipExteriorModels.md),
  [Room Machinery Models](RoomMachineryModels.md), and [Production Surface Materials](ProductionSurfaceMaterials.md).

**Note on this refresh (2026-08-24):** only §3.1 (front end/multiplayer), §3.3 (character
presentation), §4.2 (modular rooms), and §4.3 (ship systems, cryo pod) were checked against the
current codebase and corrected where stale. The remaining sections (§4.4 onward, and all of §5–§10)
were not re-verified in this pass and may also be out of date; `docs/JamesToDo.md` in particular
describes a much older prototype state and should be treated as historical, not current. Linear
project "Ginnungagap" is the current source of truth for open work - see TRO-66 for the standing
task of keeping this document synchronized.
