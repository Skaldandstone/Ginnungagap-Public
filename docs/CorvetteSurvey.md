# Corvette survey

Written by `Ginnungagap.Survey.CorvetteWalkthrough` on 2026-09-06 02:09 from `/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack`. The character was driven on foot up the objective chain, back down it, and out to every side station; everything below was met on the way. Regenerate with the test, do not edit by hand.

## The walk

| # | Leg | Deck | Where | Path (m) | Walk (s) | Snags | Outcome |
|---|-----|------|-------|----------|----------|-------|---------|
| 1 | suit rack | 3 | (120, 1200, 960) | 2.9 | 0 | 0 | arrived, played |
| 2 | workshop bench | 2 | (1300, 1400, 522) | 44.5 | 9 | 1 | arrived with snags, played |
| 3 | power station | 1 | (750, 1250, 41) | 35.5 | 0 | 0 | arrived, played |
| 4 | breach patch | 7 | (450, 1707, 2621) | no path | 23 | 0 | arrived, played |
| 5 | CIC access panel | 8 | (830, 910, 3051) | 30.5 | 1 | 0 | arrived, played |
| 6 | CIC console | 8 | (750, 1520, 3051) | 29.4 | 5 | 0 | arrived, played |
| 7 | back to the breach patch | 7 | (450, 1707, 2621) | 35.7 | 6 | 0 | arrived |
| 8 | back to the power station | 1 | (750, 1250, 41) | 128.8 | 26 | 0 | arrived |
| 9 | back to the workshop bench | 2 | (1300, 1400, 522) | 34.2 | 6 | 0 | arrived |
| 10 | back to the suit rack | 3 | (120, 1200, 960) | 44.0 | 12 | 1 | arrived with snags |
| 11 | side: CVT_BatteryRecovery | 1 | (1410, 1200, 41) | 60.2 | 6 | 1 | arrived with snags |
| 12 | side: CVT_ArmoryOverride | 4 | (93, 1600, 1331) | 76.8 | 13 | 0 | arrived |
| 13 | side: CVT_SuitPatching | 5 | (93, 1250, 1761) | 34.4 | 7 | 0 | arrived |
| 14 | side: CVT_TurretService | 5 | (1410, 1200, 1761) | 9.5 | 2 | 0 | arrived |
| 15 | side: CVT_ScrubberService | 6 | (1410, 1600, 2191) | 43.2 | 7 | 0 | arrived |
| 16 | side: CVT_Door_CVT-D07 | 7 | (750, 1000, 2560) | no path | 12 | 1 | arrived with snags |
| 17 | side: CVT_PlotterCore | 9 | (1410, 1600, 3481) | 55.5 | 9 | 0 | arrived |
| 18 | side: CVT_Door_CVT-D10-B | 10 | (1950, 1000, 3850) | 40.1 | 9 | 0 | arrived |
| 19 | side: CVT_ObsDecon | 10 | (93, 1200, 3911) | 16.9 | 3 | 0 | arrived |
| 20 | side: CVT_SensorCalibration | 11 | (1410, 1600, 4341) | 39.8 | 7 | 0 | arrived |

## Collision and movement findings

- Blocked: locked door CVT_Door_CVT-D03 at (1050, 1000, 840) (deck 3) on the way to workshop bench (vacuum beyond: suit up, then override from the panel); the override panel releases it.
- Blocked: welded door CVT_Door_CVT-D07 at (750, 1000, 2560) (deck 3) on the way to workshop bench; cut through with the tool.
- Snag: stuck at (969, 1069, 958) (deck 3) on the way to workshop bench, 3.8 m short, against CVT_Door_CVT-D03.
- Blocked: no complete path from (1003, 1327, 528) to breach patch; nearest obstacle CVT_D04_CorridorTray (Fallen cable tray, 10.0 m from the path's end). A player cuts, squeezes or overrides here.
- Snag: stuck at (969, 931, 958) (deck 3) on the way to back to the suit rack, 7.5 m short, against CVT_Door_CVT-D03.
- Snag: stuck at (976, 1069, 958) (deck 3) on the way to side: CVT_BatteryRecovery, 3.1 m short, against CVT_Door_CVT-D03.
- Blocked: no complete path from (1239, 1474, 2248) to side: CVT_Door_CVT-D07; nearest obstacle door CVT_Door_CVT-D07 (1.0 m from the path's end). A player cuts, squeezes or overrides here.
- Snag: stuck at (793, 1011, 2678) (deck 7) on the way to side: CVT_Door_CVT-D07, 1.4 m short, against nothing solid (a navmesh or path-following stall).

## Asset audit

What each interactable is made of. A station with a static mesh and no skeletal mesh is a prop that speaks only through its prompt: the activity plays as a timer or a button sequence with nothing moving on it.

| Actor | Class | Deck | Where | Made of | Note |
|-------|-------|------|-------|---------|------|
| CVT_PowerRestore | QuickDemoPowerStation | 1 | (750, 1250, 41) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_BatteryRecovery | BatteryRecoveryStation | 1 | (1410, 1200, 41) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_EngineeringOverride | MechanicalOverrideStation | 2 | (830, 910, 471) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_WorkshopBench | QuickDemoWorkshopBench | 2 | (1300, 1400, 522) | static prop | SM_Toolbox | activity station: prompt + timer/sequence, nothing animates |
| CVT_SuitRepairBench | QuickDemoSuitRepairBench | 2 | (1050, 1707, 471) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_CryoDoorOverride | MechanicalOverrideStation | 3 | (1410, 1090, 901) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_SuitStation_01 | QuickDemoSuitStation | 3 | (120, 1200, 960) | skeletal SK_SpaceMarshal_Manny | activity station: prompt + timer/sequence, nothing animates |
| CVT_SuitStation_02 | QuickDemoSuitStation | 3 | (120, 1600, 960) | skeletal SK_SpaceMarshal_Manny | activity station: prompt + timer/sequence, nothing animates |
| CVT_ArmoryOverride | MechanicalOverrideStation | 4 | (93, 1600, 1331) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_TurretService | TurretServiceStation | 5 | (1410, 1200, 1761) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_SuitPatching | SuitPatchingStation | 5 | (93, 1250, 1761) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_AirlockRepressurize | AirlockRepressurizationStation | 6 | (1700, 1710, 2191) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_ScrubberService | OxygenScrubberServiceStation | 6 | (1410, 1600, 2191) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_BreachPatch | QuickDemoBreachStation | 7 | (450, 1707, 2621) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_CICAccess | QuickDemoCICAccessStation | 8 | (830, 910, 3051) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_CICConsole | QuickDemoCICConsole | 8 | (750, 1520, 3051) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_PlotterCore | ComponentReplacementStation | 9 | (1410, 1600, 3481) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_ObsDecon | DecontaminationStation | 10 | (93, 1200, 3911) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_SensorCalibration | SensorCalibrationStation | 11 | (1410, 1600, 4341) | static prop | SM_COMPUTER_02 | activity station: prompt + timer/sequence, nothing animates |
| CVT_Supply_FieldRepairKit_D01 | InventoryItemPickup | 1 | (400, 1300, 6) | static prop | SM_Toolbox | pickup |
| CVT_Supply_CoolantGelPack_D01 | InventoryItemPickup | 1 | (1150, 1300, 6) | static prop | SM_Case_A | pickup |
| CVT_Supply_SuitPatchSealant_D02 | InventoryItemPickup | 2 | (400, 1300, 436) | static prop | SM_WireReel_A | pickup |
| CVT_Supply_TraumaKit_D03 | InventoryItemPickup | 3 | (400, 1300, 866) | static prop | SM_Case_A | pickup |
| CVT_Supply_GeneralMedicalAmpoule_D03 | InventoryItemPickup | 3 | (1150, 1300, 866) | static prop | SM_Frontier_Scanner | pickup |
| CVT_Supply_SuitPatchSealant_D04 | InventoryItemPickup | 4 | (400, 1300, 1296) | static prop | SM_WireReel_A | pickup |
| CVT_Supply_EmergencyOxygenCartridge_D04 | InventoryItemPickup | 4 | (1150, 1300, 1296) | static prop | SM_OxygenTank_B | pickup |
| CVT_Supply_EmergencyOxygenCartridge_D05 | InventoryItemPickup | 5 | (400, 1300, 1726) | static prop | SM_OxygenTank_B | pickup |
| CVT_Supply_CompoundSplint_D05 | InventoryItemPickup | 5 | (1150, 1300, 1726) | static prop | SM_RubberMat_Rolled | pickup |
| CVT_Supply_GeneralMedicalAmpoule_D06 | InventoryItemPickup | 6 | (400, 1300, 2156) | static prop | SM_Frontier_Scanner | pickup |
| CVT_Supply_EmergencyOxygenCartridge_D06 | InventoryItemPickup | 6 | (1150, 1300, 2156) | static prop | SM_OxygenTank_B | pickup |
| CVT_Supply_SuitPatchSealant_D07 | InventoryItemPickup | 7 | (400, 1300, 2586) | static prop | SM_WireReel_A | pickup |
| CVT_Supply_RecompressionAmpoule_D07 | InventoryItemPickup | 7 | (1150, 1300, 2586) | static prop | SM_Frontier_Scanner | pickup |
| CVT_Supply_CoolantGelPack_D08 | InventoryItemPickup | 8 | (400, 1300, 3016) | static prop | SM_Case_A | pickup |
| CVT_Supply_ChelationInjector_D08 | InventoryItemPickup | 8 | (1150, 1300, 3016) | static prop | SM_Frontier_Scanner | pickup |
| CVT_Supply_FieldRepairKit_D09 | InventoryItemPickup | 9 | (400, 1300, 3446) | static prop | SM_Toolbox | pickup |
| CVT_Supply_RecompressionAmpoule_D10 | InventoryItemPickup | 10 | (400, 1300, 3876) | static prop | SM_Frontier_Scanner | pickup |
| CVT_Supply_ThermalRegulationWrap_D10 | InventoryItemPickup | 10 | (1150, 1300, 3876) | static prop | SM_RubberMat_Rolled | pickup |
| CVT_Supply_EmergencyOxygenCartridge_D11 | InventoryItemPickup | 11 | (400, 1300, 4306) | static prop | SM_OxygenTank_B | pickup |
| CVT_Supply_FieldRepairKit_D11 | InventoryItemPickup | 11 | (1150, 1300, 4306) | static prop | SM_Toolbox | pickup |
| CVT_TrunkBarrier | ObstructionBarrier | 4 | (230, 345, 1450) | static prop | SM_Ceiling_HB_A | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_D04_CorridorTray | ObstructionBarrier | 4 | (700, 800, 1450) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_PlenumCrawl | ObstructionBarrier | 5 | (1550, 510, 1880) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_D06_RoomCollapse | ObstructionBarrier | 6 | (1540, 1240, 2310) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_ConduitBarrier | ObstructionBarrier | 6 | (230, 345, 2310) | static prop | SM_CABLE_MASS_04 | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_D09_CorridorTray | ObstructionBarrier | 9 | (1900, 800, 3600) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_CorridorDebris | ObstructionBarrier | 9 | (1400, 800, 3600) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_D10_RoomCollapse | ObstructionBarrier | 10 | (1540, 1240, 4030) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_D10_CorridorTray | ObstructionBarrier | 10 | (700, 800, 4030) | static prop | SM_AirDuct_Mid | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |
| CVT_CoolantBarrier | ObstructionBarrier | 10 | (230, 345, 4030) | static prop | SM_PIPE_03 | obstruction: cut/squeeze verbs, no cut or crawl animation on the barrier |

Also aboard: 38 bulkhead doors (sliding leaves animate, sound on open/close), 2 cryo pods (lid animates), 59 text signs (TextRender on plates: no printed asset), 5 objective beacons (TextRender), 0 placed meshes with the engine default material.

| Floating prop | Class | Deck | Where | Mesh | Under it (cm) | Nearest wall (cm) |
|---------------|-------|------|-------|------|---------------|-------------------|
| (0 floating props in all) | | | | | | |

Figures at the end of the walk; the crew stands at (1174, 1502, 4398).
| Figure | Class | Deck | Where | Mesh | Attached to |
|--------|-------|------|-------|------|-------------|
| CVT_SuitStation_02 | QuickDemoSuitStation | 3 | (175, 1600, 864) | SK_SpaceMarshal_Manny | nothing |
| BP_PlayerFace010 | BP_PlayerFace01_C | 11 | (1174, 1502, 4308) | SKM_MHC_Face01_Ada_FaceMesh | BP_Player_Suit_Crew0 |
| BP_PlayerFace011 | BP_PlayerFace01_C | 11 | (1174, 1502, 4308) | SKM_MHC_Face01_Ada_FaceMesh | BP_Player_Suit_Crew0 |

## Next work drawn from this survey

- 47 activity stations are static props with a text prompt: each wants a purpose-built asset with an animation for its activity (panel opening, lever, weld arc, console boot).
- 1 placed meshes render with the engine default material (grey, reads as collision).
- Floating props: (0 floating props in all): each wants a stand, a bracket or a move to the wall or deck.
- Blocked: locked door CVT_Door_CVT-D03 at (1050, 1000, 840) (deck 3) on the way to workshop bench (vacuum beyond: suit up, then override from the panel); the override panel releases it.
- Blocked: welded door CVT_Door_CVT-D07 at (750, 1000, 2560) (deck 3) on the way to workshop bench; cut through with the tool.
- Blocked: no complete path from (1003, 1327, 528) to breach patch; nearest obstacle CVT_D04_CorridorTray (Fallen cable tray, 10.0 m from the path's end). A player cuts, squeezes or overrides here.
- Blocked: no complete path from (1239, 1474, 2248) to side: CVT_Door_CVT-D07; nearest obstacle door CVT_Door_CVT-D07 (1.0 m from the path's end). A player cuts, squeezes or overrides here.
- Every snag, penetration and floor gap above is a place to stand in the editor and look.
