"""Write locked RealityScan camera priors for clean robot turntables."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / "Art/Robots/Uncorrupted/RealityScan"


def normalize(values):
    length = math.sqrt(sum(value * value for value in values))
    return tuple(value / length for value in values)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def format_vector(values):
    return " ".join(f"{value:.15g}" for value in values)


def xmp_document(position, rotation, focal_length):
    return f'''<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:xcr="http://www.capturingreality.com/ns/xcr/1.1#"
       xcr:Version="4" xcr:ExportCoordinateSystemType="3" xcr:PosePrior="locked"
       xcr:Coordinates="absolute" xcr:DistortionModel="perspective"
       xcr:DistortionCoeficients="0 0 0 0 0 0" xcr:FocalLength35mm="{focal_length:.9g}"
       xcr:Skew="0" xcr:AspectRatio="1" xcr:PrincipalPointU="0" xcr:PrincipalPointV="0"
       xcr:CalibrationPrior="locked" xcr:CalibrationGroup="0" xcr:DistortionGroup="0"
       xcr:InTexturing="1" xcr:InMeshing="1">
      <xcr:Rotation>{format_vector(rotation)}</xcr:Rotation>
      <xcr:Position>{format_vector(position)}</xcr:Position>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
'''


def process(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = tuple(manifest["target_cm"])
    focal_length = 18.0 / math.tan(math.radians(manifest["fov_degrees"] * 0.5))
    input_dir = manifest_path.parent / "InputFrames"
    for frame in manifest["frames"]:
        position = tuple(frame["camera_location_cm"])
        forward = normalize(tuple(target[index] - position[index] for index in range(3)))
        right = normalize(cross(forward, (0.0, 0.0, 1.0)))
        down = normalize(cross(forward, right))
        rotation = right + down + forward
        image_path = input_dir / frame["file"]
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        image_path.with_suffix(".xmp").write_text(
            xmp_document(position, rotation, focal_length), encoding="utf-8"
        )
        frame["camera_rotation_right_down_forward"] = [round(value, 12) for value in rotation]
    manifest["camera_prior"] = "locked"
    manifest["camera_focal_length_35mm"] = focal_length
    manifest["camera_xmp_count"] = len(manifest["frames"])
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"asset": manifest["asset"], "xmp_count": len(manifest["frames"])}


def main():
    manifests = sorted(CAPTURE_ROOT.glob("*/CaptureManifest.json"))
    if not manifests:
        raise RuntimeError(f"No clean robot capture manifests found under {CAPTURE_ROOT}")
    print(json.dumps([process(path) for path in manifests], indent=2))


if __name__ == "__main__":
    main()
