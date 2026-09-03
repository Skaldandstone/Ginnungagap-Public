# GGP-01 Coordinate and Room-ID System

The canonical dimensions and playable-sector transform live in `Config/ShipLayout.json`. The inspectable all-angle drawing is `Tools/ship-cross-section-map.html`.

## Datum and axes

- Origin: aft-most point on the ship centerline at the keel reference plane.
- `+X`: forward, measured in meters.
- `+Y`: starboard; port is negative.
- `+Z`: dorsal/up from the keel datum.
- Unreal conversion: multiply meters by 100 for centimeters. If the ship actor uses a different forward axis, apply one actor-level basis transform; room data stays in ship coordinates.

## Stable room IDs

`GGP01-D{deck}-Z{zone}-{side}-{bay}`

Example: `GGP01-D11-Z4-P-01` identifies the port room in bay 01 on ship deck 11, pressure zone 4. IDs describe topology and must not change when a seed changes room purpose, blocker, loot, damage, or lighting.

The current internal deck indices map to ship-facing decks as follows:

| Generator deck index | Ship deck |
| --- | --- |
| 1 | 09 |
| 2 | 10 |
| 3 | 11 |
| 4 | 12 |

## Playable-sector transform

The sector begins 466 m forward of the aft datum and spans 72 m. For a one-based bay number `b`, side offset `y`, and ship deck `d`:

```text
X_m = 466 + (b - 0.5) × 6
Y_m = -4.3 for port, +4.3 for starboard
Z_m = (d - 1) × 4.3
```

The 6 m × 6 m × 3.2 m value describes a **coordinate slot**, not a mandatory room size. A generated room claims one or more contiguous slots: compact 1×1 rooms, 2×1 workshops, 2×2 common or medical spaces, 3×1 cargo/machinery rooms, L-shaped combinations, and occasional double-height spaces. Exterior hull, armor, conduits, interstitial spaces, and structural frames sit outside these clear dimensions.

## Corridor graph

Corridors are generated as a connected graph over slot edges rather than as a permanent straight centerline. Valid motifs include offset spines, doglegs, cross-corridors, loops around large rooms, short service dead ends, and maintenance bypasses. The graph must provide:

- at least two independent traversable routes across the playable sector before damage blockers are applied;
- at least one loop per deck;
- at least two connections between each adjacent deck pair;
- pressure-door choke points at zone or subsystem boundaries;
- guaranteed reachability for cryo, workshop, power control, and emergency CIC;
- no corridor edges through reserved hull structure, tanks, reactor volumes, engine machinery, or hangar voids.

Room identity uses the anchor slot-the aft-most, then port-most occupied slot. The generated room record also stores its complete slot-claim set. Example: `GGP01-D10-Z4-S-05` may claim slots S05, S06, and S07 while retaining one stable room ID.

## Generator integration contract

- Generate identity from the room's anchor slot; store every additional claimed slot in its footprint.
- Store room dimensions and ship-space center independently from rendered mesh transforms.
- Generate and validate the corridor graph before assigning blockers or room archetypes.
- Treat the JSON dimensions as canonical input for map rendering, exterior blockout checks, streaming bounds, and player navigation UI.
- Export generated state keyed by stable room ID. A map consumes state such as room archetype, discovered, powered, pressurized, blocked, breached, and objective without recalculating identity.
- Whole-ship maps may use coarse deck/zone cells. Instantiate the detailed 6 m room grid only for authored or generated playable sectors.
