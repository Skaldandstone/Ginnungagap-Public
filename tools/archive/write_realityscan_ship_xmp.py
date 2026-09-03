"""Write locked RealityScan camera priors for deterministic ship turntables."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / "Art" / "Ships" / "Exterior" / "RealityScan"
FOCAL_LENGTH_35MM = 58.0
CAPTURE_RADIUS_FACTOR = 2.6


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


def cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def format_vector(values: tuple[float, ...]) -> str:
    return " ".join(f"{value:.15g}" for value in values)


def camera_pose(
    azimuth_deg: float, elevation_deg: float, radius: float
) -> tuple[tuple[float, float, float], tuple[float, ...]]:
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    horizontal = radius * math.cos(elevation)
    position = (
        horizontal * math.cos(azimuth),
        horizontal * math.sin(azimuth),
        radius * math.sin(elevation),
    )
    forward = normalize(tuple(-value for value in position))
    right = normalize(cross(forward, (0.0, 0.0, 1.0)))
    down = normalize(cross(forward, right))
    rotation = right + down + forward
    return position, rotation


def xmp_document(position: tuple[float, ...], rotation: tuple[float, ...]) -> str:
    return f"""<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:xcr="http://www.capturingreality.com/ns/xcr/1.1#"
       xcr:Version="4" xcr:ExportCoordinateSystemType="3" xcr:PosePrior="locked"
       xcr:Coordinates="absolute" xcr:DistortionModel="perspective"
       xcr:DistortionCoeficients="0 0 0 0 0 0" xcr:FocalLength35mm="{FOCAL_LENGTH_35MM:g}"
       xcr:Skew="0" xcr:AspectRatio="1" xcr:PrincipalPointU="0" xcr:PrincipalPointV="0"
       xcr:CalibrationPrior="locked" xcr:CalibrationGroup="0" xcr:DistortionGroup="0"
       xcr:InTexturing="1" xcr:InMeshing="1">
      <xcr:Rotation>{format_vector(rotation)}</xcr:Rotation>
      <xcr:Position>{format_vector(position)}</xcr:Position>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
"""


def process_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    input_dir = manifest_path.parent / "InputFrames"
    radius = max(manifest["normalized_proxy_bounds"]) * CAPTURE_RADIUS_FACTOR
    written = 0
    for frame in manifest["frames"]:
        image_path = input_dir / frame["file"]
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        position, rotation = camera_pose(
            float(frame["azimuth_deg"]), float(frame["elevation_deg"]), radius
        )
        image_path.with_suffix(".xmp").write_text(
            xmp_document(position, rotation), encoding="utf-8"
        )
        frame["camera_position"] = [round(value, 9) for value in position]
        frame["camera_rotation_right_down_forward"] = [
            round(value, 12) for value in rotation
        ]
        written += 1
    manifest["camera_prior"] = "locked"
    manifest["camera_focal_length_35mm"] = FOCAL_LENGTH_35MM
    manifest["camera_xmp_count"] = written
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"asset": manifest["asset"], "xmp_count": written}


def main() -> None:
    results = [
        process_manifest(path)
        for path in sorted(CAPTURE_ROOT.glob("*/CaptureManifest.json"))
    ]
    if not results:
        raise RuntimeError(f"No capture manifests found under {CAPTURE_ROOT}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
