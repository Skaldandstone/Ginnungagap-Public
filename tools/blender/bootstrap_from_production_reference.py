"""Create a Blender production scene scaffold from a production-reference packet.

Run with Blender and put the manifest path after `--`. An optional second argument saves the
resulting .blend file. This script creates guides and named collections, not final art.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTIONS = (
    "00_GUIDES",
    "10_BLOCKOUT",
    "20_HIGH",
    "30_LOW",
    "40_COLLISION",
    "50_SOCKETS",
    "60_VFX",
    "90_EXPORT",
)


def after_double_dash() -> list[str]:
    if "--" not in sys.argv:
        raise SystemExit("Pass a production manifest after --")
    return sys.argv[sys.argv.index("--") + 1 :]


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def child_collection(name: str, parent: bpy.types.Collection) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing is not None:
        raise RuntimeError(f"Collection already exists: {name}")
    result = bpy.data.collections.new(name)
    parent.children.link(result)
    return result


def add_bounds_guide(dimensions: list[float], target: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, dimensions[2] * 0.5))
    guide = bpy.context.object
    guide.name = "GUIDE_ApprovedBounds"
    guide.dimensions = tuple(dimensions)
    guide.display_type = "WIRE"
    guide.hide_render = True
    for collection in list(guide.users_collection):
        collection.objects.unlink(guide)
    target.objects.link(guide)
    guide["production_reference_role"] = "approved_bounds_guide"
    return guide


def add_empty(name: str, location: list[float], target: bpy.types.Collection, role: str) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "ARROWS" if role == "pivot" else "PLAIN_AXES"
    empty.empty_display_size = 0.15
    empty.location = tuple(location)
    empty["production_reference_role"] = role
    target.objects.link(empty)
    return empty


def main() -> None:
    args = after_double_dash()
    if not args:
        raise SystemExit("Pass a production manifest after --")
    manifest_path = resolve_path(args[0]).resolve()
    packet = json.loads(manifest_path.read_text(encoding="utf-8"))
    build = packet["build"]
    blender = build["blender"]

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"

    root_name = blender["root_collection"]
    if bpy.data.collections.get(root_name) is not None:
        raise RuntimeError(f"Refusing to replace existing collection: {root_name}")
    root = bpy.data.collections.new(root_name)
    scene.collection.children.link(root)
    root["production_reference_asset_id"] = packet["asset_id"]
    root["production_reference_manifest"] = manifest_path.relative_to(ROOT).as_posix()
    root["production_reference_status"] = packet["status"]
    root["production_ready"] = packet["production_ready"]
    root["source_sheet_sha256"] = packet["source_sheet"]["sha256"]

    collection_names = blender.get("collections", DEFAULT_COLLECTIONS)
    collections = {name: child_collection(f"{root_name}_{name}", root) for name in collection_names}
    guide_collection = collections.get("00_GUIDES") or next(iter(collections.values()))
    socket_collection = collections.get("50_SOCKETS") or guide_collection

    dimensions = build.get("dimensions_m")
    if isinstance(dimensions, list) and len(dimensions) == 3:
        add_bounds_guide([float(value) for value in dimensions], guide_collection)

    pivot = build.get("pivot", {})
    if isinstance(pivot.get("location_m"), list) and len(pivot["location_m"]) == 3:
        add_empty(pivot.get("name", "PIVOT_Root"), pivot["location_m"], guide_collection, "pivot")

    for socket in build.get("sockets", []):
        location = socket.get("location_m")
        if not isinstance(location, list) or len(location) != 3:
            continue
        empty = add_empty(socket["name"], location, socket_collection, "socket")
        if isinstance(socket.get("rotation_deg"), list) and len(socket["rotation_deg"]) == 3:
            empty.rotation_euler = tuple(float(value) * 0.017453292519943295 for value in socket["rotation_deg"])
        empty["authority"] = socket.get("authority", "provisional")

    readme = bpy.data.texts.new("PRODUCTION_REFERENCE_README")
    readme.write(
        f"Asset: {packet['title']}\n"
        f"Asset ID: {packet['asset_id']}\n"
        f"Status: {packet['status']}\n"
        f"Production ready: {packet['production_ready']}\n"
        f"Manifest: {manifest_path}\n"
        "Guides and sockets are metadata scaffolding. They are not final geometry.\n"
    )

    if len(args) > 1:
        output_path = resolve_path(args[1]).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        print(f"Saved production scaffold: {output_path}")
    else:
        print(f"Created production scaffold for {packet['asset_id']} without saving a .blend file.")


if __name__ == "__main__":
    main()
