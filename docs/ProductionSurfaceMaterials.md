# Production Surface Materials

`tools/build_production_surface_materials.py` creates two shared parameterized masters and eight
category instances under `/Game/Assets/Materials/Production`. The hard-surface master exposes base
color, wear color, procedural wear amount, roughness, and metallic response. The Bloom master adds
bioluminescence while retaining the same wear/noise controls.

The script applies instances to gameplay objects, pickups, drones, machinery, environment props,
ship exteriors, player wearables, and Bloom proxies/rig-prep pieces. Mesh paths remain stable.
