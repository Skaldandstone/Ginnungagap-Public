"""Imports the Lyra animation sequences (Fab: "Lyra Animation Sequences Only", Kingboars) from the
launcher's FBX download onto the crew's UE5 Manny skeleton.

They are authored on the UE5 mannequin, so no retargeting: each FBX becomes an AnimSequence on
the skeleton SKM_Manny_Simple uses, under /Game/Characters/Mannequins/Anims/Lyra/<folder>. The
folders imported are the ones the ship uses (crouching for crawlspaces, idles, hit reactions,
deaths, turns, walks, jogs, jumps, emotes); pass folder names as extra arguments for others.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/import_lyra_anims.py -NullRHI
"""
import sys
from pathlib import Path
import unreal

SRC = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\FabLibrary\Lyra_Animation_Sequences_Only-ada3c1dd\fbx\lyra_extracted\Lyra")
DEST = "/Game/Characters/Mannequins/Anims/Lyra"
MESH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
FOLDERS = ["crouch", "IdleAO", "HitReactions", "death", "turn", "Walk", "UnarmedJog", "Jump", "Emotes"]

tools = unreal.AssetToolsHelpers.get_asset_tools()
mesh = unreal.load_asset(MESH)
skeleton = mesh.skeleton if mesh else None
if not skeleton:
    print("LYRA no Manny skeleton"); raise SystemExit(1)

folders = list(FOLDERS) + [a for a in sys.argv[1:] if (SRC / a).is_dir()]
total = 0
for folder in folders:
    files = sorted((SRC / folder).glob("*.FBX")) + sorted((SRC / folder).glob("*.fbx"))
    files = [f for f in files if "Pistol" not in f.name and "Rifle" not in f.name and "Shotgun" not in f.name.title()]
    if not files:
        print(f"LYRA {folder}: nothing"); continue
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = str(f)
        t.destination_path = f"{DEST}/{folder}"
        t.automated = True; t.replace_existing = True; t.save = True
        opts = unreal.FbxImportUI()
        opts.import_mesh = False; opts.import_as_skeletal = False; opts.import_materials = False; opts.import_textures = False
        opts.import_animations = True
        opts.skeleton = skeleton
        opts.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
        t.options = opts
        tasks.append(t)
    tools.import_asset_tasks(tasks)
    made = sum(len(list(t.imported_object_paths)) for t in tasks)
    total += made
    print(f"LYRA {folder}: {made} of {len(files)} imported")
unreal.EditorAssetLibrary.save_directory(DEST)
print(f"LYRA done: {total} animations under {DEST}")
