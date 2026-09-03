# Salvage Gameplay Production Batch 03

Batch 03 is an Unreal-native mining, salvage, and EVA-recovery content family. Its geometry,
materials, gameplay definitions, actor classes, distribution catalog, and review level are generated
inside Unreal Engine 5.8; no Blender, FBX, or GLB import stage is part of this batch.

## Shipped content

Ten mountable tools and industrial weapons:

- Compact Rock Corer
- Thermal Mining Lance
- Regolith Auger
- Explosive Bolt Remover
- Magnetic Scrap Flinger
- Diamond Cable Saw
- Plasma Gouger
- Kinetic Sample Hammer
- Exterior Tether Gun
- Debris Capture Claw

Eight supporting world objects:

- Salvage Tool Rack
- Portable Tool Charger
- Rock Core Canister
- Tether Spool Case
- Thermal Cell Crate
- Explosive Bolt Caddy
- Magnetic Scrap Bin
- Salvage Survey Beacon

The canonical assets live under `/Game/Assets/Gameplay/SalvageBatch03`:

- `Meshes`: 18 Static Mesh assets built with Geometry Scripting
- `Materials`: six shared industrial, first-use ceramic, pickup, hazard, and review materials
- `Data/Weapons`: ten `UShipboardWeaponDefinition` Data Assets
- `Data/Items`: five `UItemDefinition` pickup Data Assets
- `Blueprints`: ten `AShipboardWeapon` actors, five `AInventoryItemPickup` actors, and three
  replicated prop actors
- `Data/DA_SalvageBatch03_SeedCatalog`: the weighted room-compatible distribution catalog

Open `/Game/Assets/Maps/ModelLibrary/L_SalvageGameplayBatch03_Unreal` for the in-engine lineup and
seed-point review level.

Weapons 41–46 are now approved in the clean `FactoryFirstUse` visual state: Compact Rock Corer,
Thermal Mining Lance, Regolith Auger, Explosive Bolt Remover, Magnetic Scrap Flinger, and Diamond
Cable Saw. Their target language is intact warm off-white ceramic, orange safety markings, gunmetal
and function-specific tooling, neutral indicators, and no purple Bloom material. Bloom-infected
versions are separate later-state content and must not be baked into the base equipment assets.

The five new six-view modeling references live under
`Art/Weapons/SalvageBatch03/CleanFirstUseReferences`. They are visual targets for the Unreal-native
geometry pass, not photogrammetrically consistent RealityScan inputs.

## Fab visual chassis

The Cosmoart **Low poly weapons + Test map** pack supplies 29 licensed FBX chassis under
`/Game/ThirdParty/Fab/CosmoartLowPolyWeapons`. An explicit mapping connects one chassis to each
concept weapon while preserving Ginnungagap's weapon IDs, profiles, compatibility, collision
envelopes, Blueprint classes, and seed-catalog entries. The original procedural meshes remain in the
batch as fallback and custom-head geometry sources.

Mapping provenance, confidence, and required concept-fidelity work are recorded in
`Art/Weapons/Fab/CosmoartLowPolyWeapons/WeaponConceptMapping.json`. Low-confidence mappings are
temporary actuator or drive bodies; they do not make generic rifle silhouettes final art.

Import the locally retained Fab source before rebuilding Batch 03:

```powershell
$project = (Resolve-Path .\Ginnungagap.uproject).Path
$script = (Resolve-Path .\tools\import_fab_cosmoart_weapon_pack.py).Path
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  $project "-ExecutePythonScript=$script" -unattended -nop4 -nosplash -NullRHI -NoSound
```

## Runtime distribution

`AWorldItemSeedPoint` is the common server-authoritative placement anchor for weapons, tools,
pickups, movable clutter, and fixed props. It filters catalog entries by room profile, performs
deterministic weighted rolls, applies local scatter, and prevents duplicate entries by default.
Spawned replicated actors provide the client-visible result.

`AShipDistrictGameplayDirector` now owns a catalog reference, seed count, and room-profile pool.
The generator wires the Batch 03 catalog into the production district Blueprint defaults:

- Small district: four rolls across Airlock, DamageControl, and Cargo
- Medium district: seven rolls across MachineShop, Cargo, Armory, and Recycler
- Large district: ten rolls across Cargo, EVA, GeologyLab, Science, and MachineShop

Each district derives deterministic point seeds from its district seed. Authored maps may also place
individual `AWorldItemSeedPoint` actors and select a fixed room profile and seed.

`AInventoryItemPickup` transfers its complete stack atomically into `UInventoryComponent`, uses the
item definition's world mesh and scale, and destroys itself only after a successful authoritative
transfer. `UInteractionComponent` routes client interaction requests through the owning character's
replicated component and revalidates target range on the server.

## Rebuild and validation

Run the complete Unreal-native generation pass from the repository root:

```powershell
$project = (Resolve-Path .\Ginnungagap.uproject).Path
$script = (Resolve-Path .\tools\build_salvage_gameplay_batch_03_unreal.py).Path
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  $project "-ExecutePythonScript=$script" -unattended -nop4 -nosplash -NullRHI -NoSound
```

The generator switches away from its review level before cleanup, rebuilds only the isolated Batch
03 asset root and review map, rewires the three district Blueprints, and writes
`Saved/Reports/SalvageGameplayBatch03Unreal.json`.

Expected report totals are 18 meshes, six materials, 18 actor Blueprints, 10 weapon definitions,
and five item definitions. Run the `Ginnungagap.WorldItems` automation group after C++ changes to validate stable
catalog identity and safe replicated pickup/seed-point defaults.
