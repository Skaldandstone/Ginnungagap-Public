# Asymmetric versus mode

Versus reuses the authored survival expedition and replaces the all-crew roster with two
player teams plus optional independent AI factions:

- **Protagonists:** 1–8 crew using `ACoopSurvivalCharacter` and the existing expedition loop.
- **Antagonists:** 1–4 players sharing a selected faction: Bloom, pirates, rebels, or alien.
- **Independent AI:** optional factions that pursue their own agenda. They attack protagonists
  and any antagonist faction other than their own. For example, AI pirates attack both the crew
  and player-controlled Bloom.

The native setup screen exposes the crew count, antagonist count, player antagonist faction, and
one independent AI faction. `FVersusMatchSettings` supports multiple independent factions, so a
Blueprint lobby or online-session layer can add multi-select without changing match code.

## Runtime architecture

- `AVersusGameMode` parses match URL options, caps the roster at 8v4, assigns unclaimed players
  toward the configured team ratio, selects the correct pawn class, and starts independent
  encounters.
- `AVersusGameState` replicates the match settings and phase.
- `AVersusPlayerState` replicates team/faction identity and owns server-authoritative antagonist
  skill points and unlocks.
- `UTeamAffiliationComponent` is attached to crew and hostile pawns. Its relationship rules make
  same-faction actors allies and distinct antagonist factions enemies.
- `AAntagonistPlayerCharacter` is the controllable native antagonist base. It currently supplies
  movement, replicated faction presentation, a server-authoritative primary attack, and skill
  effect lookup. Faction-specific Blueprint pawns can subclass it.
- `UAntagonistSkillTreeSubsystem` supplies separate native Bloom, pirate, rebel, and alien trees.
  Each entry has a tier, cost, prerequisites, an effect identifier, and a magnitude.

The regular shipboard weapon path consults faction affiliation before applying biological damage,
so teammates cannot damage each other through the native weapon implementation. Independent threat
AI and its close-range attacks use the same relationship check when selecting targets.

## Antagonist activities

Antagonist objectives use a separate server-authoritative activity runtime rather than treating
every faction as a crew member holding a different tool. Completing an activity awards faction
skill points and command resources, then invokes a named world-effect hook for the faction director.

| Faction | Authored activities | Primary mechanics |
| --- | --- | --- |
| Pirates | Breach locks, strip cargo, jam communications, rally boarders | Circuit intrusion, timed extraction, signal spoofing, command uplink |
| Rebels | Spoof credentials, cascade the power grid, plant false telemetry, arm a scuttle relay | Signal spoofing and infrastructure intrusion; compatible with selected crew terminals |
| Bloom | Assimilate biomass, weave mycelial routes, mimic neural patterns, establish nodes | Metabolic balance, territory weaving, neural mimicry |
| Alien | Triangulate scent, feed without exposure, prepare ambushes, mark pack routes | Scent triangulation, metabolic restraint, ambush timing |

`AAntagonistActivityNode` is the placeable world source. `UAntagonistActivityComponent` validates
range, faction, source, inputs, and completion on the server. `UAntagonistActivityWidget` provides
the native faction-colored minigame readout and is created automatically for antagonist pawns.
Pirate and rebel definitions may opt into existing human-facing stations; Bloom and alien
definitions explicitly cannot.

## Antagonist commander

The first antagonist is assigned commander by default, with replicated claim/release support for
team handoff. Operatives earn a shared command-resource pool through faction activities. The
commander spends that pool on prioritized Attack, Defend, Scout, Sabotage, Harvest, Infest, and
Rally orders. The server validates faction permissions, resource cost, commander identity, and a
maximum of eight live orders.

Same-faction AI reads the highest-priority active order and moves toward its target when it has no
immediate hostile contact. Thus a player commander can direct native reinforcements while other AI
factions remain independent and hostile to both teams. Faction vocabulary matters: Bloom can issue
Infest but not Sabotage; pirates and rebels can Sabotage but not Infest; alien packs use hunting and
rally orders rather than either technical action.

The current slice provides the replicated role, economy, order API, and AI consumption path while
the commander still possesses a field pawn. A Savage-style overhead camera, tactical map, order
placement cursor, voting/mutiny flow, and faction-specific summon/build menus remain the next UI
and presentation layer over this foundation.

## Launch and connection options

The menu launches the listen host with the dedicated mode automatically. Direct server travel uses:

```text
/Game/Assets/Maps/ShipProduction/L_Medium_ExpressSpine_Showcase
  ?game=/Script/Ginnungagap.VersusGameMode
  ?Protagonists=8
  ?Antagonists=4
  ?AntagonistFaction=Bloom
  ?IndependentAI=Pirates,Rebels
  ?listen
```

Clients may request `?Team=Protagonist` or `?Team=Antagonist`. A request is honored when that team
has room; otherwise the server fills an available team or makes the player a spectator when full.

## Extending factions

To add an antagonist type:

1. Add the enum value to `EAntagonistFaction` and its URL/display conversion.
2. Add skills in `ResetToDefaultSkillTrees`, or replace the native list with a data-asset-backed
   catalog when live balancing begins.
3. Add a faction-specific `AAntagonistPlayerCharacter` subclass and select its representative
   visuals, combat profile, active abilities, and skill-effect handlers.
4. Add an independent encounter preset if the faction can appear under AI control.
5. Add relationship, tree, roster, and network automation coverage.

The current effect identifiers deliberately separate unlock validation from ability implementation.
`GetUnlockedEffectMagnitude` already applies numeric effects such as Bloom host cooldown; active
effects such as host transfer, objective blackout, or reinforcement spawning are extension hooks
for their respective faction directors.
