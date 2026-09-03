"""Finds positional unreal.Color(...) calls, which put their channels in backwards.

unreal.Color's positional constructor is (B, G, R, A), not (R, G, B, A). FColor's C++ constructor
takes R, G, B, A, but the Python binding exposes properties in the struct's declaration order, which
for FColor is b, g, r, a. So every positional call in this project has been writing its channels
mirrored.

This is not a theory. Two call sites in build_quick_demo_four_deck_ship.py were checked against what
actually landed in the map:

    asked unreal.Color(255,  70,  35)  ->  map holds (35,  70, 255)
    asked unreal.Color(185, 220, 235)  ->  map holds (235, 220, 185)

The first is why the cryo bay rendered blue for months: a red-orange emergency light, mirrored into
saturated blue. Nobody chose that colour.

WHY THIS REPORTS RATHER THAN FIXES. A blanket swap would be wrong. Some of these values may have
been tuned by eye *after* seeing the mirrored result -- an author who wanted warm light, saw blue,
and nudged the numbers until the render looked right has already compensated, and "correcting" them
would break exactly the ones that currently look correct. There is no way to tell those apart from
the source alone.

So this prints both readings side by side and flags the ones where the two disagree in temperature,
which is where the damage is visible and the intent is usually recoverable from the variable name.
Triage by hand; the demo ship generator has already been fixed.

The durable fix for new code is to use set_light_color with an unreal.LinearColor, which takes
(r, g, b, a) and has no trap. Where an FColor is genuinely required, pass by keyword:
unreal.Color(r=255, g=70, b=35).
"""

import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

# unreal.Color( followed by at least two numeric positional args. Keyword calls are already correct
# and are skipped; so are LinearColor calls, which take (r, g, b, a) properly.
CALL = re.compile(r"unreal\.Color\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)")


def temperature(r, g, b):
    """Crude warm/cool/neutral read. Enough to tell a mirrored colour from a symmetric one."""
    if r - b > 20:
        return "warm"
    if b - r > 20:
        return "cool"
    return "neutral"


def main():
    rows = []
    for path in sorted(TOOLS.glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for match in CALL.finditer(line):
                # Skip a call quoted inside a comment. This audit's own explanatory comment in
                # build_quick_demo_four_deck_ship.py cites unreal.Color(255, 70, 35) as the example
                # of the bug, and the first version of this script counted that citation as a
                # hundredth offending call site. Caught by the triage pass, not by me.
                #
                # Crude but sufficient: a "#" anywhere before the match. A colour literal inside a
                # string that itself follows a "#" is not a case that occurs here, and the failure
                # mode of being too eager is a missed report rather than a false accusation.
                if "#" in line[:match.start()]:
                    continue
                a, b, c = (int(match.group(i)) for i in (1, 2, 3))
                # What the author almost certainly meant, and what Unreal actually stores.
                meant = (a, b, c)
                actual = (c, b, a)
                rows.append((path.name, number, meant, actual, line.strip()))

    mirrored = [r for r in rows
                if temperature(*r[2]) != temperature(*r[3])]

    print("{} positional unreal.Color(...) call(s) across {} file(s)".format(
        len(rows), len({r[0] for r in rows})))
    print("{} of them invert the colour's temperature, which is where it shows\n".format(
        len(mirrored)))

    current = None
    for name, number, meant, actual, line in mirrored:
        if name != current:
            print("  {}".format(name))
            current = name
        print("    :{:<5} meant {:>15}  {:<7} ->  got {:>15}  {:<7}".format(
            number,
            "({}, {}, {})".format(*meant), temperature(*meant),
            "({}, {}, {})".format(*actual), temperature(*actual)))
        snippet = line if len(line) <= 96 else line[:93] + "..."
        print("           {}".format(snippet))

    symmetric = len(rows) - len(mirrored)
    if symmetric:
        print("\n{} further call(s) are near-neutral, where the mirror is real but hard to see."
              .format(symmetric))

    print("\nNone of this is auto-fixable: a value tuned by eye against the mirrored output is")
    print("already compensated, and correcting it would break the one that currently looks right.")
    return 0 if not rows else 0


if __name__ == "__main__":
    sys.exit(main())
