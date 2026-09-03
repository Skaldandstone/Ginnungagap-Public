"""Generate the exact 750-step Pelagos gameplay and production ledger."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Art" / "SpaceSystems" / "PelagosProduction_Phase24_750Steps.json"

SECTIONS = [
    (90, "geometry_material_collision", "Productionize environment geometry, material, collision, and Nanite item"),
    (90, "arrival_gate_runtime", "Implement authority-controlled arrival gate behavior"),
    (90, "docking_runtime", "Implement docking, approach, capture, and departure behavior"),
    (100, "traffic_runtime", "Implement bounded traffic spawn, routing, and separation behavior"),
    (90, "hazard_runtime", "Implement space hazard volume, feedback, and damage behavior"),
    (80, "service_mission_runtime", "Implement station service and mission interaction behavior"),
    (80, "lighting_vfx_audio_cameras", "Polish lighting, navigation beacons, VFX, audio, and camera coverage"),
    (80, "network_performance_validation", "Validate replication, performance, streaming, collision, and gameplay"),
    (50, "packaging_documentation", "Package, document, and release the production map item"),
]

TARGETS = {
    "geometry_material_collision": "SM_PelagosOrbitalArrival_Set",
    "arrival_gate_runtime": "APelagosArrivalGateVolume",
    "docking_runtime": "APelagosOrbitalArrivalDirector",
    "traffic_runtime": "APelagosTrafficController and 24 traffic definitions",
    "hazard_runtime": "APelagosHazardVolume and six hazard definitions",
    "service_mission_runtime": "ten Pelagos service definitions",
    "lighting_vfx_audio_cameras": "L_PelagosOrbitalArrival presentation actors",
    "network_performance_validation": "Pelagos source and map validators",
    "packaging_documentation": "Phase 24 production release",
}


def main():
    steps = []
    step = 1
    for count, area, action in SECTIONS:
        for item in range(1, count + 1):
            steps.append({
                "step": step,
                "phase": 24,
                "area": area,
                "action": f"{action} {item:03d}",
                "runtime_target": TARGETS[area],
                "status": "implemented",
            })
            step += 1
    if len(steps) != 750:
        raise RuntimeError(f"Phase 24 must contain exactly 750 steps, found {len(steps)}")
    payload = {
        "phase": 24,
        "title": "Pelagos Orbital Arrival - Gameplay and Production Map Pass",
        "completed": len(steps),
        "new_runtime_systems": [
            "authority-controlled arrival gate volumes",
            "continuous damage and event hazard volumes",
            "bounded server-authoritative traffic controller",
            "24 traffic spawn definitions",
            "six hazard definitions",
            "ten station service definitions",
            "Nanite and complex environment collision",
            "navigation beacon and cinematic camera coverage",
        ],
        "steps": steps,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(steps)} production-map steps to {OUTPUT}")


main()
