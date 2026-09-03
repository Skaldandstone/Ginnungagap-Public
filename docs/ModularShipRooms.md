# Modular ship rooms

`AModularShipRoom` is the stable gameplay shell for reusable interior rooms. It inherits section
damage, contamination, atmosphere connections, and navigation from `AShipSection`, then adds a
room code, player-facing name, functional archetype, dimensions, and four cardinal bulkhead sockets.

## Current ten-step foundation

1. Stable room codes identify rooms in UI, saves, objectives, and telemetry.
2. Archetypes distinguish bridge, medical, cargo, engineering, escape, and support functions.
3. Per-room dimensions drive section bounds and socket placement.
4. Forward, aft, port, and starboard sockets provide a shared 1300 x 1040 x 600 kit convention.
5. `EnabledSockets` lets a room close sides that have no authored hatch.
6. Connections reserve both participating sockets and reject self-links or occupied sockets.
7. Disconnecting a socket clears both sides of the relationship.
8. `FShipRoomModuleDefinition` makes the procedural catalog editable from C++ or Blueprint defaults.
9. Corridors and bulkhead doors align between socket transforms instead of room centers.
10. Validation and automation tests reject empty identity, invalid dimensions, and bad socket pairing.

## Authoring a module

Create a Blueprint derived from `AModularShipRoom`, keep its root at the room center, and build to
the `ModuleSize` envelope. Keep the clear hatch aperture centered on any enabled socket. Art meshes
may extend into wall thickness, but walkable geometry should remain inside the section bounds.

For procedural rooms, edit `AProceduralShipBuilder::RoomModules` and its explicit `RoomConnections`
graph. Room codes and socket assignments must be unique. The corvette gameplay director requires
its thirteen named functional rooms, but their catalog order no longer affects construction.

## Topology milestone: actions 11–60

11. Added `FShipRoomConnectionDefinition` as a serializable graph edge.
12. Added explicit room-A identity.
13. Added explicit room-B identity.
14. Added an explicit socket for room A.
15. Added an explicit socket for room B.
16. Added per-edge atmosphere transfer coefficients.
17. Validated missing connection endpoints.
18. Rejected self-connections.
19. Validated transfer-coefficient range.
20. Added four branch hatch positions for eight total logical sockets.
21. Added forward-port sockets.
22. Added forward-starboard sockets.
23. Added aft-port sockets.
24. Added aft-starboard sockets.
25. Added physical scene components for every branch socket.
26. Positioned branch sockets from module dimensions.
27. Added opposite-pair rules for branch sockets.
28. Added three hatch apertures to forward walls.
29. Added three hatch apertures to aft walls.
30. Preserved centered port and starboard apertures.
31. Added an editable connection catalog to the builder.
32. Authored the bridge-to-CIC edge.
33. Authored CIC sensor, armory, and companionway edges.
34. Authored companionway medical and crew edges.
35. Authored companionway damage-control, cargo, and engineering branches.
36. Authored engineering reactor and escape-bay branches.
37. Replaced inferred socket selection with explicit topology.
38. Made corridor endpoints use selected socket transforms.
39. Made door placement use selected socket transforms.
40. Propagated configured transfer coefficients into both section links.
41. Added layout-wide definition validation.
42. Added duplicate room-code detection.
43. Added unknown endpoint detection.
44. Added duplicate socket-assignment detection.
45. Added graph reachability validation.
46. Added required corvette-room validation.
47. Added Blueprint-callable validation diagnostics.
48. Added runtime spawned-room tracking.
49. Added stable room lookup by code.
50. Added a query for completed build state.
51. Guarded against duplicate `BuildShip` calls.
52. Replaced index-based connection construction.
53. Replaced index-based corpse placement.
54. Replaced index-based Bloom dressing.
55. Replaced index-based system placement.
56. Replaced index-based armor-system placement.
57. Rebuilt patrol-section lists from spawned room actors.
58. Added connection-definition automation coverage.
59. Added eight-socket opposite-pair automation coverage.
60. Added complete default-corvette graph validation coverage.

## Multi-deck escort milestone

The first 24-room, three-deck operations district is documented in
`SmallEscortInteriorPlan.md`. Vertical stairs are authored as traversal geometry and reciprocal
`FSectionConnection` edges, so atmosphere and navigation can cross decks. Dedicated serialized
up/down module sockets remain a later native milestone; the first map does not overload a
horizontal socket with false vertical semantics.
