# Player status effects

`UPlayerStatusEffectComponent` is the server-authoritative clinical state attached to every
`ACoopSurvivalCharacter`. Active effects replicate as type, normalized severity, and remaining
duration. Blueprints can apply, remove, treat, enumerate, and display effects without coupling a
hazard or medical tool directly to the character implementation.

## Initial catalog

| Status | Primary source | Current consequence | Recovery |
| --- | --- | --- | --- |
| Hypoxia | Oxygen below 30% | Severity-scaled health loss | Restore oxygen above 45% |
| Jump psychosis | Completing a jump outside functioning cryo | Ongoing stability loss | Time or medical treatment |
| Radiation sickness | Accumulated radiation dose | Ongoing health loss | Medical stabilization |
| Decompression trauma | Vacuum or dangerously low pressure | Rapid health loss | Leave exposure, then treat |
| Hypothermia | Extreme cold | Ongoing health loss | Leave exposure, then treat |
| Heat stress | Extreme heat | Ongoing health loss | Leave exposure, then treat |
| Space motion sickness | Microgravity while unstable | Stability loss | Cryo, time, or treatment |
| CO2 toxicity | Failed scrubbing or authored atmosphere events | Stability and task loss, increased oxygen demand | Restore atmosphere and treat |
| Acute stress | Authored traumatic events | Stability and task loss, increased oxygen demand | Safety, time, or treatment |
| Hemorrhage | Trauma and authored combat events | Rapid ongoing health loss | Immediate medical treatment |
| Fracture | Collision and authored trauma events | Reduced mobility | Splint or medical treatment |
| Burn trauma | Fire, steam, or electrical events | Ongoing health loss | Cooling and medical treatment |

Repeated applications keep the worse severity and longer duration instead of creating duplicate
rows. A negative duration represents a condition that remains until its physiological source is
resolved or it is explicitly treated.

Each replicated condition also records its source category-atmosphere, jump exposure, radiation,
temperature, microgravity, trauma, fire, or psychological shock. Scanner and medical interfaces
can therefore distinguish similar symptoms caused by different incidents. The triage API returns
the most urgent condition and concise treatment guidance, with hemorrhage and decompression given
priority over less immediately lethal conditions.

## Gameplay integration

- Hazard zones feed pressure, temperature, radiation, and microgravity exposure through the
  character's existing survival update.
- Pressure-suit integrity mitigates environmental condition severity instead of acting as an
  all-or-nothing shield.
- High-energy collisions can cause acute stress, fractures, hemorrhage, and immediate health loss;
  suit integrity reduces the resulting severity and a short cooldown prevents contact spam.
- Failed life support progressively raises CO2 toxicity alongside oxygen consumption. Clean air,
  adequate oxygen, and stable surroundings gradually resolve stress, motion sickness, and CO2 load.
- A functioning cryopod protects against jump psychosis, clears hypoxia on entry, and strongly
  reduces space-motion sickness.
- Medical stabilization restores health and oxygen, reduces radiation dose, and treats the most
  severe active condition.
- Field procedures are condition-specific: hemorrhage control stops bleeding, splinting treats
  fractures, and oxygen procedures address hypoxia and CO2 toxicity.
- The visor HUD shows active conditions and severity percentages in the life-support panel.
- Bio-scanners return patient vitals and the full replicated condition list for diagnostic UI.
- Respawning clears all active conditions.

Future hazards should call `ApplyEnvironmentalExposure` when they use
`FPhysicsEnvironmentState`, or `ApplyStatusEffect` for discrete injuries such as toxins, burns, or
fractures. Medical gameplay should prefer `TreatStatusEffect` so treatment strength remains a
designer-controlled value.

## Psychosis perception layer

`UPlayerPsychosisComponent` converts jump-psychosis severity into private, local-only perception
events. It never spawns replicated gameplay enemies, changes authoritative scanner state, blocks
navigation, deals damage, or reveals hallucinations to teammates.

- Mild episodes show fleeting Bloom growth or movement at the edge of view.
- Moderate episodes add figures that appear solid, move briefly, then flicker out, plus spatial
  sounds whose source does not exist.
- Severe episodes can falsify the local helmet's Bloom warning and emit contradictory internal
  voices: warning, doubt, accusation, or dangerous false guidance.
- A fabricated Bloom warning must use the same text, severity mapping, color, icon, animation,
  audio cue, timing, and dismissal behavior as a genuine warning. The HUD must never reveal whether
  its local reading is true; only private simulation state may retain that distinction.
- Voice events expose intent, localized line text, perceived 3D position, and severity so separate
  performances can overlap around the listener in Blueprint or audio middleware.
- Cryo and future medication or grounding interactions suppress episodes temporarily and provide a
  trustworthy grounding voice. Grounding is delivered to the owning client in multiplayer.

The design takes inspiration from layered psychological-horror voice systems while using original
characters, dialogue, fiction, and presentation appropriate to Ginnungagap.

### Escalation and counterplay

The local perception component exposes four phases: `Stable`, `Uneasy`, `Distorted`, and `Break`.
Jump-psychosis severity establishes the baseline, while acute stress, hypoxia, and carbon-dioxide
toxicity amplify it. Episode selection unlocks more convincing symptoms at higher phases and avoids
immediate repetition. Active false telemetry and visual apparitions are destroyed when grounding
begins.

`PerformRealityCheck` compares the current perception layer with suit telemetry. Contradicted
hallucinations grant a short quiet period; confirmation from a scanner, teammate, or medical station
can grant a longer one. The check has a local cooldown, clears false infection telemetry, and never
changes authoritative world state. In PIE, use `PsychosisRealityCheck` to exercise the basic local
check alongside `EnablePsychosisTestMode` and `TestPsychosisEpisode`.
