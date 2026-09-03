# Gameplay Model Library

`tools/build_gameplay_model_library.py` is the reproducible first-pass model library for gameplay-visible objects outside the existing ship-kit and player-suit generators.

It generates 24 correctly scaled Unreal static meshes under `/Game/Assets/Models`:

- six handheld tools and weapons;
- five resource and consumable pickups;
- two retrieval/repair drones;
- five large ship-system silhouettes;
- two environmental/EVA fixtures;
- four Bloom enemy and hive proxies.

Run it through Unreal's Python commandlet. Generated OBJ interchange files live under `Intermediate/GameplayModels` and are not source assets; imported `.uasset` files are the runtime deliverables.

The Bloom meshes are explicitly named `Proxy`. They establish encounter scale, collision, navigation, lighting, and silhouette while production skeletal meshes, rigs, and animations are authored. The player remains based on the UE Manny skeleton; the existing modular pressure-suit kit supplies its authored visible shell.

## Production sequence

Run `tools/build_gameplay_model_showcase.py` after generation to apply the first category material
language and create `/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary`. The review map arranges
every model in category rows under neutral studio lighting.

1. Hook these silhouettes to existing C++ pickups, equipment, ship systems, drones, and enemy actors.
2. Add shared trim-sheet materials and role/status color instances.
3. Replace Bloom proxies with rigged skeletal meshes without changing gameplay dimensions.
4. Add authored LODs, sockets, destructible parts, and final collision.
5. Expand the same generator with room-specific clutter and exterior ship modules as their gameplay briefs stabilize.
