"""Prepare purchased Space Marshal FBXs as garment-only Unreal review sources.

This script is intentionally a deterministic source splitter, not a suit generator.
It preserves the vendor-authored skinned garment meshes and armature while removing
the donor head and eye geometry. Run it with Blender in background mode, for example:

    blender.exe --background --python tools/prepare_space_marshal_oversuit_sources.py -- \
        --input Intermediate/Fab/SpaceMarshal/Male/SM_Male_UE5.fbx \
        --output Intermediate/Fab/SpaceMarshal/Prepared/SM_Male_Oversuit_UE5.fbx

Purchased sources and prepared derivatives remain under ignored Intermediate/Fab.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import bpy


GARMENT_MATERIALS = {
    "SM_Suit",
    "SM_Helm",
    "MS_Visor",
    "SM_Gloves",
    "SM_Boots",
    "SM_Bags",
    "SM_Pouch",
}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def material_names(obj: bpy.types.Object) -> set[str]:
    if obj.type != "MESH":
        return set()
    return {slot.material.name for slot in obj.material_slots if slot.material}


def main() -> None:
    args = parse_args()
    source = args.input.resolve()
    destination = args.output.resolve()
    if not source.is_file():
        raise RuntimeError(f"Space Marshal FBX does not exist: {source}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)

    garments = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and material_names(obj).intersection(GARMENT_MATERIALS)
    ]
    if not garments:
        raise RuntimeError("No expected Space Marshal garment meshes were found")

    missing_materials = GARMENT_MATERIALS.difference(
        {name for obj in garments for name in material_names(obj)}
    )
    if missing_materials:
        raise RuntimeError(f"Prepared source would be incomplete; missing {sorted(missing_materials)}")

    armatures = {
        modifier.object
        for garment in garments
        for modifier in garment.modifiers
        if modifier.type == "ARMATURE" and modifier.object
    }
    if len(armatures) != 1:
        raise RuntimeError(f"Expected exactly one garment armature, found {len(armatures)}")
    armature = next(iter(armatures))

    bpy.ops.object.select_all(action="DESELECT")
    for garment in garments:
        garment.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(destination),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=False,
        mesh_smooth_type="FACE",
        path_mode="AUTO",
    )

    mesh_summary = ", ".join(
        f"{obj.name}({len(obj.data.vertices)} verts)" for obj in sorted(garments, key=lambda item: item.name)
    )
    print(f"Prepared garment-only FBX: {destination}")
    print(f"Armature: {armature.name}; meshes: {mesh_summary}")


if __name__ == "__main__":
    main()
