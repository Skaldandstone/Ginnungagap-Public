import unreal


SOURCE = r"C:\Users\James\Documents\GitHub\Ginnungagap\Art\UI\HelmetHUD\T_HelmetVisorFrame_v2.png"
DESTINATION = "/Game/UI/HelmetHUD"

task = unreal.AssetImportTask()
task.filename = SOURCE
task.destination_path = DESTINATION
task.destination_name = "T_HelmetVisorFrame"
task.automated = True
task.replace_existing = True
task.replace_existing_settings = True
task.save = True

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

texture = unreal.load_asset(f"{DESTINATION}/T_HelmetVisorFrame")
if not texture:
    raise RuntimeError("Helmet visor frame import failed")

texture.set_editor_property("srgb", True)
unreal.EditorAssetLibrary.save_loaded_asset(texture)
unreal.log(f"Imported helmet HUD visor frame: {texture.get_path_name()}")
