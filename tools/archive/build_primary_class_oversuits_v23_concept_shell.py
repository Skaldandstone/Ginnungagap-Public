"""Build clean, realistic primary oversuits from the approved concept proportions.

This is a ground-up replacement for the rejected procedural blockouts. Geometry
is garment-first: continuous tailored textile shells, restrained hard points,
human-scale gloves and boots, a close helmet bubble, and role equipment.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
PREVIEW_DIR = ASSET_DIR / "Previews_v23"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v23"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v23_Manifest.json"

CLASSES = {
    "Marine": {"code": "MAR", "role": "Security", "fabric": (.028,.032,.038), "accent": (.38,.018,.014), "armor": (.16,.18,.20)},
    "Scientist": {"code": "SCI", "role": "Crew", "fabric": (.16,.17,.16), "accent": (.025,.12,.32), "armor": (.42,.41,.36)},
    "Technician": {"code": "TEC", "role": "Engineering", "fabric": (.025,.045,.065), "accent": (.46,.12,.025), "armor": (.18,.20,.21)},
    "Medical": {"code": "MED", "role": "Medical", "fabric": (.34,.35,.33), "accent": (.025,.18,.24), "armor": (.58,.57,.52)},
}


def mat(name, color, metallic=0.0, rough=.62, fabric=False, emission=None, alpha=1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*color, alpha)
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Transmission Weight"].default_value = .35
        material.surface_render_method = "DITHERED"
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    if fabric:
        noise = material.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 72
        noise.inputs["Detail"].default_value = 2.2
        noise.inputs["Roughness"].default_value = .72
        bump = material.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .16
        bump.inputs["Distance"].default_value = .06
        material.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        material.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material["oversuit_material"] = True
    material["concept_match_pass"] = 23
    return material


def finish(obj, material, rig, bone, component, cls):
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = True
    group = obj.vertex_groups.new(name=bone)
    group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
    modifier = obj.modifiers.new("V23_OversuitRig", "ARMATURE")
    modifier.object = rig
    obj["asset_layer"] = "oversuit"
    obj["oversuit_class"] = cls
    obj["wearer_independent"] = True
    obj["concept_match_pass"] = 23
    obj["construction"] = component
    obj["rig_attachment"] = bone
    obj["concept_reference"] = "docs/concept-art/reference/suits/player-suit-role-lineup.png"
    return obj


def loft(name, sections, material, rig, bone, component, cls, segments=24, cap=True):
    """Create a smooth elliptical garment around a path.

    sections: [(center, radius_x, radius_y)] where radius_x follows the global
    front/back axis and radius_y follows the path-perpendicular lateral axis.
    """
    vertices, faces = [], []
    centers = [Vector(item[0]) for item in sections]
    for index, (center, rx, ry) in enumerate(sections):
        center = Vector(center)
        if index == 0:
            tangent = centers[1] - center
        elif index == len(sections)-1:
            tangent = center - centers[index-1]
        else:
            tangent = centers[index+1] - centers[index-1]
        tangent.normalize()
        axis_x = Vector((1,0,0))
        axis_x -= tangent * axis_x.dot(tangent)
        if axis_x.length < .01:
            axis_x = Vector((0,1,0))
        axis_x.normalize()
        axis_y = tangent.cross(axis_x).normalized()
        for step in range(segments):
            angle = math.tau * step / segments
            vertices.append(center + axis_x*(math.cos(angle)*rx) + axis_y*(math.sin(angle)*ry))
    for ring in range(len(sections)-1):
        for step in range(segments):
            nxt = (step+1) % segments
            a, b = ring*segments+step, ring*segments+nxt
            c, d = (ring+1)*segments+nxt, (ring+1)*segments+step
            faces.append((a,b,c,d))
    if cap:
        faces.append(tuple(range(segments-1,-1,-1)))
        last = (len(sections)-1)*segments
        faces.append(tuple(last+i for i in range(segments)))
    mesh = bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bevel = obj.modifiers.new("V23_SoftConstructionEdge", "BEVEL")
    bevel.width = .18
    bevel.segments = 2
    return finish(obj, material, rig, bone, component, cls)


def rounded_box(name, location, scale, material, rig, bone, component, cls, bevel=.8, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new("V23_RoundedHardware", "BEVEL")
    mod.width, mod.segments = bevel, 3
    return finish(obj, material, rig, bone, component, cls)


def torus(name, location, major, minor, material, rig, bone, component, cls, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64,
                                    minor_segments=12, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, rig, bone, component, cls)


def tube(name, points, radius, material, rig, bone, component, cls):
    curve = bpy.data.curves.new(name+"_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for node, point in zip(spline.bezier_points, points):
        node.co = point
        node.handle_left_type = node.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return finish(bpy.context.object, material, rig, bone, component, cls)


def sphere(name, location, scale, material, rig, bone, component, cls, segments=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, rig, bone, component, cls)


def create_rig(cls):
    data = bpy.data.armatures.new(f"SK_OVR23_{cls}_Skeleton")
    rig = bpy.data.objects.new(f"SK_OVR23_{cls}", data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    def bone(name, head, tail, parent=None):
        b = data.edit_bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = data.edit_bones.get(parent)
        return b
    bone("root", (0,0,0), (0,0,8))
    bone("pelvis", (0,0,68), (0,0,78), "root")
    bone("spine_01", (0,0,78), (0,0,94), "pelvis")
    bone("spine_02", (0,0,94), (0,0,112), "spine_01")
    bone("spine_03", (0,0,112), (0,0,130), "spine_02")
    bone("neck_01", (0,0,130), (0,0,140), "spine_03")
    bone("head", (0,0,140), (0,0,166), "neck_01")
    for side, sy in (("l",1),("r",-1)):
        bone(f"clavicle_{side}", (0,0,124), (0,sy*21,121), "spine_03")
        bone(f"upperarm_{side}", (0,sy*21,121), (0,sy*36,98), f"clavicle_{side}")
        bone(f"lowerarm_{side}", (0,sy*36,98), (1,sy*41,76), f"upperarm_{side}")
        bone(f"hand_{side}", (1,sy*41,76), (3,sy*42,66), f"lowerarm_{side}")
        bone(f"thigh_{side}", (0,sy*10,68), (0,sy*12,43), "pelvis")
        bone(f"calf_{side}", (0,sy*12,43), (1,sy*12,17), f"thigh_{side}")
        bone(f"foot_{side}", (1,sy*12,17), (14,sy*12,7), f"calf_{side}")
    bone("ik_hand_gun", (0,0,85), (0,0,95), "root")
    bpy.ops.object.mode_set(mode="OBJECT")
    rig["asset_layer"] = "oversuit"
    rig["wearer_independent"] = True
    rig["concept_match_pass"] = 23
    return rig


def build_common(cls, spec, rig, mats):
    p = f"OVR23_{spec['code']}"
    parts = []
    # Continuous textile pressure envelope, proportioned to the approved turnaround.
    parts.append(loft(p+"_Torso", [
        ((0,0,67),8.8,13.3), ((0,0,76),9.0,14.4), ((0,0,86),8.3,14.2),
        ((0,0,98),8.9,15.3), ((0,0,111),10.0,17.3), ((0,0,122),9.5,18.2),
        ((0,0,130),7.6,14.0)], mats["fabric"], rig, "spine_02", "continuous_textile_torso", cls))
    for side, sy in (("L",1),("R",-1)):
        limb = side.lower()
        parts.append(loft(f"{p}_UpperArm_{side}", [
            ((0,sy*20.0,121),6.2,6.5), ((0,sy*27.5,113),5.8,6.0),
            ((0,sy*34.5,100),5.1,5.2), ((0,sy*36.5,95),4.9,5.0)],
            mats["fabric"], rig, f"upperarm_{limb}", "tailored_textile_sleeve", cls))
        parts.append(loft(f"{p}_Forearm_{side}", [
            ((0,sy*36.5,95),4.8,5.0), ((.5,sy*39.0,85),4.5,4.7),
            ((1,sy*41.0,74),3.8,4.1)], mats["fabric"], rig, f"lowerarm_{limb}", "tailored_textile_sleeve", cls))
        parts.append(loft(f"{p}_Thigh_{side}", [
            ((0,sy*10.0,68),7.7,7.7), ((0,sy*10.8,58),7.2,7.0),
            ((0,sy*11.8,45),6.2,6.2), ((0,sy*12.0,41),6.0,6.0)],
            mats["fabric"], rig, f"thigh_{limb}", "tailored_textile_leg", cls))
        parts.append(loft(f"{p}_Calf_{side}", [
            ((0,sy*12.0,41),6.0,6.0), ((.4,sy*12.0,32),6.3,6.0),
            ((.8,sy*12.0,21),5.2,5.1), ((1,sy*12.0,14),4.7,4.8)],
            mats["fabric"], rig, f"calf_{limb}", "tailored_textile_leg", cls))
        # Human-scale glove and articulated fingers.
        parts.append(loft(f"{p}_GlovePalm_{side}", [
            ((1,sy*41.2,75),3.7,4.2), ((2,sy*41.7,69),3.5,4.0), ((3,sy*41.7,66),3.1,3.7)],
            mats["glove"], rig, f"hand_{limb}", "pressure_glove", cls, 20))
        for finger in range(5):
            lateral = (finger-2)*1.25
            y = sy*(41.5+lateral)
            x = 3.2 + (1.0 if finger == 0 else 0)
            parts.append(loft(f"{p}_GloveFinger_{side}_{finger}", [
                ((x,y,65.8),.62,.66), ((x+.8,y+sy*.15,63.7),.52,.55),
                ((x+1.25,y+sy*.20,62.2),.40,.43)], mats["glove"], rig,
                f"hand_{limb}", "articulated_pressure_glove", cls, 12))
        # Rugged boot as a continuous longitudinal loft, not stacked spheres.
        parts.append(loft(f"{p}_Boot_{side}", [
            ((-3,sy*12,7.5),5.2,5.7), ((2,sy*12,7.0),6.0,6.2),
            ((8,sy*12,6.2),6.1,5.4), ((15,sy*12,5.3),5.4,4.2),
            ((18,sy*12,4.8),4.1,3.2)], mats["boot"], rig, f"foot_{limb}",
            "rugged_magnetic_boot", cls, 24))
        parts.append(rounded_box(f"{p}_Sole_{side}", (7,sy*12,.9), (11.5,6.3,.8),
                                 mats["sole"], rig, f"foot_{limb}", "segmented_magnetic_sole", cls, .55))
        # Restrained protective hard points.
        parts.append(rounded_box(f"{p}_KneePad_{side}", (5.7,sy*12,42), (1.45,5.1,5.3),
                                 mats["armor"], rig, f"calf_{limb}", "low_profile_knee_pad", cls, 1.25))
        parts.append(rounded_box(f"{p}_ShinPlate_{side}", (5.1,sy*12,25), (1.15,4.5,7.2),
                                 mats["armor"], rig, f"calf_{limb}", "low_profile_shin_plate", cls, 1.1))
        parts.append(rounded_box(f"{p}_ForearmGuard_{side}", (5.1,sy*40,83), (1.0,4.0,7.2),
                                 mats["armor"], rig, f"lowerarm_{limb}", "slim_forearm_guard", cls, 1.0))
        # Trouser/sleeve seams kept close to the cloth surface.
        tube(f"{p}_OuterLegSeam_{side}", [(4.9,sy*16.7,64),(5.0,sy*17.0,51),(4.3,sy*16.2,35),(3.8,sy*15.8,18)],
             .16, mats["seam"], rig, f"thigh_{limb}", "stitched_textile_seam", cls)

    # Helmet: close bubble, two-part neck bearing, rear shell and restrained comms.
    parts.append(sphere(p+"_VisorBubble", (1.8,0,151), (13.2,13.6,16.2), mats["visor"], rig, "head", "sealed_clear_visor", cls))
    parts.append(sphere(p+"_HelmetLiner", (-5.7,0,151), (5.4,12.6,15.2), mats["liner"], rig, "head", "rear_helmet_shell", cls))
    parts.append(torus(p+"_HelmetBearing", (0,0,135.2), 13.7, 1.15, mats["armor"], rig, "neck_01", "helmet_bearing", cls))
    parts.append(torus(p+"_NeckSeal", (0,0,132.5), 12.8, 1.25, mats["gasket"], rig, "neck_01", "pressure_neck_seal", cls))
    for sy, label in ((1,"L"),(-1,"R")):
        parts.append(rounded_box(f"{p}_HelmetComms_{label}", (-2,sy*13.1,151), (2.4,1.1,4.5),
                                 mats["armor"], rig, "head", "helmet_comms_housing", cls, .8))
    # Chest interface and pack match the turnaround's restrained industrial framing.
    parts.append(rounded_box(p+"_ChestFrame", (10.8,0,111), (1.45,10.0,9.0), mats["armor"], rig,
                             "spine_03", "low_profile_chest_frame", cls, 1.2))
    parts.append(rounded_box(p+"_ChestDisplay", (12.45,0,112), (.28,6.5,4.6), mats["display"], rig,
                             "spine_03", "recessed_chest_display", cls, .4))
    parts.append(rounded_box(p+"_LifeSupportPack", (-13.0,0,107), (5.5,13.5,21), mats["armor"], rig,
                             "spine_03", "compact_life_support_pack", cls, 2.0))
    for sy, label in ((1,"L"),(-1,"R")):
        tube(f"{p}_BreathingHose_{label}", [(-2,sy*11.5,137),(-8,sy*16,129),(-14,sy*14,116)],
             .9, mats["gasket"], rig, "spine_03", "corrugated_breathing_hose", cls)
        tube(f"{p}_Harness_{label}", [(10.0,sy*12,123),(10.4,sy*10.5,103),(8.5,sy*13,80)],
             .75, mats["webbing"], rig, "spine_03", "load_bearing_webbing", cls)
    parts.append(torus(p+"_UtilityBelt", (0,0,77), 16.0, 1.35, mats["webbing"], rig, "pelvis", "utility_belt", cls))
    parts.append(rounded_box(p+"_BeltBuckle", (9.5,0,77), (1.0,3.0,2.4), mats["metal"], rig,
                             "pelvis", "quick_release_buckle", cls, .6))
    return parts


def add_role_modules(cls, spec, rig, mats):
    p = f"OVR23_{spec['code']}"
    parts = []
    if cls == "Marine":
        for y in (-7,0,7):
            parts.append(rounded_box(f"{p}_SecurityPouch_{y}", (12.5,y,99), (1.5,2.7,4.2), mats["accent"], rig, "spine_02", "security_magazine_pouch", cls, .65))
        parts.append(rounded_box(p+"_SecurityShoulderID", (3.5,-22.5,119), (1.0,4.3,3.8), mats["accent"], rig, "upperarm_r", "security_role_id", cls, .8))
    elif cls == "Scientist":
        parts.append(rounded_box(p+"_SurveyTerminal", (5.8,39.8,84), (1.1,3.7,6.0), mats["accent"], rig, "lowerarm_l", "survey_terminal", cls, .8))
        for y in (-7,7):
            parts.append(rounded_box(f"{p}_SampleCase_{y}", (7.0,y,72), (2.4,4.2,4.8), mats["armor"], rig, "pelvis", "sample_case", cls, .9))
    elif cls == "Technician":
        parts.append(rounded_box(p+"_DiagnosticTerminal", (5.8,39.8,84), (1.1,3.8,6.2), mats["accent"], rig, "lowerarm_l", "engineering_diagnostic_terminal", cls, .8))
        tube(p+"_ToolTether", [(8,-13,79),(12,-18,67),(8,-20,57)], .45, mats["accent"], rig, "pelvis", "tool_tether", cls)
        parts.append(rounded_box(p+"_ToolPouch", (5.0,-19,63), (3.2,3.3,6.0), mats["armor"], rig, "pelvis", "engineering_tool_pouch", cls, .9))
    else:
        parts.append(rounded_box(p+"_TraumaPouch", (12.0,0,98), (1.5,6.3,5.1), mats["armor"], rig, "spine_02", "medical_trauma_pouch", cls, .8))
        # Medical cross made from two flush plates.
        parts.append(rounded_box(p+"_MedicalCrossV", (13.6,0,99), (.25,1.0,3.2), mats["accent"], rig, "spine_02", "medical_role_mark", cls, .2))
        parts.append(rounded_box(p+"_MedicalCrossH", (13.6,0,99), (.25,3.2,1.0), mats["accent"], rig, "spine_02", "medical_role_mark", cls, .2))
        parts.append(rounded_box(p+"_BioMonitor", (5.8,39.8,84), (1.1,3.7,6.0), mats["accent"], rig, "lowerarm_l", "biometric_monitor", cls, .8))
    return parts


def add_interfaces(code, rig):
    specs = (("Helmet",(0,0,140),"head",80),("Collar",(0,0,132),"neck_01",70),
             ("Backpack",(-14,0,108),"spine_03",60),("Wrist_L",(1,41,74),"hand_l",40),
             ("Wrist_R",(1,-41,74),"hand_r",40),("Waist",(0,0,77),"pelvis",50),
             ("Boot_L",(2,12,13),"foot_l",20),("Boot_R",(2,-12,13),"foot_r",20))
    result=[]
    for label,loc,bone,stage in specs:
        obj=bpy.data.objects.new(f"IF_OVR23_{code}_{label}",None)
        bpy.context.scene.collection.objects.link(obj); obj.location=loc
        obj.parent=rig; obj.parent_type="BONE"; obj.parent_bone=bone
        obj["asset_layer"]="oversuit_interface"; obj["donning_stage"]=stage; obj["wearer_independent"]=True
        result.append(obj)
    return result


def setup_render():
    scene=bpy.context.scene
    world=bpy.data.worlds.new("V23_StudioWorld"); scene.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.012,.016,.022,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.18
    floor_mat=mat("V23_Floor",(.025,.030,.038),rough=.82)
    bpy.ops.mesh.primitive_plane_add(size=600,location=(0,0,0)); floor=bpy.context.object; floor.name="PREVIEW_Floor"; floor.data.materials.append(floor_mat)
    for name,loc,energy,size,color in (("Key",(220,-160,220),1_300_000,120,(1,.80,.65)),("Fill",(170,190,140),800_000,100,(.55,.72,1)),("Rim",(-140,-100,190),1_000_000,90,(.35,.58,1))):
        ld=bpy.data.lights.new(name,"AREA"); ld.energy=energy; ld.size=size; ld.color=color
        ob=bpy.data.objects.new(name,ld); scene.collection.objects.link(ob); ob.location=loc
        ob.rotation_euler=(Vector((0,0,90))-ob.location).to_track_quat("-Z","Y").to_euler()
    cd=bpy.data.cameras.new("V23_Camera"); camera=bpy.data.objects.new("V23_Camera",cd); scene.collection.objects.link(camera); cd.lens=58; scene.camera=camera
    scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=900; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"; scene.view_settings.exposure=.35
    return camera


def render_views(cls,camera):
    PREVIEW_DIR.mkdir(parents=True,exist_ok=True)
    views={"Front":((330,0,96),(0,0,86)),"ThreeQuarter":((280,-205,105),(0,0,86)),"Rear":((-330,0,98),(-3,0,87)),"Profile":((0,-345,98),(0,0,86))}
    output={}
    for label,(loc,target) in views.items():
        camera.location=loc; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
        path=PREVIEW_DIR/f"PlayerOversuit_{cls}_v23_{label}.png"; bpy.context.scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
        output[label]=str(path.relative_to(ROOT)).replace("\\","/")
    return output


def export(path,rig,meshes,interfaces):
    bpy.ops.object.select_all(action="DESELECT"); rig.select_set(True)
    for obj in meshes+interfaces: obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={"ARMATURE","MESH","EMPTY"},add_leaf_bones=False,bake_anim=False,mesh_smooth_type="FACE",axis_forward="-Y",axis_up="Z")


def build(cls,spec):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.preferences.filepaths.save_version=0
    rig=create_rig(cls)
    mats={"fabric":mat(f"M_OVR23_{cls}_Fabric",spec["fabric"],rough=.78,fabric=True),"accent":mat(f"M_OVR23_{cls}_Accent",spec["accent"],metallic=.12,rough=.48),"armor":mat(f"M_OVR23_{cls}_Armor",spec["armor"],metallic=.35,rough=.46),"glove":mat(f"M_OVR23_{cls}_Glove",(.018,.022,.026),rough=.64,fabric=True),"boot":mat(f"M_OVR23_{cls}_Boot",(.025,.030,.034),rough=.58),"sole":mat(f"M_OVR23_{cls}_Sole",(.012,.015,.018),metallic=.55,rough=.42),"seam":mat(f"M_OVR23_{cls}_Seam",(.018,.021,.024),rough=.72),"visor":mat(f"M_OVR23_{cls}_Visor",(.055,.085,.105),metallic=.08,rough=.12,alpha=.24),"liner":mat(f"M_OVR23_{cls}_HelmetShell",spec["armor"],metallic=.25,rough=.45),"gasket":mat(f"M_OVR23_{cls}_Gasket",(.012,.014,.016),rough=.82),"webbing":mat(f"M_OVR23_{cls}_Webbing",(.018,.022,.026),rough=.84,fabric=True),"metal":mat(f"M_OVR23_{cls}_Metal",(.16,.17,.17),metallic=.78,rough=.38),"display":mat(f"M_OVR23_{cls}_Display",(.015,.12,.18),metallic=.18,rough=.18,emission=(.02,.30,.52))}
    build_common(cls,spec,rig,mats); add_role_modules(cls,spec,rig,mats); interfaces=add_interfaces(spec["code"],rig)
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.get("asset_layer")=="oversuit"]
    rig["oversuit_class"]=cls; rig["role_alias"]=spec["role"]; rig["concept_match_pass"]=23; rig["mesh_count"]=len(meshes)
    camera=setup_render(); previews=render_views(cls,camera)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("PREVIEW_") or obj.type in {"CAMERA","LIGHT"}: bpy.data.objects.remove(obj,do_unlink=True)
    ASSET_DIR.mkdir(parents=True,exist_ok=True); EXPORT_DIR.mkdir(parents=True,exist_ok=True)
    blend=ASSET_DIR/f"PlayerOversuit_{cls}_v23.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    fbx=EXPORT_DIR/f"SKM_PlayerOversuit_{cls}_v23.fbx"; export(fbx,rig,meshes,interfaces); bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    return {"class":cls,"role_alias":spec["role"],"blend":str(blend.relative_to(ROOT)).replace("\\","/"),"fbx":str(fbx.relative_to(ROOT)).replace("\\","/"),"mesh_count":len(meshes),"interface_count":len(interfaces),"previews":previews}


entries=[build(cls,spec) for cls,spec in CLASSES.items()]
MANIFEST.write_text(json.dumps({"schema":1,"asset":"PrimaryOversuits_v23","status":"concept_shell_rebuild","supersedes":"PrimaryOversuits_v21 and rejected V22 extraction","references":["docs/concept-art/reference/suits/standard-suit-turnaround.png","docs/concept-art/reference/suits/player-suit-role-lineup.png"],"classes":entries},indent=2),encoding="utf-8")
print(f"PRIMARY_OVERSUITS_V23 classes={len(entries)} {MANIFEST}")
