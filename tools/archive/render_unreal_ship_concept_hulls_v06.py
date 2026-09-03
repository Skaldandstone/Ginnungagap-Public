"""Render the concept-first Iteration 06 review maps using the warmed editor path."""
from pathlib import Path

import unreal


project = Path(unreal.SystemLibrary.get_project_directory())
source_path = project / "tools/render_unreal_ship_fab_hull_sculpt.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace(
    'OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview/FabHullSculpt"',
    'OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview/ConceptHull06"',
)
source = source.replace(
    "Saved/Reports/UnrealShipFabHullSculptRenders.json",
    "Saved/Reports/UnrealShipConceptHullRendersV06.json",
)
source = source.replace(
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt\"",
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_ConceptHull06\"",
)
source = source.replace(
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt\"",
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_ConceptHull06\"",
)
source = source.replace('label.startswith("FAB_HULL_")', 'label.startswith("CONCEPT06_")')
source = source.replace("_FabHullSculpt_ThreeQuarter.png", "_ConceptHull06_ThreeQuarter.png")
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
