# James ToDo - Editor-only tasks I can't do for you

**Superseded as of 2026-08-24.** Everything below describes an early prototype state (bare-capsule
character, greybox-only ship, "Phase A–D" structure) that the project has long since grown past -
production character meshes, three authored ship districts, a full menu/lobby/multiplayer flow, and
much more now exist. This file is kept for historical context only. Current status lives in
`docs/PRD.md` (see its §7 verification/debt and §8 P0–P3 priorities), and current open work is
tracked in Linear (project "Ginnungagap", team Aurora Anvil) rather than in this file's old
Phase A–D structure.

---

This file tracks work that genuinely requires the Unreal Editor GUI (or other manual/binary-asset
steps) and can't be done via text-file edits or C++. I'll keep this updated as new items come up
across Phases B–D. Cross-reference: `docs/PRD.md` marks the corresponding items 🎨.

---

## Phase A

> Update: item #5 is now complete in C++. `ACoopSurvivalCharacter` assigns the Manny mesh and
> unarmed animation Blueprint directly and adds a modular industrial pressure suit. The older
> manual setup steps below are retained only as historical context.

### #5 - Assign a skeletal mesh + animation Blueprint to `ACoopSurvivalCharacter`

Right now the character has no mesh and renders as a bare capsule.

1. **Get a mesh + skeleton.** Easiest: Content Browser → **Add → Add Feature or Content Pack** →
   add the **"Third Person"** template pack. This gives you a mannequin skeletal mesh (e.g.
   `SKM_Quinn`/`SKM_Manny`) and a matching animation Blueprint (e.g. `ABP_Quinn`), under
   `Content/Characters/Mannequins/`.
2. **Create a Blueprint subclass** of `ACoopSurvivalCharacter` (Content Browser → right-click →
   **Blueprint Class** → parent class `CoopSurvivalCharacter`). Name it e.g. `BP_SurvivalCharacter`.
   (A pure C++ class has no per-asset defaults panel, so a Blueprint is the only practical way to
   assign a mesh without a recompile.)
3. Open it, select the **Mesh** component (inherited from `ACharacter`).
   - Set **Skeletal Mesh Asset** to the mannequin mesh.
   - Under **Animation**, set **Anim Class** to the matching anim Blueprint.
   - Fix the mesh's relative transform if it's offset from the capsule (standard mannequin offset
     is roughly location `(0, 0, -88)`, rotation `(0, 0, -90)` - copy whatever the content pack's
     own example pawn uses).
4. **Point the GameMode at the Blueprint** instead of the raw C++ class: create a Blueprint
   subclass of `AGinnungagapGameMode` (or just override in **World Settings → GameMode Override**)
   and set its **Default Pawn Class** to `BP_SurvivalCharacter`. (`AGinnungagapGameMode`'s C++
   constructor currently hardcodes `ACoopSurvivalCharacter::StaticClass()` - tell me the Blueprint's
   asset path once it exists and I can point the C++ default at it via a soft class reference, or
   just leave the override at the World Settings/Blueprint level, which takes precedence anyway.)
5. **Verify**: Play in Editor - you should see the mannequin instead of a capsule, animating based
   on `Speed`/`IsFalling` if the anim Blueprint's state machine already drives off those (the
   Third Person template's default anim BP does this out of the box).

---

## Phase B / C - now fully procedural, no editor work required

`AProceduralShipBuilder` (`Public/LevelSetup/`) builds the entire greybox ship - sections, doors,
ship-system actors, resource-acquisition actors, patrol enemies, and a player start - entirely in
C++ at runtime. `AGinnungagapGameMode::BeginPlay()` auto-spawns one (`bAutoBuildShip`, default
true), so `Content/Untitled.umap` needs **zero placed actors** for a playable ship to exist.
`APatrollingEnemyController` now also drives patrol/chase movement natively (no Behavior Tree asset
required), closing what used to be Phase C item 12.

If you'd rather use a **hand-authored** level instead of the generated greybox:
- Hand-place your own `AProceduralShipBuilder` instance in the level (the GameMode's auto-spawn is
  skipped if one already exists), or
- Set `AGinnungagapGameMode::bAutoBuildShip = false` (via a Blueprint subclass or World Settings →
  GameMode Override, same mechanism as Phase A item 4 above).

Phase C item 11 (the jump-loop content gap) is also now closed in C++: on arrival,
`UJumpSequenceSubsystem::CompleteArrival()` despawns the previous system's hazard/resource actors
and spawns a fresh set matching the new `CurrentSystemData` - no editor work, no Blueprint event
wiring required. Nothing left in Phase C.

Phase D (PIE playtesting of the generated ship and the jump loop - do sections register correctly,
do doors seal/unseal, do enemies patrol, does the HUD render, do the new arrival hazard/resource
actors actually spawn where expected and behave sensibly) is still a manual step only doable
in-editor; see `docs/PRD.md` §5 Phase D.

The win/loss/self-destruct/escape-pod system (`docs/PRD.md` §3.11) is also pure C++/procedural -
`AProceduralShipBuilder`'s new 6th spoke spawns both new actors automatically, no placement needed.
Add it to your Phase D playtesting pass: reach the escape pod bay, arm the self-destruct console,
confirm the countdown/counter-roll/detonation flow and the run-outcome HUD screen all behave as
expected.

