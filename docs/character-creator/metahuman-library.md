# MetaHuman Character-Creator Library

**Note (2026-08-24):** this appears to be the original design spec that TRO-215's two competing
runtime implementations each partially built. `CharacterCreatorWidget`'s
`BodyPreset`/`FacePreset`/`SkinTone`/`HairStyle`/`VoiceProfile` enums match this doc's "Variation
axes" exactly (4 bodies, 12 faces, 8 skins, 6 hair, 4 voices). `FirstLaunchCharacterCreationWidget`'s
`MetaHumanPresetId` matches this doc's `PlayerFaceNN`/`BP_PlayerFaceNN` assembled-Blueprint
resolution convention. Neither system currently combines the two: the preset-enum system doesn't
feed into producing a numbered assembled face, and the MetaHumanPresetId system doesn't expose the
axis-based selection UI this doc describes. Resolving TRO-215 by having the axis selection assemble
into (or select) a `PlayerFaceNN` identity, rather than picking one system and discarding the other,
may be the intended design.

The player identity system uses MetaHuman for the character and keeps wearable layers independent:

1. MetaHuman face and underlying body
2. Cryo/comfort undersuit
3. Role-specific pressure oversuit
4. Equipment, helmet, and damage layers

## Variation axes

- 12 editable MetaHuman source faces
- 4 body silhouettes: Light, Average, Broad, Heavy
- 8 skin-tone selections
- 6 hair selections
- 4 voice profiles
- 4 pressure-suit roles

The face, body, skin, and hair axes provide 2,304 visual combinations before suit role, suit color, equipment, scars, makeup, and wear are counted.

## Source faces

Editable authoring assets live in `/Game/Characters/MetaHumans/SourceFaces`. They are duplicated from Epic's installed presets so every face begins with production anatomy, eyes, teeth, skin, and facial rig data. The numbered game-facing identifiers remain stable even if an artist later sculpts or replaces a source face.

All 12 sources have joint/blend-shape DNA and high-resolution face/body texture sources. A clean-editor validation confirms that all 12 reload as assembly-ready.

## Assembled gameplay assets

The first high-quality optimized build is `/Game/Characters/MetaHumans/Assembled/PlayerFace01/BP_PlayerFace01`. Its face and body meshes, DNA, baked skin/eye/teeth maps, groom cards and bindings, materials, physics, and default clothing are stored beneath the same `PlayerFace01` folder. Reusable Epic dependencies are shared beneath `/Game/Characters/MetaHumans/Common`.

Assembly requires a DirectX 12 rendering context because MetaHuman's TextureGraph material baker is GPU-backed. Use `-dx12 -RenderOffscreen` for automated builds; `-NullRHI` is suitable for source validation but not assembly.

Faces 02-12 remain production-ready editable sources and can be assembled on demand. This avoids committing roughly 300 MB of derived runtime content for every identity before the final face and hair roster is approved.

## Runtime integration

`ACoopSurvivalCharacter` resolves assembled faces through the stable path
`/Game/Characters/MetaHumans/Assembled/PlayerFaceNN/BP_PlayerFaceNN`. Face01 is
active now; an identity whose assembled Blueprint is not present safely falls back
to the native player mesh until that face is assembled.

The native player mesh remains the authoritative movement and gameplay animation
driver. The assembled MetaHuman body uses `UMetaHumanCopyPoseAnimInstance` to copy
the pose by bone name. Do not use Leader Pose between Manny and the MetaHuman body:
their skeletons share many bone names but not matching bone indices, which deforms
the neck and shoulder girdle. MetaHuman garments may use Leader Pose from the
MetaHuman body because those assets share its skeleton.

Character-creator preview mode hides the pressure oversuit, helmet pieces, wearable
equipment, suit lights, and Epic's loose default T-shirt. The MetaHuman body uses the
dedicated `MI_MH_CryoBodysuit_Standard` technical-fabric surface as a fitted cryo
compression layer. This keeps the body/undersuit review separate from later wearable
layers without introducing another incompatible skeleton.

After assembling into an initially empty Common directory, run
`tools/unreal_repair_metahuman_materials.py` once in a clean DX12 editor. It reloads
the completed dependency graph, refreshes material-function chains, recompiles the
shared masters, and resaves their instances. The pass prevents assembly-time stale
shader maps from displaying Unreal's fallback grid material.

## Production rules

- Never merge the undersuit or pressure suit into the MetaHuman source asset.
- Assemble gameplay MetaHumans with the optimized pipeline; reserve cinematic assembly for close-up sequences.
- Keep gameplay collision and movement dimensions identical across body choices.
- Bind garments to the MetaHuman body skeleton and validate all four body silhouettes.
- Store player selections as stable enum identifiers, not Epic preset names.
- Treat MetaHuman Character assets as editable sources; runtime code references assembled gameplay assets.
