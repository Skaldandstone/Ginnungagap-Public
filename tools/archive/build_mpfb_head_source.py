"""Build a higher-quality local human source for the player-suit head.

MPFB is loaded from an explicitly supplied extracted package directory.  The
resulting .blend is self-contained and does not require the add-on at runtime.
"""

import os
import sys
from math import radians

import bpy
import bmesh
from mathutils import Vector


MPFB_ROOT = os.environ.get("GINNUNGAGAP_MPFB_ROOT")
if not MPFB_ROOT or not os.path.isdir(MPFB_ROOT):
    raise RuntimeError("GINNUNGAGAP_MPFB_ROOT must point to the folder containing mpfb")

sys.path.insert(0, MPFB_ROOT)
# MPFB normally runs as a Blender extension.  For this head-source build we only
# need its data/services, so provide a project-local extension user directory
# while importing instead of permanently installing the UI extension.
_extension_path_user = bpy.utils.extension_path_user
bpy.utils.extension_path_user = lambda _package, create=False: os.path.join(MPFB_ROOT, ".user")
os.makedirs(os.path.join(MPFB_ROOT, ".user"), exist_ok=True)
import mpfb  # noqa: E402
mpfb.MPFB_CONTEXTUAL_INFORMATION = {
    "__package__": "mpfb",
    "__package_short__": "mpfb",
    "__file__": mpfb.__file__,
}
mpfb.get_preference = lambda _name: None
from mpfb._classmanager import ClassManager as _MpfbClassManager  # noqa: E402
mpfb.ClassManager = _MpfbClassManager
if not _MpfbClassManager.isinitialized():
    _MpfbClassManager()
from mpfb.services import HumanService, TargetService  # noqa: E402
bpy.utils.extension_path_user = _extension_path_user

MH_ASSET_ROOT = os.environ.get("GINNUNGAGAP_MH_ASSET_ROOT")


def clear_scene():
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def make_principled(name, base_color, roughness=0.45, metallic=0.0, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    return mat


def make_skin_material():
    mat = bpy.data.materials.new("M_PlayerHead_Skin")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = 32.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.62
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (0.085, 0.015, 0.006, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.285, 0.078, 0.030, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.46
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.085
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.20)
    bump.inputs["Strength"].default_value = 0.11
    bump.inputs["Distance"].default_value = 0.0018
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def add_uv_sphere(name, location, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


clear_scene()

macro = TargetService.get_default_macro_info_dict()
macro.update(
    {
        "gender": 0.10,
        "age": 0.43,
        "muscle": 0.42,
        "weight": 0.46,
        "proportions": 0.53,
        "height": 0.53,
        "cupsize": 0.44,
        "firmness": 0.58,
    }
)
macro["race"] = {"asian": 0.08, "caucasian": 0.84, "african": 0.08}

human = HumanService.create_human(
    mask_helpers=True,
    detailed_helpers=True,
    extra_vertex_groups=True,
    feet_on_ground=True,
    scale=0.1,
    macro_detail_dict=macro,
)
human.name = "SRC_PlayerHead_MakeHuman"

# Keep topology and shape keys intact while assigning the official CC0 skin
# atlas when available.  The procedural material remains a deterministic
# fallback for machines without the asset pack.
skin_mhmat = None
if MH_ASSET_ROOT:
    candidate = os.path.join(
        MH_ASSET_ROOT,
        "skins",
        "young_caucasian_female",
        "young_caucasian_female.mhmat",
    )
    if os.path.isfile(candidate):
        skin_mhmat = candidate

if skin_mhmat:
    HumanService.set_character_skin(skin_mhmat, human, skin_type="MAKESKIN", material_instances=True)
    print("USING_CC0_SKIN", skin_mhmat)
else:
    skin = make_skin_material()
    human.data.materials.clear()
    human.data.materials.append(skin)
    for poly in human.data.polygons:
        poly.material_index = 0
    lips = make_principled("M_PlayerHead_Lips", (0.27, 0.045, 0.028), roughness=0.44, subsurface=0.04)
    human.data.materials.append(lips)
    lips_group = human.vertex_groups.get("lips")
    if lips_group:
        lip_indices = {
            vert.index
            for vert in human.data.vertices
            if any(member.group == lips_group.index and member.weight > 0.001 for member in vert.groups)
        }
        for poly in human.data.polygons:
            if sum(vertex in lip_indices for vertex in poly.vertices) >= max(2, len(poly.vertices) - 1):
                poly.material_index = 1
for poly in human.data.polygons:
    poly.use_smooth = True

subd = human.modifiers.new("Face_Render_Subdivision", "SUBSURF")
subd.levels = 1
subd.render_levels = 2

corners = [human.matrix_world @ Vector(corner) for corner in human.bound_box]
mins = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
maxs = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
print("HUMAN_BOUNDS", tuple(mins), tuple(maxs), "VERTS", len(human.data.vertices), "POLYS", len(human.data.polygons))

# Restore the hidden eye helpers as clean renderable eyeballs.  The centers are
# read from MPFB's rig-joint vertex groups so this stays stable if the macro
# phenotype changes.
def group_center(group_name):
    group = human.vertex_groups[group_name]
    coords = []
    shape_keys = human.data.shape_keys.key_blocks if human.data.shape_keys else None
    for vert in human.data.vertices:
        if any(member.group == group.index and member.weight > 0.001 for member in vert.groups):
            if shape_keys:
                basis = shape_keys[0].data[vert.index].co
                co = basis.copy()
                for key in shape_keys[1:]:
                    if abs(key.value) > 1.0e-6:
                        co += (key.data[vert.index].co - basis) * key.value
            else:
                co = vert.co
            coords.append(human.matrix_world @ co)
    return sum(coords, Vector()) / len(coords)


eye_white = make_principled("M_PlayerHead_EyeWhite", (0.62, 0.56, 0.48), roughness=0.19)
iris = make_principled("M_PlayerHead_IrisHazel", (0.12, 0.045, 0.012), roughness=0.24)
pupil = make_principled("M_PlayerHead_Pupil", (0.002, 0.0015, 0.001, 1.0)[:3], roughness=0.16)
eye_centers = {}
for side in ("l", "r"):
    center = group_center(f"joint-{side}-eye")
    eye_centers[side] = center
    add_uv_sphere(f"HEAD_Eye_{side.upper()}", center, (0.01375, 0.01375, 0.01375), eye_white)
    iris_center = center + Vector((0.0, -0.01325, 0.0))
    add_uv_sphere(f"HEAD_Iris_{side.upper()}", iris_center, (0.00485, 0.00165, 0.00485), iris)
    pupil_center = center + Vector((0.0, -0.01465, 0.0))
    add_uv_sphere(f"HEAD_Pupil_{side.upper()}", pupil_center, (0.00205, 0.00075, 0.00205), pupil)

# A restrained, helmet-friendly hairstyle.  Prefer the official short02 CC0
# mesh and texture, with a conforming cap as an offline fallback.
eyes_mid = (eye_centers["l"] + eye_centers["r"]) * 0.5
hair_object = None
if MH_ASSET_ROOT:
    hair_mhclo = os.path.join(MH_ASSET_ROOT, "hair", "short02", "short02.mhclo")
    if os.path.isfile(hair_mhclo):
        try:
            hair_object = HumanService.add_mhclo_asset(
                hair_mhclo,
                human,
                asset_type="hair",
                subdiv_levels=1,
                material_type="MAKESKIN",
                set_up_rigging=False,
            )
            hair_object.name = "HEAD_Hair_Short02_CC0"
            print("USING_CC0_HAIR", hair_mhclo)
        except Exception as exc:
            print("CC0_HAIR_FALLBACK", repr(exc))

if hair_object is None:
    hair = make_principled("M_PlayerHead_Hair", (0.018, 0.0045, 0.0018), roughness=0.52)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_human = human.evaluated_get(depsgraph)
    hair_mesh = bpy.data.meshes.new_from_object(evaluated_human, depsgraph=depsgraph)
    hair_object = bpy.data.objects.new("HEAD_Hair_Cap", hair_mesh)
    bpy.context.collection.objects.link(hair_object)
    hair_object.data.materials.clear()
    hair_object.data.materials.append(hair)
    for poly in hair_object.data.polygons:
        poly.material_index = 0
    bm = bmesh.new()
    bm.from_mesh(hair_mesh)
    eye_z = eyes_mid.z
    eye_y = eyes_mid.y
    remove = []
    for vert in bm.verts:
        co = hair_object.matrix_world @ vert.co
        keep_upper = co.z > eye_z + 0.039
        keep_back_sides = co.z > eye_z - 0.008 and co.y > eye_y + 0.026
        if not (keep_upper or keep_back_sides):
            remove.append(vert)
    bmesh.ops.delete(bm, geom=remove, context="VERTS")
    bm.to_mesh(hair_mesh)
    bm.free()
    for poly in hair_mesh.polygons:
        poly.use_smooth = True
    solidify = hair_object.modifiers.new("Hair_Cap_Thickness", "SOLIDIFY")
    solidify.thickness = 0.0028
    solidify.offset = 1.0
    bevel = hair_object.modifiers.new("Hairline_Soften", "BEVEL")
    bevel.width = 0.0018
    bevel.segments = 3
    smooth = hair_object.modifiers.new("Hair_Cap_Soften", "SMOOTH")
    smooth.factor = 0.35
    smooth.iterations = 2
else:
    hair = hair_object.data.materials[0] if hair_object.data.materials else make_principled(
        "M_PlayerHead_Hair", (0.018, 0.0045, 0.0018), roughness=0.52
    )

# Low-profile brows add essential expression at gameplay camera distance.
brow_material = make_principled("M_PlayerHead_Brows", (0.014, 0.003, 0.001), roughness=0.58)


def add_brow(name, x_sign):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.00215
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(2)
    eye = eye_centers["l" if x_sign > 0 else "r"]
    points = [
        (eye.x - 0.0130 * x_sign, eye.y - 0.0230, eye.z + 0.0210),
        (eye.x, eye.y - 0.0250, eye.z + 0.0240),
        (eye.x + 0.0142 * x_sign, eye.y - 0.0215, eye.z + 0.0200),
    ]
    if x_sign < 0:
        points.reverse()
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(brow_material)
    return obj


add_brow("HEAD_Brow_L", 1.0)
add_brow("HEAD_Brow_R", -1.0)

# The MakeHuman base faces -Y. Position the camera after detecting the head.
head_center = Vector((0.0, mins.y * 0.10, maxs.z - (maxs.z - mins.z) * 0.075))
head_height = (maxs.z - mins.z) * 0.145

# Add clean presentation lights and a neutral floor/backdrop.
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.018, 0.022, 0.028, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.06

def add_area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    direction = head_center - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


add_area("Key", (0.72, -1.25, head_center.z + 0.45), 65.0, 0.75, (1.0, 0.84, 0.73))
add_area("Fill", (-0.75, -0.82, head_center.z + 0.10), 28.0, 0.9, (0.62, 0.76, 1.0))
add_area("Rim", (0.20, 0.82, head_center.z + 0.45), 42.0, 0.55, (0.48, 0.66, 1.0))

camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.data.lens = 72
camera.location = (0.0, -head_height * 4.55, head_center.z)
camera.rotation_euler = (head_center - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Art", "Characters", "PlayerSuits", "Production_v6_Previews"))
os.makedirs(output_dir, exist_ok=True)
scene.render.filepath = os.path.join(output_dir, "PlayerHead_MakeHuman_Source.png")
bpy.ops.render.render(write_still=True)

blend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Art", "Characters", "PlayerSuits", "PlayerHead_MakeHuman_Source.blend"))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("SAVED", blend_path)
