"""Author the field-supply item catalogue natively inside Unreal.

The project had five item definitions and all five were salvage-specific -- a tool charger, a
tether spool, a rock core canister. Nothing a crew member would draw before going outside, and
nothing that answered any of the twelve status effects the game can inflict. The consumable fields
on UItemDefinition had existed for a while with no asset setting any of them.

Every item here drives a consumer that already exists. Oxygen, health and suit integrity are read
off the character; treatment goes through the same call the medical activities use; equipment
repair goes through the same RepairAllEquipment the benches call. Nothing here invents an effect.

What is deliberately covered, and why these ten rather than one per status effect:

  * Life support and suit integrity, because those are the two clocks that kill.
  * Equipment repair, so the repair verb exists away from a bench. The kit restores well under
    what a bench does per slot -- the trade is convenience for efficiency, not a bench in a pocket.
  * The four environmental afflictions with no in-field answer at all: radiation, decompression,
    hypothermia, hyperthermia. Field activities already treat hemorrhage, fracture, hypoxia and CO2
    toxicity, and cryo treats motion sickness and psychosis, so those needed less.
  * A general ampoule for whatever is worst, which is also the only answer to the two effects
    nothing currently inflicts (AcuteStress, BurnTrauma) should they ever be wired up.

Meshes are geometry-scripted blockouts, not final art. They read at a glance and at pickup range,
which is what a wireframe pass needs; they are meant to be replaced.

Idempotent: re-running replaces the assets in place.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_field_supplies_unreal.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

from __future__ import annotations

import unreal


ROOT = "/Game/Assets/Gameplay/FieldSupplies"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
ITEM_DATA_PATH = ROOT + "/Data/Items"
BP_PATH = ROOT + "/Blueprints"

PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions()

# Slot durability runs 0-100 and a repair bench restores 40 to every damaged slot. A carried kit
# gives well under half that: the point of walking back to a bench has to survive the existence of
# a portable option.
KIT_REPAIR_PER_SLOT = 18.0

E = unreal.PlayerStatusEffect

# form:     which blockout silhouette to build
# palette:  which shared material
# treats:   status effect this targets, or None for "whatever is worst"
SUPPLIES = [
    dict(
        id="EmergencyOxygenCartridge", label="Emergency Oxygen Cartridge",
        description="A single-charge cartridge that cross-feeds the suit tank. Refills what you "
                    "have; it does not give you a larger tank.",
        form="cartridge", palette="lifesupport", size=(14, 14, 44), mass=3.2, stack=3,
        tags=["Pickup.LifeSupport", "Field.Standard"],
        oxygen=45.0,
    ),
    dict(
        id="SuitPatchSealant", label="Suit Patch Sealant",
        description="Expanding sealant and a roll of bonded patch stock. Closes a breach well "
                    "enough to walk home on, not well enough to trust twice.",
        form="pouch", palette="lifesupport", size=(18, 8, 22), mass=0.9, stack=3,
        tags=["Pickup.LifeSupport", "Field.Standard"],
        suit=0.35,
    ),
    dict(
        id="FieldRepairKit", label="Field Repair Kit",
        description="Patch stock, seam tape and a spare seal set. Mends every worn piece a little; "
                    "a workshop bench does far more, if you can reach one.",
        form="case", palette="repair", size=(30, 14, 20), mass=4.6, stack=2,
        tags=["Pickup.Repair", "Field.Standard"],
        repair=KIT_REPAIR_PER_SLOT,
    ),
    dict(
        id="TraumaKit", label="Trauma Kit",
        description="Pressure dressings, clotting agent and a compression cuff. Stops the bleeding "
                    "and buys back some of what was lost.",
        form="case", palette="medical", size=(26, 12, 18), mass=2.4, stack=2,
        tags=["Pickup.Medical", "Field.Standard"],
        health=35.0, treats=E.HEMORRHAGE, treatment=0.70,
    ),
    dict(
        id="CompoundSplint", label="Compound Splint",
        description="A vacuum splint that sets hard around the limb. Immobilises the break; it "
                    "does not mend it.",
        form="wrap", palette="medical", size=(34, 10, 10), mass=1.1, stack=2,
        tags=["Pickup.Medical", "Field.Standard"],
        treats=E.FRACTURE, treatment=0.80,
    ),
    dict(
        id="GeneralMedicalAmpoule", label="General Medical Ampoule",
        description="A broad-spectrum ampoule that goes after whatever is worst. Weaker than "
                    "anything targeted, and the only thing to reach for when you cannot tell.",
        form="ampoule", palette="medical", size=(6, 6, 16), mass=0.35, stack=4,
        tags=["Pickup.Medical", "Field.Standard"],
        treatment=0.45,
    ),
    dict(
        id="ChelationInjector", label="Chelation Injector",
        description="Binds and flushes what the shielding let through. Slow, unpleasant, and the "
                    "only thing aboard that touches a dose.",
        form="injector", palette="hazard", size=(8, 8, 20), mass=0.4, stack=3,
        tags=["Pickup.Medical", "Hazard.Radiation"],
        treats=E.RADIATION_SICKNESS, treatment=0.60,
    ),
    dict(
        id="RecompressionAmpoule", label="Recompression Ampoule",
        description="Buys time against the bends when there is no chamber to climb into. A "
                    "stopgap, and it is meant to feel like one.",
        form="ampoule", palette="hazard", size=(6, 6, 16), mass=0.4, stack=3,
        tags=["Pickup.Medical", "Hazard.Decompression"],
        treats=E.DECOMPRESSION, treatment=0.55,
    ),
    dict(
        id="ThermalRegulationWrap", label="Thermal Regulation Wrap",
        description="A powered wrap that drives heat back into the core. Draws hard on the cell "
                    "while it works.",
        form="wrap", palette="thermal", size=(30, 14, 10), mass=1.6, stack=2,
        tags=["Pickup.Medical", "Hazard.Thermal"],
        treats=E.HYPOTHERMIA, treatment=0.75,
    ),
    dict(
        id="CoolantGelPack", label="Coolant Gel Pack",
        description="Phase-change gel against the suit's heat exchange points. Pulls a core "
                    "temperature back down before it does lasting harm.",
        form="pouch", palette="thermal", size=(22, 10, 18), mass=1.5, stack=2,
        tags=["Pickup.Medical", "Hazard.Thermal"],
        treats=E.HYPERTHERMIA, treatment=0.75,
    ),
]


def text(value):
    return unreal.TextLibrary.conv_string_to_text(value)


def xf(x=0, y=0, z=0, pitch=0, yaw=0, roll=0):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(1, 1, 1),
    )


def box(mesh, loc, dims, rotation=(0, 0, 0)):
    mesh.append_box(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), *dims, 2, 2, 2)


def cylinder(mesh, loc, radius, length, axis="z"):
    rotation = {"x": (90, 0, 0), "y": (0, 0, 90), "z": (0, 0, 0)}[axis]
    mesh.append_cylinder(
        PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
        radius, length, 20, 2, True)


def supply_mesh(d):
    """A silhouette per form. Legible at pickup range is the whole requirement here."""
    mesh = unreal.DynamicMesh()
    width, depth, height = d["size"]
    form = d["form"]

    if form == "cartridge":
        # Pressure bottle with a neck and a collar, read as gas at a glance.
        cylinder(mesh, (0, 0, height * .42), width * .5, height * .84)
        cylinder(mesh, (0, 0, height * .90), width * .22, height * .16)
        cylinder(mesh, (0, 0, height * .78), width * .58, height * .06)

    elif form == "pouch":
        # Soft-sided, with a seam across the face so it does not read as a solid block.
        box(mesh, (0, 0, height * .5), (width, depth, height))
        box(mesh, (0, -depth * .52, height * .5), (width * .78, depth * .10, height * .12))

    elif form == "case":
        # Hard case with a lid line and a carry handle: this one is meant to look openable.
        box(mesh, (0, 0, height * .42), (width, depth, height * .84))
        box(mesh, (0, 0, height * .84), (width * 1.02, depth * 1.02, height * .10))
        box(mesh, (0, 0, height * 1.02), (width * .30, depth * .12, height * .14))

    elif form == "wrap":
        # A rolled band, so it reads differently from the cases at the same size.
        cylinder(mesh, (0, 0, height * .5), height * .5, width, axis="y")
        box(mesh, (0, 0, height * .5), (width * .30, depth * 1.06, height * .34))

    elif form == "ampoule":
        # Small glass body between two collars.
        cylinder(mesh, (0, 0, height * .5), width * .5, height * .78)
        cylinder(mesh, (0, 0, height * .92), width * .34, height * .18)

    elif form == "injector":
        # Auto-injector: a body, a thumb plate, and a nose that says which end goes where.
        cylinder(mesh, (0, 0, height * .52), width * .5, height * .74)
        cylinder(mesh, (0, 0, height * .95), width * .78, height * .08)
        cylinder(mesh, (0, 0, height * .10), width * .26, height * .22)

    else:
        raise RuntimeError(f"Unknown form {form!r} on {d['id']}")

    mesh.discard_mesh_attributes()
    mesh.auto_generate_x_atlas_mesh_u_vs(0, unreal.GeometryScriptXAtlasOptions())
    mesh.recompute_normals(NORMALS)
    return mesh


def material(name, color, roughness, metallic=0.0):
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_PATH, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant3Vector, -340, -20)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -340, 130)
    rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -340, 220)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def build_materials():
    # Colour carries the category, because a player rummaging a container reads shape and colour
    # long before they read a tooltip.
    return {
        "lifesupport": material("M_FieldSupply_LifeSupportCyan", (.03, .21, .26), .38, .30),
        "repair":      material("M_FieldSupply_RepairAmber",     (.34, .17, .02), .48, .35),
        "medical":     material("M_FieldSupply_MedicalWhite",    (.52, .54, .53), .32, .06),
        "hazard":      material("M_FieldSupply_HazardYellow",    (.44, .32, .02), .44, .18),
        "thermal":     material("M_FieldSupply_ThermalViolet",   (.17, .06, .28), .40, .22),
    }


def static_mesh(d, dynamic_mesh, assigned_material):
    path = f"{MESH_PATH}/SM_{d['id']}"
    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dynamic_mesh, path, options)
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Geometry Scripting failed for {path}: {outcome}")

    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", assigned_material)
    slot.set_editor_property("material_slot_name", unreal.Name("Surface"))
    asset.set_editor_property("static_materials", [slot])
    asset.set_editor_property("light_map_resolution", 32)
    asset.set_editor_property("light_map_coordinate_index", 0)
    body = asset.get_editor_property("body_setup")
    if body:
        body.set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)

    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Source", "Unreal Geometry Scripting")
    unreal.EditorAssetLibrary.set_metadata_tag(
        asset, "Ginnungagap.Generator", "tools/build_field_supplies_unreal.py")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Fidelity", "Blockout")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def data_asset(name, folder, cls):
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    if not asset:
        raise RuntimeError(f"Could not create Data Asset {folder}/{name}")
    return asset


def blueprint(name, folder, parent):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, unreal.Blueprint, factory)
    if not asset:
        raise RuntimeError(f"Could not create Blueprint {folder}/{name}")
    return asset


def build_supply(d, meshes):
    definition = data_asset("DA_Item_" + d["id"], ITEM_DATA_PATH, unreal.ItemDefinition)
    definition.set_editor_property("item_id", unreal.Name(d["id"]))
    definition.set_editor_property("display_name", text(d["label"]))
    definition.set_editor_property("description", text(d["description"]))
    definition.set_editor_property("max_stack_size", d["stack"])
    definition.set_editor_property("unit_mass_kg", d["mass"])
    definition.set_editor_property("item_tags", [unreal.Name(tag) for tag in d["tags"]])
    definition.set_editor_property("world_mesh", meshes[d["id"]])

    # Every one of these is spent on use, which is the whole point of the category.
    definition.set_editor_property("is_consumable", True)
    definition.set_editor_property("can_drop", True)
    definition.set_editor_property("mission_item", False)

    definition.set_editor_property("oxygen_restore_percent", d.get("oxygen", 0.0))
    definition.set_editor_property("health_restore_percent", d.get("health", 0.0))
    definition.set_editor_property("suit_integrity_restore", d.get("suit", 0.0))
    definition.set_editor_property("equipment_repair_amount", d.get("repair", 0.0))
    definition.set_editor_property("treatment_strength", d.get("treatment", 0.0))

    # A targeted item names its affliction; a general one is left untargeted so UseItem sends the
    # treatment at whatever is worst instead.
    treats = d.get("treats")
    definition.set_editor_property("treats_specific_effect", treats is not None)
    if treats is not None:
        definition.set_editor_property("treated_effect", treats)

    unreal.EditorAssetLibrary.save_loaded_asset(definition)

    # A definition nobody can pick up is a row in a spreadsheet. The pickup actor is what puts it
    # in the world, and the map has none of these yet.
    bp = blueprint("BP_Pickup_" + d["id"], BP_PATH, unreal.InventoryItemPickup)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("item_definition", definition)
    cdo.set_editor_property("quantity", 1)
    cdo.get_editor_property("visual_mesh").set_static_mesh(meshes[d["id"]])
    unreal.EditorAssetLibrary.save_loaded_asset(bp)

    return definition, bp


def main():
    for folder in (MESH_PATH, MATERIAL_PATH, ITEM_DATA_PATH, BP_PATH):
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.make_directory(folder)

    materials = build_materials()
    unreal.log("Built {} shared materials".format(len(materials)))

    meshes = {}
    for d in SUPPLIES:
        meshes[d["id"]] = static_mesh(d, supply_mesh(d), materials[d["palette"]])
    unreal.log("Built {} blockout meshes".format(len(meshes)))

    for d in SUPPLIES:
        build_supply(d, meshes)
        unreal.log("  {:<28} {}".format(d["id"], d["label"]))

    unreal.log("Field supply catalogue: {} definitions, {} pickups".format(
        len(SUPPLIES), len(SUPPLIES)))


if __name__ == "__main__":
    main()
