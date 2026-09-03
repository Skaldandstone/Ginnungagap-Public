"""Reports what WBP_StartScreen actually contains, exports the menu backdrop, and prints kit
door-frame mesh bounds.

Read-only. UStartScreenWidget::BuildFallbackLayout returns early when the Blueprint's designer
tree already has a RootWidget, so what the Blueprint holds decides whether the native title
layout is ever built at all. This prints the designer tree so that question is answered from
the asset rather than guessed. Every section is guarded so one reflection gap does not cost the
others.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path> -NullRHI
(Backslash paths are mangled by the engine's own argument parsing -- "\\tools" becomes a tab.)
"""
import unreal

WIDGET = "/Game/UI/Widgets/WBP_StartScreen"
FRAMES = [
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_01_INSIDE",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_01_OUTSIDE",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOORFRAME_01_UP",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOORFRAME_01_1_3",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_LEFT",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_RIGHT",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_02_UP",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_02_DOWN",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_02_UP_002",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_02_DOWN_001",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_03",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_DOOR_03",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_FRAME_04",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/SM_FRAME_05",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_HEAD",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_LEG",
]


def walk(widget, depth=0):
    if widget is None:
        return
    try:
        name = widget.get_name()
        cls = widget.get_class().get_name()
        vis = str(widget.get_visibility())
    except Exception as e:
        unreal.log(f"INSPECT   {'  ' * depth}<unreadable widget: {e}>")
        return
    unreal.log("INSPECT   " + "  " * depth + f"{cls} '{name}' {vis}")
    try:
        if isinstance(widget, unreal.PanelWidget):
            for child in widget.get_all_children():
                walk(child, depth + 1)
        elif isinstance(widget, unreal.ContentWidget):
            walk(widget.get_content(), depth + 1)
    except Exception as e:
        unreal.log(f"INSPECT   {'  ' * depth}<children unreadable: {e}>")


def section(label, fn):
    try:
        fn()
    except Exception as e:
        unreal.log(f"INSPECT {label} failed: {e}")


def inspect_widget():
    bp = unreal.load_asset(WIDGET)
    unreal.log(f"INSPECT widget asset loaded: {bp is not None} ({type(bp).__name__ if bp else 'none'})")
    if not bp:
        return
    gen = bp.generated_class()
    unreal.log(f"INSPECT generated class: {gen.get_name() if gen else None}")
    if not gen:
        return
    cdo = unreal.get_default_object(gen)
    unreal.log(f"INSPECT CDO: {cdo.get_name() if cdo else None} class {cdo.get_class().get_name() if cdo else None}")
    tree = None
    for prop in ("widget_tree", "WidgetTree"):
        try:
            tree = cdo.get_editor_property(prop)
            break
        except Exception as e:
            unreal.log(f"INSPECT CDO has no '{prop}': {e}")
    if tree is None:
        # Fall back to the blueprint's own tree object by outer search.
        for obj in unreal.EditorAssetLibrary.load_asset(WIDGET).get_outer().__class__.__mro__:
            pass
        unreal.log("INSPECT no designer tree reachable from Python; the Blueprint's tree stays opaque here")
        return
    root = tree.get_editor_property("root_widget")
    unreal.log(f"INSPECT root_widget: {root.get_name() if root else None}")
    walk(root)


def export_backdrop():
    out_dir = unreal.SystemLibrary.get_project_saved_directory() + "Reports/StartScreen"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.export_assets(["/Game/UI/Textures/T_MainMenu_Backdrop"], out_dir)
    unreal.log(f"INSPECT exported backdrop to {out_dir}")


def mesh_bounds():
    for path in FRAMES:
        mesh = unreal.load_asset(path)
        if not mesh:
            unreal.log(f"INSPECT MESH missing {path}")
            continue
        box = mesh.get_bounding_box()
        size = box.max - box.min
        unreal.log(f"INSPECT MESH {path.rsplit('/',1)[1]}: min=({box.min.x:.0f},{box.min.y:.0f},{box.min.z:.0f}) max=({box.max.x:.0f},{box.max.y:.0f},{box.max.z:.0f}) size=({size.x:.0f},{size.y:.0f},{size.z:.0f})")


section("widget", inspect_widget)
section("export", export_backdrop)
section("bounds", mesh_bounds)
unreal.log("INSPECT done")
