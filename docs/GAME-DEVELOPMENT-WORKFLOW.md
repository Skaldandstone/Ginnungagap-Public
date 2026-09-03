# Game development workflow

## Session identity and safety

Run from the exact project root. Read the existing project brief, asset register, and relevant implementation documents before changing the game. DCC remains Godot 4.7.2 and its current 2D presentation; Ginnungagap remains Unreal 5.8. Setup does not authorize engine migration, art replacement, new gameplay frameworks, publishing, or purchases.

1. Read `git status --short` and preserve dirty and untracked work. Name one bounded change and its acceptance check before making it. Back up affected configuration. Do not reset, stash, commit all, save all, or discard unrelated work.
2. Inspect `.codex/game-toolchain.json`, run `python tools/game_pipeline.py status`, and identify the process owning the intended port. A listening port alone does not prove the correct project.
3. Confirm that the actual Codex task loaded this project's MCP entries. Project-local Codex configuration requires trust for this exact folder. The user approved exact-root trust on 2026-08-31; both canonical project configurations now load. Existing DCC task folders forward MCP connections to the Godot project, and the previously missing GitHub Ginnungagap path is a junction to the canonical Unreal project. Existing desktop tasks may need a normal task reload to refresh tools; never force a reload of a task with an active writer. Do not route game work to the old global Blender connection on 9876. Do not bypass trust through command-line overrides.
4. Before any engine mutation, inspect project identity, current scene/map, and logs. Godot must report this project's absolute root. Unreal must identify its project path (editor command line/log), expected map, and matching listener owner. Blender must report `bpy.context.scene.get('game_pipeline_root')` equal to this root and protocol 5. Recheck after opening any different `.blend` or project.
5. Serialize all operations on an editor, including save/load, screenshots, and play. Use a single writer. No tool call should run concurrently with another editor mutation or a person's unsaved edits.

## Make, inspect, exercise, record

Use this loop for every change: inspect the existing scene and references; make one bounded change; inspect errors/warnings; capture the actual viewport; exercise the affected gameplay; record evidence and the remaining limits. For spatial changes, inspect multiple useful angles, not only a flattering still. Before running or saving, inspect unsaved script buffers as well as disk files. A saved-project test does not validate an unsaved buffer; preserve and reconcile another writer's pending edits. An editor screenshot is not proof of player-controlled gameplay. A successful tool call is not visual acceptance. In Godot, select the 2D workspace before a 2D viewport capture and verify real image dimensions; the plugin can return a 2 x 2 placeholder while Script is active.

First test new tool operations and imported samples in a disposable scene or separate project. A new bridge must prove object creation, property modification, save, reopen with properties retained, removal, save, and reopen with the object absent. Never use a canonical map as the first CRUD test.

Record project root, Git HEAD, dirty baseline, intent, files/assets touched, engine and bridge versions, viewport images, input/action sequence, logs, pass/fail criteria, result, and unresolved issues. Report these separately: configuration, transport connection, actual-task tool discovery, functional testing, visual review, gameplay acceptance, and restart recovery. A failed criterion remains failed even if the MCP responds correctly.

## Windows launch commands

Use PowerShell in this project directory:

```powershell
python tools/game_pipeline.py status
python tools/game_pipeline.py ENGINE_NAME
python tools/game_pipeline.py blender
```

Replace `ENGINE_NAME` with `godot` for DCC or `unreal` for Ginnungagap. Blender is on demand; do not launch another copy if the intended project session is already listening. The launcher refuses an occupied designated port and does not terminate its owner. To close, save only the work you own, then close normally. Never discard unknown unsaved packages to complete a restart test.

Configuration lives in `.codex/config.toml` and `.codex/game-toolchain.json`. Runtime logs and scratch state are in `.codex/toolchain/state/` (Git ignored). Godot also exposes runtime logs through MCP; Unreal has LogsToolset. Blender launcher output and MCP protocol/status responses provide connection evidence. `status` tests TCP reachability only.

Blender starts with factory scene/preferences and the project-local protocol-5 add-on, preserving the unrelated global add-on and 9876 session. `pipeline-session.blend` is an initial scratch file recreated on launch. Save authored assets to explicitly named source files outside this scratch path before closing. Do not use the upstream global add-on installer or change global Blender preferences as a routine repair.

## Ports and telemetry

| Project | Engine | Blender |
|---|---|---|
| DCC | HTTP 127.0.0.1:8788; WebSocket 127.0.0.1:9500 | 127.0.0.1:9877 |
| Ginnungagap | Official Unreal MCP 127.0.0.1:8787/mcp | 127.0.0.1:9878 |

All listeners must remain loopback-only. New MCP telemetry is disabled through configuration/environment, with Unreal `ModelContextProtocol.EnableAnalytics=0` and Blender consent false. The Unreal launcher additionally passes per-session `EditorSettings` overrides for `AnalyticsPrivacySettings.bSendUsageData=False` and `CrashReportsPrivacySettings.bSendUnattendedBugReports=False`. Both were read back as false after restart. Use the launcher to retain these settings; opening the project through another route may use global defaults. Do not infer that operating-system or third-party service telemetry is changed. Keep Unreal tool discovery enabled. Fetch current tool schemas before calling them; optional nullable parameters may still need explicit `null` in this engine build.

## Assets and interchange

Inventory before downloading. Record supplier URL/receipt, exact pack version, license text or entitlement evidence, actual files, engine version tested, representative imported asset, and approval status. Folder names and successful loading do not establish rights or full compatibility. DCC's existing asset register/private-pitch restrictions remain binding. Do not publish its placeholder or derivative content.

Stage samples separately. Use a native `.blend` source plus explicit GLB export for Godot and FBX export for Unreal when appropriate. Keep `.blend` sources outside Godot `res://` unless the Blender importer is deliberately configured. The test demonstrated that an unconfigured native `.blend` importer can abort other queued imports. Validate units, axes, object dimensions, materials, normals/smoothing, collision, and (for animated assets) skeleton, retargeting, root motion, and a real playback cycle. The setup's cube round trip does not verify production rigs or animation.

For DCC, run `python tools/verify_build.py --export`. This exercises the existing readiness suite, fresh imports, clean export, archive inspection, and two exported-executable checks. The export must exclude `.codex/`, `addons/godot_ai/`, validation scenes and `_mcp_game_helper` in exported project settings. Keep Godot's helper enabled only for development; do not manually remove it from the editor project to conceal an export failure.

For Unreal, retain Epic's ModelContextProtocol and existing toolsets. Inspect logs and the actual PIE/game window, not just the editor camera. Use the existing playable test map without replacing game logic. On the setup run, `L_QuickDemo_FourDeck` entered PIE below the ship. Follow-up fixed the blocked PlayerStart and verified the saved spawn after an editor restart. Camera visibility and playable movement remain unaccepted: a compiled owner-visibility change is partial, and brief keyboard probes did not verify translation. Do not equate valid spawn coordinates or OwnerNoSee flags with gameplay proof. The 17 pending assets were subsequently identified as new concept texture imports, backed up with their source PNGs and autosaves, saved individually, and verified unchanged after a normal restart. No unknown edits were discarded. The canonical GameFeatureData asset-manager rule is now added and verified after restart. Keep failed diagnostic calls in the record; editor-level APIs may fail during PIE even when game-world actor operations work.

## Reviewed documentation

- [Godot AI 3.2.4 release](https://github.com/hi-godot/godot-ai/releases/tag/v3.2.4)
- [Epic official Unreal MCP setup](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor)
- [Blender MCP](https://github.com/ahujasid/blender-mcp)
- [Codex MCP configuration](https://developers.openai.com/codex/mcp/)
- [Unreal Agent Harness](https://github.com/per-simmons/unreal-agent-harness)

The community harness supplied useful inspect/change/capture/verify ideas. Our launchers use Windows paths and existing projects; its shell scripts, sample city, alternate gameplay frameworks, and external service setup were not executed or merged. Review upstream scripts and version compatibility before adopting any further automation.
