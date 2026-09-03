# Character Equipment and Bloom Rig Preparation

`tools/build_character_and_bloom_models.py` creates eight Manny-scale wearable modules and eight
separated Bloom body modules. Wearables live under `/Game/Characters/Player/Equipment/Meshes`.
Bloom rig-prep meshes live under `/Game/Assets/Models/Bloom/RigPrep`.

Wearables are static attachment pieces intended for helmet, chest, shoulder, accessory, and tool
sockets. Bloom modules intentionally have independent origins and no generated collision. They are
source pieces for skeletal binding, mirrored limbs, damage swaps, and Control Rig authoring; the
existing whole-body proxy meshes remain the gameplay fallback until skeletal assets are complete.

Recommended Bloom skeleton chains:

- Crawler: `root -> pelvis -> spine -> neck -> head`, plus four paired two-segment leg chains.
- Puppeteer: Manny-compatible root/pelvis/spine naming where practical, with elongated arm/leg
  chains and optional tendril chains parented to spine and clavicle joints.
- Infested drone: rigid root with independently animated nacelle and tendril bones.

`tools/validate_model_library.py` checks the critical character, Bloom, gameplay, fleet, material
showcase, and map references and enforces the expected generated-mesh floor in CI or locally.
