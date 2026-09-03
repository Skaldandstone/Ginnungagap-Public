"""Finds public functions that nothing outside their own file ever calls.

Every substantial bug found in this project over the last two days has had the same shape: a system
that works, tested or not, that nothing reaches. Eleven cryo materials with two wired. A HUD prompt
panel nothing filled. 786 UI cues, none played. BurnTrauma with zero producers. A hazard zone
temperature read only by the Bloom. A workshop bench whose grant fields were never assigned.

Each of those was found by accident, one at a time. This looks for the rest on purpose.

Heuristic, not a compiler. It reads declarations out of headers and counts identifier occurrences
across the module, so it cannot see Blueprint callers, reflection, delegate binds by name, or a call
through a base-class pointer. Everything it prints is a *question*, and the answers live in the
code. It is worth running anyway because the questions are cheap.

THE BLIND SPOT THAT MATTERS, stated plainly because it burned two investigations in a row: this
does not follow calls transitively. A function reached only through a wrapper *in its own file*
reads here as unreached, because the declaring file is excluded as "self". Two real examples, both
of which looked like findings and were not:

  - USurvivalHUDWidget's setters. Reported as unreached; they are called from RefreshAllStats, in
    the same file, driven by that widget's own NativeTick. The HUD works. (Since fixed by the access
    filter below -- they are protected -- but the same trap catches public members.)
  - UBloomDirector::TryCorruptSystem. Reported as reached only by CoreLoopPieTests, which suggested
    the Bloom never corrupts anything in play. It is called by RollForJumpSabotage one file over --
    same file, in fact -- and JumpSequenceSubsystem calls that. Corruption works.

So: before believing any entry here, grep the declaring .cpp for the name. If a same-file function
calls it, the question moves to whether *that* is reached, and this tool will not tell you.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "Source" / "Ginnungagap"

# UFUNCTION-decorated declarations only. A plain method with no reflection markup is far more likely
# to be an internal helper, and the interesting cases -- things built to be called from elsewhere --
# are the ones somebody bothered to expose.
DECL = re.compile(
    r"UFUNCTION\s*\([^)]*\)\s*(?:virtual\s+)?[\w:<>,\s\*&]+?\b(\w+)\s*\(",
    re.MULTILINE)

# Names too generic to attribute, or that Unreal itself calls.
IGNORE = {
    "BeginPlay", "Tick", "TickComponent", "EndPlay", "GetLifetimeReplicatedProps",
    "PostInitializeComponents", "OnRep_", "Server", "Multicast", "Client",
}


ACCESS = re.compile(r"^\s*(public|protected|private)\s*:", re.MULTILINE)


def is_ignored(name):
    if name in IGNORE:
        return True
    # Replication and delegate callbacks are invoked by the engine, never by our code.
    return name.startswith(("OnRep_", "Server", "Multicast", "Client", "K2_"))


def public_spans(text):
    """The character ranges of `text` sitting under a `public:` specifier.

    The first version of this script had no access filter and reported 436 of 777 declarations,
    which is not a finding, it is noise -- and the noise was actively misleading. It flagged every
    setter on SurvivalHUDWidget as unreached. Those setters are `protected` and are called from that
    widget's own RefreshAllStats, driven by its own NativeTick, which is exactly where a protected
    member is supposed to be called from.

    Excluding the declaring file is the right rule for public API and precisely the wrong rule for
    anything else, so only public declarations are considered now: "nothing outside this file calls
    it" is only a meaningful question about something meant to be called from outside.
    """
    spans = []
    marks = [(m.start(), m.group(1)) for m in ACCESS.finditer(text)]
    for index, (start, kind) in enumerate(marks):
        if kind != "public":
            continue
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        spans.append((start, end))
    return spans


def main():
    headers = sorted(ROOT.rglob("*.h"))
    sources = sorted(ROOT.rglob("*.cpp"))

    # name -> the header that declared it
    declared = {}
    for header in headers:
        text = header.read_text(encoding="utf-8", errors="replace")
        spans = public_spans(text)
        for match in DECL.finditer(text):
            name = match.group(1)
            if is_ignored(name):
                continue
            if not any(start <= match.start() < end for start, end in spans):
                continue
            declared.setdefault(name, header)

    # Count where each name appears, by file, excluding its own declaration and definition.
    uses = defaultdict(set)
    for path in headers + sources:
        text = path.read_text(encoding="utf-8", errors="replace")
        for name in declared:
            if re.search(r"\b" + re.escape(name) + r"\b", text):
                uses[name].add(path)

    findings = []
    for name, header in sorted(declared.items()):
        touching = uses[name]

        # The declaring header and its paired .cpp are where it lives, not where it is used.
        own = {header, header.with_suffix(".cpp")}
        # Public/Foo.h is often implemented in Public/Foo.cpp or Private/Foo.cpp.
        own.add(Path(str(header).replace("Public", "Private")).with_suffix(".cpp"))

        elsewhere = {p for p in touching if p not in own}
        tests_only = elsewhere and all("Tests" in p.parts or "Tests" in p.name for p in elsewhere)

        if not elsewhere:
            findings.append(("NO CALLER    ", name, header, ""))
        elif tests_only:
            findings.append(("TESTS ONLY   ", name, header,
                             ", ".join(sorted(p.name for p in elsewhere))))

    for kind, name, header, detail in findings:
        rel = header.relative_to(ROOT)
        print("{} {:<44} {}{}".format(kind, name, rel, ("  <- " + detail) if detail else ""))

    print("\n{} declarations examined, {} with nothing reaching them".format(
        len(declared), len(findings)))


if __name__ == "__main__":
    main()
