"""Surveys what the demo map is made of: every static mesh in L_QuickDemo_FourDeck, how many
instances, and which materials each draws with, so a texturing pass can be planned from numbers.

Prints MATSURVEY lines: mesh path, instance count, and the material paths on its slots (the
component overrides when set, the mesh defaults otherwise), plus a summary of materials by how
many instances draw with them.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/survey_demo_map_materials.py -NullRHI
"""
import unreal
from collections import Counter, defaultdict

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert les.load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

mesh_count = Counter()
mesh_materials = defaultdict(Counter)
material_instances = Counter()
class_count = Counter()
for actor in actors:
    class_count[actor.get_class().get_name()] += 1
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = comp.static_mesh
        if not mesh or not comp.is_visible():
            continue
        path = mesh.get_path_name().split(".")[0]
        mesh_count[path] += 1
        for i in range(comp.get_num_materials()):
            mat = comp.get_material(i)
            mpath = mat.get_path_name().split(".")[0] if mat else "<none>"
            mesh_materials[path][mpath] += 1
            material_instances[mpath] += 1

print(f"MATSURVEY actors={len(actors)} meshes={len(mesh_count)} materials={len(material_instances)}")
for path, n in mesh_count.most_common(60):
    mats = ", ".join(f"{m.split('/')[-1]}x{c}" for m, c in mesh_materials[path].most_common(4))
    print(f"MATSURVEY mesh {n:5d}  {path}  [{mats}]")
print("MATSURVEY --- materials by instance count ---")
for m, n in material_instances.most_common(40):
    print(f"MATSURVEY material {n:5d}  {m}")
print("MATSURVEY --- actor classes ---")
for c, n in class_count.most_common(30):
    print(f"MATSURVEY class {n:5d}  {c}")
