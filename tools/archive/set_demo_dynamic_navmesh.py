"""Switch the demo map's navmesh to runtime generation.

The map's RecastNavMesh was set to STATIC, which means the navmesh has to be built in the editor
and saved with the level -- and it never had been. There was no navigation data at all: the player
start did not project onto navigable floor, and neither did any of the five mission stations.

Players never noticed, because players walk on collision. Everything that paths did: the threat
director's enemies had nowhere to go, which for a demo meant to show the Bloom being dangerous is
the difference between a creature and a statue.

Static would be the right answer for shipping and building it headlessly did not work -- the
console rebuild reported success in eleven seconds for a four-deck ship and produced nothing.
Dynamic generation costs runtime performance and needs no build step, which is the correct trade
for a level that is still being re-placed by scripts nightly. Whether shipping wants to go back to
static is a real decision and is queued rather than made here.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/set_demo_dynamic_navmesh.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"


def main():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_subsystem.load_level(MAP_PATH):
        unreal.log_error("Could not load {}".format(MAP_PATH))
        return

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    meshes = [a for a in actors if a.get_class().get_name() == "RecastNavMesh"]
    if not meshes:
        unreal.log_error("No RecastNavMesh in the map; nothing to configure")
        return

    for mesh in meshes:
        before = mesh.get_editor_property("runtime_generation")
        mesh.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        after = mesh.get_editor_property("runtime_generation")
        # Read back: an enum that silently stays STATIC leaves the level with no navigation and a
        # log line saying it was configured.
        if after != unreal.RuntimeGenerationType.DYNAMIC:
            unreal.log_error("{}: runtime_generation did not take (still {})".format(
                mesh.get_actor_label(), after))
        else:
            unreal.log("  {}: {} -> {}".format(mesh.get_actor_label(), before, after))

    saved = level_subsystem.save_current_level()
    unreal.log("Configured {} navmesh actor(s). Saved {}: {}".format(len(meshes), MAP_PATH, saved))


if __name__ == "__main__":
    main()
