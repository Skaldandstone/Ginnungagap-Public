"""Capture and finish the synchronized Unreal Engine full-3D CGI trailer."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import math
import subprocess
import time
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageGrab


FPS = 30
WIDTH, HEIGHT = 1280, 720
TRAILER_SECONDS = 34.0
INTRO_SECONDS = 2.6
OUTRO_SECONDS = 3.0
SAMPLE_RATE = 48_000

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "Saved" / "Demo"
VIDEO_ONLY = DEMO / "Ginnungagap_Full3D_CGI_Trailer_Video.mp4"
SOUNDTRACK = DEMO / "Ginnungagap_Full3D_CGI_Trailer_Soundtrack.wav"
OUTPUT = DEMO / "Ginnungagap_Full3D_CGI_Trailer.mp4"
TEST_FRAME = DEMO / "Ginnungagap_Full3D_CGI_Test.png"
TEST_SHEET = DEMO / "Ginnungagap_Full3D_CGI_QA_Sheet.png"
TRIGGER = DEMO / "StartCGITrailer.trigger"
PROJECT = ROOT / "Ginnungagap.uproject"
UNREAL = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.GetWindowDC.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowDC.restype = ctypes.wintypes.HDC
user32.ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.PrintWindow.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC, ctypes.wintypes.UINT]
user32.PrintWindow.restype = ctypes.wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [ctypes.wintypes.HDC]
gdi32.CreateCompatibleDC.restype = ctypes.wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = ctypes.wintypes.HBITMAP
gdi32.SelectObject.argtypes = [ctypes.wintypes.HDC, ctypes.wintypes.HGDIOBJ]
gdi32.SelectObject.restype = ctypes.wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [ctypes.wintypes.HDC]
SW_RESTORE = 9
KEYUP = 0x0002


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.wintypes.LONG),
        ("biHeight", ctypes.wintypes.LONG),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.wintypes.DWORD * 3)]


gdi32.GetDIBits.argtypes = [
    ctypes.wintypes.HDC,
    ctypes.wintypes.HBITMAP,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(BITMAPINFO),
    ctypes.wintypes.UINT,
]
gdi32.GetDIBits.restype = ctypes.c_int


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def find_window(expected_process_id: int, timeout: float = 120.0) -> int:
    deadline = time.time() + timeout
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    while time.time() < deadline:
        matches: list[int] = []

        def callback(hwnd: int, _lparam: int) -> bool:
            process_id = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            if process_id.value != expected_process_id:
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                title = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title, length + 1)
                if title.value.startswith("Ginnungagap") and user32.IsWindowVisible(hwnd):
                    matches.append(hwnd)
            return True

        user32.EnumWindows(callback_type(callback), 0)
        if matches:
            return matches[0]
        time.sleep(0.25)
    raise RuntimeError("Timed out waiting for the Unreal trailer window")


def client_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + rect.right, point.y + rect.bottom


def focus_window(hwnd: int) -> None:
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)


def grab_window(hwnd: int) -> Image.Image:
    """Render a window by handle so capture is not affected by foreground-app occlusion."""
    outer = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(outer)):
        raise RuntimeError("GetWindowRect failed")
    outer_width = outer.right - outer.left
    outer_height = outer.bottom - outer.top
    source_dc = user32.GetWindowDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(source_dc)
    bitmap = gdi32.CreateCompatibleBitmap(source_dc, outer_width, outer_height)
    previous = gdi32.SelectObject(memory_dc, bitmap)
    try:
        if not user32.PrintWindow(hwnd, memory_dc, 2):
            return ImageGrab.grab(client_rect(hwnd))
        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = outer_width
        info.bmiHeader.biHeight = -outer_height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0
        buffer = ctypes.create_string_buffer(outer_width * outer_height * 4)
        if not gdi32.GetDIBits(memory_dc, bitmap, 0, outer_height, buffer, ctypes.byref(info), 0):
            raise RuntimeError("GetDIBits failed")
        image = Image.frombuffer("RGB", (outer_width, outer_height), buffer, "raw", "BGRX", 0, 1)
        client = ctypes.wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(client))
        client_origin = ctypes.wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(client_origin))
        offset_x = client_origin.x - outer.left
        offset_y = client_origin.y - outer.top
        return image.crop((offset_x, offset_y, offset_x + client.right, offset_y + client.bottom))
    finally:
        gdi32.SelectObject(memory_dc, previous)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, source_dc)


def key(vk: int, down: bool) -> None:
    user32.keybd_event(vk, 0, 0 if down else KEYUP, 0)


def tap(vk: int) -> None:
    key(vk, True)
    key(vk, False)


def type_text(value: str) -> None:
    for character in value:
        packed = user32.VkKeyScanW(ord(character))
        vk = packed & 0xFF
        modifiers = (packed >> 8) & 0xFF
        if modifiers & 1:
            key(0x10, True)
        key(vk, True)
        key(vk, False)
        if modifiers & 1:
            key(0x10, False)


def console(command: str) -> None:
    tap(0xC0)
    time.sleep(0.12)
    type_text(command)
    tap(0x0D)
    time.sleep(0.12)


def title_card(title: str, subtitle: str, seconds: float, outro: bool = False):
    frames = int(round(seconds * FPS))
    rng = np.random.default_rng(77 if not outro else 117)
    stars = [(int(rng.integers(0, WIDTH)), int(rng.integers(0, HEIGHT)), int(rng.integers(40, 145))) for _ in range(180)]
    for index in range(frames):
        image = Image.new("RGB", (WIDTH, HEIGHT), (2, 4, 9))
        draw = ImageDraw.Draw(image)
        for x, y, glow in stars:
            draw.point((x, y), fill=(glow // 2, glow // 3, glow))
        pulse = 0.5 + 0.5 * math.sin(index * 0.12)
        accent = (112 + int(32 * pulse), 30, 220 + int(30 * pulse))
        draw.rectangle((72, 78, 80, 642), fill=accent)
        draw.text((120, 238), title, font=font(54 if not outro else 61, True), fill=(235, 238, 244))
        draw.text((123, 320), subtitle, font=font(23), fill=(160, 169, 185))
        draw.text((123, 613), "FULL 3D IN-ENGINE CINEMATIC", font=font(14, True), fill=accent)
        alpha = min(1.0, index / 12.0, (frames - index - 1) / 12.0)
        array = np.asarray(image, dtype=np.float32)
        yield np.asarray(np.clip(array * max(0.0, alpha), 0, 255), dtype=np.uint8)


SHOT_LABELS = (
    (0.0, 3.5, "A DEAD SHIP DRIFTS"),
    (3.5, 7.0, "RUN"),
    (7.0, 10.5, "THE BODIES WERE SEALED"),
    (10.5, 14.0, "THE CREW IS STILL MOVING"),
    (14.0, 17.5, "THE MACHINES ARE HUNGRY"),
    (17.5, 23.5, "HOLD THE CORRIDOR"),
    (23.5, 27.0, "GRAVITY FAILURE"),
    (27.0, 32.0, "THE COLONY IS IN THE REACTOR"),
    (32.0, 34.0, "THE BLOOM ADAPTS"),
)


def finish_frame(frame: Image.Image, trailer_time: float) -> np.ndarray:
    image = frame.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, WIDTH, 34), fill=(0, 0, 0, 255))
    draw.rectangle((0, HEIGHT - 34, WIDTH, HEIGHT), fill=(0, 0, 0, 255))
    for start, end, label in SHOT_LABELS:
        if start <= trailer_time < end:
            local = trailer_time - start
            fade = min(1.0, local / 0.35, (end - trailer_time) / 0.4)
            if fade > 0:
                box_alpha = int(150 * fade)
                text_alpha = int(238 * fade)
                draw.rectangle((54, 568, 620, 650), fill=(0, 0, 0, box_alpha))
                draw.rectangle((54, 568, 60, 650), fill=(125, 28, 245, text_alpha))
                draw.text((84, 591), label, font=font(25, True), fill=(245, 245, 248, text_alpha))
            break
    result = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    return np.asarray(result, dtype=np.uint8)


def build_soundtrack(duration: float) -> None:
    count = int(duration * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    rng = np.random.default_rng(9321)

    drone = (0.16 * np.sin(2 * np.pi * 32.0 * t)
             + 0.09 * np.sin(2 * np.pi * 47.0 * t + 0.8)
             + 0.055 * np.sin(2 * np.pi * 73.0 * t + 1.7))
    modulation = 0.55 + 0.45 * np.sin(2 * np.pi * 0.087 * t) ** 2
    noise = rng.normal(0, 1, count)
    noise = np.convolve(noise, np.ones(100) / 100.0, mode="same") * 0.10
    audio = drone * modulation + noise

    visual_offset = INTRO_SECONDS
    cut_times = [0.0, 3.5, 7.0, 10.5, 14.0, 17.5, 23.5, 27.0, 32.0, 34.0]
    for shot_index, cut in enumerate(cut_times):
        center = int((visual_offset + cut) * SAMPLE_RATE)
        length = int((0.9 if shot_index in (5, 7, 8) else 0.55) * SAMPLE_RATE)
        end = min(count, center + length)
        if end <= center:
            continue
        x = np.arange(end - center) / SAMPLE_RATE
        env = np.exp(-x * (3.2 if shot_index in (5, 7, 8) else 5.0))
        impact = (0.40 * np.sin(2 * np.pi * (48 - 18 * x) * x) + rng.normal(0, 0.16, len(x))) * env
        audio[center:end] += impact

    # Alarm rhythm, weapon bursts, and reactor pulse.
    for beat in np.arange(visual_offset + 4.0, visual_offset + 24.0, 1.35):
        center = int(beat * SAMPLE_RATE)
        length = min(int(0.18 * SAMPLE_RATE), count - center)
        x = np.arange(length) / SAMPLE_RATE
        audio[center:center + length] += 0.11 * np.sin(2 * np.pi * 620 * x) * np.exp(-x * 12)
    for beat in (visual_offset + 18.4, visual_offset + 19.1, visual_offset + 20.3, visual_offset + 21.8, visual_offset + 22.5):
        center = int(beat * SAMPLE_RATE)
        length = min(int(0.14 * SAMPLE_RATE), count - center)
        x = np.arange(length) / SAMPLE_RATE
        burst = rng.normal(0, 0.5, length) * np.exp(-x * 28) + 0.22 * np.sin(2 * np.pi * 95 * x) * np.exp(-x * 16)
        audio[center:center + length] += burst
    reactor_start = visual_offset + 27.0
    mask = t >= reactor_start
    ramp = np.clip((t - reactor_start) / 6.0, 0, 1)
    audio += mask * ramp * 0.17 * np.sin(2 * np.pi * (58 + 5 * np.sin(t * 0.7)) * t)

    fade = np.minimum(np.clip(t / 1.8, 0, 1), np.clip((duration - t) / 2.4, 0, 1))
    audio = np.tanh(audio * 1.35) * fade
    left = audio
    right = np.roll(audio, 41) * 0.96
    stereo = np.column_stack((left, right)).reshape(-1)
    pcm = (np.clip(stereo, -0.96, 0.96) * 32767).astype(np.int16)
    with wave.open(str(SOUNDTRACK), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def launch_unreal() -> subprocess.Popen:
    if not UNREAL.exists():
        raise FileNotFoundError(UNREAL)
    args = [
        str(UNREAL), str(PROJECT), "/Game/Untitled", "-game", "-CGITrailer",
        "-CGITrailerDelay=60", "-CGITrailerTimeDilation=0.38", "-windowed", "-ForceRes",
        f"-ResX={WIDTH}", f"-ResY={HEIGHT}", "-NoSplash", "-NoLoadingScreen", "-NoSound",
        "-ExecCmds=r.VSync 0,r.ScreenPercentage 100,r.MotionBlurQuality 4,r.BloomQuality 5",
    ]
    return subprocess.Popen(args, cwd=ROOT)


def capture(test_only: bool) -> Path:
    DEMO.mkdir(parents=True, exist_ok=True)
    TRIGGER.unlink(missing_ok=True)
    process = launch_unreal()
    hwnd = 0
    try:
        hwnd = find_window(process.pid)
        focus_window(hwnd)
        time.sleep(4.0)
        focus_window(hwnd)
        rect = client_rect(hwnd)
        if rect[2] - rect[0] < 1000 or rect[3] - rect[1] < 600:
            raise RuntimeError(f"Unexpected Unreal client size: {rect}")
        user32.SetCursorPos(rect[2] + 20, rect[3] + 20)

        if test_only:
            TRIGGER.write_text("start\n", encoding="utf-8")
            test_times = (2.0, 5.2, 8.7, 12.2, 15.7, 20.5, 25.2, 29.5, 33.0)
            captured: list[Image.Image] = []
            start = time.perf_counter()
            for shot_time in test_times:
                while time.perf_counter() - start < shot_time:
                    time.sleep(0.02)
                focus_window(hwnd)
                captured.append(grab_window(hwnd).resize((426, 240), Image.Resampling.LANCZOS))
            sheet = Image.new("RGB", (1278, 720), (0, 0, 0))
            draw = ImageDraw.Draw(sheet)
            for index, (shot_time, frame) in enumerate(zip(test_times, captured)):
                x = (index % 3) * 426
                y = (index // 3) * 240
                sheet.paste(frame, (x, y))
                draw.rectangle((x + 8, y + 8, x + 86, y + 33), fill=(0, 0, 0))
                draw.text((x + 16, y + 11), f"{shot_time:04.1f}s", font=font(14, True), fill=(220, 220, 230))
            sheet.save(TEST_SHEET)
            return TEST_SHEET

        writer = imageio.get_writer(str(VIDEO_ONLY), fps=FPS, codec="libx264", quality=8, macro_block_size=None)
        try:
            for frame in title_card("GINNUNGAGAP", "Something aboard the corvette is rebuilding itself", INTRO_SECONDS):
                writer.append_data(frame)

            TRIGGER.write_text("start\n", encoding="utf-8")
            start = time.perf_counter()
            total_frames = int(round(TRAILER_SECONDS * FPS))
            for frame_index in range(total_frames):
                target = start + frame_index / FPS
                while True:
                    remaining = target - time.perf_counter()
                    if remaining <= 0:
                        break
                    time.sleep(min(remaining, 0.003))
                if frame_index % 90 == 0:
                    focus_window(hwnd)
                grabbed = grab_window(hwnd)
                writer.append_data(finish_frame(grabbed, frame_index / FPS))

            for frame in title_card("DO NOT LET IT JUMP", "Survive the ship. Burn out the Bloom.", OUTRO_SECONDS, True):
                writer.append_data(frame)
        finally:
            writer.close()

        duration = INTRO_SECONDS + TRAILER_SECONDS + OUTRO_SECONDS
        build_soundtrack(duration)
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([
            ffmpeg, "-y", "-i", str(VIDEO_ONLY), "-i", str(SOUNDTRACK),
            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", str(OUTPUT),
        ], check=True)
        return OUTPUT
    finally:
        TRIGGER.unlink(missing_ok=True)
        if hwnd and user32.IsWindow(hwnd):
            focus_window(hwnd)
            try:
                console("quit")
            except Exception:
                pass
        try:
            process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-only", action="store_true", help="Capture one representative 3D frame and exit")
    args = parser.parse_args()
    print(capture(args.test_only))


if __name__ == "__main__":
    main()
