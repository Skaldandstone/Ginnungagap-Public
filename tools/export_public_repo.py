"""Builds the public, linkable snapshot of the project as a fresh repository.

The working repository cannot be published as it is: Content/ is 24 GB, almost all of it licensed
Fab packs that may not be redistributed, and its history carries the same. So the public repo is
a curated snapshot, rebuilt from scratch each time this runs, with no history of its own beyond
its snapshot commits:

    Source/, Config/, tools/, docs/ (concept art consolidated), .game-guide/project.json,
    Content/Assets/, Content/UI/, Content/Input/, Ginnungagap.uproject, plus a reviewer-facing
    README (tools/public_repo/README.md) and LICENSE (tools/public_repo/LICENSE).

Everything else -- every Fab pack under Content/, Content/Characters (donor packs), Art/ (source
scenes, 5 GB), Saved/, Intermediate/, salvage/ -- stays out. Binary assets are tracked with Git LFS
in the export so GitHub's 100 MB file limit does not bite; any single file over 95 MB is skipped
and listed so it can be dealt with by hand.

    python tools/export_public_repo.py [--dest C:/path/Ginnungagap-Public] [--push]

--push commits the snapshot and pushes to the export's `origin` (set once, see README).
"""
import argparse
import datetime as dt
import fnmatch
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = ROOT.parent.parent / "GitHub" / "Ginnungagap-Public"

INCLUDE_DIRS = ["Source", "Config", "tools", "docs", "Content/Assets", "Content/UI", "Content/Input"]
INCLUDE_FILES = ["Ginnungagap.uproject", ".gitattributes", ".editorconfig"]
EXCLUDE_GLOBS = [
    "**/__pycache__/**", "**/*.pyc", "**/.DS_Store", "**/Thumbs.db",
    "tools/public_repo/**",           # the templates themselves
    "docs/**/*.krita-report.txt",
    "**/*.blend1",
]
MAX_FILE_BYTES = 95 * 1024 * 1024
LFS_PATTERNS = ["*.uasset", "*.umap", "*.png", "*.jpg", "*.jpeg", "*.wav", "*.blend", "*.fbx", "*.exr", "*.tga", "*.psd", "*.kra", "*.mp4", "*.pdf", "*.db"]
FAB_PACKS_NOTE = [
    "Abandonned_Brutalist", "Alien_Biomass", "Alien_Cave_biome", "Alien_planet", "Dam_city",
    "DeadBodies_Poses_nikoff", "FreeAnimationLibrary", "HorrorAmbientSFX", "Ice_Station", "MagmaSciFiPistol",
    "ModSci_EngiProps", "ModSci_Engineer", "Modular_Scifi_Mechanic_Base", "SF_Brutalist_city", "SF_White_desert",
    "Sci-Fi_Flying_Cargo_Ship", "SciFiUISFX", "SciFiWorld", "SciFi_ToiletMech", "Sci_Fi_city", "Scifi_Hideout",
    "kb3d_missiontominerva", "Frontier_EngineersToolbox",
]


def excluded(rel):
    return any(fnmatch.fnmatch(rel, pattern) for pattern in EXCLUDE_GLOBS)


def git(dest, *args, check=True):
    return subprocess.run(["git", *args], cwd=dest, check=check, capture_output=True, text=True)


def copy_tree(dest):
    copied, skipped_big, total = 0, [], 0
    for rel_dir in INCLUDE_DIRS:
        src = ROOT / rel_dir
        if not src.exists():
            continue
        for path in src.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if excluded(rel):
                continue
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                skipped_big.append((rel, size))
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
            total += size
    for rel in INCLUDE_FILES:
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, dest / rel)
            copied += 1
    return copied, total, skipped_big


def write_meta(dest, skipped_big):
    templates = ROOT / "tools" / "public_repo"
    shutil.copy2(templates / "LICENSE", dest / "LICENSE")
    readme = (templates / "README.md").read_text(encoding="utf-8")
    readme = readme.replace("{{FAB_PACKS}}", "\n".join(f"- `{name}`" for name in FAB_PACKS_NOTE))
    readme = readme.replace("{{SNAPSHOT_DATE}}", dt.date.today().isoformat())
    big = "\n".join(f"- `{rel}` ({size // (1024 * 1024)} MB)" for rel, size in skipped_big) or "- none"
    readme = readme.replace("{{SKIPPED_FILES}}", big)
    (dest / "README.md").write_text(readme, encoding="utf-8")
    (dest / ".gitignore").write_text("/Binaries/\n/DerivedDataCache/\n/Intermediate/\n/Saved/\n/Build/\n*.sln\n*.suo\n*.user\n.vs/\n__pycache__/\n", encoding="utf-8")
    attributes = ["* text=auto eol=lf"]
    attributes += [f"{pattern} filter=lfs diff=lfs merge=lfs -text" for pattern in LFS_PATTERNS]
    (dest / ".gitattributes").write_text("\n".join(attributes) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default=str(DEFAULT_DEST))
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    dest = Path(args.dest)

    origin = None
    if (dest / ".git").exists():
        remotes = git(dest, "remote", "get-url", "origin", check=False)
        origin = remotes.stdout.strip() or None
        # Wipe the working tree but keep .git so the snapshot commits stack on the same repo.
        for entry in dest.iterdir():
            if entry.name == ".git":
                continue
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
    else:
        dest.mkdir(parents=True, exist_ok=True)
        git(dest, "init", "-b", "main")
        git(dest, "lfs", "install", "--local")

    copied, total, skipped_big = copy_tree(dest)
    write_meta(dest, skipped_big)
    print(f"copied {copied} files, {total / (1024 * 1024):.0f} MB; skipped {len(skipped_big)} over 95 MB")
    for rel, size in skipped_big:
        print(f"  skipped {rel} ({size // (1024 * 1024)} MB)")

    git(dest, "add", "-A")
    status = git(dest, "status", "--porcelain").stdout
    if not status.strip():
        print("nothing changed since the last snapshot")
        return
    message = f"Snapshot {dt.date.today().isoformat()} from the working repository"
    git(dest, "commit", "-q", "-m", message + "\n\nBuilt by tools/export_public_repo.py.")
    print("committed:", message)
    if args.push:
        if not origin:
            raise SystemExit("no origin on the export; add one with `git remote add origin <url>` and rerun with --push")
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=dest, check=True)
        print("pushed to", origin)


if __name__ == "__main__":
    main()
