# Archived tool scripts

356 scripts that ran once to generate an asset, a showcase map, or a concept pass, and will not run
again. Moved here on 2 September 2026 so `tools/` shows only what is live.

Nothing is deleted. They are `git mv`d, so history follows each file, and any of them still runs
from this folder — the ones that take paths use `Path(__file__).parent.parent` as the project root,
which is unchanged by the move.

## What stayed in `tools/`

The demo pipeline — build the ship, dress the slice and corridors, set atmosphere, place depth
lights, capture hero shots, and the fixes applied to the demo map — plus the audit, survey and
validation tools, which are the ones worth running again on a tree that keeps changing.

Six scripts were kept that would otherwise have been archived, because live scripts reference them
by name in their comments and a reader following that trail should find the file where it was.

## The rule this got wrong once

Five scripts were archived and restored the same day: `game_pipeline.py`,
`production_reference_pipeline.py`, `validate_thrust_tower_packets.py`, `export_pelagos_for_unreal.py`
and `write_realityscan_uncorrupted_robot_xmp.py`. All five appear in documentation as commands you
are told to run -- ```python tools/game_pipeline.py status``` and the like -- so archiving them broke
instructions somebody was expected to follow.

The distinction that matters, and that the first pass missed: a doc *citing* a script as the thing
that produced an asset is provenance, and the script can move. A doc *instructing* you to run it is a
live dependency, and it cannot. Around 90 archived scripts are cited; five were instructions.

Before archiving anything else from here, check it against:

    grep -rhoE 'python +tools[\/][a-z0-9_]+\.py' docs/ AGENTS.md

## Before restoring one

Check what it assumes. Most of these were written against a project state that has moved: the
four-deck ship has been regenerated, dressed, re-lit and had its light channel order corrected since
most of these last ran. A script that "worked" in July may now place things into a map that no
longer has room for them.
