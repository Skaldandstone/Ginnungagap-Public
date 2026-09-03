"""Render presentation stills of the dressed demo slice.

Separate from capture_slice_review.py, which exists to answer "is this broken" and frames every room
the same way from above so that faults are easy to compare. These are the opposite: hand-placed,
eye-level, composed, and at presentation resolution. A review shot and a hero shot want different
things from the same room and trying to get both from one rig gets neither.

Camera positions were hand-chosen in the first version and one of six landed -- the cryo camera
ended up inside a pod, the CIC camera behind a console. Composing a shot by typing coordinates into
a room full of props you cannot see is guessing. Room cameras are now derived from a rule: stand in
the doorway and look in, which is both reliably clear of the contents and the composition a player
actually gets walking in. Corridors keep hand-placed cameras, having nothing to be inside of.

Shots are eye-level at 165cm because the demo is first person and a grant reviewer should be
looking at what a player looks at. Nothing is shot from above.

No fill lighting and no exposure override: what comes out is what the map does. If a frame is too
dark the answer is to light the map, not the camera.

Run with ExecCmds rather than ExecutePythonScript:
    UnrealEditor.exe <project> -ExecCmds="py <this file>" -nosplash -NoSound

-ExecutePythonScript quits the editor the moment the script returns and this schedules work on a
tick callback, so it would exit cleanly having rendered nothing. It also needs the windowed editor:
high-res screenshots require a real viewport and UnrealEditor-Cmd.exe silently produces no files.
"""

import os
import time
from pathlib import Path

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
OUTPUT = Path(unreal.SystemLibrary.get_project_saved_directory()) / "HeroShots"

WIDTH, HEIGHT = 2560, 1440
EYE = 165.0

# Seconds each shot converges before it is taken. Longer than the review rig: Lumen accumulates,
# streamed textures arrive on their own schedule, and a hero shot that is one frame short of
# converged looks like a bad renderer rather than an early build.
# Raised from 12, and the frame floor below it from 45.
#
# Both were set when the demo map held a few hundred actors. It now holds ~900 dressed actors plus
# biomass, capsules, industrial props and five threats, and Lumen has correspondingly more to
# converge. Two symptoms point the same way: shots started exceeding a 420s task deadline, and the
# workshop came back visibly darker than its previous render despite nothing in that room having
# been lit differently -- which is what an unconverged indirect bounce looks like.
#
# Frames and wall clock both, still, for the original reason: a frame in a stalled editor costs
# nothing and the counter drains instantly.
SETTLE_SECONDS = 30.0

# Longest a single shot may take before the batch gives up on it and moves to the next.
#
# Generous, because a legitimately slow shot is worth waiting for: Lumen convergence on a dark room
# is genuinely slower than on a lit one, and one shot has honestly taken ten minutes. This is the
# guard against the other case, where is_task_done() simply never comes true -- which has now
# happened twice and cost half an hour of an unattended batch the second time.
# Raised from 420. At 420 a full batch lost four of eight shots in one run -- the map has gained
# roughly 300 dressing actors, six biomass masses, four capsules and 25 industrial props since that
# number was set, and Lumen has correspondingly more to converge. The guard is still doing its job
# (the batch finished rather than hanging on the first stuck shot), it was simply set for a lighter
# level than the one that exists now.
SHOT_DEADLINE_SECONDS = 900.0

# Deck section centres. Floors sit 195 below.
DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0


def at(deck, x, y, height=EYE):
    return unreal.Vector(x, y, DECK[deck] - FLOOR_DROP + height)


# Rooms to shoot, by the deck and centre they sit at. Cameras are derived rather than hand-placed.
#
# The first version hand-placed six cameras from coordinates and one of the six landed. The cryo
# camera ended up inside a pod and the CIC camera behind a console: composing a shot by typing
# numbers, in a room full of props you cannot see, is guessing. A rule that frames every room
# adequately beats six guesses that mostly do not.
#
# The rule: stand in the doorway and look in. Every room opens onto the central corridor, so the
# doorway is a known position -- corridor side, room centre X -- and looking from there into the
# room is both reliably clear of the contents and the composition a player actually gets when they
# walk in.
#
# The rule has one exception, and it is the exception a rule like this always grows: a room crowded
# enough that every direction has something a metre from the lens.
#
# The CIC holds four stations, two chairs, a holographic plot and three tall concept props inside
# 11 x 10 m. Two doorway shots produced a black silhouette across the middle of frame, and the
# second attempt moved the camera out of one obstruction and into a different one. A third guess was
# not worth taking, so tools/survey_cic_room.py measured the room instead, and this camera is placed
# against those measurements: from the back corner, looking diagonally across, on a line that
# threads the 219cm gap between two of the concept props and puts the holographic plot dead on axis
# at 5.7 m.
#
# The cryo bay was tried as a second exception and put back. Worth keeping the reasoning, because
# the attempt disproved the thing it was testing.
#
# With the lids shut, the doorway shot put two bright horizontal glass planes across the middle of
# frame, so the camera was raised to 250cm to look down the row instead of across it. That made it
# **worse**: a horizontal lid seen from above presents its whole area, where from the side it
# presents an edge. The high camera maximised exactly what it was meant to reduce.
#
# Shooting along the row instead is not available -- the room is 1100 x 1000 and the four pods span
# 720 of it, so any camera at the row's end is inside the first pod.
#
# Which leaves the conclusion: the lid glass is bright in every framing this room allows, and no
# camera position fixes that. M_Cryo_CrackedFrostGlass is the lever, not the lens. Reverted to the
# doorway rule, which remains the best of the three.
#
# The per-shot heights below survive the revert. They are a real improvement to the rig -- the CIC
# aims slightly up at a holographic plot and a floor-level subject wants the opposite, and a single
# fixed eye level cannot do both.
#
# So a room may override the rule with explicit camera and target offsets from its own centre, plus
# both heights. All zeros means "use the doorway rule", which is every other room.
#
# (name, deck, room X, room Y, fov, cam dx, cam dy, cam height, target dx, target dy, target height)
ROOM_SHOTS = [
    ("01_CryoWake",     3, -6600.0, -680.0, 78.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("03_EngineRoom",   2, -6600.0, -680.0, 78.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("04_CIC",          3,  6600.0,  680.0, 74.0, -400.0, 400.0, EYE,    300.0, -300.0, EYE + 35.0),
    ("05_BloomBreach",  3,  5400.0, -680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("07_Workshop",     3, -5400.0, -680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("08_PowerControl", 2, -5400.0,  680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
]

# Corridor shots keep hand-placed cameras: a corridor has no contents to be inside of, and the one
# hand-placed shot that worked was down the spine.
# (name, deck, camera X, target X, field of view)
# X positions matter now in a way they did not before. The corridors light every other 12 m bay, so
# the fixtures sit at -6600, -4200, -1800 and so on, and a camera standing between two of them opens
# on a black foreground. -6300 puts the camera just inside the first pool: lit where the player is,
# falling away down the length of the ship, which is the shot.
CORRIDOR_SHOTS = [
    ("02_CorridorSpine", 3, -6300.0, 2500.0, 80.0),
    ("06_LowerDeck",     1, -1500.0, 5000.0, 82.0),
]

# How far into the corridor the camera stands, and how far past the room centre it looks.
DOORWAY_OFFSET = 260.0
LOOK_PAST = 300.0


def build_shots():
    """(name, camera, target, fov) for every shot."""
    shots = []

    for (name, deck, room_x, room_y, fov,
         cam_dx, cam_dy, cam_h, tgt_dx, tgt_dy, tgt_h) in ROOM_SHOTS:
        if cam_dx or cam_dy or tgt_dx or tgt_dy:
            # Hand-placed against the room's measured contents, heights included -- the CIC looks
            # slightly up at a holographic plot and cryo looks down at a floor of pods, and no
            # single eye level serves both.
            shots.append((
                name,
                at(deck, room_x + cam_dx, room_y + cam_dy, cam_h),
                at(deck, room_x + tgt_dx, room_y + tgt_dy, tgt_h),
                fov,
            ))
            continue

        # Rooms sit either side of the centreline; the doorway is on whichever side faces it.
        side = 1.0 if room_y > 0.0 else -1.0
        shots.append((
            name,
            at(deck, room_x, side * DOORWAY_OFFSET),
            at(deck, room_x, room_y + side * LOOK_PAST, EYE - 45.0),
            fov,
        ))

    for name, deck, camera_x, target_x, fov in CORRIDOR_SHOTS:
        shots.append((
            name,
            at(deck, camera_x, 0.0),
            at(deck, target_x, 0.0, EYE - 25.0),
            fov,
        ))

    shots.sort(key=lambda shot: shot[0])
    return shots


SHOTS = build_shots()


def configure_camera(camera, fov):
    component = camera.get_component_by_class(unreal.CameraComponent)
    component.set_editor_property("field_of_view", fov)
    # The map's own post process is the look being presented. Overriding it here would produce
    # images the game does not make.
    component.set_editor_property("post_process_blend_weight", 0.0)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load " + MAP)

    unreal.AutomationLibrary.finish_loading_before_screenshot()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # Ceilings hidden, as in the review rig. A first-person camera does not see much deckhead, but
    # the kit's ceiling tiles sit low enough to clip the top of a wide shot.
    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if "SM_CEILING" in label or "Ceiling_" in label:
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)

    only = {name.strip() for name in os.environ.get("HERO_SHOT_ONLY", "").split(",")
            if name.strip()}
    pending = [s for s in SHOTS if not only or s[0] in only]
    if not pending:
        unreal.log_error("No shots matched HERO_SHOT_ONLY")
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")
        return

    state = {"pending": pending, "task": None, "camera": None, "output": None,
             "name": "", "frames": 0, "started": time.time(), "callback": None}

    def schedule_next():
        name, location, target, fov = state["pending"].pop(0)
        for command in ("ShowFlag.Grid 0", "ShowFlag.Sprites 0",
                        "ShowFlag.SelectionOutline 0", "ShowFlag.CompositeEditorPrimitives 0"):
            unreal.SystemLibrary.execute_console_command(world, command)

        camera = actors_api.spawn_actor_from_class(
            unreal.CameraActor, location,
            unreal.MathLibrary.find_look_at_rotation(location, target))
        camera.set_actor_label("HeroShotCamera_" + name)
        configure_camera(camera, fov)

        output = (OUTPUT / ("Hero_" + name + ".png")).resolve()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            WIDTH, HEIGHT, str(output), camera=camera, delay=1.0, force_game_view=True)
        if not task or not task.is_valid_task():
            raise RuntimeError("Could not schedule hero shot " + name)
        state.update(task=task, camera=camera, output=output, name=name,
                     frames=0, started=time.time())

    def advance(_delta):
        state["frames"] += 1
        elapsed = time.time() - state["started"]

        # A shot that never finishes must not take the rest of the batch with it.
        #
        # is_task_done() has now failed to come true twice, both times on the *second* shot of a
        # batch: once for ten minutes and once for twenty-five, and the second one was killed by
        # hand. Whatever the cause, hanging forever is the wrong response to it -- the whole point
        # of a batch is coming back to eight finished images, and one stuck shot silently costing
        # the other seven is worse than one missing image.
        #
        # So a shot gets its deadline and then the batch moves on. The file is checked either way,
        # because a task that never reports done sometimes wrote its image anyway.
        timed_out = elapsed > SHOT_DEADLINE_SECONDS
        if not timed_out and (state["frames"] < 150
                or elapsed < SETTLE_SECONDS
                or not state["task"].is_task_done()):
            return

        if timed_out:
            unreal.log_warning("HERO {} did not report done within {:.0f}s; moving on".format(
                state["name"], SHOT_DEADLINE_SECONDS))

        if state["output"].exists():
            unreal.log("HERO captured {}".format(state["name"]))
        else:
            unreal.log_error("HERO missing {}".format(state["output"]))

        actors_api.destroy_actor(state["camera"])
        if state["pending"]:
            schedule_next()
        else:
            unreal.unregister_slate_post_tick_callback(state["callback"])
            unreal.log("HERO all shots complete")
            unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance)


if __name__ == "__main__":
    main()
