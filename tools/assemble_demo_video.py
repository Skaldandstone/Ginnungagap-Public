"""Assembles the recorded walkthrough frames into the demo video.

The walkthrough test, run under a windowed editor with -GinnungagapRecordWalk and a fixed 30 Hz
timestep, writes one screenshot per frame -- Frame_000000.png onward -- of the player's own view,
HUD included, from the opening shot on the sleeper through the title card. This turns that
sequence into an H.264 MP4 with ffmpeg, which is on this machine through winget's yt-dlp bundle.

No audio: a screenshot has none. The roar, the hull strike, the alarms are all real in-game sounds
and can be laid back in from their source WAVs under Intermediate/ShipProduction/Environment on
the same fixed timeline, but that is an edit, not a capture.

    python tools/assemble_demo_video.py [--fps 30] [--keep-frames]
"""
import argparse
import datetime as dt
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
OUT_DIR = ROOT / "Saved" / "Video"


def find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = list((Path.home() / "AppData/Local/Microsoft/WinGet/Packages").glob("**/ffmpeg*/bin/ffmpeg.exe"))
    if candidates:
        return str(candidates[0])
    raise SystemExit("ffmpeg not found on PATH or under WinGet packages")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--keep-frames", action="store_true")
    parser.add_argument("--skip-lead-in", type=int, default=2,
                        help="frames to drop from the start; the first two are the editor viewport before PIE has drawn")
    args = parser.parse_args()

    frames = sorted(FRAMES.glob("Frame_*.png"))[args.skip_lead_in:]
    if not frames:
        raise SystemExit("No Frame_*.png under " + str(FRAMES) + "; record the walk first")
    # ffmpeg's image sequence demuxer wants contiguous numbering from a start index.
    staging = OUT_DIR / "frames"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for index, frame in enumerate(frames):
        (staging / f"f_{index:06d}.png").hardlink_to(frame) if hasattr(Path, "hardlink_to") else shutil.copy2(frame, staging / f"f_{index:06d}.png")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    output = OUT_DIR / f"Ginnungagap_DemoWalk_{stamp}.mp4"
    command = [
        find_ffmpeg(), "-y", "-framerate", str(args.fps), "-i", str(staging / "f_%06d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-movflags", "+faststart", str(output),
    ]
    print(" ".join(command))
    subprocess.run(command, check=True)
    seconds = len(frames) / args.fps
    print(f"wrote {output} ({len(frames)} frames, {seconds:.1f} s at {args.fps} fps)")
    if not args.keep_frames:
        shutil.rmtree(staging)


if __name__ == "__main__":
    main()
