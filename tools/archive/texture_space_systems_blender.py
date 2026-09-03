"""Phase four: pack original bitmap textures and add twenty texture/shading production upgrades."""

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
TEX = OUT / "Textures"
BLEND = OUT / "SpaceSystems_Master.blend"
PREVIEW = OUT / "SpaceSystems_Phase4_Textures.png"
REPORT = OUT / "SpaceSystems_Phase4_Report.json"

TEXTURES = {
    "M_Planet_Ocean": TEX / "T_Planet_OceanClouds.png",
    "M_Planet_Volcanic": TEX / "T_Planet_VolcanicLava.png",
    "M_Planet_Ice": TEX / "T_Planet_FracturedIce.png",
    "M_Gas_Giant": TEX / "T_Planet_GasBands.png",
}


def image_pbr(material_name, path, bump_strength, rough_min, rough_max, emission_strength=0.0):
    material = bpy.data.materials.get(material_name)
    if not material:
        raise RuntimeError(f"Missing material: {material_name}")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial"); output.location = (720, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (420, 0)
    image = bpy.data.images.load(str(path), check_existing=True); image.name = path.stem; image.pack()
    tex = nodes.new("ShaderNodeTexImage"); tex.name = "Packed Planet Albedo"; tex.image = image
    tex.interpolation = "Cubic"; tex.extension = "REPEAT"; tex.projection = "FLAT"; tex.location = (-520, 80)
    coords = nodes.new("ShaderNodeTexCoord"); coords.location = (-920, 80)
    mapping = nodes.new("ShaderNodeMapping"); mapping.location = (-720, 80)
    links.new(coords.outputs["UV"], mapping.inputs["Vector"]); links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    rgb = nodes.new("ShaderNodeRGBToBW"); rgb.location = (-260, -120)
    rough = nodes.new("ShaderNodeMapRange"); rough.location = (0, -100)
    rough.inputs["From Min"].default_value = 0; rough.inputs["From Max"].default_value = 1
    rough.inputs["To Min"].default_value = rough_min; rough.inputs["To Max"].default_value = rough_max
    links.new(tex.outputs["Color"], rgb.inputs["Color"]); links.new(rgb.outputs["Val"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump"); bump.location = (170, -240)
    bump.inputs["Strength"].default_value = bump_strength; bump.inputs["Distance"].default_value = .16
    links.new(rgb.outputs["Val"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if emission_strength:
        ramp = nodes.new("ShaderNodeValToRGB"); ramp.name = "Emission Mask"; ramp.location = (-10, 170)
        ramp.color_ramp.elements[0].position = .48; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].position = .72; ramp.color_ramp.elements[1].color = (1, .05, .001, 1)
        links.new(rgb.outputs["Val"], ramp.inputs["Fac"]); links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    material["source_texture"] = str(path.relative_to(ROOT)).replace("\\", "/")
    material["packed_texture"] = True
    material["pbr_channels"] = "BaseColor,Roughness,Bump" + (",Emission" if emission_strength else "")
    return image, mapping


def enhance_station_material():
    material = bpy.data.materials.get("M_StationHull")
    if not material or material.node_tree.nodes.get("PanelVoronoi"):
        return
    nodes = material.node_tree.nodes; links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    coord = nodes.new("ShaderNodeTexCoord"); coord.location = (-700, -200)
    voronoi = nodes.new("ShaderNodeTexVoronoi"); voronoi.name = "PanelVoronoi"; voronoi.location = (-480, -200)
    voronoi.distance = "EUCLIDEAN"; voronoi.inputs["Scale"].default_value = 14
    bump = nodes.new("ShaderNodeBump"); bump.name = "PanelSeams"; bump.location = (100, -190)
    bump.inputs["Strength"].default_value = .18; bump.inputs["Distance"].default_value = .04
    links.new(coord.outputs["Generated"], voronoi.inputs["Vector"])
    links.new(voronoi.outputs["Distance"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def enhance_ring_material():
    material = bpy.data.materials.get("M_Ring_Ice")
    if not material or material.node_tree.nodes.get("RingDustNoise"):
        return
    nodes = material.node_tree.nodes; links = material.node_tree.links; bsdf = nodes.get("Principled BSDF")
    noise = nodes.new("ShaderNodeTexNoise"); noise.name = "RingDustNoise"; noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 24; noise.inputs["Detail"].default_value = 5
    ramp = nodes.new("ShaderNodeValToRGB"); ramp.name = "RingDustColor"
    ramp.color_ramp.elements[0].color = (.015, .02, .025, 1); ramp.color_ramp.elements[1].color = (.45, .6, .7, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


def enhance_jump_material():
    material = bpy.data.materials.get("M_JumpMembrane")
    if not material or material.node_tree.nodes.get("EnergyDistortion"):
        return
    nodes = material.node_tree.nodes; links = material.node_tree.links; bsdf = nodes.get("Principled BSDF")
    noise = nodes.new("ShaderNodeTexNoise"); noise.name = "EnergyDistortion"; noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 6; noise.inputs["Detail"].default_value = 9; noise.inputs["Distortion"].default_value = 1.5
    ramp = nodes.new("ShaderNodeValToRGB"); ramp.name = "EnergyColorRamp"
    ramp.color_ramp.elements[0].color = (0, .01, .08, 1); ramp.color_ramp.elements[1].color = (.02, .45, 1, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 18


def main():
    scene = bpy.context.scene
    loaded = {}
    loaded["ocean"], ocean_mapping = image_pbr("M_Planet_Ocean", TEXTURES["M_Planet_Ocean"], .24, .18, .58)
    loaded["volcanic"], volcanic_mapping = image_pbr("M_Planet_Volcanic", TEXTURES["M_Planet_Volcanic"], .5, .34, .82, 2.3)
    loaded["ice"], ice_mapping = image_pbr("M_Planet_Ice", TEXTURES["M_Planet_Ice"], .42, .15, .5)
    loaded["gas"], gas_mapping = image_pbr("M_Gas_Giant", TEXTURES["M_Gas_Giant"], .12, .28, .62)

    # 1-4 are original packed albedo textures; 5-8 are per-world bump networks.
    # 9-12 are per-world roughness networks; 13 is volcanic emission masking.
    ocean_mapping.inputs["Scale"].default_value = (1.4, .9, 1)
    volcanic_mapping.inputs["Scale"].default_value = (1.15, 1.0, 1)
    ice_mapping.inputs["Scale"].default_value = (1.2, .85, 1)
    gas_mapping.inputs["Scale"].default_value = (1.0, 1.65, 1)

    # 14. Station panel microstructure.
    enhance_station_material()
    # 15. Procedural ring-dust shading.
    enhance_ring_material()
    # 16. Animated-looking jump energy distortion.
    enhance_jump_material()
    # 17. Texture provenance and license metadata.
    for key, image in loaded.items():
        image["asset_role"] = f"original_{key}_planet_texture"
        image["project"] = "Ginnungagap"
        image["generation_method"] = "OpenAI built-in image generation"
    # 18. Texture inspection camera.
    camera = bpy.data.objects.get("Camera_TextureInspection")
    if not camera:
        bpy.ops.object.camera_add(location=(13, 8, 3))
        camera = bpy.context.object; camera.name = "Camera_TextureInspection"; camera.data.lens = 78
        target = bpy.data.objects.get("Ocean_World")
        if target:
            camera.rotation_euler = (target.location - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera.data.dof.use_dof = True; camera.data.dof.focus_object = target; camera.data.dof.aperture_fstop = 8
    # 19. Phase-four render preset and preview.
    scene.camera = bpy.data.objects.get("Camera_CinematicOverview") or scene.camera
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW); scene["phase4_steps"] = 20; scene["asset_version"] = "4.0"
    scene["packed_original_textures"] = 4
    bpy.ops.render.render(write_still=True)
    # 20. Save, report, and texture manifest.
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "phase": 4, "steps": 20, "asset_version": "4.0", "packed_textures": len(loaded),
        "texture_files": [str(p.relative_to(ROOT)).replace("\\", "/") for p in TEXTURES.values()],
        "objects": len(bpy.data.objects), "materials": len(bpy.data.materials), "images": len(bpy.data.images),
        "features": ["four original albedo maps", "four bump networks", "four roughness networks",
                     "volcanic emission mask", "UV scaling", "station panel texture", "ring dust shader",
                     "jump energy shader", "packed images", "texture camera", "texture manifest"]
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


main()
