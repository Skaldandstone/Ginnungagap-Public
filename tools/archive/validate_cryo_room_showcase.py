"""Validate the CRYO-01 in-engine review map."""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_CryoRoom_Review"
unreal.EditorLevelLibrary.load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
labels = {actor.get_actor_label(): actor for actor in actors}
required = {"CRYO01_Art_Shell", "CRYO01_Art_Machinery", "CRYO01_PlayerStart",
            "CRYO01_AmbientFill", "CRYO01_CondensationHaze"}
missing = sorted(required - labels.keys())
pods = [actor for label, actor in labels.items() if label.startswith("CRYO01_GameplayPod_")]
thaw = [label for label in labels if label.startswith("CRYO01_ThawLight_")]
emergency = [label for label in labels if label.startswith("CRYO01_EmergencyLight_")]
if missing:
    raise RuntimeError("CRYO-01 review map missing: " + ", ".join(missing))
if len(pods) != 4:
    raise RuntimeError(f"CRYO-01 review map has {len(pods)} gameplay pods; expected 4")
expected_parts = {
    "VisualMesh": "SM_CryoPod_GS_Base",
    "BedInsert": "SM_CryoPod_GS_Bed",
    "DetailTrim": "SM_CryoPod_GS_Details",
    "Restraints": "SM_CryoPod_GS_Restraints",
    "StatusLights": "SM_CryoPod_GS_StatusLights",
    "LidFrame": "SM_CryoPod_GS_LidFrame",
    "LidGlass": "SM_CryoPod_GS_LidGlass",
}
for pod in pods:
    mesh_components = {component.get_name(): component for component in pod.get_components_by_class(unreal.StaticMeshComponent)}
    for component_name, asset_name in expected_parts.items():
        component = mesh_components.get(component_name)
        mesh = component.get_editor_property("static_mesh") if component else None
        if not mesh or mesh.get_name() != asset_name:
            raise RuntimeError(f"{pod.get_actor_label()} is not using reusable part {asset_name}")
    pivots = {component.get_name(): component for component in pod.get_components_by_class(unreal.SceneComponent)}
    pivot = pivots.get("LidPivot")
    rotation = pivot.get_editor_property("relative_rotation") if pivot else None
    if not rotation or abs(rotation.roll + 40.0) > 0.1 or abs(rotation.pitch) > 0.1:
        raise RuntimeError(f"{pod.get_actor_label()} lid is not hinged around its long-body closing axis")
    rake = pivots.get("PodRakePivot")
    rake_rotation = rake.get_editor_property("relative_rotation") if rake else None
    rake_location = rake.get_editor_property("relative_location") if rake else None
    if not rake_rotation or abs(rake_rotation.roll) > 0.1:
        raise RuntimeError(f"{pod.get_actor_label()} is globally rotated instead of using a baked-in cant")
    if not rake_location or abs(rake_location.z) > 0.1:
        raise RuntimeError(f"{pod.get_actor_label()} is hovering instead of resting on its level skid")
if len(thaw) != 4 or len(emergency) != 3:
    raise RuntimeError(f"CRYO-01 lighting incomplete: {len(thaw)} thaw, {len(emergency)} emergency")
pod_locations = sorted((pod.get_actor_location() for pod in pods), key=lambda point: point.y)
for left, right in zip(pod_locations, pod_locations[1:]):
    spacing = right.y - left.y
    if spacing < 235.0:
        raise RuntimeError(f"CRYO-01 pods have only {spacing:.1f} cm center spacing")
if any(abs(point.x - 156.2) > 1.0 or abs(point.z) > 1.0 for point in pod_locations):
    raise RuntimeError("CRYO-01 gameplay proxies no longer align with the authored pod row")
damaged = sum(unreal.Name("Damaged") in pod.tags for pod in pods)
nominal = sum(unreal.Name("Nominal") in pod.tags for pod in pods)
if (nominal, damaged) != (2, 2):
    raise RuntimeError(f"CRYO-01 state composition is {nominal} nominal/{damaged} damaged; expected 2/2")
player_location = labels["CRYO01_PlayerStart"].get_actor_location()
if not (-550.0 < player_location.y < 550.0 and 90.0 <= player_location.z <= 130.0):
    raise RuntimeError(f"CRYO-01 player start is outside the walkable review envelope: {player_location}")
unreal.log(f"CRYO-MAP PASS: {len(actors)} actors, 4 aligned pods (2 nominal/2 damaged), "
           "7 authored lights, player start and haze")
