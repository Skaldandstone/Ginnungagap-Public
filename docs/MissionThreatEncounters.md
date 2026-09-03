# Mission threat encounters

`AShipThreatDirector` adds hostile encounters without changing `UBloomDirector`. This allows a
boarding action or alien incursion to be the mission's primary antagonist in a Bloom-free run, or
to occur at the same time as an active Bloom stage.

## Included presets

| Preset | Composition | Intended pressure |
| --- | --- | --- |
| `PirateBoarding` | 3 breachers, 2 gunners | Close-range entry team backed by ranged fire |
| `RebelTakeover` | 3 saboteurs, 1 heavy | Fast disruption team with a durable anchor |
| `AlienHuntingPack` | 2 biped hunters, 3 quadruped stalkers | Coordinated pursuit |
| `AlienBrood` | 6 arachnoped ambushers, 1 quadruped stalker | Numerous fragile ambushers |
| `MixedAlienIncursion` | Biped, quadruped, and arachnoped aliens | Full mixed-threat encounter |

Every preset is independent of the Bloom and allows overlap by default. For a custom encounter,
set `Preset` to `Custom`, edit `EncounterDefinition.SpawnGroups`, then use:

- `bRequiresBloom` for a threat that only becomes eligible after Bloom activation.
- `bCanOverlapBloom` to permit or prevent simultaneous activation.
- `bPrimaryAntagonist` to register a required kill objective and block jumping until resolved.

## Level use

Place `AShipThreatDirector` in an authored mission level and choose a preset. Optional
`SpawnAnchors` give exact entry points; otherwise the director chooses seeded ship sections and
falls back to a radius around itself. Multiple directors can coexist for multi-faction missions.

`AShipDistrictGameplayDirector.ThreatPreset` exposes the same presets for production districts.
`Custom` retains the district's legacy Bloom patrol, so existing maps do not change until a preset
is deliberately selected.

The current alien meshes are replacement-ready proxies built from the project's existing creature
silhouettes. Their faction, combat logic, objective state, and Bloom independence are native C++
gameplay and do not depend on the proxy art.
