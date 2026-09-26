# Save compatibility

New characters use automatic SQLite snapshots. This page covers older
replay-based saves; a new player does not need to import anything.

## Loading an older character

Use **Continue game** in the main menu. An unfinished older adventure resumes
at its saved decision with its original story rules and manual `save` / `load`
checkpoints. Until that adventure ends, use `save` before quitting.

At the ending, `next` upgrades the same character to continuing journeys and
autosaving. Loading an already completed older save upgrades it automatically.
The original JSON remains untouched as a recovery backup.

The upgrade keeps the name, save ID, money, equipment, unused repair kits and
achievements. It starts at level 1 without retroactive XP. Unrecorded historical
achievement times and levels remain explicitly unknown. A non-refusal ending
starts journey 2; refusal starts journey 1 again.

An upgraded character appears once in the menu. The older JSON backup is hidden
and cannot bring back an archived character accidentally. Repeated loading does
not reset progress or duplicate rewards.

## Importing an unnamed save

**Manage saves → Import an older save** reads `saves/adventure-v3.json`.
Its decisions are validated before a named copy is created; the original stays
untouched. Version-2 saves require the preserved `v0.1.0` game.

## Deletion and recovery

- Current journey characters are archived inside `saves/journeys.sqlite3`.
  Use **Manage saves → Restore** if the name is not already used. Honour records
  remain visible and are marked as belonging to an archived character.
- Older JSON saves move to `saves/deleted/`. Restore a copy manually to
  `saves/<character.id>.json` without overwriting another save. The in-game
  Restore option applies to SQLite journey characters.

Back up the entire `saves/` directory while the game is closed. Always launch
from the same directory, because save paths are relative to the working directory.

## Technical safeguards

Each current-game transition runs on a copy of the character state. Snapshot
and honour updates commit in a single SQLite transaction; a failed write leaves
the previous saved state intact. Revision checks prevent a stale game window
from overwriting newer progress. This is local single-player storage, not an
anti-cheat system: replacing the database manually can bypass those safeguards.
