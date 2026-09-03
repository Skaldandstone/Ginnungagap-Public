# Bloom Fab + RealityScan Enemy Prototypes

The first articulated Bloom enemy pass is implemented as two native gameplay archetypes:

- `ABloomReanimatedCrewEnemy` keeps a Manny-compatible skeletal pressure shell for animation and
  uses the Fab Alien Biomass and White Desert crystal packs as infection growth sources.
- `ABloomMechanizedEnemy` uses the Fab Modular Sci-Fi Mechanic JACK body, head, arm, and leg meshes
  as independently articulated rigid parts, then layers the same Bloom biomass/crystal language on
  top.

Both classes derive through `AProgressiveBloomEnemy` from `AHorrorEnemy`, so health, damage, simple
AI, zero-g behavior, replication, team affiliation, and Bloom hazard exposure remain available.

## Progressive infection

Every host carries a replicated `InfectionProgress` value from 0 to 1 and exposes four readable
local phases: Seeded, Colonizing, Puppeteered, and Overgrown. By default the value follows the
global `UBloomDirector` stage, but designers can disable that link and author a local value for a
specific encounter. Infection progress also drives the attached `UPathogenLoadComponent`, shedding
rate, staged mesh reveals, and combat tuning.

The host also owns a non-shadow-casting local infection light. Its radius and intensity rise with
the square of infection progress so Seeded enemies do not flood dark corridors, while terminal
hosts clearly advertise danger. Crew use a hot magenta cue and accelerate from 215 to 365 cm/s;
mechanized hosts use a larger cool-violet field and rise from 105 to 225 cm/s. This preserves the
crew's pursuing role and the machine's slower bruiser silhouette as both mature. The same derived
speed is written into the active patrol controller's patrol/chase tuning, preventing AI state
changes from restoring generic movement speeds.

Progressive hosts now own their contact-combat loop instead of relying on the chase controller to
modify player health. The authority selects the nearest hostile pawn inside the current attack
range, verifies line of sight, and applies normal Unreal damage plus a direct pathogen dose. Crew
attack intervals tighten from 1.6 to 0.7 seconds and transfer up to 8 exposure units; machinery
tightens from 2.4 to 1.25 seconds and transfers up to 14. Before each strike, an unreliable
multicast starts a 0.35-second light surge and Blueprint telegraph event on every peer. The committed
attack also raises a Blueprint event for animation, sound, camera response, and impact effects.

The installed Fab animation library is used where its content and skeleton are appropriate.
`tools/audit_bloom_fab_animations.py` inventories the available animation assets and writes
`Saved/Reports/BloomFabAnimationAudit.json`. The current audit found 30 pack-native Dead Bodies
poses (21 lying and 9 seated), all terminal two-frame poses, but no Fab locomotion or melee clips.
The crew therefore uses `AS_DeadBody_Pose_Lie_04`, `AS_DeadBody_Pose_Lie_11`, and
`AS_DeadBody_Pose_Lie_17` as replicated death variants. At death it switches to the pack's own
`SKM_Manny_Simple`, ensuring each animation runs on its exact source skeleton rather than relying
on an unsafe same-name skeleton assumption.

Until suitable Fab combat sets are added, all living visual parts sit beneath a shared native
motion pivot. The crew uses it for a short whole-body lunge; the rigid robot combines a forward
weight shift with a dedicated striking-arm rotation. Multicast attack timing drives these poses on
every peer and blends through a short recovery rather than snapping immediately to idle. The robot
intentionally remains on rigid-part motion because its JACK body is assembled from static meshes,
not a compatible skeletal rig.

Lethal damage produces a reliable terminal discharge. Nearby hostile pawns receive a distance-
attenuated pathogen dose, the corpse's shedding rate rises for its remaining five-second lifetime,
and the infection light expands into a 1.25-second burst. Crew select one of the compatible Fab
lying poses while machinery slumps and drops both arms. `tools/build_bloom_combat_pose_showcase.py` authors the brightly lit
`/Game/Assets/Maps/Bloom/L_Bloom_CombatPose_Showcase` and renders the idle, windup, and death poses
to `Art/Characters/BloomEnemies/Combat/BloomCombatPoses.png`.

The two host families deliberately use different response curves. Reanimated crew begin changing
early and grow from 85 to 140 health as chest, head, arm, and leg growths emerge. Mechanized hosts
resist the early stages, then accelerate through Puppeteer and Manifestation, growing from 180 to
320 health as core, arm, and crown structures appear. Damage and reach scale alongside health, so
progression changes silhouette and encounter role rather than only swapping a material.

`tools/build_bloom_progression_showcase.py` authors
`/Game/Assets/Maps/Bloom/L_Bloom_Progression_Showcase` with four locked examples of each family and
renders `Art/Characters/BloomEnemies/Progression/BloomProgression_Lineup.png`. The automation test
`Ginnungagap.Gameplay.Bloom.Enemies.ProgressiveStageMapping` guards normalized monotonic mappings,
the earlier humanoid curve, terminal saturation, pathogen-component presence, and the infection
visibility lights. The map uses independent neutral inspection keys for every specimen plus broad
front, fill, and rim sources; the neutral keys expose Fab mesh detail while the colored local glow
continues to communicate gameplay state.

## RealityScan workflow

`tools/build_bloom_fab_realityscan_prototypes.py` creates the review map at
`/Game/Assets/Maps/Bloom/L_Bloom_FabRealityScan_Prototypes` and renders two deterministic 36-frame
turntables beneath `Art/Characters/BloomEnemies/RealityScan`. Each capture manifest records the
design-authority concept, exact Fab sources, project sources, gameplay class, camera transforms, and
the rule that a reconstructed shell is a surface/retopology reference rather than an animation rig.

`tools/write_realityscan_bloom_xmp.py` writes locked camera priors. The existing
`tools/run_realityscan_unreal_pilot.ps1` performs reconstruction and enforces the promotion gate.

The initial 768 px pilot registered 36/36 images for both enemies, proving the virtual-camera
pipeline. The generated surfaces remained below the 10,000-face promotion floor (1,260 humanoid;
3,174 robot), so both outputs are deliberately quarantined and are not imported into `/Game`.
Future scans should increase surface feature density and capture resolution before relaxing any
gate. The articulated Unreal source classes remain the gameplay masters regardless of scan status.

## Next production pass

1. Replace fixed crystal placement with socket-specific transforms validated across every phase in motion.
2. Add compatible Fab or bespoke phase-specific infected idle, locomotion, stagger, melee, and
   zero-g animation sets; retain the audited Fab terminal poses for death variation.
3. Author a feature-rich neutral scan material and recapture at 1600-2048 px.
4. Promote a passing RealityScan shell only as a sculpt/retopology reference.
5. Skin the humanoid shell to the Manny skeleton and rigid-bind the robot parts to a Control Rig.
