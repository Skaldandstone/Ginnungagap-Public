"""Make the Space Marshal shell wearable by putting it on the Manny skeleton.

The suit could not be assigned to the player because the oversuit follows the body through
SetLeaderPoseComponent, which binds by skeleton identity, and the Space Marshal carried its own
skeleton asset.

That looked like it needed a Blender rebind, the way the cryo undersuit did. It does not. Comparing
the two properly -- the mesh's own bone hierarchy rather than the shared Skeleton asset's bone tree,
which is a different and larger set -- they are identical: 89 bones, same names, nothing in one that
is not in the other. The shell was authored on the Manny rig and the import simply created a
duplicate skeleton rather than reusing SK_Mannequin.

So this is a reassignment, not a retarget.

Done on a duplicate rather than in place. The original stays exactly as it is for whatever the suit
work needs it for, and the copy follows the naming the cryo undersuit already established
(SK_CryoBodysuit_V32_Manny). Reassigning skeletons on a source asset someone else is iterating on
is the kind of helpfulness that costs an afternoon.

Idempotent: re-running replaces the copy.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/rebind_space_marshal_to_manny.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

SOURCE = ("/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/"
          "Iteration_06_UncorruptedProductionShell/Source/SKM_V25_I06_SpaceMarshalMale")
TARGET_DIR = "/Game/Characters/PlayerSuits/PrimaryOversuits/SpaceMarshalManny"
TARGET = TARGET_DIR + "/SK_SpaceMarshal_Manny"
MANNY_SKELETON = "/Game/Characters/Mannequins/Meshes/SK_Mannequin"
FBX = None  # resolved at runtime from the project directory


def bone_names(mesh):
    """Bone hierarchy of the mesh itself, via a throwaway component.

    Deliberately not the Skeleton asset's bone_tree: that is the union across every mesh sharing
    the skeleton, so comparing it against a single mesh reports a difference that is not real. That
    mistake is what made this look like a Blender job.
    """
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
    component = actor.skeletal_mesh_component
    component.set_skeletal_mesh_asset(mesh)

    names = []
    index = 0
    while index < 512:
        name = str(component.get_bone_name(index))
        if not name or name == "None":
            break
        names.append(name)
        index += 1

    actors.destroy_actor(actor)
    return names


def main():
    global FBX
    project = unreal.SystemLibrary.get_project_directory()
    FBX = project + "SourceArt/Fab/SpaceMarshalMale/FBX/SM_Male_UE5.fbx"
    if not unreal.Paths.file_exists(FBX):
        unreal.log_error("Missing purchased source FBX: {}".format(FBX))
        return

    for path in (SOURCE, MANNY_SKELETON):
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.log_error("Missing: {}".format(path))
            return

    source = unreal.EditorAssetLibrary.load_asset(SOURCE)
    skeleton = unreal.EditorAssetLibrary.load_asset(MANNY_SKELETON)

    # Refuse rather than produce a garbled suit. A mismatched hierarchy would still "assign" and
    # would only show itself as a deforming mess at runtime.
    manny_mesh = unreal.EditorAssetLibrary.load_asset(
        "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
    source_bones = bone_names(source)
    manny_bones = bone_names(manny_mesh)

    # Compared as sets, not as lists.
    #
    # The first version required identical order and refused: both meshes carry the same 89 bones
    # with the same names, but the Marshal lists the legs before the spine and Manny does the
    # reverse. Unreal maps a mesh onto a skeleton by bone name, not by index order, so ordering is
    # not what makes an assignment valid -- membership is. The strict check was rejecting a rebind
    # that works.
    only_source = sorted(set(source_bones) - set(manny_bones))
    only_manny = sorted(set(manny_bones) - set(source_bones))

    if only_source or only_manny:
        unreal.log_error(
            "Hierarchies differ, refusing to reassign. source={} manny={} "
            "source_only={} manny_only={}".format(
                len(source_bones), len(manny_bones), only_source[:10], only_manny[:10]))
        return

    unreal.log("Hierarchies match: {} bones, identical names ({} differs in order only)".format(
        len(source_bones), "order" if source_bones != manny_bones else "nothing"))

    if unreal.EditorAssetLibrary.does_asset_exist(TARGET):
        unreal.EditorAssetLibrary.delete_asset(TARGET)
    if not unreal.EditorAssetLibrary.does_directory_exist(TARGET_DIR):
        unreal.EditorAssetLibrary.make_directory(TARGET_DIR)

    # Re-imported against SK_Mannequin rather than duplicated and reassigned.
    #
    # Duplicating and setting the Skeleton property is the obvious approach and Unreal does not
    # allow it: Skeleton is read-only from Python, and the attempt fails with an exception rather
    # than quietly doing nothing. Naming the skeleton in the import options is the supported route,
    # and it is also the more honest one -- the importer binds the mesh to that skeleton properly
    # instead of swapping a pointer and hoping the indices agree.
    task = unreal.AssetImportTask()
    task.filename = str(FBX)
    task.destination_path = TARGET_DIR
    task.destination_name = TARGET.split("/")[-1]
    task.automated = True
    task.save = True
    task.replace_existing = True

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = False
    options.create_physics_asset = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    options.skeleton = skeleton
    options.skeletal_mesh_import_data.normal_import_method = (
        unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    copy = unreal.EditorAssetLibrary.load_asset(TARGET)
    if not isinstance(copy, unreal.SkeletalMesh):
        unreal.log_error("Import produced no skeletal mesh at {} (created {})".format(
            TARGET, list(task.imported_object_paths)))
        return

    # Read back. An import that silently falls back to creating its own skeleton leaves the suit
    # exactly as unwearable as before, with a log line saying it was rebound.
    applied = copy.get_editor_property("skeleton")
    if applied != skeleton:
        unreal.log_error("Imported onto the wrong skeleton: {} rather than {}".format(
            applied.get_name() if applied else "None", skeleton.get_name()))
        return

    unreal.EditorAssetLibrary.save_loaded_asset(copy)
    unreal.log("SK_SpaceMarshal_Manny now on {} -- {} bones".format(
        applied.get_name(), len(bone_names(copy))))


if __name__ == "__main__":
    main()
