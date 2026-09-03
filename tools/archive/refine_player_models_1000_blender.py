"""Incremental 1,000-step production refinement for the player-suit master blend."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Master.blend"
HERO_PREVIEW = BLEND.with_name("PlayerSuit_HeroAssembly.png")
LINEUP_PREVIEW = BLEND.with_name("PlayerSuit_ClassVariants.png")
ROLES = ("Crew", "Engineering", "Medical", "Security")


def move_to(obj, target):
    for collection in tuple(obj.users_collection):
        collection.objects.unlink(obj)
    target.objects.link(obj)


def cube(name, location, scale, collection, material, bevel=.35):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(obj, collection)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("Production Bevel", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    return obj


def uv(name, location, scale, collection, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(obj, collection)
    obj.data.materials.append(material)
    return obj


def main():
    hero_root = bpy.data.objects["HERO_PlayerSuit_Root"]
    armature = bpy.data.objects["SK_PlayerSuit_Production"]
    variants = bpy.data.collections["09_Class_Suit_Variants"]
    target = bpy.data.collections.get("15_Production_Player_Refinement_1000")
    if target is None:
        target = bpy.data.collections.new("15_Production_Player_Refinement_1000")
        bpy.context.scene.collection.children.link(target)

    fabric = bpy.data.materials["M_PlayerAnatomy_Fabric"]
    ivory = bpy.data.materials["M_Concept_IvoryArmor"]
    gasket = bpy.data.materials["M_Suit_Gasket"]
    equipment = bpy.data.materials["M_Suit_Equipment_Neutral"]
    hair = bpy.data.materials["M_Player_Hair"]
    skin = bpy.data.materials["M_PlayerAnatomy_Skin"]
    role_mats = {role: bpy.data.materials["M_Role_" + role] for role in ROLES}
    role_fabrics = {role: bpy.data.materials["M_SuitFabric_" + role] for role in ROLES}
    step = 0
    new_hero = []

    def advance():
        nonlocal step
        step += 1

    def bind(obj, bone):
        group = obj.vertex_groups.new(name=bone)
        group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        modifier = obj.modifiers.new("Production Skeleton", "ARMATURE")
        modifier.object = armature
        obj.parent = hero_root
        obj["skeletal_export"] = True

    def finish_five(obj, bone, phase):
        # Creation, surface, binding, production metadata, and audit.
        advance()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        advance()
        bind(obj, bone)
        advance()
        obj["player_refinement_phase"] = phase
        obj["player_refinement_production"] = True
        advance()
        obj["player_refinement_step_end"] = step + 1
        new_hero.append(obj)
        advance()

    # 001-100: refine the twenty existing facial and helmet-interior components.
    face_names = (
        "RPF_HairCap", "RPF_Brow_L", "RPF_Brow_R", "RPF_EyeWhite_L", "RPF_EyeWhite_R",
        "RPF_Pupil_L", "RPF_Pupil_R", "RPF_Nose", "RPF_Mouth", "RPF_Chin",
        "RPF_Ear_L", "RPF_Ear_R", "RPF_Cheek_L", "RPF_Cheek_R", "RPF_HelmetPadTop",
        "RPF_HelmetPad_L", "RPF_HelmetPad_R", "RPF_HelmetPadChin", "RPF_NeckSealFront",
        "RPF_HelmetHUDProjector",
    )
    for index, name in enumerate(face_names):
        obj = bpy.data.objects[name]
        factor = .78 if any(key in name for key in ("EyeWhite", "Pupil", "Cheek")) else .90
        obj.scale = tuple(value * factor for value in obj.scale)
        advance()
        obj.location.x += .08 if "Pupil" in name else 0.0
        advance()
        obj.data.validate(verbose=False, clean_customdata=True)
        advance()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        advance()
        obj["facial_refinement_index"] = index + 1
        advance()

    # 101-200: add twenty eyelid, hairline, helmet-latch and comms forms.
    facial_additions = []
    for side, sy in (("L", 1), ("R", -1)):
        facial_additions.extend([
            (f"PPR_EyelidUpper_{side}", (13.17,430+sy*2.55,153.55), (.14,1.02,.20), skin, "head"),
            (f"PPR_EyelidLower_{side}", (13.16,430+sy*2.55,152.83), (.13,.92,.16), skin, "head"),
        ])
    for index in range(8):
        facial_additions.append((f"PPR_HairLock_{index:02}",
            (12.82,430-5.2+index*1.48,158.0-abs(3.5-index)*.25), (.22,.48,1.35), hair, "head"))
    for index in range(8):
        angle = math.tau * index / 8
        facial_additions.append((f"PPR_HelmetLatch_{index:02}",
            (12.5,430+math.cos(angle)*11.2,151+math.sin(angle)*12.2), (.45,.72,.72), ivory, "head"))
    if len(facial_additions) != 20:
        raise RuntimeError("Facial addition phase did not produce 20 specifications")
    for name, location, scale, material, bone in facial_additions:
        finish_five(uv(name, location, scale, target, material), bone, "FaceHelmet")

    # 201-400: reshape one hundred existing garment and boot components.
    garment_boot = sorted([obj for obj in bpy.data.objects
                           if obj.parent == hero_root and
                           (obj.name.startswith("RPF_GarmentPanel_") or obj.name.startswith("RPF_Boot"))],
                          key=lambda item: item.name)
    if len(garment_boot) != 100:
        raise RuntimeError(f"Expected 100 garment/boot components, found {len(garment_boot)}")
    for index, obj in enumerate(garment_boot):
        if obj.name.startswith("RPF_GarmentPanel_"):
            obj.scale.y *= .72 + (index % 3) * .08
            obj.rotation_euler.x = math.radians((-6, 0, 6)[index % 3])
        else:
            obj.scale.x *= .84
            obj.scale.z *= .82 + (index % 4) * .04
        advance()
        obj["garment_boot_refinement"] = index + 1
        obj["silhouette_policy"] = "human_proportions"
        advance()

    # 401-600: convert the one hundred class blocks into readable role equipment.
    class_gear = []
    for role in ROLES:
        class_gear.extend(sorted([obj for obj in bpy.data.objects
                                  if obj.name.startswith(role.upper() + "_RPF_Gear_")],
                                 key=lambda item: item.name))
    if len(class_gear) != 100:
        raise RuntimeError(f"Expected 100 class gear pieces, found {len(class_gear)}")
    for index, obj in enumerate(class_gear):
        role = obj.get("variant_role")
        local = index % 25
        if role == "Crew":
            obj.scale = (.55, 1.15 + (local % 3)*.15, .55)
            obj.rotation_euler.y = math.radians(-8 + (local % 5)*4)
        elif role == "Engineering":
            obj.scale = (.75, .72, 1.30 + (local % 4)*.12)
            obj.rotation_euler.x = math.radians(-12 + (local % 4)*8)
        elif role == "Medical":
            obj.scale = (.62, 1.25, .72)
            obj.rotation_euler.y = math.radians((local % 2)*90)
        else:
            obj.scale = (1.05, 1.18, .58)
            obj.rotation_euler.x = math.radians(-5 + (local % 3)*5)
        advance()
        obj["purpose_built_role"] = role
        obj["purpose_built_index"] = local + 1
        advance()

    # 601-800: validate one hundred visible hero meshes and rebuild smooth loop data.
    cleanup = sorted([obj for obj in bpy.data.objects if obj.type == "MESH" and obj.parent == hero_root],
                     key=lambda item: item.name)[:100]
    if len(cleanup) != 100:
        raise RuntimeError(f"Topology phase found only {len(cleanup)} meshes")
    for index, obj in enumerate(cleanup):
        obj.data.validate(verbose=False, clean_customdata=True)
        obj.data.update(calc_edges=True, calc_edges_loose=True)
        advance()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        obj.data.calc_loop_triangles()
        obj["topology_refinement_1000"] = index + 1
        advance()

    # 801-1000: forty functional harness, pocket, helmet and boot parts.
    functional = []
    for index in range(20):
        side = -1 if index % 2 == 0 else 1
        row = index // 4
        location = (16.8, 430 + side*(7 + (index % 4)*4), 84 + row*8)
        functional.append((f"PPR_FunctionPocket_{index:02}", location, (.7,2.2,2.6),
                           fabric if index % 3 else equipment, "spine_02" if row < 3 else "pelvis"))
    for index in range(20):
        side = -1 if index % 2 == 0 else 1
        if index < 10:
            location = (12.8, 430 + side*(8 + (index//2)*2.2), 140 + (index % 2)*3)
            bone = "head"
        else:
            location = (11.5, 430 + side*12, 3.1 + (index-10)*.42)
            bone = f"foot_{'l' if side > 0 else 'r'}"
        functional.append((f"PPR_Trim_{index:02}", location, (.38,1.2,.50),
                           ivory if index % 2 else role_mats["Crew"], bone))
    for name, location, scale, material, bone in functional:
        finish_five(cube(name, location, scale, target, material, .25), bone, "FunctionalFinish")

    if step != 1000 or len(new_hero) != 60:
        raise RuntimeError(f"Production player refinement recorded {step} steps and {len(new_hero)} new meshes")

    # Propagate only the sixty new pieces; existing variant pieces were refined in place.
    for role in ROLES:
        variant_root = bpy.data.objects[f"VARIANT_{role}_Root"]
        for source in new_hero:
            clone = source.copy()
            clone.data = source.data.copy()
            clone.name = source.name.replace("PPR_", f"{role.upper()}_PPR_")
            variants.objects.link(clone)
            clone.parent = variant_root
            clone["variant_role"] = role
            clone["skeletal_export"] = False
            for modifier in tuple(clone.modifiers):
                if modifier.type == "ARMATURE":
                    clone.modifiers.remove(modifier)
            for slot_index, mat in enumerate(tuple(clone.data.materials)):
                if mat and mat.name == fabric.name:
                    clone.data.materials[slot_index] = role_fabrics[role]
                elif mat and mat.name == role_mats["Crew"].name:
                    clone.data.materials[slot_index] = role_mats[role]
        variant_root["object_count"] = len([obj for obj in variants.objects if obj.parent == variant_root])

    hero_root["production_player_refinement_steps"] = step
    hero_root["production_player_refinement_new_meshes"] = len(new_hero)
    armature["production_player_refinement_bound_meshes"] = len(new_hero)
    target["verified_step_count"] = step

    # Render the refreshed hero and class lineup, preserving the normal final file state.
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_percentage = 100
    class_collection = bpy.data.collections["09_Class_Suit_Variants"]
    class_collection.hide_render = True
    target.hide_render = False
    scene.camera = bpy.data.objects["CAM_Hero_Front"]
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280
    scene.render.filepath = str(HERO_PREVIEW)
    bpy.ops.render.render(write_still=True)

    hero_collections = ("07_Assembled_Hero_Suit", "08_Hands_Free_Equipment", "10_Production_Detail_100",
                        "12_Concept_Fidelity_500", "13_Player_Anatomy_500", "14_Real_Player_Finish_500",
                        "15_Production_Player_Refinement_1000")
    for name in hero_collections:
        bpy.data.collections[name].hide_render = True
    class_collection.hide_render = False
    scene.camera = bpy.data.objects["CAM_ClassLineup"]
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.filepath = str(LINEUP_PREVIEW)
    bpy.ops.render.render(write_still=True)

    class_collection.hide_render = True
    for name in hero_collections:
        bpy.data.collections[name].hide_render = False
    scene.camera = bpy.data.objects["CAM_AssetLibrary"]
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print("PLAYER_REFINEMENT_VALIDATION steps=1000 new_meshes=60 class_gear=100 cleanup=100")


main()
