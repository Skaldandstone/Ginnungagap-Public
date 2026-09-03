"""Capture a repeatable walkthrough of the runtime-built military corvette."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageGrab


FPS = 24
WIDTH, HEIGHT = 1280, 720
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Saved" / "Demo" / "Ginnungagap_Military_Corvette_Walkthrough.mp4"

user32 = ctypes.windll.user32
SW_RESTORE = 9
KEYUP = 0x0002


def find_window() -> int:
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if title.value.startswith("Ginnungagap"):
                matches.append(hwnd)
        return True

    user32.EnumWindows(callback_type(callback), 0)
    if not matches:
        raise RuntimeError("The Ginnungagap game window is not running")
    return matches[0]


def client_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + rect.right, point.y + rect.bottom


def key(vk: int, down: bool) -> None:
    user32.keybd_event(vk, 0, 0 if down else KEYUP, 0)


def tap(vk: int) -> None:
    key(vk, True)
    key(vk, False)


def type_text(value: str) -> None:
    """Type ASCII text into Unreal's console without clipboard dependencies."""
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
    time.sleep(0.15)
    type_text(command)
    tap(0x0D)
    time.sleep(0.6)


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def card(title: str, subtitle: str, accent=(102, 239, 220), seconds=2.0):
    frames = int(seconds * FPS)
    for i in range(frames):
        image = Image.new("RGB", (WIDTH, HEIGHT), (3, 8, 13))
        draw = ImageDraw.Draw(image)
        draw.rectangle((68, 82, 76, 638), fill=accent)
        draw.text((112, 238), title, font=font(52, True), fill=(235, 246, 244))
        draw.text((115, 315), subtitle, font=font(23), fill=(155, 178, 180))
        draw.text((115, 615), "REAL-TIME IN-ENGINE FOOTAGE  |  AUG 2026", font=font(14), fill=accent)
        fade = min(1.0, i / 8, (frames - i) / 8)
        yield np.asarray(image, dtype=np.uint8), fade


def overlay(frame: Image.Image, heading: str, detail: str) -> Image.Image:
    frame = frame.convert("RGB")
    veil = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(veil)
    draw.rounded_rectangle((28, 28, 630, 112), 8, fill=(2, 8, 12, 188), outline=(102, 239, 220, 190), width=2)
    draw.text((50, 43), heading, font=font(25, True), fill=(235, 246, 244, 255))
    draw.text((51, 78), detail, font=font(16), fill=(163, 190, 190, 255))
    return Image.alpha_composite(frame.convert("RGBA"), veil).convert("RGB")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    hwnd = find_window()
    user32.ShowWindow(hwnd, SW_RESTORE)
    # Windows may reject a plain SetForegroundWindow call from a background process.
    # A brief topmost toggle reliably exposes the standalone game for pixel capture.
    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(0.8)
    left, top, right, bottom = client_rect(hwnd)
    cx, cy = (left + right) // 2, (top + bottom) // 2
    user32.SetCursorPos(cx, cy)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.5)

    writer = imageio.get_writer(str(OUTPUT), fps=FPS, codec="libx264", quality=8, macro_block_size=None)
    try:
        for frame, _ in card("MILITARY CORVETTE", "Ginnungagap medium-ship level walkthrough"):
            writer.append_data(frame)

        shots = [
            ("BRIDGE", "Command deck, helm consoles, and forward tactical lighting", "BugItGo 4700 0 0 0 180 0", 3.5, ord("W"), (2, 0)),
            ("COMBAT INFORMATION CENTER", "Armored operations room linking command to the ship's spine", "BugItGo 3150 0 0 0 180 0", 3.5, ord("W"), (-2, 0)),
            ("CENTRAL COMPANIONWAY", "The main junction branches to medical, berthing, and damage control", "BugItGo 500 0 0 0 180 0", 4.0, ord("W"), (3, 0)),
            ("MEDICAL AND CREW WINGS", "Color-coded lateral compartments provide clear navigation", "BugItGo 0 850 0 0 90 0", 3.5, ord("W"), (-3, 0)),
            ("CARGO AND DRONE BAY", "Military storage, cover positions, and resource operations", "BugItGo -1550 -900 0 0 180 0", 3.5, ord("D"), (3, 0)),
            ("ENGINEERING", "Life support and reactor control occupy the armored aft section", "BugItGo -3150 0 0 0 180 0", 4.0, ord("W"), (-2, 0)),
            ("ESCAPE BAY", "Twin evacuation compartments terminate the aft damage-control routes", "BugItGo -4000 900 0 0 90 0", 3.5, ord("W"), (2, 0)),
        ]
        for heading, detail, command, duration, vk, mouse_delta in shots:
            console(command)
            key(vk, True)
            for i in range(int(duration * FPS)):
                # Codex can surface progress while the capture is running; keep the game as the
                # capture target even if another desktop window briefly requests focus.
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                if i % 8 == 0:
                    user32.mouse_event(0x0001, mouse_delta[0], mouse_delta[1], 0, 0)
                captured = ImageGrab.grab((left, top, right, bottom)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                writer.append_data(np.asarray(overlay(captured, heading, detail), dtype=np.uint8))
                time.sleep(0.008)
            key(vk, False)

        for frame, _ in card("READY FOR DEPLOYMENT", "13 compartments  |  connected corridors  |  functional ship systems", (235, 90, 100), 2.5):
            writer.append_data(frame)
    finally:
        for vk in (ord("W"), ord("A"), ord("S"), ord("D")):
            key(vk, False)
        writer.close()
        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    print(OUTPUT)


if __name__ == "__main__":
    main()
