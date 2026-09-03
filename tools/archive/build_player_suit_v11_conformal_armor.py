"""Replace floating primitive armor studies with rigged conformal V11 shells."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v8.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v11.blend"
PREVIEWS = SUIT_DIR / "Production_v11_Previews"
REPORT = SUIT_DIR / "PlayerSuit_Production_v11_ConformalArmor.json"


def make_material(name, color, metallic, roughness):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def conformal_patch(source, name, predicate, collection, material, thickness=.008):
    patch = source.copy()
    patch.data = source.data.copy()
    patch.name = name
    patch.data.name = name + "_Mesh"
    collection.objects.link(patch)
    selected = [vertex.index for vertex in patch.data.vertices
                if predicate(patch.matrix_world @ vertex.co)]
    if len(selected) < 20:
        raise RuntimeError(f"Conformal patch {name} selected only {len(selected)} vertices")
    group = patch.vertex_groups.get("V11_ArmorRegion") or patch.vertex_groups.new(name="V11_ArmorRegion")
    group.add(selected, 1.0, "REPLACE")
    mask = patch.modifiers.new("V11_RegionMask", "MASK")
    mask.vertex_group = group.name
    mask.threshold = .5
    patch.modifiers.move(len(patch.modifiers) - 1, 0)
    solidify = patch.modifiers.new("V11_ArmorThickness", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 1.0
    solidify.use_even_offset = True
    patch.modifiers.move(len(patch.modifiers) - 1, 1)
    bevel = patch.modifiers.new("V11_SoftManufacturedEdge", "BEVEL")
    bevel.width = .003
    bevel.segments = 3
    patch.modifiers.move(len(patch.modifiers) - 1, 2)
    patch.data.materials.clear()
    patch.data.materials.append(material)
    patch["v11_conformal_shell"] = True
    patch["selected_vertex_count"] = len(selected)
    patch["shell_thickness_m"] = thickness
    patch.hide_render = False
    return patch


def render(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)), "Back": Vector((0, 4.4, 1.02)),
        "Side": Vector((4.4, 0, 1.02)), "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 60
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v11_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v8"]
    armature.name = "RIG_PlayerSuit_Production_v11"
    base = bpy.data.objects["SK_PlayerSuit_Production_v8_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v11_BaseGarment"
    # Reject the earlier add-on geometry while retaining V8 as a checkpoint.
    hidden_collections = []
    for name in ("SUIT_PRODUCTION_v7_AUTHORED_SHELLS", "SUIT_PRODUCTION_v8_50_PASSES"):
        old = bpy.data.collections.get(name)
        if old:
            for obj in old.objects:
                obj.hide_render = True
            hidden_collections.append(name)

    collection = bpy.data.collections.new("SUIT_PRODUCTION_v11_CONFORMAL_ARMOR")
    bpy.context.scene.collection.children.link(collection)
    armor = make_material("M_V11_MutedCeramic", (.29, .33, .34), .30, .36)
    dark = make_material("M_V11_DarkComposite", (.025, .038, .044), .45, .34)
    patches = []

    def add(name, predicate, material=armor, thickness=.008):
        patches.append(conformal_patch(base, name, predicate, collection, material, thickness))

    # Coordinate windows intentionally overlap slightly; the dark separator
    # material and physical thickness make the construction breaks readable.
    add("SKV11_ChestUpper", lambda p: p.y < -.025 and abs(p.x) < .205 and 1.235 < p.z < 1.405)
    add("SKV11_ChestLower", lambda p: p.y < -.035 and abs(p.x) < .175 and 1.080 < p.z <= 1.235, dark, .007)
    add("SKV11_Shoulder_L", lambda p: p.y < .055 and p.x < -.155 and 1.225 < p.z < 1.410)
    add("SKV11_Shoulder_R", lambda p: p.y < .055 and p.x > .155 and 1.225 < p.z < 1.410)
    add("SKV11_Forearm_L", lambda p: p.y < .035 and p.x < -.270 and .940 < p.z < 1.160, dark, .007)
    add("SKV11_Forearm_R", lambda p: p.y < .035 and p.x > .270 and .940 < p.z < 1.160, dark, .007)
    add("SKV11_Thigh_L", lambda p: p.y < -.020 and p.x < -.035 and .610 < p.z < .835, dark, .006)
    add("SKV11_Thigh_R", lambda p: p.y < -.020 and p.x > .035 and .610 < p.z < .835, dark, .006)
    add("SKV11_Knee_L", lambda p: p.y < -.035 and p.x < -.035 and .475 < p.z <= .610)
    add("SKV11_Knee_R", lambda p: p.y < -.035 and p.x > .035 and .475 < p.z <= .610)
    add("SKV11_Shin_L", lambda p: p.y < -.020 and p.x < -.030 and .240 < p.z <= .475)
    add("SKV11_Shin_R", lambda p: p.y < -.020 and p.x > .030 and .240 < p.z <= .475)
    add("SKV11_Boot_L", lambda p: p.y < .040 and p.x < -.025 and .025 < p.z <= .220, dark, .007)
    add("SKV11_Boot_R", lambda p: p.y < .040 and p.x > .025 and .025 < p.z <= .220, dark, .007)

    # Helmet correction is retained, but no new floating collar primitives.
    helmet_changes = []
    for name, factor in {
        "SKV6_Helmet_ClearDome": (.84, .84, .90),
        "SKV6_Helmet_LowerPressureRing": (.80, .80, .72),
        "SKV6_Helmet_UpperIvoryRing": (.80, .80, .72),
        "SKV6_Helmet_LockBand": (.82, .82, .78),
        "SKV6_Helmet_InnerNeckGasket": (.86, .86, .84),
    }.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.scale = tuple(obj.scale[index] * factor[index] for index in range(3))
            obj["v11_conformal_review"] = "compacted"
            helmet_changes.append(name)

    base["asset_status"] = "ART_DIRECTION_REVIEW_V11_CONFORMAL_ARMOR"
    base["runtime_replacement"] = False
    base["rejected_studies"] = "V9 bulbous armor; V10 floating plate armor"
    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v11", "status": "conformal_armor_review",
        "hidden_primitive_collections": hidden_collections,
        "conformal_patch_count": len(patches),
        "patches": [{"name": obj.name, "vertices": obj["selected_vertex_count"]} for obj in patches],
        "helmet_changes": helmet_changes,
    }, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render(scene, bpy.data.objects["CAM_HighPolyReview"], [base, *patches])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V11_CONFORMAL_ARMOR", f"patches={len(patches)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
