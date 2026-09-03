# Uncorrupted Fab + RealityScan Robot Prototypes

This pass establishes four clean shipboard-robot baselines derived from the imported Fab `Modular_Scifi_Mechanic_Base` kit. The concept authority is `docs/concept-art/reference/bloom/uncorrupted-robot-baselines.png`.

## Prototype set

| Prototype | Gameplay class | Silhouette goal | Fab recipe |
| --- | --- | --- | --- |
| Compact maintenance | `ACompactMaintenanceRobot` | Low, four-limbed inspection and repair chassis | JACK body/limbs, scanner bar, and compact manipulator |
| Tall utility | `ATallUtilityRobot` | Upright general-purpose shipboard worker | JACK body, head, limbs, and chest display panel |
| Heavy cargo | `AHeavyCargoRobot` | Broad, load-bearing frame with short heavy legs and orange cargo pods | Enlarged JACK body/limbs, equipment-box pods, and mechanical crane |
| Security sentry | `ASecuritySentryRobot` | Low magnetic crawler with four articulated anchor points and an elevated scanner silhouette | Fab power-generator hull, four JACK clamp limbs, four broad magnetic contact pads, scanner bar, response arm, and orange power pod |

The actors use the project's light armor, dark structure, and safety-orange materials. They start operational, uncorrupted, fully intact, and fully charged. The shared runtime model provides standby/working/disabled/corrupted states, damage and repair, battery consumption and recharge, player interaction, replicated state/resources, role capabilities, and cyan/green/red/purple status-light feedback. The security crawler additionally exposes replicated magnetic-anchor engagement and clamp strength for zero-g surface traversal. No wheeled locomotion, Bloom biomass, crystal, or corruption material is part of the clean constructors.

Role tuning keeps their gameplay identities separate: maintenance has the best repair output and work efficiency, utility remains the general-purpose manipulator, cargo has the highest integrity and carrying capacity, and security has the longest sensor range.

Prototype review map:

`/Game/Assets/Maps/Robotics/L_Uncorrupted_FabRealityScan_Prototypes`

## RealityScan capture and reconstruction

Each rigid assembly was rendered from 36 locked views at 1600 x 1600. The capture manifest is stored beside each input set under `Art/Robots/Uncorrupted/RealityScan/<Asset>/CaptureManifest.json`; matching XMP files provide locked camera priors.

| Asset | Registered | Components | Vertices | Faces | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| CompactMaintenanceRobot_RS_I02 | 36 / 36 | 1 | 6,912 | 13,696 | Pass |
| TallUtilityRobot_RS_I02 | 36 / 36 | 1 | 12,050 | 24,004 | Pass |
| HeavyCargoRobot_RS_I02 | 36 / 36 | 1 | 13,976 | 27,772 | Pass |
| SecuritySentryRobot_RS_I02 | 36 / 36 | 1 | 13,367 | 26,534 | Pass |

Each `RealityScanOutput` directory contains the `.rsproj`, textured `.obj`, alignment report, logs, and `RealityScanGate.json`.

The original reconstruction is preserved beside each of the first three assets as `RealityScanOutput_Iteration01`; iteration 02 is their promoted role-equipment pass. The rejected wheeled security reconstruction was removed from the active art tree and archived under `Saved/Archive/RejectedWheeledSecuritySentryRealityScan_I01`; only the magnetic-crawler iteration is promoted.

The scan output is approved only as a unified surface, sculpt, bake, and retopology reference. The Unreal modular actor remains the animation and gameplay master so joints, damage states, tool swaps, and later Bloom corruption can remain modular.

## Rebuild workflow

1. Build the editor target after changing the robot classes.
2. Run `tools/build_uncorrupted_robot_fab_realityscan_prototypes.py` through an offscreen Unreal Editor session with rendering enabled.
3. Run `python tools/write_realityscan_uncorrupted_robot_xmp.py`.
4. Run `tools/run_realityscan_unreal_pilot.ps1` once per asset and promote only outputs whose gate is `pass`.

The capture script deliberately records Fab and project source assets in each manifest so later mesh substitutions remain auditable.
