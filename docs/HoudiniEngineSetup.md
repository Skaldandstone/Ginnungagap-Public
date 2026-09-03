# Houdini Engine setup

## Current project state

- The official SideFX Houdini Engine for Unreal source is installed project-locally at `Plugins/HoudiniEngine`.
- The plugin is explicitly enabled in `Ginnungagap.uproject`.
- The selected source is the official Houdini 22.0 branch for Unreal Engine 5.8 and is stamped for Houdini 22.0.423.
- `GinnungagapEditor Win64 Development` compiled all 230 plugin and project actions successfully on 2026-08-29. UnrealBuildTool reported only `License not activated`.
- The plugin can compile without the Houdini runtime, but it cannot create or cook Houdini sessions until the matching runtime is installed.
- Procedural ship generation must wait for art-direction approval. The plugin installation does not authorize replacing approved concept or production-reference assets.

## Why the full authoring product is required

Houdini Engine loads and cooks Houdini Digital Assets in Unreal. It does not replace Houdini as the tool used to author those assets. The ship, room, spline, kit, and damage generators therefore require a compatible Houdini authoring product as well as the Unreal plugin.

The project is pinned to Houdini 22.0.423 so the authoring runtime, HDA definitions, and Unreal plugin use the same API build.

## Account-safe CLI installation

SideFX requires an authenticated installer settings file and explicit EULA acceptance. Do not add the settings file, account password, client secret, or license credentials to this repository.

1. Sign in at <https://www.sidefx.com/download/> and download the signed Windows SideFX Launcher installer.
2. Create the installer settings file using SideFX's documented account or client-credential workflow.
3. Record the EULA date shown by SideFX when accepting the current agreement.
4. In Windows PowerShell, from `C:\Users\James\Documents\Unreal Projects\Ginnungagap`, run:

```powershell
.\tools\install_houdini_runtime.ps1 -LauncherInstallerPath 'C:\Path\To\install-houdini-launcher.exe' -SettingsFile 'C:\Private\sidefx-installer-settings.ini' -EulaDate 'YYYY-MM-DD'
```

If the launcher is already installed, omit `-LauncherInstallerPath`:

```powershell
.\tools\install_houdini_runtime.ps1 -SettingsFile 'C:\Private\sidefx-installer-settings.ini' -EulaDate 'YYYY-MM-DD'
```

The script verifies SideFX Authenticode signatures, uses the official `houdini_installer.exe` CLI, installs Houdini 22.0.423 by default, and checks the expected install directory. Use `-WhatIf` to inspect the intended commands without installing.

## First Unreal validation after installation

1. Restart Unreal Editor.
2. Open the Houdini Engine menu and start a session.
3. Confirm the session reports Houdini 22.0.423.
4. Create a disposable test HDA outside canonical content and verify one cook.
5. Do not begin ship or room generation until the revised gravity-true concepts are approved.

## Planned production use after approval

The first generator should consume the canonical production packet rather than infer structure from a raster image. It should expose:

- a true vertical-stack ship frame with `+X` bow/up-stack and `-X` aft toward engines and gravity;
- straight parallel main-engine centerlines along `X`, a common aft nozzle plane, and separate maneuvering-thruster groups;
- transverse `YZ` floor plates and engine-relative deck ordering;
- complete story layers from structural floor and utility plenum through occupied volume, ceiling, and next deck;
- room envelopes, clearance volumes, vents, squeeze gaps, doors, and ladders;
- asymmetric engine clusters and massing controls;
- named walk, crouch, crawl, vent, and squeeze traversal splines with boundary sockets and matching volumes;
- separate power, data, coolant, air, hidden Bloom, rail, and damage-path splines;
- modular kit identifiers and deterministic seeds;
- collision, navigation, LOD, material slot, decal, light, and render-layer mappings;
- JSON import and export matching the production-reference manifests;
- acceptance checks that reject canted main engines, nozzle exits off the common aft plane, floors outside the occupant-to-engine load path, mirrored filler, missing routes, and floor normals not aligned to `+X`.

## Official references

- SideFX scripted installation: <https://www.sidefx.com/docs/houdini/licensing/script_houdini_installations.html>
- Houdini Engine for Unreal introduction: <https://www.sidefx.com/docs/houdini/unreal/intro.html>
- Official Unreal plugin source: <https://github.com/sideeffects/HoudiniEngineForUnreal>
