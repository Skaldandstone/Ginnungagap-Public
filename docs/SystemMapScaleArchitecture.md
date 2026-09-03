# System Map and Local Operations Scale

Ginnungagap uses two deliberately separate spatial representations.

## Astronomical system map

The strategic system map is measured in astronomical units. It represents orbital order, relative
distance, travel cost and time, sensor uncertainty, belts, major hazards, jump boundaries, and the
locations from which local operations can be entered. It is a navigation model and may use a
nonlinear visual projection; it is never instantiated directly in Unreal centimeters.

`FSystemMapCoordinate` stores an orbital radius in AU, true anomaly, and inclination. `FStarSystemData`
owns the system extent and its available `FLocalOperationsVolumeDefinition` entries.

Recommended authored scale:

- inner system: 0.1–0.8 AU
- temperate/Pelagos region: approximately 1 AU
- outer giants: 3–8 AU
- ice, comet, and debris regions: 10–30 AU
- interstellar jump boundary: outside the major authored orbits

Planet radii and orbit spacing may be exaggerated visually, but labels, travel calculations, hazard
exposure, and route selection use the astronomical data.

## Local operations volume

A local operations volume is a streamed, ship-relative gameplay bubble measured in kilometers. It
contains the geometry and actors required for flight, docking, EVA, salvage, resources, hazards,
traffic, and missions near one selected point of interest.

The legacy `AProceduralStarSystemMap` class now explicitly serves this role. Its default playable
diameter is 60 km, converted to a 3,000,000 cm Unreal radius when built. The class name remains for
asset and code compatibility; new UI and documentation should call it a local operations volume.

Pelagos Orbital Arrival is one local operations volume anchored to Pelagos on the astronomical map.
Its station is a point-of-interest marker at system-map scale, not the system-map subject.

## Transition

1. The system map displays AU-scale bodies and available destinations.
2. The crew selects a point of interest and plans a route.
3. Travel resolves at strategic scale.
4. The selected `FLocalOperationsVolumeDefinition` streams or generates its kilometer-scale level.
5. Local flight and operations occur without moving astronomical bodies through Unreal world space.
6. Departure returns state changes and discoveries to the strategic system map.

`FSystemPointOfInterest::WorldLocation` remains the local actor/contact location. Its
`SystemMapCoordinate` is authoritative for strategic presentation; the two fields must not be
derived from one another.
