# Layered Player Character and Pressure Suit

The survival pawn now separates the character, fitted cryo/bodysuit, and rigid pressure oversuit
into independent runtime layers. The hidden UE Manny mesh remains the animation driver using
`ABP_Unarmed`; the authored V32 bodysuit shares its exact skeleton and follows it with Leader Pose.
The assembled MetaHuman supplies the face, eyes, teeth, and groom layers. Its placeholder torso,
legs, feet, and body mesh are hidden, so the character no longer reads as wearing a T-shirt and no
duplicate body geometry clips through the fitted garment.

The project explicitly enables the engine `LiveLink` plugin because the shared MetaHuman facial
animation Blueprint contains Live Link pose graph nodes. The default assembled face is resolved
after plugin startup rather than from the pawn's static constructor, preventing those graph types
from being deserialized before their modules exist.

`bPressureOversuitEquipped` controls the rigid helmet, collar, plates, pack, gloves, boots, and role
modules separately from the bodysuit. It defaults to false for the cryo wake/suiting-up state and
replicates independently from `PressureSuitRole`. Call `SetPressureOversuitEquipped` when gameplay
finishes the suiting sequence; the V32 bodysuit remains present underneath.

`MetaHumanCharacterClass` is a replicated, runtime-swappable assembled MetaHuman Blueprint class.
Character-creator face variants therefore reuse the same Manny driver, V32 garment, and oversuit
modules instead of requiring separate combined meshes. Face01 is only the default selection;
future assembled faces can be assigned with `SetMetaHumanCharacterClass`.

Character profiles persist `MetaHumanPresetId` rather than an asset path. The first-launch creator
cycles only presets whose assembled Blueprint resolves, applies the choice to its live preview,
and broadcasts both the legacy creation event and `OnCharacterCreatedWithPreset`. Existing saves
fall back to `PlayerFace01` without invalidating the rest of the profile.

The moved project currently preserves the imported V32 skeletal-mesh asset but not its original
FBX/Blend source. Run `tools/export_cryo_bodysuit_v32_source_recovery.py` through Unreal Python to
recover an editable FBX under `Build/Unreal/PlayerSuits/CryoBodysuitV32` before the next topology or
weight-paint pass.

## Known drift (2026-08-24)

This document describes only the `MetaHumanPresetId`/`FirstLaunchCharacterCreationWidget` system
above. A second, independently-built character-appearance system now also exists at runtime -
`BodyPreset`/`FacePreset`/`SkinTone`/`HairStyle`/`VoiceProfile` resolved through
`CharacterCreatorWidget` - as a result of merging two divergent branches of work. See TRO-215 for
the decision on which becomes canonical.

Relatedly, the "Standalone primary class oversuits" section below states that oversuit art is
"intentionally not promoted into runtime content until the parallel player/undersuit work
establishes the final shared skeleton." That gate has partially been crossed since this was
written: `ACoopSurvivalCharacter` now has a runtime `PrimaryOversuitMesh` component with
per-role soft-object-pointer meshes (`CrewPrimaryOversuit`, `EngineeringPrimaryOversuit`,
`MedicalPrimaryOversuit`, `SecurityPrimaryOversuit`) and role-based swap logic, introduced by the
same merge as the `CharacterCreatorWidget` system above. Whether the specific V16/V17+ art below is
what's assigned to those soft pointers has not been verified.

## Playable Blueprints

- `/Game/Characters/Player/Blueprints/BP_Player_Suit_Crew`
- `/Game/Characters/Player/Blueprints/BP_Player_Suit_Engineering`
- `/Game/Characters/Player/Blueprints/BP_Player_Suit_Medical`
- `/Game/Characters/Player/Blueprints/BP_Player_Suit_Security`

`AGinnungagapGameMode` uses the crew variant as its default pawn. Each Blueprint inherits the
survival, inventory, interaction, zero-G, camera, and equipment systems from
`ACoopSurvivalCharacter`.

## Modular Meshes

The kit under `/Game/Characters/Player/Suit/Meshes` contains separate helmet shell, visor,
pressure collar, chest plate, life-support pack, shoulder pad, forearm computer, knee pad,
boot shell, glove, and thigh-pouch meshes. Four swappable chest modules give crew, engineering,
medical, and security distinct equipment silhouettes. Components follow the mannequin bones
during animation and have no collision; the character capsule remains authoritative for movement.

## Materials and role variants

`M_PlayerSuit_Master` exposes `SkinTexture`, `Roughness`, and `Metallic`. Four generated albedo
skins under `/Game/Characters/Player/Skins/Textures` reproduce the concept lineup's crew,
engineering, medical, and security palettes, while `M_PlayerSuit_Visor` and `MI_Suit_Visor`
provide the translucent visor.
Change `Pressure Suit Role` on any `ACoopSurvivalCharacter` Blueprint or placed instance to swap
the hard-suit material set. The same source skins also back the six existing character-profile
appearance choices through material instances under `/Game/Materials/Characters`.

`FCharacterProfile::SuitRole` persists the selected role in the existing character save. The
first-launch widget exposes `OnSuitRoleSelected` to Blueprint and automatically binds optional
`CrewRoleButton`, `EngineeringRoleButton`, `MedicalRoleButton`, and `SecurityRoleButton` widgets.
The spawned local pawn sends its saved role through a reliable server RPC; `PressureSuitRole`
then replicates with an OnRep visual refresh for other clients.

Character creation also supports a live 512x512 SceneCapture preview through the optional
`SuitPreviewImage`, `SelectedSuitRoleText`, `RotatePreviewLeftButton`, and
`RotatePreviewRightButton` bindings. Role changes update the preview immediately. When no
Blueprint widget tree is supplied, the native widget constructs a functional fallback layout
containing the preview, four role buttons, rotation controls, name input, and confirmation.

At runtime, every non-visor suit part uses a dynamic material instance. `DamageAmount` follows
inverse suit integrity, `GrimeAmount` combines damage with radiation exposure, and `BloomAmount`
tracks normalized pathogen load. These parameters tint the role albedo through rust-brown wear,
dark accumulated grime, and emissive amethyst contamination without replacing the underlying
PBR skin. Pathogen state and load replicate with the owning component, while suit-integrity
OnRep updates condition visuals immediately on remote clients.

The owner-only capsule-mounted first-person camera is the default gameplay view.
`ACoopSurvivalCharacter::SetFirstPersonView` switches locally between it and the spring-arm
third-person camera, allowing traversal or scripted scenarios to opt into third person and then
return to first person. The Manny body remains hidden while still evaluating every bone; the V32
bodysuit and optional rigid modules consume that pose. Helmet, visor, collar, and backpack retain
owner-no-see behavior in first person to avoid camera clipping. `ValidateSuitAttachmentBones`
checks every required Manny attachment bone at BeginPlay and reports missing rig dependencies
explicitly.

The survival HUD is presented as a projection on the visor's inner pressure pane. Its persistent
layer is limited to suit/body telemetry, a restrained aiming reference, interaction context, and
critical warnings. Information that belongs to the ship-destination selection, detailed maps,
inventory management, repairs, and configuration-stays on physical consoles or dedicated menus.

Multiplayer regression coverage lives in `Private/Tests/PlayerSuitReplicationTests.cpp` under
`Ginnungagap.Multiplayer.PlayerSuit`. The tests verify the role RepNotify contract, replicated
pathogen state/load, all four profile enum values, and client-side resolution of every role
material and role-specific module mesh.

Each role now includes base-color, tangent-space normal, roughness, metallic, and ambient-
occlusion textures. The modular OBJ sources contain cylindrical UV0 coordinates with explicit
seam handling; Unreal generates the separate lightmap channel during import. Run
`tools/generate_player_skin_pbr.py` before the Unreal build script whenever an albedo changes.

## Regeneration

The complete kit is reproducible by running `tools/build_player_suit_assets.py` through Unreal's
Python Script commandlet. Generated OBJ source files are intermediate build products under
`Saved/GeneratedSuit`; the checked-in `.uasset` files under `Content` are the runtime assets.

The neutral-light comparison map is rebuilt with `tools/build_player_suit_showcase.py`. Use
`tools/set_player_suit_showcase_view.py` with `SUIT_SHOWCASE_VIEW` set to `front`, `side`, or
`rear`, then run `tools/capture_player_suit_showcase.py` with the desired output filename. The
builder restores the canonical four-role lineup, disables character-owned cameras and animation,
and activates the fixed showcase camera so repeated captures remain directly comparable.

Final reference renders are stored at:

- `Saved/Renders/PlayerSuitLineup-front.png`
- `Saved/Renders/PlayerSuitLineup-side.png`
- `Saved/Renders/PlayerSuitLineup-rear.png`

## Five-step refinement pass

The full-design refinement adds a sealed smoked visor with an inner pressure pane, connected
knee/shin armor, layered boot shells, articulated glove geometry, a larger forearm computer,
and enlarged role-specific chest modules. Rigid components use a stronger role-color response
than the fabric undersuit, while chest modules receive a restrained role-colored status emission.
The custom chest and life-support meshes are aligned to their authored axes at runtime so their
depth remains correct on the Manny skeleton.

Current verification renders are stored at:

- `Saved/Renders/PlayerSuitRefinement5-front.png`
- `Saved/Renders/PlayerSuitRefinement5-side.png`
- `Saved/Renders/PlayerSuitRefinement5-rear.png`

The `Ginnungagap.Multiplayer.PlayerSuit` automation group must pass after regeneration; it covers
network asset resolution and the replicated role/pathogen visual contract.

## Standalone primary class oversuits (V16)

> **Naming note.** These `.blend` filenames predate the role vocabulary and are kept as-is so
> existing references stay valid. `EPressureSuitRole` is canonical everywhere in code: Marine is
> Security, Scientist is Crew, Technician is Engineering, Medical is unchanged. The old
> `EPlayerClass` enum was retired rather than renamed, because two enums naming one concept is what
> let the art and code vocabularies drift apart in the first place.

The first wearer-independent class pass lives under
`Art/Characters/PlayerSuits/PrimaryOversuits`. It uses the physically separated V15 pressure
shell as a shared envelope and produces four modular skeletal garments with no player body or
undersuit geometry:

- `PlayerOversuit_Marine_v16.blend` - reinforced boarding/recovery armor; maps to the existing
  replicated `Security` suit role.
- `PlayerOversuit_Scientist_v16.blend` - survey sensors and sealed sample storage; maps to
  `Crew`.
- `PlayerOversuit_Technician_v16.blend` - thermal protection, power cells, cable reel, and a
  tool-arm dock; maps to `Engineering`.
- `PlayerOversuit_Medical_v16.blend` - patient telemetry, injector bank, trauma storage, and a
  sterile equipment pack; maps directly to `Medical`.

Each file retains only its oversuit armature, the common pressure-envelope meshes, and its own
class modules. FBX review exports are written to
`Build/Unreal/PlayerSuits/PrimaryOversuits`; they are intentionally not promoted into runtime
content until the parallel player/undersuit work establishes the final shared skeleton and the
animated fit, collision, Unreal import, and multiplayer loadout gates pass.

Regenerate with `tools/build_primary_class_oversuits.py` through Blender, then run
`tools/validate_primary_class_oversuits.py`. The manifest records both the canonical gameplay
class and current `EPressureSuitRole` alias so migration can happen without silently changing
saved profiles or replicated visuals.

### V17 construction and donning pass

V17 preserves the standalone V16 separation contract and adds the construction needed for a
credible wearable garment: a continuous four-piece waist/hip yoke, upper-arm shells, elbow and
ankle pressure interfaces, magnetic sole rails, chest harness rails, rear-entry spine and
over-center latches, helmet crown protection, and communications pods. Class equipment receives
a secondary silhouette pass: Marine cuirass and hardpoints, Scientist sensor/sample bracing,
Technician folded tool-arm and thermal hardware, and Medical rescue/triage fittings.

Eight named attachment interfaces accompany each suit: neck seal, chest lock, waist lock, paired
wrists, paired boots, and life-support pack dock. Asset metadata records the ordered don and doff
sequences and identifies the eventual runtime equipment slot as `Chest`. The current fit reference
is the independent V28 cryo bodysuit, but no character or undersuit geometry is copied into any
V17 oversuit file.

Run `tools/refine_primary_class_oversuits_v17.py` through Blender, followed by
`tools/validate_primary_class_oversuits_v17.py`. Review exports live under
`Build/Unreal/PlayerSuits/PrimaryOversuits_v17`; runtime promotion remains gated on the finalized
shared skeleton, animated fit, pressure-interface fit, Unreal skeletal import, and multiplayer
equip replication.

### V18 curved-form pass

V18 directly addresses the blockout appearance of V17. It removes the dominant rectangular chest
and pack housings, the segmented box waist yoke, the floating helmet crown rail, and selected box
class modules. Their replacements use tapered convex chest shells, a continuous elliptical waist
ring, curved life-support shroud, conformal crown pad, tubular harness struts, rounded storage and
power housings, and larger four-segment manufactured edge radii on retained small hardware.

The four primary silhouettes remain functionally distinct, but now derive their identity from
curvature and mass distribution instead of stacks of cubes: a broad Marine cuirass, asymmetric
Scientist instrument pod and sensor fairing, Technician service bib and thermal backplane, and
clean Medical telemetry and sterile-pack shells. Generate with
`tools/refine_primary_class_oversuits_v18.py`, then validate with
`tools/validate_primary_class_oversuits_v18.py`.

### V19 dedicated smooth-shell pass

V19 removes the remaining V11 full-body meshes that used region masks to expose torso, shoulder,
forearm, thigh, knee, and shin armor. Those inherited surfaces were responsible for the ragged
edges and uneven limb finish still visible after V18. Only the two better-shaped V11 boot shells
remain.

Each class now receives dedicated smooth upper-torso and abdominal pressure envelopes, a pelvis
bridge, forearm gauntlets and curved plates, sealed glove shells and knuckle guards, thigh and shin
gaiters, knee bellows and rounded pads, curved shin armor, wrist cuffs, and restrained class-color
knee inserts. These pieces remain bone-addressable modular oversuit geometry rather than copied
player or undersuit meshes. Generate with `tools/refine_primary_class_oversuits_v19.py`, then run
`tools/validate_primary_class_oversuits_v19.py`.

### V20 tailoring and surface-construction pass

V20 tailors the clean V19 pressure volumes to reduce the mannequin-like silhouette, with shallower
torso depth, a narrower abdomen and pelvis, slimmer gauntlets, gloves, thigh and shin gaiters, and
tighter knee/underarm bellows. A fine bonded-pressure-textile shader replaces the uniform smooth
finish on the flexible envelope.

Construction detail now includes a center pressure closure, diagonal chest panels, four abdominal
seams, triple elbow and knee accordion rings, longitudinal thigh and shin seams, palm plates,
individual knuckle guards, and restrained class-color torso/limb piping. Marine cuirass ribs,
Scientist instrument dials, Technician service-bib heat ribs, and Medical sterile telemetry borders
provide class-specific surface language without returning to blockout boxes. Generate with
`tools/refine_primary_class_oversuits_v20.py`, then run
`tools/validate_primary_class_oversuits_v20.py`.

### V21 integration, gloves, and boots

V21 replaces the proud straight V20 seam rods with surface-following Bezier seams converted to
exportable mesh. Center closure, chest, abdomen, thigh, and shin paths now follow the tailored
ellipsoid shells, while elbow and knee articulation is reduced from three oversized rings to two
compact dark bellows.

The mitten-like glove is rebuilt as a pressure palm, four separate fingers, thumb, and knuckle
guard per hand. The final V11 holdouts-the two boot meshes-are removed and replaced by dedicated
ankle envelopes, heel and instep shells, toe caps, magnetic soles, and four tread contacts per
foot. V21 therefore contains no V11 mesh at all. Generate with
`tools/refine_primary_class_oversuits_v21.py`, then run
`tools/validate_primary_class_oversuits_v21.py`.

## Ten-step production pass

The subsequent production pass tightens the helmet shell, smoked visor, dual pressure collar,
chest harness, shoulder caps, forearm computer, gloves, knee/shin guards, boot shells, and rear
life-support pack. All custom meshes now receive explicit authored-axis attachment transforms in
`ApplyPressureSuitVisuals`, avoiding dependency on the original primitive-component rotations.

Verification renders for this pass are stored at:

- `Saved/Renders/PlayerSuitRefinement10-front-final.png`
- `Saved/Renders/PlayerSuitRefinement10-side.png`
- `Saved/Renders/PlayerSuitRefinement10-rear.png`

The editor target compiled successfully and both `Ginnungagap.Multiplayer.PlayerSuit` automation
tests passed after this pass.

## Attachment and presentation pass

The next ten-task pass removes the visor crown artifact, moves the smoked dome forward, tightens
the collar, remounts chest modules and thigh pouches, and corrects shoulder, forearm, knee, and
boot attachment transforms. The showcase builder also creates color-coded role-label actors for
Crew, Engineering, Medical, and Security.

Current renders are stored at:

- `Saved/Renders/PlayerSuitTasks10-front-labeled.png`
- `Saved/Renders/PlayerSuitTasks10-side.png`
- `Saved/Renders/PlayerSuitTasks10-rear.png`

The editor target and both multiplayer suit automation tests passed after regeneration.

## Visor and armor polish pass

This ten-step pass adds role-tinted dynamic visor materials, Fresnel edge reflection, shadow-free
visor rendering, per-role chest-module scale and emission, stronger rigid-armor color contrast,
and final fit adjustments for gloves, thigh pouches, and the life-support pack.

Verification renders are stored at:

- `Saved/Renders/PlayerSuitPolish10-front.png`
- `Saved/Renders/PlayerSuitPolish10-side.png`
- `Saved/Renders/PlayerSuitPolish10-rear.png`

The editor target compiled successfully and both multiplayer suit automation tests passed.

## Animated pose audit

Use `tools/set_player_suit_showcase_pose.py` to freeze every showcase character at the same
animation time for attachment and clipping review. Set `SUIT_SHOWCASE_POSE` to `combat`,
`attack`, or `run`; combine it with `tools/set_player_suit_showcase_view.py` to audit the pose
from the canonical front, side, and rear cameras. The pose script uses Manny animation assets,
single-node playback, and a deterministic paused time so captures remain comparable.

The first combat-pose audit exposed an open visor/face band. `SM_Suit_Visor` is now generated as
a sealed ellipsoid dome and mounts closer to the head, eliminating that gap while preserving the
role tint and Fresnel edge reflection. The verified front capture is stored at:

- `Saved/Renders/PlayerSuitCombatPose-visor-fixed.png`

Both `Ginnungagap.Multiplayer.PlayerSuit` automation tests passed after the visor regeneration
and runtime attachment update.

## V7 authored-shell review pipeline

The next non-destructive art pass is defined by `tools/build_player_suit_production_v7.py`. It
keeps the validated V6 garment, head, and skeleton while introducing separate hard-surface armor,
serviceable life-support components, physical fasteners, raised garment seams, and explicit
ceramic/fabric/gunmetal/safety material families. V7 is a review asset and does not replace the
runtime suit.

`tools/validate_player_suit_production_v7.py` checks required modules and bone attachments,
material completeness, finite articulated deformation bounds, and produces a deterministic QA
pose render plus JSON report. `tools/export_player_suit_production_v7.py` packages the approved
review source for Unreal, and `tools/import_player_suit_production_v7_review.py` imports it only to
`/Game/Characters/Player/Suit/V7Review`. Promotion to `PackagedCombined` remains gated on visual,
deformation, physics, and multiplayer validation.

## V8 fifty-pass art batch

`tools/refine_player_suit_v8_50_passes.py` applies fifty individually logged production passes to
the modular V7 review source. The batch develops the full articulation chain, pressure helmet,
life-support pack, magnetic boots, equipment interfaces, physical construction cues, shader
finish, LOD policy, collision review, and deterministic QA presentation. Its exact ledger is
written to `Art/Characters/PlayerSuits/PlayerSuit_Production_v8_50Passes.json` when executed.

`tools/validate_player_suit_v8_50_passes.py` rejects missing or duplicated passes, sparse output,
incorrect critical bone attachments, absent materials/LOD candidates/collision proxies, and
non-finite articulated deformation. V8 remains explicitly review-only until the same promotion
gates documented for V7 pass in Unreal.
### Primary class oversuits V22 - rejected extraction experiment

V22 tested extraction from `PlayerSuit_Master.blend`. Visual review rejected it because the source geometry remained an automated detail blockout and did not match the realistic concept art. It is retained only as an experiment and is not an approved player asset.

### Primary class oversuits V23 - clean concept shell

V23 is a ground-up garment-first reconstruction using `standard-suit-turnaround.png` and `player-suit-role-lineup.png` as the visual authority. It replaces the inflated mannequin construction with continuous tailored textile shells, human proportions, a close helmet bubble, restrained hard points, compact life support, articulated pressure gloves, and realistic longitudinal boots. Role color is limited to identification and equipment accents.

The Marine/Security, Scientist/Crew, Technician/Engineering, and Medical/Medical outputs are standalone 22-bone garments with eight explicit donning interfaces and contain no player, face, hair, or undersuit geometry.

### Primary class oversuits V24 - Unreal-authored production pivot

V24 ends the procedural Blender silhouette passes. V16–V23 remain reference and validation experiments; none is a production visual target. The authoritative references are `standard-suit-turnaround.png`, `player-suit-role-lineup.png`, and `player-suiting-up-armory-concept.png`.

`unreal-primary-oversuit-v24-target.png` is the approved visual target for the in-engine sculpt pass: shared realistic pressure-garment construction, natural adult proportions, restrained role color, and class identity driven by practical equipment rather than silhouette-breaking blockout shapes.

The production route starts from a realistic, rigged garment donor and performs fit, deletion, remesh, sculpt, PolyGroup, UV, bake, and hard-surface adaptation in Unreal Modeling Mode. Source marketplace meshes remain untouched. Project-owned duplicates are rebound to the common player skeleton and assigned as separate class skeletal meshes on `ACoopSurvivalCharacter::PrimaryOversuitMesh`. Leader Pose drives the garment without merging it into the player or undersuit. Assigning a primary oversuit automatically hides the legacy bone-attached blockout pieces.

The preferred donor is [Space Marshal - SciFi Soldier - Female](https://www.fab.com/listings/9d757d44-d61b-4aab-9f93-120a32080468) because its layered pressure garment, restrained protection, equipment scale, and class color variants most closely match the concept language. [Space Adventurer](https://www.fab.com/listings/3c38fb9b-810c-4de2-834e-3f8560ef4e66) is a secondary cloth/construction reference. [SciFi Soldier](https://www.fab.com/listings/d087974b-841c-44d9-8733-6c2c53e6f2d1) is limited to Security/Marine hard-surface reference, and [Space Male](https://www.fab.com/listings/53881999-23eb-4eba-87f3-bc39ac442c7b) is limited to modular-fragment and Epic-skeleton workflow reference.

The matching Space Marshal female and male packs are now purchased and available to the project.
`tools/prepare_space_marshal_oversuit_sources.py` deterministically removes the donor heads and eyes
while preserving the seven skinned garment modules and their authored armature. Purchased FBXs,
textures, and prepared derivatives stay under ignored `Intermediate/Fab/SpaceMarshal`; they are
not committed as raw source files and are not supplied to generative AI systems.

`tools/import_space_marshal_oversuit_review.py` imports the garment-only female and male fits,
selected PBR maps, shared material instances, and four role variants to
`/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal`. The review map is
`L_SpaceMarshal_ClassLineup`; `tools/render_space_marshal_oversuit_review.py` produces both a
lit capture and a base-color diagnostic under `Saved/Renders`. This remains a donor review, not a
runtime promotion: the male source uses its vendor UE5 hierarchy and the female review source uses
its working Biped hierarchy. Both must be duplicated, fitted, and rebound to the project's common
Manny/Quinn skeleton before Leader Pose assignment or multiplayer equipment validation.

`tools/setup_primary_oversuit_v24_sculpt_workspace.py` creates those project-owned duplicates at
`/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/Working/Iteration_01` and assembles
`L_PrimaryOversuit_V24_Sculpt`. The map contains four independent role working meshes, separate
male/female fit copies, overlapping Manny/Quinn clearance references, approved concept boards,
and neutral sculpt cameras. The Space Marshal review folder remains the immutable donor source.

`tools/fit_primary_oversuit_v24_shared_form.py` creates the first topology-preserving Unreal fit
layer, `V24_SharedFit_I01`, on the male body-fit copy and the four topology-identical role meshes.
The pass works in each weighted bone's local frame, reducing the inflated radial volume of the
boots, calves, thighs, forearms, gloves, shoulders, and torso without shortening the limbs,
moving joints, changing topology, or altering the helmet. It is stored as an overwriteable morph
target rather than baked into the donor geometry. The female Biped working copy remains a separate
topology and deliberately does not receive the male morph.

The sculpt workspace previews the shared-fit morph at full weight. Crew is the first active role
pass, recorded as `CrewPass01SharedFitReady`; its next gate is practical survey equipment and
surface breakup guided by the approved role lineup. All five fitted assets remain marked
`PlayerSuitRuntimeReady=False` until project-skeleton rebind, pose deformation, body clearance,
and multiplayer equipment tests pass. `tools/validate_primary_oversuit_v24_sculpt_workspace.py`
verifies the morph targets, topology split, enabled Unreal sculpt plugins, metadata, map actors,
and promotion gate.

`tools/refine_primary_oversuit_v24_crew_five_passes.py` executes the next five Crew steps over the
authored garment sections instead of adding procedural blockout parts. Four additive morphs clean
the flexible-shell silhouette, compact the helmet/collar assembly, settle the donor pack and
pouches into a practical harness, and add local elbow/knee/wrist/ankle clearance. The fifth pass
creates `MI_PrimaryOversuit_Crew_Work_I01`, reducing the saturated role tint while retaining the
donor PBR texture, normal, and ORM response. The resulting Crew stack is:

1. `V24_SharedFit_I01`
2. `V24_Crew_01_SilhouetteCleanup`
3. `V24_Crew_02_HelmetCollar`
4. `V24_Crew_03_EquipmentSettle`
5. `V24_Crew_04_MobilityClearance`
6. `MI_PrimaryOversuit_Crew_Work_I01` surface treatment

The five Crew passes preserve all 25,421 source vertices and remain isolated from Engineering,
Medical, and Security. Crew first advances to `CrewPass05ConceptReview`.
`tools/render_primary_oversuit_v24_crew_five_passes.py` produces the exposure-independent geometry
normal comparison at `Saved/Renders/PrimaryOversuitV24_CrewFivePasses_Normal`.

`tools/build_primary_oversuit_v24_crew_modules.py` completes the next two Crew construction passes
without procedural primitives. It separates compact connected islands from the purchased donor's
authored `SM_Pouch` section, preserves their UVs and topology, recenters and modestly scales them,
and creates independent `SM_Crew_HarnessMonitor_Work_I01` and
`SM_Crew_SurveyToolMount_Work_I01` static working assets. The sculpt map places the monitor on the
upper chest and the survey carrier on the left hip, and includes `CAM_Crew_Modules_Closeup` for
direct in-editor review. Both module assets carry donor provenance, explicit no-AI-use metadata,
and `PlayerSuitRuntimeReady=False`. Crew is now `CrewPass07ModuleReview`; socket or skeletal
attachment, deformation testing, multiplayer equip validation, and the monitor-screen surface
remain promotion gates.

RealityScan 2.2 is reserved for a future physical mannequin capture, not concept-image
reconstruction. Its simplified textured result will be imported only as a fold, seam, bulk, and
equipment-scale reference. The capture requirements and handoff are documented in
`docs/RealityScanOversuitCapture.md`.
