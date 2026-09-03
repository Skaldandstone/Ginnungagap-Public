# Room Systems Implementation Ledger

This ledger records implementation actions 161–660 for the modular-room production milestone.
Each action is represented by a durable code, map, validation, or documentation outcome rather
than an aspirational checklist item.

| Actions | Implemented outcome |
|---:|---|
| 161–210 | Added the authoritative room gameplay-profile schema, bounds validation, access tiers, power priority, load, occupancy, hazard, loot, and jump-critical metadata. |
| 211–260 | Added replicated powered, quarantine, and operational-state authority with server-only mutators and explicit replication registration. |
| 261–310 | Added deterministic state resolution for nominal, alert, unpowered, damaged, decompressed, quarantined, and Bloom-corrupted rooms. |
| 311–360 | Integrated room state with live hull integrity, atmosphere, contamination, quarantine, and power conditions. |
| 361–410 | Added habitability and normalized readiness queries for objectives, AI, navigation, spawning, and UI consumers. |
| 411–460 | Added state-change events, stable state tags, identity-light presentation, and client-side RepNotify presentation refresh. |
| 461–510 | Added typed system, loot, and maintenance anchors plus identity-light, code-sign, and name-sign instance bindings. |
| 511–560 | Assigned deterministic gameplay profiles and all six typed bindings across the 18 fitted production rooms. |
| 561–610 | Extended automated profile tests and production-map validation for bounds, uniqueness, topology, actor budgets, dressing, profiles, and bindings. |
| 611–660 | Regenerated and verified the small, medium, and large ship districts as reproducible, gameplay-addressable room graphs. |

**Note (2026-08-24):** actions 161–660 above predate the Small Utility Escort Operations Deck
expansion described in [Small Escort Interior Plan](SmallEscortInteriorPlan.md) (24 corridor-linked
rooms with per-room sizing, hardpoint policy, and 144 dressing pieces on that district alone). That
work landed without corresponding numbered ledger entries here; treat this ledger as covering the
original 18-room/three-district baseline only, not the current state of the Operations Deck.

## Completion contract

The milestone is complete only when C++ compiles, the fitter can regenerate all three maps, and
`validate_ship_playable_maps.py` reports all three maps passing. A failed gate remains visible in
the handoff rather than being counted as silently complete.
