# Bloom Enemy Expansion

`tools/build_bloom_enemy_expansion.py` creates ten additional Bloom assets under
`/Game/Assets/Models/Bloom/Expansion`: reanimated-crew infection shells, infested-drone rigid rig
parts, a spore sac, calcified barricade, floor growth, and ceiling-stalker proxy.

Crew overlays are designed to attach to an existing Manny-compatible corpse skeleton. Drone parts
retain independent pivots for rigid skeletal binding. Encounter-scale proxies and destructible
growths receive generated collision; attachment and rig-source pieces intentionally do not.

The newer Fab-derived articulated prototypes and their RealityScan capture/promotion workflow are
documented in `docs/BloomFabRealityScanPrototypes.md`. Their gameplay classes are
`ABloomReanimatedCrewEnemy` and `ABloomMechanizedEnemy`.
