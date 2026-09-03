# Ship Build Queue

This queue tracks exterior ship assets intended to become navigable or encounter-scale vessels.

## Priority queue

| Priority | Ship | Status | Intended role | Next production gate |
| --- | --- | --- | --- | --- |
| 1 | GGP-01 **Wayfarer exterior blockout** | Fidelity blockout v2 complete; v1 rejected for missing major masses | Full-scale replacement-ready exterior shell | Carve true hangar apertures, then validate v2 against front/side/top concept views in Unreal |

## GGP-01 Wayfarer

- Visual identity: extremely long armored wedge, layered dorsal spine, broad rectangular mid-body, reinforced prow, a nine-aperture clustered main engine block, and paired lateral maneuvering-engine sponsons.
- Surface language: charcoal and gunmetal armor, exposed structural ribs, extremely sparse navigation and habitation lights, cyan engine emission, and modular damage panels. Avoid city-like window grids.
- Command silhouette: the otherwise blind armored hull is contrasted by one open panoramic bridge/CIC viewport complex high on the forward dorsal hull. Use broad dark structural glass with visible mullions; do not cover it with permanent armor shutters.
- Armament language: a restrained battery of recessed dorsal and ventral mass-driver turrets, paired broadside point-defense emplacements, and armored missile-cell banks. Weapons sit inside protected hull recesses and share the ship's planar armor language.
- Hangar language: the large port and starboard midship openings are paired, navigable hangar mouths-not weapon recesses. Each exposes a deep multi-deck bay with launch deck, overhead ribs, service galleries, retractable segmented blast doors, and an internal pressure curtain.
- Hangar shielding: each open mouth carries a transparent atmospheric containment membrane seated inside its structural frame. At idle it is visible mainly as a cyan edge glimmer, slight background refraction, and faint moving interference bands; it brightens locally when craft, debris, or characters cross it.
- Airlock language: personnel and cargo locks use a standardized chamfered docking collar, recessed double pressure doors, amber hazard frame, short cyan approach-light bars, external handholds, and a centered docking target. They remain much smaller than hangar mouths and sparse enough to function as landmarks.
- Gameplay constraint: target a 24-deck, roughly 1,150 m-long capital ship. The current four-deck, 12-column generator is one 72 m-long playable damage-control sector on ship decks 09–12, not the whole interior.
- Production approach: modular mid-poly hull kit, Nanite-compatible hero shell, tileable hull materials, trim-sheet edge details, decal pass, separate emissive engine meshes, and swappable damaged panels.
- Required LOD/use cases: close EVA traversal, medium encounter view, distant arrival cinematic, and shadow-only proxy.
- Concept references:
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_JumpArrival.png`
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_ModelSheet.png`
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_ModelSheet_v2.png` (current exterior direction)
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_ModelSheet_v3.png` (current hangar and airlock direction)
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_ModelSheet_v4.png` (current shielded-hangar direction)
  - `Content/ConceptArt/Ships/GGP01_Wayfarer_CrossSections_v1.png` (mixed-volume interior and maze-corridor direction)

### Build checklist

- [ ] Lock dimensions and reconcile the procedural interior with the hull silhouette.
- [ ] Block out the 24-deck stack, seven pressure zones, lift trunks, hangars, multi-deck machinery voids, and the Decks 09–12 playable sector.
- [x] Create a low-detail in-engine blockout with independently replaceable hull, armor, engine, hangar, shield, bridge, weapon, and airlock modules.
- [x] Create a 1:1-scale editable Blender blockout and export a GLB snapshot for engine import.
- [x] Restore concept-critical large masses: engine shoulders, broadside shelves, hangar sponsons, dorsal terraces, prow cheeks, ventral fins, and weapon trenches.
- [ ] Validate player scale and EVA traversal in Unreal.
- [ ] Build the modular high-detail exterior and collision proxies.
- [ ] Author hull, heat damage, emissive, and decal materials.
- [ ] Block out panoramic bridge glazing, recessed weapon sockets, missile cells, and lateral thruster sponsons as separate modules.
- [ ] Cut the paired hangar volumes through the exterior shell and align them with Decks 13–16 before detailing either interior or hull.
- [ ] Build one reusable airlock-collar kit with personnel, cargo, sealed, cycling, and damaged states.
- [ ] Author the hangar containment-shield material, frame emitters, crossing ripple, impact response, and power-failure state.
- [ ] Create intact, derelict, and breached variants.
- [ ] Add engine VFX sockets and jump-arrival attachment points.
- [ ] Produce close, medium, and distant performance profiles.
