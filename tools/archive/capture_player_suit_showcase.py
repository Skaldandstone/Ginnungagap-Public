"""Capture the standalone Unreal suit showcase window to a project PNG."""

import ctypes
import ctypes.wintypes
import time
import sys
from pathlib import Path
from PIL import Image, ImageGrab


OUTPUT_NAME = sys.argv[2] if len(sys.argv) > 2 else "PlayerSuitLineup.png"
OUTPUT = Path(__file__).resolve().parents[1] / "Saved" / "Renders" / OUTPUT_NAME
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", ctypes.wintypes.DWORD), ("biWidth", ctypes.wintypes.LONG),
                ("biHeight", ctypes.wintypes.LONG), ("biPlanes", ctypes.wintypes.WORD),
                ("biBitCount", ctypes.wintypes.WORD), ("biCompression", ctypes.wintypes.DWORD),
                ("biSizeImage", ctypes.wintypes.DWORD), ("biXPelsPerMeter", ctypes.wintypes.LONG),
                ("biYPelsPerMeter", ctypes.wintypes.LONG), ("biClrUsed", ctypes.wintypes.DWORD),
                ("biClrImportant", ctypes.wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.wintypes.DWORD * 3)]


def capture_window(hwnd, width, height):
    window_dc = user32.GetDC(hwnd)
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    old = gdi32.SelectObject(memory_dc, bitmap)
    user32.PrintWindow(hwnd, memory_dc, 3)
    info = BITMAPINFO()
    info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = width
    info.bmiHeader.biHeight = -height
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(info), 0)
    image = Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1).copy()
    gdi32.SelectObject(memory_dc, old)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memory_dc)
    user32.ReleaseDC(hwnd, window_dc)
    return image


def find_game_window():
    found = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if title.value.startswith("Ginnungagap") and "Editor" not in title.value:
                rect = ctypes.wintypes.RECT()
                user32.GetClientRect(hwnd, ctypes.byref(rect))
                found.append((rect.right * rect.bottom, hwnd))
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return max(found)[1] if found else None


def main():
    hwnd = None
    requested_pid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    for _ in range(90):
        if requested_pid:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            process = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, requested_pid)
            if process:
                matches = []
                callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                def by_pid(candidate, _):
                    pid = ctypes.wintypes.DWORD()
                    user32.GetWindowThreadProcessId(candidate, ctypes.byref(pid))
                    if pid.value == requested_pid and user32.IsWindowVisible(candidate):
                        matches.append(candidate)
                    return True
                user32.EnumWindows(callback_type(by_pid), 0)
                ctypes.windll.kernel32.CloseHandle(process)
                if matches:
                    sized = []
                    for candidate in matches:
                        rect = ctypes.wintypes.RECT()
                        user32.GetClientRect(candidate, ctypes.byref(rect))
                        sized.append((rect.right * rect.bottom, candidate))
                    hwnd = max(sized)[1]
        else:
            hwnd = find_game_window()
        if hwnd:
            break
        time.sleep(1)
    if not hwnd:
        raise RuntimeError("Standalone Ginnungagap showcase window was not found")

    user32.ShowWindow(hwnd, 9)
    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    # Allow the streamed level, skeletal meshes, and shader resources to settle.
    time.sleep(10)

    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    bounds = (point.x, point.y, point.x + rect.right, point.y + rect.bottom)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    capture_window(hwnd, rect.right, rect.bottom).save(OUTPUT)
    user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
    user32.PostMessageW(hwnd, 0x0010, 0, 0)
    print(OUTPUT)


if __name__ == "__main__":
    main()
