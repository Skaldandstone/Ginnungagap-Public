"""Render isolated hero and class-lineup previews from the current player-suit master."""

import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Master.blend"
HERO = BLEND.with_name("PlayerSuit_HeroAssembly.png")
LINEUP = BLEND.with_name("PlayerSuit_ClassVariants.png")

LIBRARY = ("01_Core_Armor", "02_Limb_Armor", "03_Equipment", "04_Role_Modules",
           "05_Blender_Detail_Pass", "06_Magnetic_Suit_System", "80_Unreal_Export_Ready")
HERO_COLLECTIONS = ("07_Assembled_Hero_Suit", "08_Hands_Free_Equipment", "10_Production_Detail_100",
                    "12_Concept_Fidelity_500", "13_Player_Anatomy_500", "14_Real_Player_Finish_500",
                    "15_Production_Player_Refinement_1000")


for name in LIBRARY:
    bpy.data.collections[name].hide_render = True
for name in HERO_COLLECTIONS:
    bpy.data.collections[name].hide_render = False
bpy.data.collections["09_Class_Suit_Variants"].hide_render = True

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.camera = bpy.data.objects["CAM_Hero_Front"]
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.filepath = str(HERO)
bpy.ops.render.render(write_still=True)

for name in HERO_COLLECTIONS:
    bpy.data.collections[name].hide_render = True
bpy.data.collections["09_Class_Suit_Variants"].hide_render = False
scene.camera = bpy.data.objects["CAM_ClassLineup"]
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.filepath = str(LINEUP)
bpy.ops.render.render(write_still=True)

bpy.data.collections["09_Class_Suit_Variants"].hide_render = True
for name in HERO_COLLECTIONS:
    bpy.data.collections[name].hide_render = False
scene.camera = bpy.data.objects["CAM_AssetLibrary"]
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print("Rendered isolated player-suit hero and class previews")
