"""Moves the loose concept-art folders into one reference tree and rewrites every path to them.

docs/concept-art/ grew by accretion: eight subject folders at the top level, three dated folders
that each hold a production-reference packet set plus a scatter of hero iterations, and a fleet
folder inside one of the dated ones. This puts every loose image under docs/concept-art/reference/
by subject and leaves the dated production-reference packets exactly where they are -- those are
a schema-validated system (tools/validate_production_references.py) whose JSON points at its own
sheets by path, and moving them buys nothing.

Files are moved with git mv so LFS pointers and history follow. Every text file under docs/,
tools/, .game-guide/ and the README that mentions an old path gets the new one, then the packet
validator runs, so a broken reference is a failure here and not a surprise later.

    python tools/consolidate_concept_art.py            # move + rewrite + validate
    python tools/consolidate_concept_art.py --dry-run  # report only
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CA = "docs/concept-art"

# (old path relative to repo, new path relative to repo). Directories move whole.
MOVES = [
    (f"{CA}/bloom-enemies", f"{CA}/reference/bloom"),
    (f"{CA}/ships", f"{CA}/reference/ships"),
    (f"{CA}/ship-rooms", f"{CA}/reference/rooms"),
    (f"{CA}/player-suits", f"{CA}/reference/suits"),
    (f"{CA}/space-systems", f"{CA}/reference/space"),
    (f"{CA}/ui", f"{CA}/reference/ui"),
    (f"{CA}/versus", f"{CA}/reference/versus"),
    (f"{CA}/cic-interactions", f"{CA}/reference/cic"),
    (f"{CA}/2026-08-29/replacement-fleet", f"{CA}/reference/ships/replacement-fleet"),
    (f"{CA}/2026-08-28/ginnungagap-bloom-companionway-v1.png", f"{CA}/reference/bloom/companionway-v1.png"),
    (f"{CA}/2026-08-28/ginnungagap-bloom-mechanized-host-v1.png", f"{CA}/reference/bloom/mechanized-host-v1.png"),
]
# The hero iterations for the mechanized host: every loose file in the 2026-08-31 folder.
HERO_ITERATIONS_DIR = f"{CA}/2026-08-31"
HERO_ITERATIONS_DEST = f"{CA}/reference/bloom/mechanized-host-iterations"

TEXT_SUFFIXES = {".md", ".json", ".csv", ".py", ".txt", ".yaml", ".yml", ".ini"}
REWRITE_ROOTS = ["docs", "tools", ".game-guide", "README.md"]


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True, text=True)


def expand_moves():
    moves = list(MOVES)
    hero = ROOT / HERO_ITERATIONS_DIR
    if hero.exists():
        for entry in sorted(hero.iterdir()):
            if entry.is_file():
                moves.append((f"{HERO_ITERATIONS_DIR}/{entry.name}", f"{HERO_ITERATIONS_DEST}/{entry.name.replace('ginnungagap-bloom-', '')}"))
    return [(a, b) for a, b in moves if (ROOT / a).exists()]


def rewrite_text(moves, dry_run):
    # Longest old paths first, so a directory rename does not clobber a more specific file move.
    ordered = sorted(moves, key=lambda ab: -len(ab[0]))
    changed = 0
    for root in REWRITE_ROOTS:
        base = ROOT / root
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES]
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new_text = text
            for old, new in ordered:
                new_text = new_text.replace(old, new)
                # Also the path as written without the docs/ prefix, which some manifests use.
                new_text = new_text.replace(old[len("docs/"):], new[len("docs/"):])
            if new_text != text:
                changed += 1
                print(f"  rewrite {path.relative_to(ROOT)}")
                if not dry_run:
                    path.write_text(new_text, encoding="utf-8")
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    moves = expand_moves()
    print(f"{len(moves)} move(s):")
    for old, new in moves:
        print(f"  {old}  ->  {new}")
        if not args.dry_run:
            (ROOT / new).parent.mkdir(parents=True, exist_ok=True)
            git("mv", old, new)
    changed = rewrite_text(moves, args.dry_run)
    print(f"{changed} text file(s) rewritten")

    validator = ROOT / "tools" / "validate_production_references.py"
    if validator.exists() and not args.dry_run:
        result = subprocess.run([sys.executable, str(validator)], cwd=ROOT, capture_output=True, text=True)
        print(result.stdout[-2000:])
        if result.returncode != 0:
            print(result.stderr[-2000:])
            raise SystemExit("production-reference validation failed after the move")
    print("done")


if __name__ == "__main__":
    main()
