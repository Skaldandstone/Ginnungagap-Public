"""Validate and index Ginnungagap production-reference packets.

This script uses only the Python standard library so it can run outside Blender and Unreal.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = ROOT / "docs" / "concept-art"
OUTPUT_DIR = REFERENCE_ROOT / "production-reference"
PACKET_GLOB = "*.production.json"
INVENTORY_COLLECTIONS = (
    (ROOT / "Content" / "Assets" / "ConceptArt", "unreal-concept-library", "primary-concept-art"),
    (ROOT / "docs" / "concept-art", "documentation-concepts", "design-reference"),
    (ROOT / "Art" / "Weapons" / "Concepts", "weapon-concept-boards", "concept-board"),
    (ROOT / "Art" / "ShipRooms" / "CryoPodConceptV4", "cryo-production-iteration", "production-iteration"),
    (ROOT / "Art" / "Ships" / "Exterior" / "ConceptMatch", "ship-concept-match", "production-iteration"),
    (ROOT / "Art" / "Ships" / "Exterior" / "ConceptRemasterV01", "ship-remaster-v01", "superseded-iteration"),
    (ROOT / "Art" / "Ships" / "Exterior" / "ConceptRemasterV02", "ship-remaster-v02", "superseded-iteration"),
    (ROOT / "Art" / "Ships" / "Exterior" / "ConceptRemasterV03", "ship-remaster-v03", "superseded-iteration"),
    (ROOT / "Art" / "Ships" / "Exterior" / "UnrealSculptReview", "ship-sculpt-review", "production-review"),
    (ROOT / "Art" / "Characters" / "PlayerSuits" / "RealityScan" / "V25_ConceptLock" / "Input", "player-suit-concept-lock", "production-reference"),
    (ROOT / "Art" / "Characters" / "BloomEnemies" / "Progression", "bloom-progression", "production-reference"),
    (ROOT / "Art" / "Weapons" / "RealityScan" / "CompactRockCorer_Pilot" / "CleanReference", "rock-corer-clean-reference", "production-reference"),
    (ROOT / "Art" / "Weapons" / "SalvageBatch03" / "CleanFirstUseReferences", "salvage-clean-reference", "production-reference"),
    (ROOT / "Art" / "SpaceSystems", "space-system-art", "production-reference"),
    (ROOT / "Art" / "UI", "ui-art", "production-reference"),
    (ROOT / "Build" / "RealityScan" / "CryoTurnaround" / "InputViews", "cryo-turnaround-input", "capture-reference"),
    (ROOT / "Content" / "Assets" / "Ships" / "Exterior" / "UnrealSculpt" / "References", "unreal-ship-sculpt-reference", "production-reference"),
)
VISUAL_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".gif", ".svg"}
REQUIRED_KEYS = {
    "schema_version",
    "asset_id",
    "title",
    "category",
    "status",
    "production_ready",
    "source_sheet",
    "authority",
    "build",
    "acceptance_checks",
}


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_dimensions(path: Path) -> tuple[int | None, int | None]:
    if path.suffix.lower() == ".svg":
        header_text = path.read_text(encoding="utf-8", errors="ignore")[:8192]
        width_match = re.search(r'\bwidth=["\']([0-9.]+)', header_text)
        height_match = re.search(r'\bheight=["\']([0-9.]+)', header_text)
        if width_match and height_match:
            return round(float(width_match.group(1))), round(float(height_match.group(1)))
        viewbox_match = re.search(r'\bviewBox=["\'][^"\']*?([0-9.]+)\s+([0-9.]+)["\']', header_text)
        if viewbox_match:
            return round(float(viewbox_match.group(1))), round(float(viewbox_match.group(2)))
        return None, None
    with path.open("rb") as handle:
        header = handle.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return struct.unpack(">II", header[16:24])
        if header[:6] in {b"GIF87a", b"GIF89a"}:
            return struct.unpack("<HH", header[6:10])
        if header[:2] != b"\xff\xd8":
            return None, None
        handle.seek(2)
        while True:
            marker_prefix = handle.read(1)
            if not marker_prefix:
                return None, None
            if marker_prefix != b"\xff":
                continue
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if marker in {b"\xd8", b"\xd9"}:
                continue
            size_raw = handle.read(2)
            if len(size_raw) != 2:
                return None, None
            size = struct.unpack(">H", size_raw)[0]
            if marker and marker[0] in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                payload = handle.read(5)
                if len(payload) != 5:
                    return None, None
                height, width = struct.unpack(">HH", payload[1:5])
                return width, height
            handle.seek(max(0, size - 2), 1)


def resolve_project_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return ROOT / Path(*value.replace("\\", "/").split("/"))


def packet_paths() -> list[Path]:
    return sorted(REFERENCE_ROOT.glob(f"20??-??-??/production-reference/{PACKET_GLOB}"))


def validate_packet(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        packet = load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"{repo_path(path)}: {exc}"]

    missing = sorted(REQUIRED_KEYS.difference(packet))
    if missing:
        errors.append(f"{repo_path(path)}: missing keys: {', '.join(missing)}")
        return errors

    if packet["schema_version"] != "1.0.0":
        errors.append(f"{repo_path(path)}: schema_version must be 1.0.0")
    if not str(packet["asset_id"]).startswith("GGP."):
        errors.append(f"{repo_path(path)}: asset_id must start with GGP.")
    if packet["production_ready"] and packet["status"] != "production-ready":
        errors.append(f"{repo_path(path)}: production_ready requires status production-ready")

    source = packet.get("source_sheet", {})
    source_path = resolve_project_path(str(source.get("path", "")))
    if not source_path.is_file():
        errors.append(f"{repo_path(path)}: source sheet missing: {source.get('path')}")
    else:
        expected_hash = str(source.get("sha256", "")).lower()
        actual_hash = sha256(source_path)
        if expected_hash != actual_hash:
            errors.append(f"{repo_path(path)}: source sheet SHA-256 mismatch")
        width, height = image_dimensions(source_path)
        if width != source.get("width_px") or height != source.get("height_px"):
            errors.append(
                f"{repo_path(path)}: source dimensions mismatch, expected "
                f"{source.get('width_px')}x{source.get('height_px')}, found {width}x{height}"
            )

    authority = packet.get("authority", {})
    for key in ("approved", "provisional", "conflicts"):
        if not isinstance(authority.get(key), list):
            errors.append(f"{repo_path(path)}: authority.{key} must be an array")

    build = packet.get("build", {})
    for key in ("coordinate_system", "parts", "materials", "sockets", "states", "blender", "unreal"):
        if key not in build:
            errors.append(f"{repo_path(path)}: build.{key} is required")
    coordinate = build.get("coordinate_system", {})
    if coordinate.get("unreal_units_per_meter") != 100:
        errors.append(f"{repo_path(path)}: Unreal units per meter must be 100")

    implementation_profile = packet.get("implementation_profile", "core")
    if implementation_profile not in {"core", "expanded"}:
        errors.append(f"{repo_path(path)}: implementation_profile must be core or expanded")
    if implementation_profile == "expanded":
        if not isinstance(packet.get("metadata"), dict):
            errors.append(f"{repo_path(path)}: expanded packets require metadata")
        for key in ("rig", "animation", "vfx", "spline_mapping", "render_mapping", "implementation"):
            if not isinstance(build.get(key), dict):
                errors.append(f"{repo_path(path)}: expanded packets require build.{key}")

    for source_entry in packet.get("concept_sources", []):
        if not source_entry.get("required", False):
            continue
        concept_path = resolve_project_path(str(source_entry.get("path", "")))
        if not concept_path.exists():
            errors.append(f"{repo_path(path)}: required concept source missing: {source_entry.get('path')}")

    for source_set in packet.get("concept_source_sets", []):
        if not source_set.get("required", False):
            continue
        source_root = resolve_project_path(str(source_set.get("root", "")))
        if not source_root.is_dir():
            errors.append(f"{repo_path(path)}: required concept source set missing: {source_set.get('root')}")

    check_ids = [check.get("id") for check in packet.get("acceptance_checks", [])]
    if len(check_ids) != len(set(check_ids)):
        errors.append(f"{repo_path(path)}: acceptance check ids must be unique")
    return errors


def validate() -> list[dict[str, Any]]:
    paths = packet_paths()
    if not paths:
        raise RuntimeError(f"No packets found under dated production-reference batches in {REFERENCE_ROOT}")
    errors: list[str] = []
    packets: list[dict[str, Any]] = []
    for path in paths:
        errors.extend(validate_packet(path))
        packet = load_json(path)
        packet["_manifest_path"] = repo_path(path)
        packets.append(packet)
    if errors:
        raise RuntimeError("\n".join(errors))
    print(f"Validated {len(packets)} production-reference packets.")
    return packets


def write_index(packets: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    entries = []
    for packet in sorted(packets, key=lambda item: item["asset_id"]):
        conflicts = packet["authority"]["conflicts"]
        entries.append(
            {
                "asset_id": packet["asset_id"],
                "title": packet["title"],
                "category": packet["category"],
                "status": packet["status"],
                "production_ready": packet["production_ready"],
                "implementation_profile": packet.get("implementation_profile", "core"),
                "companion_to": packet.get("companion_to"),
                "manifest": packet["_manifest_path"],
                "source_sheet": packet["source_sheet"]["path"],
                "is_superseded": bool(packet.get("superseded_by")),
                "superseded_by": packet.get("superseded_by"),
                "blocking_conflict_count": sum(1 for item in conflicts if item.get("severity") == "blocker"),
                "pending_check_count": sum(
                    1 for item in packet["acceptance_checks"] if item.get("status") in {"pending", "blocked"}
                ),
                "unreal_destination": packet["build"]["unreal"]["destination_root"],
                "blender_collection": packet["build"]["blender"]["root_collection"],
            }
        )

    catalog = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "packet_count": len(entries),
        "active_packet_count": sum(1 for item in entries if not item["is_superseded"]),
        "production_ready_count": sum(1 for item in entries if item["production_ready"]),
        "blocked_count": sum(1 for item in entries if item["blocking_conflict_count"] > 0),
        "active_blocked_count": sum(
            1 for item in entries if not item["is_superseded"] and item["blocking_conflict_count"] > 0
        ),
        "assets": entries,
    }
    catalog_path = OUTPUT_DIR / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    csv_path = OUTPUT_DIR / "UnrealProductionReferences.csv"
    fields = [
        "Name",
        "AssetId",
        "Title",
        "Category",
        "Status",
        "ProductionReady",
        "ImplementationProfile",
        "CompanionTo",
        "SupersededBy",
        "BlockingConflictCount",
        "PendingCheckCount",
        "SourceSheet",
        "Manifest",
        "UnrealDestination",
        "BlenderCollection",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "Name": entry["asset_id"].replace(".", "_"),
                    "AssetId": entry["asset_id"],
                    "Title": entry["title"],
                    "Category": entry["category"],
                    "Status": entry["status"],
                    "ProductionReady": str(entry["production_ready"]).lower(),
                    "ImplementationProfile": entry["implementation_profile"],
                    "CompanionTo": entry["companion_to"] or "",
                    "SupersededBy": entry["superseded_by"] or "",
                    "BlockingConflictCount": entry["blocking_conflict_count"],
                    "PendingCheckCount": entry["pending_check_count"],
                    "SourceSheet": entry["source_sheet"],
                    "Manifest": entry["manifest"],
                    "UnrealDestination": entry["unreal_destination"],
                    "BlenderCollection": entry["blender_collection"],
                }
            )
    print(f"Wrote {repo_path(catalog_path)} and {repo_path(csv_path)}.")


def inventory(packets: list[dict[str, Any]] | None = None) -> None:
    if packets is None:
        packets = []
        for packet_path in packet_paths():
            packet = load_json(packet_path)
            packet["_manifest_path"] = repo_path(packet_path)
            packets.append(packet)

    packet_links: dict[str, set[str]] = {}
    packet_link_roots: list[tuple[str, str]] = []
    for packet in packets:
        linked_paths = [packet.get("source_sheet", {}).get("path")]
        linked_paths.extend(source.get("path") for source in packet.get("concept_sources", []))
        for linked_path in linked_paths:
            if not linked_path or Path(str(linked_path)).suffix.lower() not in VISUAL_SUFFIXES:
                continue
            normalized_link = Path(*str(linked_path).replace("\\", "/").split("/")).as_posix().lower()
            packet_links.setdefault(normalized_link, set()).add(packet["asset_id"])
        for source_set in packet.get("concept_source_sets", []):
            source_root = source_set.get("root")
            if not source_root:
                continue
            normalized_root = Path(*str(source_root).replace("\\", "/").split("/")).as_posix().rstrip("/").lower()
            packet_link_roots.append((normalized_root, packet["asset_id"]))

    records: list[dict[str, Any]] = []
    seen: set[Path] = set()
    active_collections: list[dict[str, Any]] = []
    for source_root, collection, source_kind in INVENTORY_COLLECTIONS:
        if not source_root.is_dir():
            continue
        active_collections.append(
            {"root": repo_path(source_root), "collection": collection, "source_kind": source_kind}
        )
        for path in sorted(source_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in VISUAL_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            width, height = image_dimensions(path)
            normalized = repo_path(path)
            lowered = normalized.lower()
            linked_ids = set(packet_links.get(lowered, set()))
            for linked_root, asset_id in packet_link_roots:
                if lowered == linked_root or lowered.startswith(f"{linked_root}/"):
                    linked_ids.add(asset_id)
            linked_packet_ids = sorted(linked_ids)
            records.append(
                {
                    "path": normalized,
                    "collection": collection,
                    "source_kind": source_kind,
                    "format": path.suffix.lower().lstrip("."),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "width_px": width,
                    "height_px": height,
                    "linked_packet_ids": linked_packet_ids,
                    "reference_candidate": any(
                        token in lowered
                        for token in ("production-reference", "sheet", "turnaround", "orthographic", "blueprint", "lineup")
                    ),
                    "capture_or_preview": any(
                        token in lowered for token in ("/inputframes/", "realityscanoutput", "_preview", "/previews/")
                    ),
                }
            )

    by_collection = {
        collection: sum(1 for item in records if item["collection"] == collection)
        for collection in sorted({item["collection"] for item in records})
    }
    by_source_kind = {
        source_kind: sum(1 for item in records if item["source_kind"] == source_kind)
        for source_kind in sorted({item["source_kind"] for item in records})
    }
    for collection_entry in active_collections:
        collection_entry["visual_file_count"] = by_collection.get(collection_entry["collection"], 0)
    output = {
        "schema_version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "collections": active_collections,
        "configured_collection_count": len(active_collections),
        "populated_collection_count": len(by_collection),
        "primary_collection": "Content/Assets/ConceptArt",
        "visual_file_count": len(records),
        "image_count": len(records),
        "reference_candidate_count": sum(1 for item in records if item["reference_candidate"]),
        "packet_linked_visual_count": sum(1 for item in records if item["linked_packet_ids"]),
        "unlinked_visual_count": sum(1 for item in records if not item["linked_packet_ids"]),
        "by_collection": by_collection,
        "by_source_kind": by_source_kind,
        "visuals": records,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "concept-art-inventory.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {repo_path(output_path)} with {len(records)} visual files.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "index", "inventory", "all"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "validate":
            validate()
        elif args.command == "index":
            write_index(validate())
        elif args.command == "inventory":
            inventory()
        else:
            packets = validate()
            write_index(packets)
            inventory(packets)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
