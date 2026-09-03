"""Sorts the mirrored unreal.Color(...) calls into confidence tiers, so the review is short.

audit_color_channel_order.py establishes the bug and refuses to guess: unreal.Color's positional
constructor is (B, G, R, A), every positional call in this project writes its channels mirrored, and
a blanket "correction" would break any value that was tuned by eye *against* the mirrored render.
That restraint is right. But it leaves 100 call sites needing a human, which is not a review anyone
finishes.

This does not fix anything either. It splits those 100 into three tiers so that only the last one
actually needs judgement:

  UNAMBIGUOUS  The source states an intent that the emitted colour contradicts. A light named
               "WarmKey" declared (255, 228, 210) and emitting cool is not a tuned value; it is a
               warm light that came out blue. Nobody eye-tunes toward a name they then contradict.

  LIKELY       No temperature word, but the value is a recognisable convention rather than a
               nudged number: near-white lighting tints, saturated emergency reds, the cyan label
               colour used for text renders. Eye-tuning lands on arbitrary values, not on
               (255, 238, 218) repeated verbatim in three separate files.

  UNCERTAIN    No naming signal, and a value that could plausibly be where somebody stopped
               nudging. These are the only ones worth a human's time.

THE CORROBORATION SIGNAL, which is the part worth trusting most. A value tuned by eye is tuned
against one render, in one file, for one shot. It has no reason to reappear. So when the same
declared triple, or the same name with the same declared temperature, shows up in two or more
independent files, that repetition is itself evidence of a shared convention that was written down
rather than nudged into place. This is checked against every positional call in the project, not
just the mirrored ones, and it is a property of the corpus rather than of anyone's taste.

WHERE THIS CAN BE WRONG, stated plainly because the tiers look more confident than they are:

  * A name can outlive its value. Someone could have named a light "WarmKey", seen blue, and
    decided the blue looked better -- keeping the name and the compensated numbers. Nothing in the
    source rules this out. The tiers rank how much the source asserts, not what happened.
  * Corroboration proves copying, not correctness. If a mirrored value was copied between files,
    the repetition is real and the intent reading is still wrong.
  * UNCERTAIN is the honest tier, not the leftover one. A call lands there when the evidence is
    absent, so it should be read as "look at the render", not "probably fine".

Reads only source text; no Unreal needed. Run from anywhere:  python tools/triage_color_channel_order.py
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

# Shared with the audit deliberately: one definition of what counts as a mirrored call, so the two
# scripts cannot drift apart. Importing does not run the audit -- its main() is guarded.
sys.path.insert(0, str(TOOLS))
from audit_color_channel_order import CALL, temperature  # noqa: E402

# Words that state a temperature outright. If one of these is in the name and the light emits the
# opposite, the source is contradicting itself.
WARM_WORDS = {
    "warm", "amber", "ember", "sunset", "sunrise", "tungsten", "orange", "red", "fire", "flame",
    "heat", "lava", "sodium", "candle", "emergency", "warning", "alarm", "alert", "danger",
    "hazard", "caution", "critical", "gold", "rust",
}
COOL_WORDS = {
    "cool", "cold", "blue", "azure", "cyan", "ice", "icy", "frost", "moon", "moonlight", "sky",
    "teal", "daylight", "arctic", "chill", "steel", "cryo",
}

# Names carrying a project palette rather than a temperature word. Their expected temperature is
# not hardcoded -- it is derived from how the project itself declares them (see corroborate()).
PALETTE_HINT = {
    "crew", "engineering", "medical", "security", "reactor", "damage", "cargo", "escape",
    "armory", "bridge", "sensors", "companionway", "science", "galley", "berth",
}

# Strings that are Unreal property names rather than anything the author named. Without this they
# shadow the real signal: in `fill_comp.set_editor_property("light_color", ...)` the meaningful word
# is "fill", and "light_color" would otherwise win for being nearer the call.
PROPERTY_STRINGS = {
    "light_color", "text_render_color", "color", "tint", "intensity", "light_intensity",
    "attenuation_radius", "source_radius", "outer_cone_angle", "inner_cone_angle", "mobility",
    "relative_location", "relative_rotation", "world_location", "material", "text",
}

# Same-line name signals, most specific first.
LABEL = re.compile(r"""["']([A-Za-z][A-Za-z0-9_ .-]{1,40})["']\s*[:,)]""")
ASSIGN = re.compile(r"^\s*(\w+)\s*=[^=]")
OWNER = re.compile(r"\b(\w+?)(?:_comp(?:onent)?)?\.(?:light_component|text_render|set_editor_property)\b")
ENCLOSING = re.compile(r"^\s*(\w+)\s*(?:[:=]|\s*=)\s*[\[({]")
TOKEN = re.compile(r"[A-Za-z][a-z]*|[A-Z]+(?![a-z])")


def tokens(name):
    """WarmKey -> {warm, key};  light_color -> {light, color};  "Cool Fill" -> {cool, fill}."""
    if not name:
        return set()
    return {t.lower() for t in TOKEN.findall(name.replace("_", " "))}


def name_for(lines, index, line, match_start):
    """Best available name for a call, and whether it came from the call's own line.

    Same-line evidence is what the author wrote next to the colour. An enclosing name found by
    walking upward is weaker -- it describes the collection, not the entry -- so it is marked.
    """
    head = line[:match_start]

    labels = [l for l in LABEL.findall(head) if l.lower() not in PROPERTY_STRINGS]
    if labels:
        return labels[-1], True

    owner = OWNER.search(head)
    if owner and owner.group(1) not in {"self", "actor", "comp", "component", "obj"}:
        return owner.group(1), True

    assign = ASSIGN.search(head)
    if assign:
        return assign.group(1), True

    # Nothing on this line -- but the call may have started on an earlier one. A colour on the
    # second line of `rect("CRYO01_V4_Key", ...)` is still that light's colour, so an earlier line
    # counts as same-line evidence whenever its brackets are still open here.
    depth = 0
    for back in range(index - 1, max(index - 9, -1), -1):
        depth += lines[back].count(")") - lines[back].count("(")
        depth += lines[back].count("]") - lines[back].count("[")
        if depth < 0:
            # This line opened the expression our colour sits inside. Its label, if it has one, is
            # the name of the thing being built. Anything above it is a different statement, so
            # stop either way and fall through to the weaker enclosing-collection search.
            labels = [l for l in LABEL.findall(lines[back]) if l.lower() not in PROPERTY_STRINGS]
            if labels:
                return labels[0], True
            break

    # Still nothing. Walk up for the collection this entry sits in.
    for back in range(index - 1, max(index - 16, -1), -1):
        enclosing = ENCLOSING.match(lines[back])
        if enclosing:
            return enclosing.group(1), False
        if lines[back].strip().startswith("def "):
            break
    return None, False


def looks_like_light_tint(r, g, b):
    """A near-white lighting tint: bright, low spread. The standard way to warm or cool a light."""
    return min(r, g, b) >= 165 and (max(r, g, b) - min(r, g, b)) <= 95


def looks_like_emergency_red(r, g, b):
    """Saturated red-orange. The alarm colour, not somewhere a nudge stops."""
    return r >= 200 and g <= 135 and b <= 95


def looks_like_signal_cyan(r, g, b):
    """The bright cyan/azure used for readable text renders and holo labels."""
    return b >= 200 and g >= 150 and r <= 150


def collect():
    """Every positional call in the project, mirrored or not, with its name and context."""
    rows = []
    for path in sorted(TOOLS.glob("*.py")):
        if path.name in {Path(__file__).name, "audit_color_channel_order.py"}:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            stripped = line.strip()
            for match in CALL.finditer(line):
                a, b, c = (int(match.group(i)) for i in (1, 2, 3))
                name, direct = name_for(lines, index, line, match.start())
                rows.append({
                    "file": path.name,
                    "line": index + 1,
                    "meant": (a, b, c),
                    "actual": (c, b, a),
                    "name": name,
                    "direct": direct,
                    "tokens": tokens(name),
                    "source": stripped,
                    # A colour quoted inside a comment or docstring emits nothing at all.
                    "prose": stripped.startswith("#") or stripped.startswith('"""'),
                })
    return rows


def corroborate(rows):
    """Which declared values and names recur across independent files.

    An eye-tuned value belongs to one render. Repetition across files means it was written down
    once and copied -- a convention, which the mirror then breaks everywhere at once.
    """
    by_value = defaultdict(set)
    by_token = defaultdict(lambda: defaultdict(set))
    for row in rows:
        if row["prose"]:
            continue
        by_value[row["meant"]].add(row["file"])
        for token in row["tokens"]:
            by_token[token][temperature(*row["meant"])].add(row["file"])

    repeated_values = {v: len(files) for v, files in by_value.items() if len(files) >= 2}
    # A token counts only if every file that uses it declares the same temperature.
    agreeing_tokens = {}
    for token, by_temp in by_token.items():
        real = {t: f for t, f in by_temp.items() if t != "neutral"}
        if len(real) == 1:
            temp, files = next(iter(real.items()))
            if len(files) >= 2:
                agreeing_tokens[token] = temp
    return repeated_values, agreeing_tokens


def classify(row, repeated_values, agreeing_tokens):
    """Tier, plus the reason -- the reason is the part James should be checking, not the tier."""
    meant, actual = row["meant"], row["actual"]
    emitted = temperature(*actual)
    declared = temperature(*meant)
    name = row["name"] or ""
    toks = row["tokens"]

    stated = (WARM_WORDS & toks and "warm") or (COOL_WORDS & toks and "cool") or None
    if stated and row["direct"] and stated != emitted:
        return "UNAMBIGUOUS", '"{}" states {}, emits {}'.format(name, stated, emitted)

    palette = PALETTE_HINT & toks
    if palette and row["direct"]:
        token = sorted(palette)[0]
        if agreeing_tokens.get(token) == declared:
            files = "the project's palette"
            return "UNAMBIGUOUS", '"{}" is {} in {}, emits {}'.format(name, declared, files, emitted)
        return "LIKELY", '"{}" is a role name; declared {}, emits {}'.format(name, declared, emitted)

    if meant in repeated_values:
        return "LIKELY", "{} is declared verbatim in {} files".format(
            "({}, {}, {})".format(*meant), repeated_values[meant])

    for token in sorted(toks):
        if token in agreeing_tokens and row["direct"] and agreeing_tokens[token] == declared:
            return "LIKELY", '"{}" is {} wherever it appears, emits {}'.format(name, declared, emitted)

    if looks_like_light_tint(*meant):
        return "LIKELY", "near-white lighting tint, not a nudged value"
    if looks_like_emergency_red(*meant):
        return "LIKELY", "saturated emergency red"
    if looks_like_signal_cyan(*meant) and "text_render_color" in row["source"]:
        return "LIKELY", "signal cyan for a text render"

    why = []
    if not name:
        why.append("no name in scope")
    elif not row["direct"]:
        why.append('only an enclosing name ("{}")'.format(name))
    else:
        why.append('name "{}" says nothing about temperature'.format(name))
    why.append("mid-saturation value that a nudge could land on")
    return "UNCERTAIN", "; ".join(why)


def main():
    rows = collect()
    repeated_values, agreeing_tokens = corroborate(rows)

    mirrored = [r for r in rows
                if temperature(*r["meant"]) != temperature(*r["actual"])]
    prose = [r for r in mirrored if r["prose"]]
    live = [r for r in mirrored if not r["prose"]]

    tiers = defaultdict(list)
    for row in live:
        tier, reason = classify(row, repeated_values, agreeing_tokens)
        row["reason"] = reason
        tiers[tier].append(row)

    print("{} mirrored positional call(s); {} emit colour, {} only quote it in prose\n".format(
        len(mirrored), len(live), len(prose)))
    for tier in ("UNAMBIGUOUS", "LIKELY", "UNCERTAIN"):
        print("  {:<12} {:>3}".format(tier, len(tiers[tier])))
    print()

    for tier in ("UNAMBIGUOUS", "LIKELY", "UNCERTAIN"):
        print("=" * 96)
        print("{}  ({})".format(tier, len(tiers[tier])))
        print("=" * 96)
        current = None
        for row in sorted(tiers[tier], key=lambda r: (r["file"], r["line"])):
            if row["file"] != current:
                print("\n  {}".format(row["file"]))
                current = row["file"]
            print("    :{:<5} declared {:>15} {:<7} -> emits {:>15} {:<7}".format(
                row["line"],
                "({}, {}, {})".format(*row["meant"]), temperature(*row["meant"]),
                "({}, {}, {})".format(*row["actual"]), temperature(*row["actual"])))
            print("           {}".format(row["reason"]))
            if tier == "UNCERTAIN":
                snippet = row["source"]
                print("           {}".format(
                    snippet if len(snippet) <= 88 else snippet[:85] + "..."))
        print()

    if prose:
        print("=" * 96)
        print("NOT CALLS  ({}) -- colours quoted in comments or docstrings; these emit nothing".format(
            len(prose)))
        print("=" * 96)
        for row in prose:
            print("  {}:{}  {}".format(row["file"], row["line"], row["source"][:80]))
        print()

    print("Nothing here is fixed and nothing here should be fixed in bulk. UNAMBIGUOUS means the")
    print("source contradicts itself, not that the render is wrong -- a name can outlive the value")
    print("it was given. Check one render per file before trusting a tier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
