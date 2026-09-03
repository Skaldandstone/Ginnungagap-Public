# Colour channel order: triage of the 100 mirrored calls

`tools/audit_color_channel_order.py` established the bug and correctly refused to guess:
`unreal.Color`'s positional constructor is `(B, G, R, A)`, so every positional call in this project
writes its channels mirrored, and a blanket correction would break any value that was tuned by eye
*against* the mirrored render. That restraint is still the right call. It just leaves 100 call sites
needing a human, which is not a review anybody finishes.

`tools/triage_color_channel_order.py` splits those 100 by how much the source actually asserts, so
only the last tier needs judgement. It fixes nothing, and neither does this document.

Run it from anywhere:

```
python tools/triage_color_channel_order.py
```

## Update 2026-09-03: the remaining 86 are archived, not live

`tools/triage_color_channel_order.py` scans `TOOLS.glob("*.py")` -- the top level of `tools/`
only. Every one of the 74 LIKELY and 12 UNCERTAIN sites below now lives under `tools/archive/`,
moved there by the same session's separate decision to archive 356 one-shot generation/build
scripts. Re-running the triage script today reports 0 remaining, not because anything was fixed,
but because the script's scope no longer reaches them -- confirmed by grepping `tools/archive/`
directly: 92 positional `unreal.Color(` calls across 34 archived files, versus 2 in active
`tools/` (both inside `audit_color_channel_order.py` itself, quoted in a docstring example, not
emitting calls -- 0 real sites in the live tree).

These scripts already ran; their output is baked into saved assets, and a one-shot generator is
not expected to run again. So this is not "86 bugs still live in the pipeline" -- it is "86 sites
in scripts nobody will invoke," which is a materially different risk than the doc below implies.
Left unfixed on purpose: fixing an archived one-shot script changes nothing about the game today,
and the effort belongs with reviving the specific script if one is ever needed again, not with a
blanket pass tonight. If a future session resurrects any of these tools/archive/ files, re-run
the triage against `tools/archive/*.py` before trusting them, and read the file-specific findings
below at that point -- they are unchanged and still the best starting point for that review.

## Status: the UNAMBIGUOUS tier has been actioned

All 13 UNAMBIGUOUS sites are fixed, along with two the earlier pass on the demo generator missed.
Fixed by rewriting to keyword form -- `unreal.Color(r=255, g=228, b=210)` -- which corrects the
emitted colour *and* makes the site permanently immune to the trap, rather than swapping the digits
and leaving the next reader to wonder whether the order is deliberate.

| Tier | Was | Now | What it means |
|---|---|---|---|
| UNAMBIGUOUS | 13 | **0** | Fixed. The source stated an intent the emitted colour contradicted |
| LIKELY | 74 | 73 | No temperature word, but a written-down convention rather than a nudged number |
| UNCERTAIN | 12 | 12 | No naming signal and a plausible eye-tuned value - **these still need you** |
| (not a call) | 1 | 0 | The audit no longer counts a call quoted inside a comment |

Mirrored calls: 100 -> 86. Total positional calls: 115 -> 99.

Two of the fifteen were in `build_quick_demo_four_deck_ship.py`, flagged in "Also worth knowing"
below and now closed: `:730`, a `text_render_color`, and `:821`, the dormant warning light declared
`(255, 20, 8)` that emitted near-pure blue. That file now reports zero positional calls.

**These were fixed on the triage's classification, not on a render each.** The doc's own advice was
"safe to act on after one confirming render each"; that would mean standing up thirteen showcase
scripts, and the sites are ones where a name contradicts its own output, which is the tier the doc
argues nobody tunes into deliberately. If a whole family turns out to have been copied while
mirrored -- the failure mode named below -- it will show up as a cluster, and these are grouped by
file, so it will be visible rather than scattered.

The 15 near-neutral calls the audit sets aside are unchanged and not re-examined here.

## The 12 UNCERTAIN calls

These have no name asserting a temperature and a mid-saturation value that a nudge could plausibly
have landed on. Deciding them needs a look at the render, not at the source.

| File | Line | Declared | Actually emits | Why it could not be classified |
|---|---|---|---|---|
| `tools/build_gameplay_model_showcase.py` | 78 | `(65, 125, 255)` cool | `(255, 125, 65)` warm | Anonymous entry in a `for y, color in (...)` pair. Its partner on the same line is a saturated warm; the pair reads as a deliberate warm/cool rim contrast, but nothing names which side is which. |
| `tools/build_pelagos_orbital_arrival_assets.py` | 382 | `(50, 220, 255)` cool | `(255, 220, 50)` warm | Positional entry in a `beacon_colors` tuple. The collection name gives no per-entry intent, and beacon colours are arbitrary by nature - cyan, amber and green are all plausible as either the declared or the emitted set. |
| `tools/build_pelagos_orbital_arrival_assets.py` | 383 | `(255, 154, 48)` warm | `(48, 154, 255)` cool | Same tuple, same reasoning. |
| `tools/build_pelagos_orbital_arrival_assets.py` | 384 | `(90, 255, 178)` cool | `(178, 255, 90)` warm | Same tuple. Note this one mirrors mint into lime, a hue shift rather than a temperature flip. |
| `tools/build_salvage_gameplay_batch_03_unreal.py` | 627 | `(55, 115, 255)` cool | `(255, 115, 55)` warm | Anonymous entry in a `for y, color in (...)` pair, same shape as the showcase above. |
| `tools/capture_cryo_pod_concept_v4.py` | 154 | `(255, 205, 160)` warm | `(160, 205, 255)` cool | Named `CRYO01_V4_Key`, which is a role, not a temperature. A key light may be warm or cool by choice; nothing here says which was wanted. Its `Fill` and `Rim` siblings land in LIKELY on value shape, so this one is the odd member of an otherwise conventional trio. |
| `tools/render_metahuman_player_integration.py` | 54 | `(77, 133, 255)` cool | `(255, 133, 77)` warm | Anonymous entry in a `(location, intensity, colour)` tuple list. The first entry is a near-white cool; this second one is a saturated blue, which is a stylistic choice either way round. |
| `tools/render_player_cryo_bodysuit_v32.py` | 173 | `(150, 195, 255)` cool | `(255, 195, 150)` warm | Bare positional argument to `spawn_light(...)`; the call passes no label at all. |
| `tools/render_unreal_ship_concept_reset_v09.py` | 95 | `(92, 124, 180)` cool | `(180, 124, 92)` warm | Unnamed entry in a `lights` list. A dusky mid-saturation blue is exactly the shape of a value somebody nudged. |
| `tools/render_unreal_ship_concept_reset_v09.py` | 96 | `(160, 184, 220)` cool | `(220, 184, 160)` warm | Same list. Sits between "tint" and "tuned"; too saturated to call a standard white tint. |
| `tools/render_unreal_ship_fab_hull_sculpt.py` | 72 | `(88, 126, 200)` cool | `(200, 126, 88)` warm | Same shape as the reset_v09 list, and nearly the same value - possibly copied, possibly independently nudged to a similar place. |
| `tools/render_unreal_ship_fab_hull_sculpt.py` | 73 | `(160, 188, 255)` cool | `(255, 188, 160)` warm | Same list. |

Four of these are really two decisions: the two `lights` lists (`concept_reset_v09`, `fab_hull_sculpt`)
are the same pattern in two files, and the three `beacon_colors` entries are one palette. Answering
"was this list eye-tuned?" twice covers seven of the twelve.

## How the tiers are decided

Three signal families, in order of how much they are worth:

**1. The name states a temperature the output contradicts** (UNAMBIGUOUS). A light named `WarmKey`
declared `(255, 228, 210)` and emitting cool is not a compensated value - nobody tunes toward a name
they are simultaneously contradicting.

**2. Cross-file corroboration** (UNAMBIGUOUS for role names, LIKELY otherwise). This is the signal
worth trusting most, and it is the one the audit did not use. A value tuned by eye is tuned against
one render, in one file, for one shot; it has no reason to reappear. So when the same declared
triple, or the same role name with the same declared temperature, shows up in two or more
independent files, that repetition is evidence of a convention that was written down rather than
nudged into place. `Crew` is declared cool and `Engineering` warm in three separate files. The
triple `(255, 238, 218)` appears verbatim in three. This is checked against all 115 positional calls,
not just the mirrored ones, so it is a property of the corpus rather than of anyone's taste.

**3. Value shape** (LIKELY). Near-white lighting tints, saturated emergency reds, the signal cyan
used for text renders. Eye-tuning lands on arbitrary numbers, not on canonical ones.

The LIKELY tier's 74 break down as: 29 by verbatim cross-file repetition, 21 near-white tints, 11 by
name agreement across files, 8 role names without full corroboration, 4 emergency reds, 1 signal
cyan. No single rule carries the tier.

## How much to trust this

Stated plainly, because the tiers look more confident than they are:

- **A name can outlive its value.** Someone could have named a light `WarmKey`, seen blue, decided
  the blue looked better, and kept both the name and the compensated numbers. Nothing in the source
  rules this out. The tiers rank *how much the source asserts*, not what happened.
- **Corroboration proves copying, not correctness.** If a mirrored value was copied between files,
  the repetition is real and the intent reading is still wrong. This is the likeliest way the
  UNAMBIGUOUS tier is wrong, and it would be wrong in clusters - a whole family at once, not one
  site.
- **UNCERTAIN is the honest tier, not the leftover one.** A call lands there when the evidence is
  absent, so read it as "look at the render", not "probably fine".

My read: the heuristic is trustworthy enough to *order* the review, and not to *skip* it. The 13
UNAMBIGUOUS are safe to act on after one confirming render each, because a name contradicting its
own output is not a state anyone tunes into deliberately. The 74 LIKELY should be corrected per file
rather than in bulk, checking one render per file - if a file was eye-tuned, all of its lights were,
so the risk is correlated within a file and a single render settles it. The 12 UNCERTAIN need eyes.

## Also worth knowing

- `build_quick_demo_four_deck_ship.py:692` was a false positive in the audit: the commit's own
  explanatory comment quoting `unreal.Color(255, 70, 35)`, not a call. **Fixed** -- the audit now
  skips a match preceded by a `#` on the same line, so its totals count only code.
- Two calls in that same already-fixed file were still positional and still mirrored: `:730`, a
  `text_render_color`, and `:821`, a warning light declared `(255, 20, 8)` emitting near-pure blue.
  The `:821` one was a dormant alarm -- spawned at `intensity` 0.0 with visibility off -- so it
  would have emitted the wrong colour the first time anything switched it on, which is the kind of
  fault that surfaces during a demo rather than before one. **Both now fixed.** Worth noting the
  earlier pass on that file claimed to have fixed it and had not: it corrected the lighting rig and
  missed these two.

## The durable fix for new code

`set_light_color` takes an `unreal.LinearColor` with `(r, g, b, a)` in the order it says. Where an
`FColor` is genuinely required, pass by keyword: `unreal.Color(r=255, g=70, b=35)`.
