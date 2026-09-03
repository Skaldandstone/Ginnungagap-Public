"""Derive game-ready PBR channels from the approved concept-art skin albedos."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Content" / "Characters" / "Player" / "Skins" / "Source"


def save_gray(values, path):
    Image.fromarray(np.clip(values * 255.0, 0, 255).astype(np.uint8), "L").save(path)


def build_channels(role):
    path = SOURCE / f"T_PlayerSkin_{role}.png"
    image = Image.open(path).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    height = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    # Fine fabric detail drives the tangent-space normal without baking lighting.
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    strength = 5.0
    normal = np.dstack((-dx * strength, -dy * strength, np.ones_like(height)))
    normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-6)
    normal = normal * 0.5 + 0.5
    Image.fromarray((normal * 255).astype(np.uint8), "RGB").save(
        SOURCE / f"T_PlayerSkin_{role}_Normal.png")

    saturation = rgb.max(axis=2) - rgb.min(axis=2)
    roughness = np.clip(0.84 - saturation * 0.22 - height * 0.12, 0.48, 0.9)
    save_gray(roughness, SOURCE / f"T_PlayerSkin_{role}_Roughness.png")

    # Only dark, low-saturation reinforcement/hardware regions receive metallic response.
    metallic = np.clip((0.42 - height) * 2.8, 0, 1) * np.clip(1.0 - saturation * 1.6, 0, 1)
    metallic = np.where(metallic > 0.38, metallic * 0.42, 0.0)
    save_gray(metallic, SOURCE / f"T_PlayerSkin_{role}_Metallic.png")

    blurred = np.asarray(Image.fromarray((height * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(radius=10)), dtype=np.float32) / 255.0
    ao = np.clip(0.86 + (height - blurred) * 0.75, 0.62, 1.0)
    save_gray(ao, SOURCE / f"T_PlayerSkin_{role}_AO.png")


def main():
    for role in ("Crew", "Engineering", "Medical", "Security"):
        build_channels(role)


if __name__ == "__main__":
    main()
