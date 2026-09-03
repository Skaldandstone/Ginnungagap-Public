"""Validate the generated MetaHuman body lattice and its runtime class references."""

import unreal


CATALOG_PATH = "/Game/Characters/MetaHumans/DA_PlayerMetaHumanCatalog"
EXPECTED_IDS = {
    f"{stature}_{frame}"
    for stature in ("compact", "medium", "tall")
    for frame in ("narrow", "standard", "broad")
}


def main():
    catalog = unreal.load_asset(CATALOG_PATH)
    if catalog is None:
        raise RuntimeError(f"Missing catalog: {CATALOG_PATH}")

    variants = list(catalog.get_editor_property("body_variants"))
    found_ids = {str(variant.variant_id) for variant in variants}
    if found_ids != EXPECTED_IDS:
        raise RuntimeError(f"Unexpected variant ids: {sorted(found_ids)}")

    assembled = []
    for variant in variants:
        variant_id = str(variant.variant_id)
        character_path = (
            "/Game/Characters/MetaHumans/Generated/MHC_Player_"
            + "_".join(part.title() for part in variant_id.split("_"))
        )
        if unreal.load_asset(character_path) is None:
            raise RuntimeError(f"Missing source MetaHuman Character: {character_path}")

        actor_class = variant.get_editor_property("assembled_actor_class")
        if actor_class is not None:
            assembled.append(variant_id)
        unreal.log_warning(
            f"GGP_METAHUMAN_VERIFY={variant_id};"
            f"height={variant.authored_measurements.height_cm:.0f};"
            f"shoulder={variant.authored_measurements.shoulder_width_cm:.0f};"
            f"assembled={actor_class is not None}"
        )

    if not assembled:
        raise RuntimeError("Catalog has no assembled runtime body")
    unreal.log_warning(
        f"GGP_METAHUMAN_VERIFY_COMPLETE=variants={len(variants)};"
        f"assembled={len(assembled)};ids={','.join(assembled)}"
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
