# Ship Exterior Models

`tools/build_ship_exterior_models.py` generates full-scale exterior silhouettes for the 1.4 km
small utility escort, 2.4 km military corvette, and 6.5 km expedition carrier. It also creates
reusable engine-cluster, radiator-wing, sensor-mast, cargo-pod, and docking-collar modules.

The geometry follows the approved concept roles while remaining legally distinct. The silhouettes
are suitable for exterior traversal planning, sensor views, cinematics, streaming-distance tests,
and later panel/detail replacement. Generated OBJ files are intermediate; Unreal `.uasset` meshes
under `/Game/Assets/Ships/Exterior/Meshes` are runtime assets.

An isolated RealityScan review pass for the same three concepts is documented in
`docs/RealityScanShipFleet.md`. Those scans are comparison candidates and do not replace the
runtime assets without visual approval.
