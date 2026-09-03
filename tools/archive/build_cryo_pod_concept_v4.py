"""Build a concept-faithful reusable CRYO-01 pod and export modular Unreal FBXs."""
from pathlib import Path
import math
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Art" / "ShipRooms" / "CryoPodConceptV4"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "Cryo" / "ConceptV4"
BLEND = ART / "CryoPod_ConceptV4.blend"
PREVIEW = ART / "CryoPod_ConceptV4_Preview.png"
CLOSED_PREVIEW = ART / "CryoPod_ConceptV4_ClosedPreview.png"


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                   bpy.data.cameras, bpy.data.lights):
        for block in list(blocks):
            if block.users == 0:
                blocks.remove(block)


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def link_only(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def mat(name, color, metallic=0.0, roughness=0.45, emission=None, transmission=0.0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result.diffuse_color = (*color, 1.0)
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["Alpha"].default_value = 0.34
        result.surface_render_method = "DITHERED"
        noise = result.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.noise_dimensions = "3D"
        noise.inputs["Scale"].default_value = 8.0
        noise.inputs["Detail"].default_value = 5.0
        noise.inputs["Roughness"].default_value = 0.72
        ramp = result.node_tree.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.30
        ramp.color_ramp.elements[0].color = (0.04, 0.10, 0.12, 1.0)
        ramp.color_ramp.elements[1].position = 0.70
        ramp.color_ramp.elements[1].color = (0.55, 0.78, 0.84, 1.0)
        bump = result.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.10
        bump.inputs["Distance"].default_value = 0.012
        result.node_tree.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        result.node_tree.links.new(ramp.outputs["Color"], bump.inputs["Height"])
        result.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return result


def bevel(obj, width=0.025, segments=3):
    modifier = obj.modifiers.new("ProductionEdgeSoftening", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    return obj


def box(name, loc, dims, material, target, radius=0.025, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel(obj, radius, 3)
    return link_only(obj, target)


def cylinder(name, loc, radius, depth, material, target, rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth_by_angle()
    bevel(obj, 0.012, 2)
    return link_only(obj, target)


def curve_tube(name, points, radius, material, target, cyclic=False):
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    data.resolution_u = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for control, point in zip(spline.bezier_points, points):
        control.co = point
        control.handle_left_type = "AUTO"
        control.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def text_label(name, body, loc, size, material, target, normal_side=-1):
    data = bpy.data.curves.new(name + "_Text", "FONT")
    data.body = body
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.size = size
    data.extrude = 0.0015
    data.bevel_depth = 0.0005
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    if normal_side < 0:
        basis = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0)))
    else:
        basis = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))
    obj.rotation_euler = basis.to_euler()
    obj.data.materials.append(material)
    target.objects.link(obj)
    return obj


SECTIONS = [
    (-1.46, 0.48), (-1.34, 0.57), (-1.02, 0.64), (-0.35, 0.69),
    (0.45, 0.70), (1.02, 0.66), (1.31, 0.56), (1.43, 0.43),
]


def contour(inset=0.0, flare=0.0):
    left = [(-max(0.18, width - inset) - flare, y, 0.0) for y, width in SECTIONS]
    right = [(max(0.18, width - inset) + flare, y, 0.0) for y, width in reversed(SECTIONS)]
    return left + right


def prism(name, lower, upper, material, target, lower_flare=0.0, upper_flare=0.0, inset=0.0):
    low = contour(inset, lower_flare)
    high = contour(inset, upper_flare)
    count = len(low)
    verts = [(x, y, lower) for x, y, _ in low] + [(x, y, upper) for x, y, _ in high]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, nxt + count, index + count))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(material)
    bevel(obj, 0.035, 4)
    return obj


def sloped_prism(name, lower_at_y, upper_at_y, material, target, inset=0.0):
    """Create a contour-following slab whose bed plane rises toward the head."""
    outline = contour(inset)
    count = len(outline)
    verts = ([(x, y, lower_at_y(y)) for x, y, _ in outline] +
             [(x, y, upper_at_y(y)) for x, y, _ in outline])
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, nxt + count, index + count))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(material)
    bevel(obj, 0.028, 4)
    return obj


def ring(name, z_bottom, z_top, outer_inset, inner_inset, material, target):
    outer = contour(outer_inset)
    inner = contour(inner_inset)
    count = len(outer)
    verts = ([(x, y, z_bottom) for x, y, _ in outer] +
             [(x, y, z_top) for x, y, _ in outer] +
             [(x, y, z_bottom) for x, y, _ in inner] +
             [(x, y, z_top) for x, y, _ in inner])
    faces = []
    for index in range(count):
        nxt = (index + 1) % count
        ob, ot = index, index + count
        ib, it = index + count * 2, index + count * 3
        faces.extend(((ob, nxt, nxt + count, ot),
                      (ib, it, nxt + count * 3, nxt + count * 2),
                      (ot, nxt + count, nxt + count * 3, it)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(material)
    bevel(obj, 0.024, 3)
    return obj


LID_HINGE_Y = 1.22
LID_SEAL_Z = 0.20
LID_OUTER_CROWN = 0.62
LID_INNER_CROWN = 0.47
LID_DOME_CENTER_WORLD_Y = 0.55


BERTH_CANT_DEGREES = 7.5


def berth_surface_z(world_y):
    """Locked concept cant: low at the feet, raised at the head."""
    return 0.405 + (world_y - SECTIONS[0][0]) * math.tan(math.radians(BERTH_CANT_DEGREES))


def lid_outline(offset=0.0, subdivisions=7):
    """Hinge-local outline derived from the base's exact upper-rail contour."""
    profile = [(world_y - LID_HINGE_Y, width + offset) for world_y, width in SECTIONS]
    side = []
    for section_index in range(len(profile) - 1):
        y0, w0 = profile[section_index]
        y1, w1 = profile[section_index + 1]
        for step in range(subdivisions):
            t = step / subdivisions
            smooth = t * t * (3.0 - 2.0 * t)
            side.append((y0 + (y1 - y0) * t, w0 + (w1 - w0) * smooth))
    side.append(profile[-1])
    return [(-width, y, LID_SEAL_Z) for y, width in side] + [
        (width, y, LID_SEAL_Z) for y, width in reversed(side)
    ]


def lid_pressure_band(name, outer_offset, inner_offset, lower_z, upper_z,
                      material, target):
    """Build a shallow armored sealing band instead of a pipe-like lid rim."""
    outer = lid_outline(outer_offset)
    inner = lid_outline(inner_offset)
    count = len(outer)
    verts = ([(x, y, lower_z) for x, y, _ in outer] +
             [(x, y, upper_z) for x, y, _ in outer] +
             [(x, y, lower_z) for x, y, _ in inner] +
             [(x, y, upper_z) for x, y, _ in inner])
    faces = []
    for index in range(count):
        nxt = (index + 1) % count
        ob, ot = index, index + count
        ib, it = index + count * 2, index + count * 3
        faces.extend(((ob, nxt, nxt + count, ot),
                      (ib, it, nxt + count * 3, nxt + count * 2),
                      (ot, nxt + count, nxt + count * 3, it),
                      (ob, ib, nxt + count * 2, nxt)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(material)
    bevel(obj, 0.014, 3)
    return obj


def section_width(world_y):
    """Interpolate the shared base/lid half-width at a longitudinal station."""
    if world_y <= SECTIONS[0][0]:
        return SECTIONS[0][1]
    if world_y >= SECTIONS[-1][0]:
        return SECTIONS[-1][1]
    for (y0, w0), (y1, w1) in zip(SECTIONS, SECTIONS[1:]):
        if y0 <= world_y <= y1:
            t = (world_y - y0) / (y1 - y0)
            t = t * t * (3.0 - 2.0 * t)
            return w0 + (w1 - w0) * t
    return SECTIONS[-1][1]


def canopy_bridge_points(world_y, inset=0.10, samples=18):
    """Follow the locked outer dome with a thin transverse structural bridge."""
    width = max(0.20, section_width(world_y) - inset)
    foot_y = SECTIONS[0][0]
    head_y = SECTIONS[-1][0]
    progress = max(0.0, min(1.0, (world_y - foot_y) / (head_y - foot_y)))
    slope = 0.35 + 0.90 * progress
    points = []
    for index in range(samples + 1):
        x = -width + (2.0 * width * index / samples)
        arch = math.sqrt(max(0.0, 1.0 - (x / width) ** 2))
        points.append((x, world_y - LID_HINGE_Y,
                       LID_SEAL_Z + LID_OUTER_CROWN * slope * arch + 0.012))
    return points


def glass_lens(name, material, target, parent):
    boundary = lid_outline(-0.105, 12)
    count = len(boundary)
    center = Vector((0.0, LID_DOME_CENTER_WORLD_Y - LID_HINGE_Y, LID_SEAL_Z))
    foot_y = SECTIONS[0][0] - LID_HINGE_Y
    head_y = SECTIONS[-1][0] - LID_HINGE_Y

    def longitudinal_slope(y):
        progress = max(0.0, min(1.0, (y - foot_y) / (head_y - foot_y)))
        return 0.35 + 0.90 * progress

    ring_count = 18
    verts = [(center.x, center.y,
              LID_SEAL_Z + LID_OUTER_CROWN * longitudinal_slope(center.y))]
    # Concentric loft rings form a continuous compound dome rather than a flat fan.
    for ring_index in range(1, ring_count + 1):
        radius = ring_index / ring_count
        # A half-ellipse gives the canopy a steep shoulder and unmistakable
        # human-clearance crown. Keep this independent from the sealing rim.
        arch = math.sqrt(max(0.0, 1.0 - radius * radius))
        for x, y, _ in boundary:
            vertex_y = center.y + (y - center.y) * radius
            dome_z = (LID_SEAL_Z + LID_OUTER_CROWN * arch *
                      longitudinal_slope(vertex_y))
            verts.append((center.x + (x - center.x) * radius,
                          vertex_y, dome_z))
    bottom_center_index = len(verts)
    verts.append((center.x, center.y,
                  LID_SEAL_Z + LID_INNER_CROWN * longitudinal_slope(center.y)))
    bottom_start = len(verts)
    # Matching inner loft creates a true hollow dome with ~6-9 cm shell depth.
    for ring_index in range(1, ring_count + 1):
        radius = ring_index / ring_count
        arch = math.sqrt(max(0.0, 1.0 - radius * radius))
        for x, y, _ in boundary:
            vertex_y = center.y + (y - center.y) * radius
            inner_z = (LID_SEAL_Z + LID_INNER_CROWN * arch *
                       longitudinal_slope(vertex_y))
            verts.append((center.x + (x - center.x) * radius,
                          vertex_y, inner_z))
    faces = []
    for i in range(count):
        nxt = (i + 1) % count
        faces.append((0, 1 + i, 1 + nxt))
    for ring_index in range(1, ring_count):
        previous = 1 + (ring_index - 1) * count
        current = previous + count
        for i in range(count):
            nxt = (i + 1) % count
            faces.append((previous + i, current + i, current + nxt, previous + nxt))
    for i in range(count):
        nxt = (i + 1) % count
        faces.append((bottom_center_index, bottom_start + nxt, bottom_start + i))
    for ring_index in range(1, ring_count):
        previous = bottom_start + (ring_index - 1) * count
        current = previous + count
        for i in range(count):
            nxt = (i + 1) % count
            faces.append((previous + i, previous + nxt, current + nxt, current + i))
    top_edge = 1 + (ring_count - 1) * count
    bottom_edge = bottom_start + (ring_count - 1) * count
    for i in range(count):
        nxt = (i + 1) % count
        faces.append((top_edge + i, bottom_edge + i, bottom_edge + nxt, top_edge + nxt))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(material)
    obj.parent = parent
    bevel(obj, 0.018, 3)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def build():
    reset()
    ART.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    base = collection("CRYO_POD_BASE")
    lid = collection("CRYO_POD_LID")
    presentation = collection("PRESENTATION")

    hull = mat("M_Cryo_BlackenedSteel", (0.018, 0.022, 0.024), 0.82, 0.29)
    edge = mat("M_Cryo_EdgeWear", (0.075, 0.067, 0.055), 0.88, 0.24)
    inset = mat("M_Cryo_InsetPanel", (0.028, 0.032, 0.032), 0.66, 0.38)
    cushion = mat("M_Cryo_Cushion", (0.006, 0.007, 0.007), 0.05, 0.82)
    rubber = mat("M_Cryo_Rubber", (0.008, 0.009, 0.009), 0.0, 0.58)
    amber = mat("M_Cryo_Amber", (0.22, 0.045, 0.008), 0.18, 0.28, (1.0, 0.16, 0.015))
    cyan = mat("M_Cryo_CyanStatus", (0.015, 0.20, 0.25), 0.16, 0.18,
               (0.02, 0.55, 0.72))
    marking = mat("M_Cryo_Marking", (0.27, 0.31, 0.30), 0.42, 0.22)
    glass = mat("M_Cryo_FrostedGlass", (0.055, 0.19, 0.23), 0.1, 0.16,
                (0.04, 0.19, 0.26), 0.74)

    # Low, floor-planted tapered sarcophagus shell.
    prism("SM_CryoPodV4_Foundation", 0.06, 0.22, hull, base, lower_flare=0.10, upper_flare=0.04)
    ring("SM_CryoPodV4_LowerShell", 0.20, 0.50, -0.055, 0.205, hull, base)
    ring("SM_CryoPodV4_DeepTub", 0.43, 0.76, 0.0, 0.205, hull, base)
    ring("SM_CryoPodV4_PerimeterWearRail", 0.735, 0.81, -0.025, 0.105, edge, base)
    sloped_prism("SM_CryoPodV4_RecessedMattress",
                 lambda y: berth_surface_z(y) - 0.085,
                 berth_surface_z, cushion, base, inset=0.245)

    # Segmented upholstery defines an actual human-length berth.
    berth_sections = (
        (-1.05, 0.58, 0.00), (-0.62, 0.66, 0.00),
        (-0.19, 0.74, 0.01), (0.24, 0.80, 0.025),
        (0.67, 0.76, 0.045), (1.02, 0.66, 0.07),
    )
    for idx, (y, width, lift) in enumerate(berth_sections):
        box(f"SM_CryoPodV4_Cushion_{idx:02d}", (0, y, berth_surface_z(y) + 0.045 + lift * 0.15),
            (width, 0.36, 0.085 + lift * 0.50), cushion, base, 0.055,
            rotation=(math.radians(BERTH_CANT_DEGREES + lift * 7.0), 0, 0))
    box("SM_CryoPodV4_HeadBolster", (0, 1.14, berth_surface_z(1.14) + 0.035),
        (0.70, 0.30, 0.13), cushion, base, 0.065,
        rotation=(math.radians(BERTH_CANT_DEGREES + 5.0), 0, 0))
    for side in (-1, 1):
        x = side * 0.47
        curve_tube(f"SM_CryoPodV4_InnerBolster_{side:+d}",
                   [(x * 0.86, -1.14, berth_surface_z(-1.14) + 0.035),
                    (x, -0.45, berth_surface_z(-0.45) + 0.035),
                    (x, 0.52, berth_surface_z(0.52) + 0.035),
                    (x * 0.82, 1.08, berth_surface_z(1.08) + 0.035)],
                   0.075, cushion, base)

    # Dense, readable hard-surface language from the concept turnaround.
    for side in (-1, 1):
        x = side * 0.70
        for idx, y in enumerate((-0.98, -0.42, 0.14, 0.70)):
            box(f"SM_CryoPodV4_SidePanel_{side:+d}_{idx}", (x, y, 0.43),
                (0.055, 0.42, 0.25), inset, base, 0.022)
            box(f"SM_CryoPodV4_SidePanelTrim_{side:+d}_{idx}", (x + side * 0.031, y, 0.43),
                (0.018, 0.31, 0.14), edge, base, 0.014)
        curve_tube(f"SM_CryoPodV4_ServicePipe_{side:+d}",
                   [(x + side * 0.035, -1.08, 0.32), (x + side * 0.08, -0.68, 0.33),
                    (x + side * 0.08, 0.18, 0.34), (x + side * 0.04, 0.91, 0.40)],
                   0.028, edge, base)
        curve_tube(f"SM_CryoPodV4_LowerCoolantLine_{side:+d}",
                   [(x + side * 0.045, -1.05, 0.27), (x + side * 0.11, -0.82, 0.25),
                    (x + side * 0.09, -0.26, 0.23), (x + side * 0.12, 0.38, 0.28),
                    (x + side * 0.06, 0.96, 0.34)], 0.021, rubber, base)
        cylinder(f"SM_CryoPodV4_LineManifold_{side:+d}",
                 (x + side * 0.060, -1.06, 0.30), 0.072, 0.032, inset, base,
                 rotation=(0, math.pi / 2, 0), vertices=28)
        for y in (-1.22, -0.70, -0.18, 0.34, 0.86):
            box(f"SM_CryoPodV4_VerticalRib_{side:+d}_{y:+.2f}", (x + side * 0.052, y, 0.43),
                (0.045, 0.075, 0.48), edge, base, 0.018)
        for y in (-1.12, 1.02):
            cylinder(f"SM_CryoPodV4_SideServicePort_{side:+d}_{y:+.2f}",
                     (x + side * 0.082, y, 0.43), 0.13, 0.035, hull, base,
                     rotation=(0, math.pi / 2, 0), vertices=36)
            cylinder(f"SM_CryoPodV4_SideServicePortRing_{side:+d}_{y:+.2f}",
                     (x + side * 0.104, y, 0.43), 0.085, 0.018, edge, base,
                     rotation=(0, math.pi / 2, 0), vertices=32)
        for y in (-0.82, -0.20, 0.42, 0.82):
            for z in (0.24, 0.64):
                cylinder(f"SM_CryoPodV4_Rivet_{side:+d}_{y:+.2f}_{z:.2f}",
                         (x + side * 0.095, y, z), 0.018, 0.014, edge, base,
                         rotation=(0, math.pi / 2, 0), vertices=16)

    # Recessed service console and restrained status lighting: readable at
    # gameplay distance without turning the pod into arbitrary greeble noise.
    box("SM_CryoPodV4_ServiceConsole", (-0.744, 0.15, 0.57),
        (0.055, 0.46, 0.22), inset, base, 0.025)
    box("SM_CryoPodV4_ServiceConsoleScreen", (-0.778, 0.15, 0.59),
        (0.018, 0.29, 0.095), cyan, base, 0.018)
    text_label("SM_CryoPodV4_UnitMarking", "CRYO-01",
               (-0.756, -0.96, 0.565), 0.062, marking, base)
    text_label("SM_CryoPodV4_ServiceMarking", "STASIS / A",
               (-0.757, -0.96, 0.515), 0.024, marking, base)
    for y in (-0.72, 0.46):
        for side in (-1, 1):
            box(f"SM_CryoPodV4_LatchReceiver_{side:+d}_{y:+.2f}",
                (side * 0.718, y, 0.72), (0.085, 0.18, 0.12), hull, base, 0.025)

    # Shaped armored nose replaces the earlier stack of rectangular toe blocks.
    # The guards follow the tapered hull and leave the main fascia recessed.
    for name, z, radius, span in (("Lower", 0.22, 0.048, 0.46),
                                  ("Upper", 0.54, 0.036, 0.39)):
        curve_tube(f"SM_CryoPodV4_FootGuard_{name}",
                   [(-span, -1.49, z), (-span * 0.68, -1.555, z + 0.012),
                    (0.0, -1.585, z + 0.02),
                    (span * 0.68, -1.555, z + 0.012), (span, -1.49, z)],
                   radius, edge, base)
    box("SM_CryoPodV4_RecessedFootFascia", (0, -1.515, 0.39),
        (0.57, 0.045, 0.25), inset, base, 0.065)
    box("SM_CryoPodV4_FootLamp", (0, -1.542, 0.42),
        (0.31, 0.018, 0.070), amber, base, 0.030)
    for side in (-1, 1):
        cylinder(f"SM_CryoPodV4_FootFastener_{side:+d}",
                 (side * 0.235, -1.548, 0.31), 0.025, 0.018, edge, base,
                 rotation=(math.pi / 2, 0, 0), vertices=20)
    for side in (-1, 1):
        box(f"SM_CryoPodV4_SideLamp_{side:+d}", (side * 0.728, -0.43, 0.43),
            (0.018, 0.28, 0.075), amber, base, 0.018)

    # Integrated circular trunnions; nothing floats or sticks out unsupported.
    for side in (-1, 1):
        x = side * 0.70
        cylinder(f"SM_CryoPodV4_HingeHousing_{side:+d}", (x, 1.22, 0.67), 0.205, 0.115,
                 hull, base, rotation=(0, math.pi / 2, 0), vertices=40)
        cylinder(f"SM_CryoPodV4_HingeRing_{side:+d}", (x + side * 0.063, 1.22, 0.67), 0.145, 0.025,
                 edge, base, rotation=(0, math.pi / 2, 0), vertices=40)
        cylinder(f"SM_CryoPodV4_HingeHub_{side:+d}", (x + side * 0.080, 1.22, 0.67), 0.067, 0.032,
                 inset, base, rotation=(0, math.pi / 2, 0), vertices=32)

    # Four broad isolation feet visually carry the mass and prevent hovering.
    for side in (-1, 1):
        for y in (-0.98, 0.76):
            box(f"SM_CryoPodV4_IsolationFoot_{side:+d}_{y:+.2f}",
                (side * 0.46, y, 0.035), (0.30, 0.34, 0.07), rubber, base, 0.045)

    # Head-end plumbing manifold and restraint anchors give the berth a clear
    # medical function rather than reading as generic upholstered furniture.
    box("SM_CryoPodV4_HeadManifold", (0, 1.30, 0.57),
        (0.62, 0.14, 0.18), inset, base, 0.045)
    for side in (-1, 1):
        cylinder(f"SM_CryoPodV4_RespiratorPort_{side:+d}",
                 (side * 0.20, 1.385, 0.58), 0.052, 0.025, cyan, base,
                 rotation=(math.pi / 2, 0, 0), vertices=28)
        cylinder(f"SM_CryoPodV4_HarnessAnchor_{side:+d}",
                 (side * 0.48, 0.60, 0.74), 0.055, 0.040, edge, base,
                 rotation=(0, math.pi / 2, 0), vertices=28)

    lid_root = bpy.data.objects.new("CRYO_POD_LID_PIVOT", None)
    lid.objects.link(lid_root)
    lid_root.location = (0, 1.22, 0.68)
    lid_root.rotation_euler.x = math.radians(-72)
    lid_root["hinge_axis"] = "local_x"
    lid_root["closed_angle_degrees"] = 0.0
    lid_root["open_angle_degrees"] = -72.0
    lid_root["closed_foot_reach_m"] = SECTIONS[0][0] - LID_HINGE_Y
    lid_root["closed_outer_width_m"] = 2.0 * (max(width for _, width in SECTIONS) + 0.04)
    lid_root["shared_mating_contour"] = "SECTIONS / base upper rail"
    lid_root["outer_dome_crown_m"] = LID_OUTER_CROWN
    lid_root["inner_dome_crown_m"] = LID_INNER_CROWN
    lid_root["dome_profile"] = "head-biased crown tapering continuously to foot"
    pressure_band = lid_pressure_band("SM_CryoPodV4_LidPressureBand", 0.050, -0.055,
                                      LID_SEAL_Z - 0.045, LID_SEAL_Z + 0.045,
                                      hull, lid)
    outer = curve_tube("SM_CryoPodV4_LidOuterFrame", lid_outline(0.035), 0.046, hull, lid, True)
    inner = curve_tube("SM_CryoPodV4_LidInnerFrame", lid_outline(-0.070), 0.022, edge, lid, True)
    gasket_points = [(x, y, LID_SEAL_Z - 0.055) for x, y, _ in lid_outline(-0.015)]
    gasket = curve_tube("SM_CryoPodV4_PressureGasket", gasket_points, 0.022,
                        rubber, lid, True)
    pressure_band.parent = lid_root
    outer.parent = lid_root
    inner.parent = lid_root
    gasket.parent = lid_root
    glass_lens("SM_CryoPodV4_DomedGlass", glass, lid, lid_root)
    for bridge_index, (world_y, radius, material) in enumerate((
            (-0.72, 0.018, edge),
            (0.76, 0.022, hull))):
        bridge = curve_tube(f"SM_CryoPodV4_CanopyBridge_{bridge_index}",
                            canopy_bridge_points(world_y), radius, material, lid)
        bridge.parent = lid_root
    for side in (-1, 1):
        arm = box(f"SM_CryoPodV4_LidHingeArm_{side:+d}", (side * 0.46, -0.10, 0),
                  (0.11, 0.30, 0.12), hull, lid, 0.04)
        arm.parent = lid_root
        linkage = curve_tube(f"SM_CryoPodV4_LidLinkage_{side:+d}",
                             [(side * 0.46, 0.01, 0.00),
                              (side * 0.50, -0.14, 0.08),
                              (side * 0.55, -0.34, LID_SEAL_Z)],
                             0.052, hull, lid)
        linkage.parent = lid_root
        pivot = cylinder(f"SM_CryoPodV4_LidPivot_{side:+d}",
                         (side * 0.46, -0.01, 0.0), 0.085, 0.075,
                         edge, lid, rotation=(0, math.pi / 2, 0), vertices=32)
        pivot.parent = lid_root
        for latch_index, y in enumerate((-1.94, -0.76)):
            latch = box(f"SM_CryoPodV4_LidLatch_{side:+d}_{latch_index}",
                        (side * 0.64, y, LID_SEAL_Z - 0.005),
                        (0.10, 0.20, 0.11), edge, lid, 0.028)
            latch.parent = lid_root

    # Neutral studio presentation for silhouette comparison.
    floor = box("StudioFloor", (0, 0, -0.02), (5.5, 5.5, 0.06),
                mat("M_Studio", (0.22, 0.22, 0.21), 0.0, 0.62), presentation, 0.01)
    floor.hide_select = True
    world = bpy.context.scene.world
    world.color = (0.055, 0.055, 0.055)
    for name, loc, energy, size, color in (
        ("Key", (-3.2, -3.3, 4.1), 720, 3.0, (1.0, 0.82, 0.66)),
        ("Fill", (3.1, -0.4, 2.4), 430, 2.6, (0.45, 0.64, 1.0)),
        ("Rim", (0.3, 3.8, 3.6), 620, 2.2, (0.72, 0.86, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        obj.rotation_euler = ((Vector((0, 0, 0.65)) - obj.location).to_track_quat("-Z", "Y").to_euler())
        presentation.objects.link(obj)
    camera_data = bpy.data.cameras.new("CryoPodConceptCamera")
    camera = bpy.data.objects.new("CryoPodConceptCamera", camera_data)
    camera.location = (-5.2, -5.8, 3.05)
    camera.rotation_euler = ((Vector((0, 0, 0.80)) - camera.location).to_track_quat("-Z", "Y").to_euler())
    camera_data.lens = 62
    presentation.objects.link(camera)

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.10
    scene["concept_reference"] = "docs/concept-art/reference/rooms/cryo-pod-realityscan-turnaround-v2.png"
    scene["usable_bed_length_m"] = 2.45
    scene["pod_envelope_m"] = "1.55 x 3.05 x 2.30 open"
    scene["lid_is_separate_animated_asset"] = True

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)
    lid_root.rotation_euler.x = 0.0
    scene.render.filepath = str(CLOSED_PREVIEW)
    bpy.ops.render.render(write_still=True)
    lid_root.rotation_euler.x = math.radians(-72)
    scene.render.filepath = str(PREVIEW)

    # FBX does not carry Blender curves as static-mesh geometry. Convert every
    # authored pipe/frame to mesh for Unreal, then export the lid in hinge-local
    # space so the engine can rotate it around a real pivot.
    for group in (base, lid):
        for obj in list(group.objects):
            if obj.type in {"CURVE", "FONT"}:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.convert(target="MESH")
    for obj in list(lid.objects):
        if obj.type == "MESH" and obj.parent == lid_root:
            local_matrix = obj.matrix_basis.copy()
            obj.parent = None
            obj.matrix_basis = local_matrix

    for group, filename in ((base, "SM_CryoPod_ConceptV4_Base.fbx"),
                            (lid, "SM_CryoPod_ConceptV4_Lid.fbx")):
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group.objects:
            if obj.type == "MESH":
                obj.select_set(True)
        bpy.context.view_layer.objects.active = next((obj for obj in group.objects if obj.type == "MESH"), None)
        bpy.ops.export_scene.fbx(filepath=str(EXPORT / filename), use_selection=True,
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                                 object_types={"MESH"}, use_mesh_modifiers=True,
                                 mesh_smooth_type="FACE",
                                 add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")
    print(f"CRYO-V4 PREVIEW: {PREVIEW}")


if __name__ == "__main__":
    build()
