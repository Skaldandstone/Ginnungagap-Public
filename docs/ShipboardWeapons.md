# Shipboard weapon foundation

The runtime weapon foundation treats weapons as physical world objects rather than player- or
drone-specific inventory entries. `AShipboardWeapon` owns the mesh, safe and unsafe firing profiles,
cooldown, recoil, hull risk, and traversal envelope. `UWeaponMountComponent` supplies the operator.
The same weapon actor can be released from a player mount and attached to an aerial or robotic drone
mount without losing its modification state.

## First playable vertical slice

`ACaptiveBoltDriver` is spawned on `ACoopSurvivalCharacter` by default. It uses the existing rivet-tool
mesh as a temporary visual until the dedicated captive-bolt asset is imported.

- Primary fire: left mouse or gamepad right trigger.
- Toggle the unsafe extended bolt: `V` or gamepad D-pad up.
- Right magnetic glove moved from gamepad right trigger to left trigger to avoid an input collision.
- Safe mode has short reach, moderate biological damage, low recoil, and no hull damage.
- Unsafe mode increases reach, damage, impulse, recoil, cooldown, hull impact, and breach severity.

The server executes the trace, biological damage, physical impulse, recoil, and ship damage. Fire
cosmetics multicast to clients through `ReceiveFireCosmetics`, which Blueprint subclasses can use for
animation, audio, light, particles, decals, and camera response.

## Creating a weapon

1. Derive a Blueprint or C++ class from `AShipboardWeapon`.
2. Assign a mesh and muzzle position.
3. Configure `SafeProfile` and `UnsafeModifiedProfile`.
4. Configure the oriented `CollisionEnvelope`, including its center offset and optional folded size.
5. Set player, aerial-drone, and robotic-drone compatibility.
6. Mount the actor through `UWeaponMountComponent::MountWeapon`.

For large content sets, create `UShipboardWeaponDefinition` Data Assets and assign them to thin
Blueprint actor classes. The definition is a primary asset named `ShipboardWeapon:<WeaponId>`.

## Drone integration

Add `UWeaponMountComponent` to an aerial drone Blueprint, set `OperatorType` to `AerialDrone`, and
orient the component along the drone's firing axis. AI can call `FireAlongMountForward`; directed
orders can call `FireWeapon` with a sensor-derived origin and direction. Recoil is applied to a
physics-simulating drone root, so weapon mass, bracing, and counter-thrusters can remain meaningful.

Heavy robotic drones use the identical workflow with `OperatorType = RoboticDrone`.

Before applying thrust or accepting a navigation segment, drone movement code calls
`CanMoveMountedWeapon`. This uses the same oriented sweep and passage rules as the player, so aerial
drones cannot carry a broad or long tool through geometry simply because their chassis fits.

## Collision-envelope authoring

Mounted weapons are checked with an oriented box sweep against world-static and world-dynamic
geometry. Player movement input is rejected before entry, while existing zero-g velocity is clipped
only along the blocking normal. Backing away and sliding free remain possible.

Use `ATraversalClearanceVolume` where raw level collision cannot express a meaningful aperture, such
as a hatch, duct mouth, squeeze gap, or partially blocked corridor:

1. Center the volume on the aperture and point its local X axis along the travel direction.
2. Set `ClearWidthCm` along local Y and `ClearHeightCm` along local Z to the real clear opening.
3. Make `ApproachDepthCm` long enough to overlap the operator before the weapon reaches the opening.
4. Leave automatic folding enabled for collapsible tools, or disable it when folding should require an
   explicit player or drone order.
5. Bind `OnTraversalRejected` or the character's `ReceiveWeaponTraversalBlocked` event for UI, audio,
   animation, and contextual third-person feedback.

Passage fitting projects the rotated weapon envelope onto the opening, so a long tool can pass muzzle
first yet fail when carried broadside. Oversized operators can always retreat toward their entry side.

Projectile flight, tethers, foam accumulation, thermal transfer, and autonomous target doctrine remain
specialized weapon-subclass concerns built on this shared foundation.

## Production content batches

The first broad mining/salvage family is documented in
`docs/SalvageGameplayBatch03.md`. Its ten tool-weapons share the mount and traversal conventions
above; eight related world objects provide ammunition, samples, charging, storage, and navigation
support. Unreal Geometry Scripting builds the meshes, Data Assets, actor Blueprints, weighted
world-item catalog, district defaults, and in-engine review map in one reproducible editor pass.
