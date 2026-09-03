# High-Priority Gameplay Foundations

**Status:** first implementation slice, compiled and automation-tested  
**Linear:** TRO-68, TRO-69, TRO-70, TRO-71

This document records the first code slice for four high-priority systems. These issues remain in
progress because production content, full gameplay integration, replication policy, and PIE tuning
are still required.

## Mission and objectives

`UMissionObjectiveSubsystem` owns run-level objectives. An `FMissionObjectiveDefinition` supports:

- required or optional objectives;
- hidden-until-active objectives;
- automatic or manual activation;
- prerequisite objective IDs;
- progress targets;
- jump-blocking objectives;
- cross-system persistence;
- persistent-currency rewards.

Objectives transition through Pending, Active, Completed, Failed, and Abandoned states. Required
unresolved objectives can prevent `UJumpSequenceSubsystem::BeginJumpWarningCountdown()`. Arrival
removes objectives that are not marked to persist across systems.

Blueprints can subscribe to `OnObjectiveChanged` and `OnJumpReadinessChanged` to build objective
tracking and terminal presentation without polling.

### Remaining mission work

- timed objectives and failure consequences;
- procedural mission templates and generation;
- objective-specific actors/listeners;
- primary/side-objective UI;
- reward balancing and resource rewards;
- multiplayer authority and replication;
- end-to-end mission content.

## Player inventory

`UInventoryComponent` is attached to `ACoopSurvivalCharacter`. `UItemDefinition` Data Assets define
stable item IDs, display data, mass, stack size, drop policy, mission-item status, and free-form
tags. The replicated component supports:

- stack merging and splitting;
- slot and mass capacity;
- add/remove/query operations;
- atomic transfer between inventories;
- Blueprint change notifications.

`AInventoryItemPickup` now supplies the generic replicated world stack. Successful interaction
performs an atomic server-side inventory transfer before destroying the pickup. `AWorldItemSeedPoint`
and `UWorldItemSeedCatalog` provide deterministic, weighted, room-filtered distribution for pickups,
weapons, tools, and props. Client interactions are routed through a reliable character-owned server
RPC and revalidated against range and interface support before execution.

### Remaining inventory work

- inventory drop requests and container actors;
- quick slots and item use;
- death/disconnect handling;
- save-game serialization;
- encumbrance effects;
- equipment and fabrication integration;
- production item definitions and UI.

## Ship power

Every `AShipSystemActor` now owns a `UShipPowerNodeComponent`. `UShipPowerGridSubsystem` groups
nodes by bus and allocates available generation to consumers in priority order. It supports:

- generators, storage, and consumers;
- bus IDs and load-shedding priority;
- minimum operating-power fractions;
- damaged generator output;
- storage charge/discharge rates;
- replicated online, damage, allocation, and powered state;
- Blueprint-readable bus snapshots.

`AShipSystemActor::IsOperational()` combines Bloom corruption and power state.

### Remaining power work

- generator/storage actors in the procedural ship;
- tuned demand and priority per ship-system type;
- enforce `IsOperational()` in every system action;
- manual breaker, rerouting, and load-shedding interactions;
- power terminal UI, alarms, and audio;
- resource/fuel consumption and repair costs;
- multiplayer authority and PIE tuning.

## Damage control

Every `AShipSection` now owns a replicated `UShipDamageComponent`. It models:

- hull integrity;
- breach severity;
- fire intensity;
- electrical fault severity;
- local atmosphere percentage;
- breach/fire atmosphere loss;
- fire-driven hull damage;
- passive repressurization after sealing;
- repair, sealing, suppression, and electrical-repair operations.

`UShipDamageControlSubsystem` locates damaged and most-critical sections. Electrical damage in a
section reduces the output/availability of power nodes on ship systems located inside its bounds.

### Remaining damage-control work

- damage sources from hazards, enemies, collisions, and landing errors;
- repair tools, parts, durations, interruption, and class modifiers;
- local atmosphere effects on characters, fire, and audio;
- breach/fire actors and VFX;
- door/ventilation pressure transfer;
- system-specific fault consequences;
- mission hooks, HUD/terminal presentation, replication authority, and PIE tuning.

## Automated validation

The `Ginnungagap.Gameplay` automation group currently covers:

- mission activation, progress, completion, prerequisites, and jump gating;
- inventory capacity, stacking, mass, and atomic transfer;
- ship damage critical-state/repair behavior and damaged power output.

Run from the command line with:

```powershell
UnrealEditor-Cmd.exe Ginnungagap.uproject -unattended -nop4 -NullRHI `
  "-ExecCmds=Automation RunTests Ginnungagap.Gameplay; Quit" `
  -TestExit="Automation Test Queue Empty" -log
```
