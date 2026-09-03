# Complete Asset Catalog

`tools/build_complete_asset_catalog.py` creates `/Game/Assets/Maps/ModelLibrary/L_CompleteAssetCatalog`
and stages every generated static model in a review grid. Extremely large models are scaled only in
the review map; source asset dimensions remain unchanged. Full fleet hulls remain in the dedicated
fleet scale-comparison map.

`tools/validate_model_library.py` enforces critical references across every generated library and a
minimum static-mesh count, making missing imports visible in local automation and CI.
