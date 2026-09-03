"""Photograph the dressed slice under its own lighting.

Separate from capture_quick_demo_four_deck_ship.py rather than a flag on it, because the two want
opposite things. That script adds fill lights and pins exposure, which is correct for photographing
an unlit greybox -- without the fill you get a black frame. Applied to a room that now has real
lights it double-lights everything and blows the whole frame to white, which is exactly what
happened the first time and is a property of the capture rig, not of the map.

So this adds no lights at all and leaves exposure alone. What comes out is what the map actually
looks like, which is the only thing worth judging.

Cameras look across each room from a back corner toward the far wall rather than straight in from
the threshold. The threshold framing put the lens inside a suited crew member in the cryo bay and
filled half the frame with their leg; standing back and looking across shows the shell, which is
what is being reviewed.

Ceilings are hidden for the duration so there is something to see. The map is never saved.

Run with ExecCmds rather than ExecutePythonScript:
    UnrealEditor.exe <project> -ExecCmds="py <this file>" -nosplash -NoSound

That matters. -ExecutePythonScript quits the editor the moment the script returns, and this script
schedules work on a Slate tick callback that then never runs -- it exits cleanly having rendered
nothing. It also needs the windowed editor: high-res screenshots need a real viewport, so
UnrealEditor-Cmd.exe silently produces no files.
"""

import os
import time
from pathlib import Path

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
OUTPUT = Path(unreal.SystemLibrary.get_project_saved_directory()) / "RoomReviews" / "SliceReview"

# Room code -> friendly name, for the six rooms the dressing pass covers.
ROOMS = [
    ("QD-03-01", "CryoBay"),
    ("QD-03-02", "Workshop"),
    ("QD-02-01", "EngineRoom"),
    ("QD-02-14", "PowerControl"),
    ("QD-03-11", "BloomBreach"),
    ("QD-03-24", "CIC"),
]

# Room shell is 1100 x 1000 x 400, but the kit's wall pieces are 109cm deep and protrude inward, so
# the usable interior is nearer 880 x 780.
#
# Two framings failed before this one, both for the same reason: a fixed offset at standing height
# in a furnished room lands inside something. The corner offset put the lens 11cm from a wall face;
# the along-the-axis offset put it inside a CIC console. There is no eye-height position that is
# guaranteed clear, because the whole point of dressing a room is to fill it.
#
# So look down from just under the deckhead instead. Above every prop, clear of the walls, and it
# frames floor, two walls and the contents in one shot -- which is what a review needs and a
# player's eye view is not.
# Seconds each shot is allowed to converge before it is taken.
SETTLE_SECONDS = 8.0

CAMERA_OFFSET = unreal.Vector(-300.0, -250.0, 155.0)
TARGET_OFFSET = unreal.Vector(120.0, 100.0, -160.0)

# Corridor shots are framed differently: eye height, on the centreline, looking down the length.
# A corridor is judged on how it reads receding into the distance, which a down-angle destroys.
# (name, deck centre Z, camera X, target X)
CORRIDORS = [
    ("CorridorD03_Fwd", 1255.0, -6000.0, 2500.0),
    ("CorridorD03_Aft", 1255.0, 3000.0, -4500.0),
    ("CorridorD02_Fwd", 735.0, -5000.0, 3500.0),
]
CORRIDOR_EYE = 160.0
FLOOR_DROP = 195.0


def configure_camera(camera, fov=90.0):
    component = camera.get_component_by_class(unreal.CameraComponent)
    component.set_editor_property("field_of_view", fov)

    # Deliberately not overriding exposure. Whatever the scene does on its own is the thing being
    # reviewed; forcing a bias here would hide the problem it is meant to reveal.
    component.set_editor_property("post_process_blend_weight", 0.0)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load " + MAP)

    unreal.AutomationLibrary.finish_loading_before_screenshot()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = actors_api.get_all_level_actors()

    rooms = {}
    for actor in actors:
        if actor.get_class().get_name() != "ModularShipRoom":
            continue
        rooms[str(actor.get_editor_property("room_code"))] = actor

    # Hide ceilings -- both the greybox ones and the kit pieces this pass added -- or every shot is
    # the underside of a ceiling panel.
    for actor in actors:
        label = actor.get_actor_label()
        if "Ceiling_" in label or "SM_CEILING" in label:
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)

    # Long capture runs have hung twice partway through, so it must be possible to shoot only the
    # part that changed rather than re-rendering everything to see one new view.
    only = {name.strip() for name in os.environ.get("SLICE_CAPTURE_ONLY", "").split(",")
            if name.strip()}

    views = []
    for code, name in ROOMS:
        if only and name not in only:
            continue
        room = rooms.get(code)
        if not room:
            unreal.log_error("Room {} not in map; skipping".format(code))
            continue
        origin, _ = room.get_actor_bounds(only_colliding_components=False)
        centre = unreal.Vector(origin.x, origin.y, origin.z)
        views.append((
            name,
            centre + CAMERA_OFFSET,
            centre + TARGET_OFFSET,
        ))

    for name, centre_z, cam_x, target_x in CORRIDORS:
        if only and name not in only:
            continue
        floor_z = centre_z - FLOOR_DROP
        views.append((
            name,
            unreal.Vector(cam_x, 0.0, floor_z + CORRIDOR_EYE),
            unreal.Vector(target_x, 0.0, floor_z + CORRIDOR_EYE - 20.0),
        ))

    if not views:
        unreal.log_error("No rooms to photograph")
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")
        return

    state = {"pending": list(views), "task": None, "camera": None,
             "output": None, "name": "", "frames": 0, "started": time.time(),
             "callback": None}

    def schedule_next():
        name, location, target = state["pending"].pop(0)
        for command in ("ShowFlag.Grid 0", "ShowFlag.Sprites 0",
                        "ShowFlag.SelectionOutline 0", "ShowFlag.CompositeEditorPrimitives 0"):
            unreal.SystemLibrary.execute_console_command(world, command)

        camera = actors_api.spawn_actor_from_class(
            unreal.CameraActor, location,
            unreal.MathLibrary.find_look_at_rotation(location, target))
        camera.set_actor_label("SliceReviewCamera_" + name)
        configure_camera(camera)

        output = (OUTPUT / ("Slice_" + name + ".png")).resolve()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1600, 900, str(output), camera=camera, delay=1.0, force_game_view=True)
        if not task or not task.is_valid_task():
            raise RuntimeError("Could not schedule capture for " + name)
        state.update(task=task, camera=camera, output=output, name=name,
                     frames=0, started=time.time())

    def advance(_delta_seconds):
        state["frames"] += 1

        # Frames alone were not enough: five of six shots once landed inside the same second,
        # because a frame in a stalled editor costs nothing and the counter ran out instantly. The
        # renderer needs wall-clock time to converge -- Lumen accumulates over many frames, and
        # streamed textures and shaders arrive on their own schedule -- so gate on elapsed seconds
        # as well and let whichever is slower win.
        if (state["frames"] < 45
                or time.time() - state["started"] < SETTLE_SECONDS
                or not state["task"].is_task_done()):
            return

        if not state["output"].exists():
            unreal.log_error("Slice capture missing: {}".format(state["output"]))
        else:
            unreal.log("Slice captured {}".format(state["name"]))

        actors_api.destroy_actor(state["camera"])
        if state["pending"]:
            schedule_next()
        else:
            unreal.unregister_slate_post_tick_callback(state["callback"])
            unreal.log("Slice review captures complete")
            unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance)


if __name__ == "__main__":
    main()
