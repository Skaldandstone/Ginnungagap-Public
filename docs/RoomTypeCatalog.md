# Ship Room Type Catalog

This is the canonical room and interior-space catalog for ship planning, procedural-layout design, and concept-art tracking. Individual ships select a subset of these room types according to role, scale, crew, and mission. A room type appearing here does not imply that every ship must contain it.

The GGP-01 Wayfarer currently supplies the established baseline. The additional types below are approved for future Wayfarer sectors and other ship classes.

## Established room types

### Command and mission control

- Primary panoramic bridge
- Flag CIC
- Emergency CIC
- Auxiliary CIC
- Navigation and helm
- Tactical operations
- Secure command
- Strategic sensors
- Sensor analysis
- Observation room
- Briefing room
- Mission-planning room
- Secure communications
- Communications repair
- Chart room
- Secure-records archive
- Encrypted archive
- Drone control
- Redundant flight control
- Officer cabin
- Officer berthing
- Secure storage

### Crew habitat

- Cryo bay
- Cryo refuge
- Crew cabin
- Bunkroom
- Galley
- Medical bay
- Washroom
- Commons
- Recreation room
- Hydroponics
- Life-support access
- General stores
- Field workshop
- Player workshop

### Mission operations and hangars

- Multi-deck hangar bay
- Launch floor
- Recovery floor
- Recovery-machinery room
- Armored magazine
- Maintenance pit
- Ready room
- Flight control
- Hangar workshop
- Service gallery
- Overhead crane and utility level
- Drone storage
- Blast-door machinery room
- Cargo exchange
- General laboratory
- Cross-ship logistics tunnel

### Engineering

- Main engine room
- Reactor room
- Jump-machinery room
- Drive control
- Coolant-pump room
- Power-converter room
- Power control
- Power-distribution room
- Fuel-conditioning room
- Machine shop
- Battery room
- Damage-control center
- Engine-access space
- Reactor-transfer trunk

### Cargo, service, and utilities

- Cargo hold
- Bulk-cargo hold
- Tankage compartment
- Water-recovery room
- Waste-processing room
- Waste-recovery room
- Fabrication-feedstock store
- General stores
- Landing-equipment room
- Handling-equipment room
- Utility junction
- Cargo-handling rail corridor

### Access and survival

- Personnel airlock
- Cargo airlock
- Emergency airlock
- EVA airlock
- Escape-pod station
- Suit recess
- Service recess
- Lift trunk
- Armored stairwell
- Maintenance ladder and hatch
- Emergency pressure trunk

## Approved additions

### Command, flag, and security

- Captain's cabin
- Flag suite
- Security station
- Brig
- Armory
- Evidence locker

### Dining, hygiene, and fitness

- Wardroom
- Mess hall
- Shower room
- Locker room
- Laundry
- Gymnasium

### Expanded medical

- Surgical bay
- Isolation ward
- Quarantine ward
- Pharmacy
- Morgue

### Computing and ship intelligence

- AI core
- Server room
- Data center

### EVA and damage control

- EVA preparation room
- Decontamination room
- Suit-repair room
- Fire-control room
- Damage-control locker

`Fire-control room` means firefighting, atmosphere isolation, and emergency-response coordination. Weapon direction uses `Gunnery control` below.

### Industry and fabrication

- Fabrication bay
- Refinery
- Additive-manufacturing shop

### Specialized science

- Xenobiology laboratory
- Materials laboratory
- Astronomy laboratory
- Medical-research laboratory

### Cultural and civilian

- Chapel
- Memorial room
- Quiet room
- Passenger berthing
- Civilian commons

### Ship-role-specific rooms

- Carrier squadron-operations room
- Freighter cargo-control office
- Research sample-containment laboratory
- Colony administration room
- Colony seed vault
- Warship gunnery-control room

These role-specific types are not universal. They provide distinct anchors when a carrier, freighter, research vessel, colony ship, or warship needs a stronger identity than the shared baseline rooms provide.

## Runtime coverage

The current procedural generator instantiates only these distinct gameplay spaces:

- Cryo bay
- Player workshop
- Emergency CIC
- Main engine room
- Power control
- Impact-breached compartment

Airlocks, escape pods, suit recesses, and vertical hatches are generated as room features. All other catalog entries are design-approved but require an archetype field, weighted placement rules, geometry kits, and gameplay dressing before they can appear as distinct generated rooms.

## Concept-art tracking rule

Concept-art filenames should use a stable room-type slug and ship ID where applicable, for example:

`GGP01_Room_CaptainsCabin_v1.png`

Ship-agnostic explorations may use `GGPXX`. Damage, power, occupation, and contamination are presentation states of a room type rather than separate room types.
