"""Retargets UE4-mannequin animation packs onto the crew's UE5 Manny skeleton.

Fab's free animation packs (the Free Animation Library's crouch and prone loops, the Character
Interaction add-on's lever and button work) ship on SK_Mannequin, the UE4 skeleton; the crew is
SKM_Manny_Simple. This builds the two IK rigs with the engine's auto retarget definitions, an IK
retargeter between them with auto-mapped chains, and batch-retargets the chosen folders into
/Game/Characters/Mannequins/Anims/Retargeted/<pack>, prefixed "RT_". Re-runs replace.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/retarget_ue4_anims.py -NullRHI

Pass folders on the command line as extra arguments (after the script path) to retarget other
packs; the defaults below are the ones the ship uses.
"""
import sys
import unreal

TARGET_MESH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
SOURCE_MESH_CANDIDATES = [
    "/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SK_Mannequin",
    "/Game/Interaction/Characters/UE4Mannequin/Meshes/SK_Mannequin",
]
RIG_DIR = "/Game/Characters/Mannequins/Rigs/Retarget"
OUT_ROOT = "/Game/Characters/Mannequins/Anims/Retargeted"
DEFAULT_FOLDERS = {
    "Crouch": "/Game/FreeAnimationLibrary/Animations/Crouch",
    "Prone": "/Game/FreeAnimationLibrary/Animations/UnarmedProne",
    "Interaction": "/Game/Interaction/Animations/Interaction",
    "Ladder": "/Game/FreeAnimationLibrary/Animations/Ladder",
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def load_mesh(path):
    m = unreal.load_asset(path)
    return m if isinstance(m, unreal.SkeletalMesh) else None


def make_rig(name, mesh):
    path = f"{RIG_DIR}/{name}"
    # Reused when it exists: deleting and recreating in one session left the new asset without a
    # controller.
    rig = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if not rig:
        rig = tools.create_asset(name, RIG_DIR, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
    controller = unreal.IKRigController.get_controller(rig)
    if not controller:
        print(f"RETARGET rig {name}: no controller"); return rig
    controller.set_skeletal_mesh(mesh)
    ok = controller.apply_auto_generated_retarget_definition()
    unreal.EditorAssetLibrary.save_loaded_asset(rig)
    print(f"RETARGET rig {name}: auto definition {'ok' if ok else 'FAILED'} on {mesh.get_name()}")
    return rig


def make_retargeter(name, source_rig, target_rig):
    path = f"{RIG_DIR}/{name}"
    rtg = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if not rtg:
        rtg = tools.create_asset(name, RIG_DIR, unreal.IKRetargeter, unreal.IKRetargetFactory())
    controller = unreal.IKRetargeterController.get_controller(rtg)
    if not controller:
        print(f"RETARGET retargeter {name}: no controller"); return rtg
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, source_rig)
    controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, target_rig)
    controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    # The UE4 and UE5 mannequins share a rest pose closely enough that aligning the target to the
    # source's chains keeps the arms and legs where the animation expects them.
    try:
        controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    except Exception as error:  # older signature
        print(f"RETARGET align skipped: {error}")
    unreal.EditorAssetLibrary.save_loaded_asset(rtg)
    print(f"RETARGET retargeter {name} built")
    return rtg


def anims_in(folder):
    data = registry.get_assets_by_path(folder, recursive=True)
    return [d for d in data if d.asset_class_path.asset_name == "AnimSequence"]


def main():
    target = load_mesh(TARGET_MESH)
    source = next((m for m in (load_mesh(p) for p in SOURCE_MESH_CANDIDATES) if m), None)
    if not target or not source:
        print(f"RETARGET missing meshes: target={bool(target)} source={bool(source)}")
        return
    source_rig = make_rig("IK_UE4_Mannequin_Auto", source)
    target_rig = make_rig("IK_Manny_Auto", target)
    rtg = make_retargeter("RTG_UE4_To_Manny", source_rig, target_rig)

    folders = dict(DEFAULT_FOLDERS)
    for arg in sys.argv[1:]:
        if arg.startswith("/Game/"):
            folders[arg.rstrip("/").rsplit("/", 1)[1]] = arg
    total = 0
    for pack, folder in folders.items():
        assets = anims_in(folder)
        if not assets:
            print(f"RETARGET {pack}: no animations under {folder}")
            continue
        inputs = unreal.IKRetargetBatchOperationInputs()
        inputs.assets_to_retarget = assets
        inputs.source_mesh = source
        inputs.target_mesh = target
        inputs.ik_retarget_asset = rtg
        inputs.prefix = "RT_"
        pass
        try:
            out = unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)
        except Exception as error:
            print(f"RETARGET {pack}: batch failed: {error}")
            continue
        total += len(out)
        # The batch drops its output beside the source (at /Game for these packs): move each new
        # animation into the pack's own folder under OUT_ROOT.
        moved = 0
        for o in out:
            src = str(o.package_name)
            name = src.rsplit("/", 1)[1]
            dst = f"{OUT_ROOT}/{pack}/{name}"
            if src != dst and unreal.EditorAssetLibrary.rename_asset(src, dst):
                moved += 1
        print(f"RETARGET {pack}: {len(out)} animation(s) from {len(assets)}, {moved} moved to {OUT_ROOT}/{pack}")
    unreal.EditorAssetLibrary.save_directory(OUT_ROOT)
    unreal.EditorAssetLibrary.save_directory(RIG_DIR)
    print(f"RETARGET done: {total} animation(s)")


main()
