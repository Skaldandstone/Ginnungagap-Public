# Space-System Models

`tools/build_space_system_models.py` creates ten celestial and orbital meshes plus the seven exact
star, planet, and sky materials referenced by the procedural star-system implementation.

The mesh library includes reusable star/planet/moon bodies, asteroid variants, orbital resource
nodes, navigation beacons, collector satellites, and drone relays. Celestial meshes omit collision;
interactive orbital objects and asteroid resources receive generated collision.
