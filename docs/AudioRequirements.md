# Audio Requirements

What this project needs to stop being silent, in the order it matters.

Compiled 2026-08-25 against `9b8fbc84` by surveying every sound property in the codebase and every
system that plainly should make noise and has no hook for one. Counts are from the build, not
estimates.

**Current state:** roughly eight sound assets exist in the entire project. Eight `USoundBase`
properties are declared across three files, and every one of them is unassigned. Nothing else in
the game has an audio hook at all.

---

## 1. The gap that breaks a mechanic

**The stealth system is silent to the player.**

`UPlayerNoiseEmitterComponent` computes how loud the player is — from speed, magnetic boots, and
optionally the real microphone — and reports it to `UNoisePerceptionSubsystem` so enemies can hear
it. It never plays a sound.

So the AI knows exactly how much noise the player is making and the player has no idea. That is the
central feedback loop of a stealth game missing entirely: a player cannot learn to move quietly if
moving loudly sounds identical.

This is not polish. Until it is fixed, `Sec_SoundDampers` and `Crew_RunSilent` — two of the eleven
active skills — are mechanics the player cannot perceive themselves using, and the
microphone-listening feature has no audible consequence at all.

**Needed:** movement audio whose volume tracks `GetCurrentNoiseLevel()`, so what the player hears is
what the enemy hears. This wants a code hook as well as assets, and it should be built from the
existing loudness value rather than as a parallel system — two sources of truth for "how loud am I"
would drift immediately.

---

## 2. Declared, unassigned

Eight properties exist and are wired into behaviour. Assigning an asset is the entire job — no code
required.

| Property | Class | Fires when |
|---|---|---|
| `MagnetEngageSound` | `ACoopSurvivalCharacter` | Magnetic boots clamp to a surface |
| `MagnetReleaseSound` | `ACoopSurvivalCharacter` | Boots release |
| `ThrusterLoopSound` | `ACoopSurvivalCharacter` | Rotation thruster held |
| `ThrusterParticle` | `ACoopSurvivalCharacter` | *(VFX, not audio — listed because it is the same gap)* |
| `ShipHumSound` | `AShipEnvironmentController` | Ambient bed, ties to power state |
| `AlarmSound` | `AShipEnvironmentController` | Hull breach, depressurisation, jump warning |
| `BloomSound` | `AShipEnvironmentController` | Bloom presence in a compartment |
| `PhantomBloomSound` | `UPlayerPsychosisComponent` | Hallucinated Bloom — must be indistinguishable from the real one |

`docs/MagneticSuitTraversal.md` already specifies the intended traversal audio.

`PhantomBloomSound` is worth a note: psychosis works by making the player doubt what they heard, so
it should reuse the *same* asset as `BloomSound` rather than a distinct one. A phantom that sounds
different is not a hallucination, it is a tell.

---

## 3. Systems with no audio hook at all

These need a code hook *and* an asset. Counts are what exists in the demo map today.

| System | Scale | What it needs |
|---|---|---|
| `ABulkheadDoor` | **114 in the demo map** | Open, close, seal, and a distinct locked/refused sound. The player crosses these constantly and they are the main spatial punctuation of the ship. |
| Weapons | **23 definitions** | Fire, dry-fire, reload, impact. `ShipboardWeaponTypes.h` has no sound field. |
| `ACryoPodSystem` | 4 in the demo map | Lid cycle, occupancy, and the wake sequence — the game's opening moment and currently mute. |
| `UPlayerActivityComponent` | 250 procedure presets | Work loops for repair, medical and salvage, plus success and failure stingers. Activities are a primary verb and give no audible feedback. |
| `AShipboardThreat` | 8 spawned per encounter | Idle vocalisation, alert, and movement. Without these the stealth loop has no audible warning, so detection arrives with no build-up. |
| `UAstrophysicsHazardComponent` | — | Radiation clicks, pressure alarm, thermal stress. These are survival readouts the player currently must watch the HUD to notice. |
| `UItemDefinition` | 28 definitions | Pick up, drop, use. |
| Menus and HUD | 16 widgets | Navigation, confirm, refuse, and alert tones. |

---

## 4. Minimum bed for a filmable demo

If the goal is footage and a first playtest rather than completeness, this is the shortest list that
gets there. Ordered by how much each changes the result.

1. **Room-tone ambience**, ideally varying by deck — the single biggest change to how footage feels,
   and one asset can carry it.
2. **Footsteps, driven by the stealth loudness value** — fixes §1 and makes movement legible.
   Needs a distinct magnetic-boot variant; the model already differentiates boot noise by
   `MagneticBootNoiseMultiplier`.
3. **Bulkhead doors** — 114 of them, and the player passes through constantly.
4. **The four unassigned traversal properties** — boots and thruster are fully implemented and
   completely silent.
5. **Threat vocalisation and alert** — without it, being detected has no warning.
6. **Hull and machinery noise** near the engine and power spaces, which the mission chain routes
   the player through deliberately.

Everything else in §3 can wait for a slice.

---

## Notes for whoever sources this

- The ship is **1.4 km** and mostly enclosed. Reverb and occlusion will do a lot of the work;
  consider whether the audio design leans on submixes per deck rather than per-asset variation.
- Power state changes what should be audible. `AShipEnvironmentController` already tracks it and
  `ShipHumSound` is meant to follow it, so an unpowered deck should sound wrong, not just dark.
- The Bloom's audio identity is unestablished. The concept art fixes its **visual** identity
  (violet, `#7A549F`, sampled from `Corvette_BloomReactor_Concept.png`); nothing equivalent exists
  for sound, and it is the antagonist of the game.
- Nothing here is licensed or sourced yet. This document is the requirement, not an inventory.
