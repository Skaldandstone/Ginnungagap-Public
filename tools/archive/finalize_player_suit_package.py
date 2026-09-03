"""Apply exactly 100 production configuration steps to the packaged Unreal suit assets."""

import unreal


ROOT = "/Game/Characters/Player/Suit/PackagedCombined"
ROLES = ("Crew", "Engineering", "Medical", "Security")
CHANNELS = ("BaseColor", "Normal", "Roughness", "Metallic", "AO")
FILENAMES = {
    "BaseColor": "T_PlayerSkin_{role}",
    "Normal": "T_PlayerSkin_{role}_Normal",
    "Roughness": "T_PlayerSkin_{role}_Roughness",
    "Metallic": "T_PlayerSkin_{role}_Metallic",
    "AO": "T_PlayerSkin_{role}_AO",
}
PARAMETERS = {
    "BaseColor": "SkinTexture",
    "Normal": "NormalTexture",
    "Roughness": "RoughnessTexture",
    "Metallic": "MetallicTexture",
    "AO": "AOTexture",
}


def load(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Required packaged suit asset is missing: {path}")
    return asset


def main():
    steps = []

    def complete(label):
        steps.append(label)
        unreal.log(f"PlayerSuitFinalize [{len(steps):03}/100] {label}")

    textures = {}
    # Steps 001-060: three production settings for each of twenty authored textures.
    for role in ROLES:
        textures[role] = {}
        for channel in CHANNELS:
            name = FILENAMES[channel].format(role=role)
            texture = load(f"{ROOT}/Textures/{role}/{name}.{name}")
            textures[role][channel] = texture
            texture.set_editor_property("srgb", channel == "BaseColor")
            complete(f"{role} {channel}: configure sRGB")
            compression = unreal.TextureCompressionSettings.TC_DEFAULT
            if channel == "Normal":
                compression = unreal.TextureCompressionSettings.TC_NORMALMAP
            elif channel in ("Roughness", "Metallic", "AO"):
                compression = unreal.TextureCompressionSettings.TC_MASKS
            texture.set_editor_property("compression_settings", compression)
            complete(f"{role} {channel}: configure compression")
            texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
            complete(f"{role} {channel}: configure mip generation")
            unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)

    # Steps 061-084: create four role MIs and bind all five authored texture channels.
    master = load("/Game/Characters/Player/Suit/Materials/M_PlayerSuit_Master.M_PlayerSuit_Master")
    role_materials = {}
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    for role in ROLES:
        path = f"{ROOT}/Materials/MI_PackagedSuit_{role}"
        mi = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if not mi:
            mi = asset_tools.create_asset(f"MI_PackagedSuit_{role}", f"{ROOT}/Materials",
                                          unreal.MaterialInstanceConstant,
                                          unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", master)
        role_materials[role] = mi
        complete(f"{role}: create material instance and bind master")
        for channel in CHANNELS:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi, PARAMETERS[channel], textures[role][channel])
            complete(f"{role}: bind {channel} texture")
        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)

    # Steps 085-096: configure and tag the four combined role meshes.
    for role in ROLES:
        mesh = load(f"{ROOT}/Variants/{role}/SM_PlayerSuit_{role}.SM_PlayerSuit_{role}")
        mesh.set_editor_property("allow_cpu_access", False)
        complete(f"{role}: disable runtime CPU mesh access")
        for slot in range(len(mesh.get_editor_property("static_materials"))):
            mesh.set_material(slot, role_materials[role])
        complete(f"{role}: assign packaged role material")
        unreal.EditorAssetLibrary.set_metadata_tag(mesh, "PlayerSuitPackage",
                                                    f"Role={role};Equipment={'Drone' if role in ('Crew','Medical') else 'ToolArm'}")
        complete(f"{role}: write class/loadout metadata")
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    # Steps 097-100: configure the two modular hands-free equipment meshes.
    for equipment, asset_name, classes in (
        ("ToolArm", "SM_Suit_ToolArm", "Engineering,Security"),
        ("UtilityDrone", "SM_Suit_UtilityDrone", "Crew,Medical"),
    ):
        mesh = load(f"{ROOT}/Equipment/{equipment}/{asset_name}.{asset_name}")
        mesh.set_editor_property("allow_cpu_access", False)
        complete(f"{equipment}: disable runtime CPU mesh access")
        unreal.EditorAssetLibrary.set_metadata_tag(mesh, "PlayerSuitEquipmentClasses", classes)
        complete(f"{equipment}: write compatible-class metadata")
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    if len(steps) != 100:
        raise RuntimeError(f"Finalization completed {len(steps)} steps instead of 100")
    unreal.log("Player suit packaged finalization complete: exactly 100 steps")


main()
