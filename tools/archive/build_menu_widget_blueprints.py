"""
Creates Widget Blueprint assets for the native menu widgets (TRO-38/39/40).

Why these are created empty
--------------------------
Every menu widget builds its layout in C++ via BuildFallbackLayout(), which begins:

    if (!WidgetTree || WidgetTree->RootWidget) return;

So an *empty* Widget Blueprint (no root widget) still renders the existing, already-styled C++
layout. That makes this script safe to run: it converts "code-only" into "designer-editable"
without changing how anything looks today.

The moment a designer drops a root widget into one of these, that screen's C++ fallback stops
running entirely and the Blueprint owns the whole layout. That is deliberate -- partial override
would mean two layout systems fighting -- but it does mean a screen is all-or-nothing. Rebuild the
screen fully in UMG rather than adding one widget and expecting the rest to remain.

Widget names must match the BindWidget/BindWidgetOptional properties on the parent C++ class to
bind. All menu bindings are BindWidgetOptional, so a partially-built screen still compiles; any
control left unbuilt is simply absent rather than an error.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_menu_widget_blueprints.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

PACKAGE_PATH = "/Game/UI/Widgets"

# Asset name -> parent C++ class. Screens the menu flow instantiates, plus the skill payload and
# ability-bar widgets. The ability bar is a HUD element rather than a menu, but it follows the same
# empty-Blueprint-keeps-the-C++-layout contract and designers will want to restyle it, so it is
# created here rather than left code-only. Other in-world widgets remain excluded.
WIDGETS = {
    "WBP_BootSplash": unreal.BootSplashWidget,
    "WBP_StartScreen": unreal.StartScreenWidget,
    "WBP_ModeSelect": unreal.ModeSelectWidget,
    "WBP_MapCustomization": unreal.MapCustomizationWidget,
    "WBP_MultiplayerOptions": unreal.MultiplayerOptionsWidget,
    "WBP_MultiplayerLobby": unreal.MultiplayerLobbyWidget,
    "WBP_CharacterCreator": unreal.CharacterCreatorWidget,
    "WBP_FirstLaunchCharacterCreation": unreal.FirstLaunchCharacterCreationWidget,
    "WBP_PreGameLoadout": unreal.PreGameLoadoutWidget,
    "WBP_SettingsMenu": unreal.SettingsMenuWidget,
    "WBP_SkillTree": unreal.SkillTreeWidget,
    "WBP_SkillPayloadPicker": unreal.SkillPayloadPickerWidget,
    "WBP_SkillPayloadEntry": unreal.SkillPayloadEntryWidget,
    "WBP_SkillAbilityBar": unreal.SkillAbilityBarWidget,
    "WBP_LoadingTransition": unreal.LoadingTransitionWidget,
    "WBP_ProgressionMenu": unreal.ProgressionMenuWidget,
}


def build():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    created, existing, failed = [], [], []

    for asset_name, parent_class in sorted(WIDGETS.items()):
        asset_path = "{}/{}".format(PACKAGE_PATH, asset_name)

        # Idempotent: never clobber a layout a designer has already built.
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            existing.append(asset_name)
            continue

        factory = unreal.WidgetBlueprintFactory()
        factory.set_editor_property("parent_class", parent_class)

        asset = asset_tools.create_asset(
            asset_name=asset_name,
            package_path=PACKAGE_PATH,
            asset_class=unreal.WidgetBlueprint,
            factory=factory,
        )

        if asset is None:
            failed.append(asset_name)
            continue

        unreal.EditorAssetLibrary.save_asset(asset_path)
        created.append(asset_name)

    unreal.log("=== Menu Widget Blueprints ===")
    unreal.log("Created:  {}".format(", ".join(created) if created else "none"))
    unreal.log("Existing: {}".format(", ".join(existing) if existing else "none"))
    if failed:
        # Surface rather than swallow: a silent miss here looks like a working run.
        unreal.log_error("Failed:   {}".format(", ".join(failed)))
        raise RuntimeError("{} widget blueprint(s) could not be created".format(len(failed)))

    unreal.log(
        "Each asset is empty on purpose, so the C++ fallback layout still renders. "
        "Adding a root widget makes that screen Blueprint-owned end to end."
    )


build()
