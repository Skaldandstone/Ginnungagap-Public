"""Dumps M_Ship_Hull_OffWhite's graph, because it exposes no parameters to tune.

The cryo shot clips 5.4% of frame at p90 luminance 0.916; Sheet 11's cryo bay clips 1.2% at p90
0.348 and never approaches white. The clipped pixels sit in the top third of frame, on large wall
panels wearing this material -- not on the floor, which was the first guess and was wrong.

This material is a plain Material with no scalar or vector parameters, so a MaterialInstance can
override nothing and the asset's own graph is the only lever. Before touching a graph, read it.
"""

import unreal

PATH = "/Game/Assets/Ships/Production/Materials/M_Ship_Hull_OffWhite.M_Ship_Hull_OffWhite"

material = unreal.load_asset(PATH)
if not material:
    unreal.log_error("HULL no asset at {}".format(PATH))
else:
    unreal.log("HULL {}  ({})".format(PATH, type(material).__name__))

    try:
        expressions = unreal.MaterialEditingLibrary.get_material_expressions(material)
    except Exception as error:
        expressions = []
        unreal.log_warning("HULL could not list expressions: {}".format(error))

    unreal.log("HULL {} expression node(s)".format(len(expressions)))
    for expression in expressions:
        kind = type(expression).__name__
        detail = ""
        # The values worth seeing: constants feeding base colour, roughness, metallic.
        for prop in ("constant", "r", "g", "b", "parameter_name", "default_value"):
            try:
                value = expression.get_editor_property(prop)
            except Exception:
                continue
            detail += "  {}={}".format(prop, value)
        unreal.log("HULL   {:<38}{}".format(kind, detail))

    unreal.log("HULL ---- end ----")
