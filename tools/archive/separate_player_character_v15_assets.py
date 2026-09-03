"""Split V14 into independent character/undersuit and oversuit Blender assets."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v14.blend"
CHARACTER_OUTPUT = SUIT_DIR / "PlayerCharacter_Undersuit_v15.blend"
OVERSUIT_OUTPUT = SUIT_DIR / "PlayerOversuit_Separated_v15.blend"
PREVIEWS = SUIT_DIR / "Production_v15_Previews"
MANIFEST = SUIT_DIR / "PlayerCharacter_v15_Separation.json"


def accepted_sets():
    body = set(bpy.data.collections["CHARACTER_V13_BODY"].objects)
    undersuit = set(bpy.data.collections["CHARACTER_V13_UNDERSUIT"].objects)
    oversuit = set(bpy.data.collections["CHARACTER_V13_OVERSUIT"].objects)
    return body, undersuit, oversuit


def remove_objects(objects):
    for obj in list(objects):
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def purge_empty_semantic_collections():
    for collection in list(bpy.data.collections):
        if collection.name.startswith("CHARACTER_V13_") and not collection.objects:
            bpy.data.collections.remove(collection)


def purge_nonlayer_geometry(keep):
    review_geometry = {"HighPolyReview_Floor", "StudioFloor"}
    remove_objects([
        obj for obj in bpy.data.objects
        if obj.type in {"MESH", "CURVE"} and obj not in keep and obj.name not in review_geometry
    ])


def trim_embedded_rear_pack(undersuit):
    keep_group = undersuit.vertex_groups.get("V15_UndersuitEnvelope") or undersuit.vertex_groups.new(
        name="V15_UndersuitEnvelope"
    )
    keep, removed = [], []
    for vertex in undersuit.data.vertices:
        world = undersuit.matrix_world @ vertex.co
        embedded_pack = world.y > .145 and 1.08 < world.z < 1.54 and abs(world.x) < .25
        (removed if embedded_pack else keep).append(vertex.index)
    if len(removed) < 20:
        raise RuntimeError(f"Embedded oversuit trim selected too few vertices: {len(removed)}")
    keep_group.add(keep, 1.0, "REPLACE")
    mask = undersuit.modifiers.get("V15_RemoveEmbeddedRearPack") or undersuit.modifiers.new(
        "V15_RemoveEmbeddedRearPack", "MASK"
    )
    mask.vertex_group = keep_group.name
    mask.threshold = .5
    undersuit.modifiers.move(len(undersuit.modifiers) - 1, 0)
    undersuit["v15_embedded_oversuit_vertices_removed"] = len(removed)
    return len(removed)


def render_views(prefix, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)),
        "Profile": Vector((4.4, 0, 1.02)),
        "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 62
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"{prefix}_{label}.png")
        bpy.ops.render.render(write_still=True)


def build_character_asset():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    body, undersuit, oversuit = accepted_sets()
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v14"]
    # Remove every accepted outer component and all rejected/generated suit-study
    # geometry. The character file must not silently contain a disabled oversuit.
    remove = set(oversuit)
    for obj in bpy.data.objects:
        if obj in body or obj in undersuit or obj == armature:
            continue
        if (obj.name.startswith(("SKV6_Helmet_", "SKV7_", "SKV8_", "SKV9_", "SKV10_", "SKV11_", "SKV12_"))
                or obj.get("character_layer") == "oversuit"
                or obj.get("v11_conformal_shell")
                or obj.get("v12_panel_finish")):
            remove.add(obj)
    remove_objects(remove)
    purge_nonlayer_geometry(body | undersuit)
    purge_empty_semantic_collections()
    armature.name = "RIG_PlayerCharacter_Undersuit_v15"
    character_collection = bpy.data.collections.get("CHARACTER_V13_BODY")
    character_collection.name = "CHARACTER_V15_BODY"
    undersuit_collection = bpy.data.collections.get("CHARACTER_V13_UNDERSUIT")
    undersuit_collection.name = "CHARACTER_V15_UNDERSUIT"
    under = next(iter(undersuit))
    under.name = "SK_PlayerCharacter_Undersuit_v15"
    removed_embedded_vertices = trim_embedded_rear_pack(under)
    under["asset_status"] = "PLAYER_CHARACTER_UNDERSUIT_V15"
    under["contains_oversuit"] = False
    render_views("PlayerCharacter_Undersuit_v15", [obj for obj in [*body, under] if obj.name in bpy.data.objects])
    bpy.ops.wm.save_as_mainfile(filepath=str(CHARACTER_OUTPUT), check_existing=False)
    return {
        "file": str(CHARACTER_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "body_objects": sorted(obj.name for obj in body if obj.name in bpy.data.objects),
        "undersuit_objects": [under.name],
        "oversuit_objects": [],
        "embedded_oversuit_vertices_removed": removed_embedded_vertices,
    }


def build_oversuit_asset():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    body, undersuit, oversuit = accepted_sets()
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v14"]
    remove_objects([obj for obj in body if obj != armature])
    remove_objects(undersuit)
    # Purge rejected study geometry while retaining only the accepted semantic
    # oversuit set and review-scene infrastructure.
    remove = []
    for obj in bpy.data.objects:
        if obj in oversuit or obj == armature or obj.type in {"CAMERA", "LIGHT"}:
            continue
        if (obj.name.startswith(("SKV7_", "SKV8_", "SKV9_", "SKV10_", "SKV11_", "SKV12_"))
                or obj.get("v12_review_status")
                or obj.get("v7_authored_shell")
                or obj.get("v8_production_detail")):
            remove.append(obj)
    remove_objects(remove)
    purge_nonlayer_geometry(oversuit)
    purge_empty_semantic_collections()
    armature.name = "RIG_PlayerOversuit_v15"
    oversuit_collection = bpy.data.collections.get("CHARACTER_V13_OVERSUIT")
    oversuit_collection.name = "PLAYER_OVERSUIT_V15"
    for obj in oversuit:
        if obj.name in bpy.data.objects:
            obj["asset_status"] = "PLAYER_OVERSUIT_V15"
            obj["contains_character"] = False
    render_views("PlayerOversuit_v15", [obj for obj in oversuit if obj.name in bpy.data.objects])
    bpy.ops.wm.save_as_mainfile(filepath=str(OVERSUIT_OUTPUT), check_existing=False)
    return {
        "file": str(OVERSUIT_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "skeleton_reference": armature.name,
        "character_objects": [],
        "undersuit_objects": [],
        "oversuit_objects": sorted(obj.name for obj in oversuit if obj.name in bpy.data.objects),
    }


def main():
    character = build_character_asset()
    oversuit = build_oversuit_asset()
    MANIFEST.write_text(json.dumps({
        "schema": 1, "version": 15, "status": "physically_separated",
        "source_assembly": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "character_asset": character, "oversuit_asset": oversuit,
        "default_gameplay_asset": "character_asset",
        "assembly_policy": "oversuit is attached explicitly by loadout; never embedded in character asset",
    }, indent=2), encoding="utf-8")
    print("V15_ASSET_SEPARATION", f"character={CHARACTER_OUTPUT}",
          f"oversuit={OVERSUIT_OUTPUT}", f"oversuit_parts={len(oversuit['oversuit_objects'])}")


if __name__ == "__main__":
    main()
