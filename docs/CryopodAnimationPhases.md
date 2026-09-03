# Cryopod Animation Production Phases

## Phase 1 - playable blockout (implemented)

- Bidirectional pod state machine: enter, confirm, seal, sedate, wake, release, and exit.
- Player movement lock with limited first-person camera control during the sequence.
- Failed first release attempt and successful auxiliary-power retry.
- Procedural canopy, restraint, status-light, camera, and player-root motion.
- Four-pod compact cryo bank: two functional pods and two damaged rear pods.
- Initial spawn begins inside the occupied primary pod and hands control back after exit.

All timing values live on `ACryopod` as editable defaults. The procedural motion is a blockout and should be replaced by animation montages without changing the gameplay state transitions.

## Phase 2 - animation assets

- The playable blockout now includes an articulated 11-part pose rig on `AExplorerCharacter`. It is owner-hidden for first person, visible to other players, and driven by `ECryopodBodyPose`.
- Create shared entry, settle, restraint-check, waking, sit-up, leg-swing, stumble, and recovery clips.
- Add additive personality variants: calm, nervous, exhausted, claustrophobic, violent wake, and injured.
- Add first-person arms and third-person full-body alignment markers.
- Replace root interpolation with motion-warp targets supplied by the pod.

### Production rig contract

The replacement humanoid skeleton should expose pelvis, spine, head, left/right upper arm, forearm, thigh, and calf chains. Animation or Control Rig poses map directly to these gameplay poses:

| Gameplay pose | Production clip/control pose |
| --- | --- |
| `Entering` | approach, turn, lower, and align to pod bed |
| `Dormant` | restrained neutral sleep loop |
| `Groggy` | breath recovery, eye focus, and head instability additive |
| `ReachControl` | right-hand internal control reach with hand IK |
| `BraceRelease` | failed press plus left-hand pod-rim brace |
| `PushCanopy` | two-hand canopy push with hand IK |
| `SitUp` | torso recovery, cough, and leg swing |
| `ExitStumble` | step-down, knee buckle, pod-rim brace, and recovery |

The pod supplies inside and exit transforms today. Production assets should add named alignment targets for pelvis, both hands, both feet, and head; those targets can drive Motion Warping and Control Rig without changing pod state authority.

## Phase 3 - pod presentation

- Replace primitive shell with production pod mesh, articulated canopy, latches, restraints, and internal control.
- Add condensation wipe, frost breakup, coolant drain, vapor, sparks, and damaged-pod leakage.
- Add mechanical loops, failed-release impacts, breathing, coughs, hull vibration, and muffled sealed audio.
- Drive cyan/amber/red emissive states through material parameters.

## Phase 4 - jump orchestration

- Add ship-level readiness coordinator with `Unassigned -> Approaching -> Entering -> Inside -> Confirmed -> Sealed -> Sedated` per player.
- Gate jump commitment on all required occupied pods reaching `Sedated`.
- Support disconnect, incapacity, timeout, emergency release, and squad cancellation policies.
- Connect the interior sedation blackout to the exterior jump sequence and arrival wake event.

## Phase 5 - network and polish

- Make the server authoritative for assignment, interaction gates, and state transitions.
- Replicate pod state, phase start time, occupant, and damage state; derive animation progress locally.
- Validate late join, reconnect, packet loss, simultaneous confirmation, and pod destruction cases.
- Add accessibility options for sequence duration, camera motion, flashes, and interaction holds.
