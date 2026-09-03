# Stealth, noise, and enemy perception

**Status:** noise, visibility, and Bloom adaptation implemented; builds clean and automation-tested
(53/53); PIE tuning still to come
**Linear:** TRO-76

Detection used to be a single rule: "is a hostile pawn within `DetectionRange` and in line of
sight" -- effectively 360-degree vision, resolved instantly. This adds hearing as an independent
channel, a forward vision cone, and gradual detection, so being unseen is no longer the same as
being undetected and a partial sighting is no longer an automatic one.

## Model

Noise is a **world event, not an actor**. A source reports a noise once at a location; it decays
on its own. Listeners *pull* (`QueryLoudestAudibleNoise`) rather than being pushed to, which keeps
falloff, occlusion, and decay in one place instead of re-implemented per AI controller.

`UNoisePerceptionSubsystem` (a `UWorldSubsystem`) owns that record and all the hearing rules:

- **Loudness** is an abstract `0..1` scale, deliberately *not* decibels and *not* tied to the audio
  engine mix, so stealth can be tuned without touching sound assets. `1.0` means "audible at
  `MaxPropagationDistance`"; `0.25` means audible at a quarter of it.
- **Falloff** is linear to the audible edge, then faded by age, so a listener loses interest
  gradually instead of snapping from certain to forgotten.
- **Occlusion** applies `OcclusionAttenuation` when static geometry blocks the direct path.
  Deliberately `ECC_WorldStatic` only: a crew member standing in a doorway should not muffle
  the noise behind them, and pawns move too often for that to read as a consistent rule.
- **Coalescing**: continuous sources (footsteps, a live microphone) collapse to one entry per
  instigator+category. Without this they would push a new event every tick and starve louder,
  more significant noise out of the list.
- When the list is full it evicts the **quietest** entry, not the oldest, so a gunshot is never
  dropped in favour of a stale footstep.

Everything is authority-only. Clients reporting noise directly would let a modified client fake or
suppress stimuli for everyone.

## Emitting noise

`UPlayerNoiseEmitterComponent` sits on `ACoopSurvivalCharacter` and derives noise from what the
player is physically doing:

- **Movement** - mapped from speed between `SilentSpeedThreshold` and `LoudSpeedThreshold`.
  Derived on the server from replicated movement state, so it cannot be suppressed client-side.
- **Magnetic boots** - multiply movement noise by `MagneticBootNoiseMultiplier`. This is
  intentional design tension: the safe traversal option is the loud one.
- **Instant noise** - `ReportInstantNoise()` for one-off events such as dropped objects.

Two other systems report directly, both data-driven rather than hardcoded:

- **Weapons** - `FWeaponFiringProfile::FiringNoiseLoudness`. Per *profile*, not per weapon, so a
  weapon's safe and unsafe modes differ naturally; the stock unsafe profile is maximally loud, so
  the unsafe modification trades stealth for power rather than being strictly better. All three
  `TryFire` exit paths (trace, projectile, rescue shield) go through one helper, so a future
  delivery mode cannot silently skip reporting. Attributed to the *operator*, not the weapon actor,
  so hostility and self-ignore checks resolve against the crew member who fired - falling back to
  the weapon when unmounted, since a turret still makes noise.
- **Activity stations** - `FPlayerActivityDefinition::WorkNoiseLoudness`, reported continuously
  while the activity runs, so repairing under pressure carries real risk. Reported from the
  *station's* location rather than the worker's: the machinery is what an investigating AI should
  walk to. Reporting every tick is intended - coalescing (above) is exactly the case this was
  designed for.
- **Thrown objects** - `ThrownObjectImpactLoudness` on the character, reported where the object
  lands. This is the game's **distraction verb**, and it reuses the existing `ThrowMagneticObject`
  rather than adding a bespoke noisemaker item.

  The critical detail: the noise is attributed to the *thrown object*, not the thrower. Attributing
  it to the player would let the hostility and self-ignore rules discard it outright - the AI must
  investigate the clatter, not the person who caused it. Loudness scales with impact speed, and
  only the first impact reports, since a tumbling object would otherwise fire on every bounce and
  the landing point is the signal worth acting on.

`GetCurrentNoiseLevel()` exposes the loudest thing the player is currently doing, intended for a
HUD noise meter. That is the player-facing tell: it shows *what you are broadcasting*, never what
the AI knows, so stealth stays legible without exposing AI internals.

## Microphone input (opt-in)

Players can optionally let their real microphone drive in-game noise, so talking or shouting in
voice chat can actually give away a position.

**This is off by default and built so that opting in cannot leak audio.** The contract, enforced
in `UPlayerNoiseEmitterComponent`:

- Nothing opens a capture device until `SetMicrophoneNoiseEnabled(true)`.
- Capture runs **only on the locally controlled pawn** - never for remote players, never on the
  server.
- Captured samples are reduced to a single RMS value **in the same call that reads them**, and the
  buffer is discarded immediately. Audio is never written to disk, never replicated, never routed
  to the audio engine, and never held between frames.
- Only the derived `0..1` loudness scalar leaves the machine. Speech content cannot be
  reconstructed from a single amplitude number sampled a few times a second.
- A missing, busy, or refused microphone is treated as an ordinary situation, not an error: the
  player simply produces no voice noise and the rest of stealth is unaffected.

**Any change that stores, forwards, or plays back the captured buffer breaks this contract.**

Server-side, reported loudness is clamped to `MaxMicrophoneLoudness` and decays between client
updates, so a client that stops sending (crash, packet loss, or deliberate silence) fades out
rather than staying loud forever. The clamp means the worst a modified client can do is make
*itself* louder than it really is.

`MaxMicrophoneLoudness` is deliberately below `1.0`: shouting should be a real liability, but never
more informative to the AI than firing a weapon.

## Visibility

`UPlayerVisibilityComponent` supplies a single `0..1` multiplier scaling how quickly an observer
notices this actor. Two factors compound:

- **Light** - derived from `AModularShipRoom::bPowered`, *not* from rendering. Querying actual
  scene luminance would be expensive, unavailable on a dedicated server, and hard to reason about
  as a designer. Keying off the existing power system instead makes **"cut the lights in that
  room" a real stealth verb**, built on `UShipPowerGridSubsystem` and room state that already
  exist. Outside a registered room (EVA, unbuilt space) it fails *open* to fully lit rather than
  granting free concealment.
- **Movement** - holding still is the cheapest stealth option available, since the character has
  no crouch verb.

They multiply rather than add, so standing still in a dark room is meaningfully better than either
alone - which is what makes both worth doing. The result is floored at `MinimumVisibility`: total
invisibility reads as a bug and leaves the AI no counterplay.

## Enemy perception

`APatrollingEnemyController` gained a three-state awareness model:

| State | Meaning | Behaviour |
| --- | --- | --- |
| `Unaware` | No stimulus | Normal patrol at `PatrolSpeed` |
| `Suspicious` | Heard something, or partially saw something, but has no confirmed target | Moves to investigate at `InvestigateSpeed`, searches for `InvestigateDurationSeconds` |
| `Alert` | Confirmed visible target | Pursues at `ChaseSpeed` |

**Vision is a forward cone** (`VisionConeHalfAngleDegrees`). Detection previously used
`LineOfSightTo` with no facing check, so enemies effectively saw 360° and approaching from behind
gained the player nothing.

**Detection accumulates rather than triggering instantly.** Certainty builds while a target is
exposed (scaled by distance, how central it is in the cone, and its visibility multiplier) and
drains when it is not. Between `SuspicionDetectionThreshold` and `ConfirmedDetectionThreshold` the
AI knows something is there without having identified it, and walks over to check. This is what
makes darkness and stillness worth using: they buy enough time to break line of sight and drain the
certainty, rather than merely delaying an inevitable detection.

Sight outranks hearing: a confirmed visible target supersedes any noise investigation. Hearing only
reacts to noise from an actor the AI is actually hostile to (`AreActorsHostile`), so a boarding
party does not investigate its own squadmates' footsteps.

Investigation deliberately does **not** disturb the patrol route, so the AI resumes where it left
off once a search expires. `HearingRangeScale` lets larger or Bloom-adapted hosts hear further
without changing the shared noise rules.

`GetDetectionProgress()` is exposed as the player-facing tell (a rising detection indicator), while
raw internals such as the candidate actor itself stay private.

## Bloom adaptation

Bloom-aligned hosts sharpen as the organism matures. `GetBloomPerceptionScale()` runs from `1.0` at
`Latent` to `MaxBloomPerceptionScale` at `Manifestation`, and multiplies sight range, hearing range,
and how fast certainty builds - so evading a late-run Bloom is materially harder than evading an
early one.

Two constraints are deliberate:

- **Faction-gated.** Only hosts whose `TeamAffiliationComponent` faction is `Bloom` adapt. A pirate
  boarding party does not gain sharper senses because the Bloom matured elsewhere on the ship; they
  are not part of the organism. An unpossessed controller resolves to the neutral `1.0` rather than
  assuming Bloom, so no AI is silently buffed by default.
- **Cone angle is excluded.** Widening vision toward 360° as the Bloom matures would delete the
  approach-from-behind counterplay the cone exists to create. Scaling *range* and *recognition
  speed* pressures the player while leaving an option open - late game should be harder, not
  optionless.

The curve is anchored at both ends rather than stepped per stage, so inserting a new stage between
`Latent` and `Manifestation` does not silently rescale the whole progression.

### Learning from crew behaviour

The Bloom also learns *which evasion approach the crew relies on*. This mirrors the director's
existing hazard-resistance lifecycle rather than adding a parallel mechanism:

| Phase | Hazards | Stealth tactics |
| --- | --- | --- |
| During play | `RegisterHazardExposure` | `RegisterStealthTacticUse` |
| At a jump | `OnSystemJump` converts exposure to resistance | same call converts use to counter-adaptation |
| Read back | `GetHazardEffectiveness` | `GetStealthTacticEffectiveness` |

`EBloomStealthTactic` is deliberately coarse - `Darkness`, `Stillness`, `Distraction` - because the
organism adapts to *how* the crew avoids it, not to individual inputs.

Three properties carry the design:

- **Adaptation lands only at jumps.** Effectiveness does not move mid-run. That is what makes it
  *hidden*: the crew discovers the dark stopped hiding them on arrival, not while crouched in it.
- **Counters decay each jump before new use is applied.** Without decay the Bloom could only ever
  harden, so a crew that changed approach could never win back ground and an early over-reliance
  would be permanent. Leaning on one trick erodes it; variety restores it.
- **Learning requires the tactic to be used against a perceiving Bloom host.** Standing in a dark
  room alone teaches the organism nothing - being *missed* because of the dark is what it learns
  from. A pirate observing the same thing teaches it nothing either.

Effectiveness is floored at `MinStealthTacticEffectiveness` rather than reaching zero: a tactic that
stops working entirely removes a verb from the player instead of pressuring them.

## Testing

`Ginnungagap.Gameplay.Stealth.*` covers the audibility maths and the tuning-default guardrails
without needing a world, so an accidental edit to a shipped tuning value fails a test rather than
silently changing gameplay.

Occlusion tracing, AI reaction, and microphone capture all need real geometry or real hardware, so
they are PIE/manual test cases rather than automation.

## Not done yet

- **Partial cover** - visibility is per-actor, not per-body-part. Leaning out from behind a
  bulkhead is not modelled; line of sight is still all-or-nothing.
- **Remaining noise sources** - weapons, activity stations, and thrown objects report; doors and
  damaged machinery still do not. `ReportInstantNoise()` is the entry point for them.
- **HUD tells** - `GetCurrentNoiseLevel()` (how loud you are) and `GetDetectionProgress()` (how
  close an observer is to confirming you) are both exposed, but nothing displays either yet.
- **Bloom adaptation** - stage-scaled senses and tactic-reliance learning are both in. Not yet:
  adaptation to *where* the crew goes (route learning), or to noise-source type.

- **Tuning** - every threshold in this document is a first guess and needs a PIE pass.
