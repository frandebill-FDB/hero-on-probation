# Hero on Probation

A short English-language comic fantasy RPG about questionable heroes and ordinary
deliveries. Create a character, recruit a companion, fight or negotiate, and
collect ten funny endings. Keep growing across three rotating delivery jobs.
This is a light collection game, not a tightly balanced combat challenge.

## Install and run

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/). Play needs no GUI,
network service, external dataset or third-party runtime dependency.

```sh
git clone https://github.com/frandebill-FDB/hero-on-probation.git
cd hero-on-probation
uv venv
uv pip install -e .
uv run -m hero_on_probation
```

These are the course's editable-install and module-launch commands.
Run from the same project directory each time to use the same local saves.

## Your first journey

Choose **1. New game** and enter a name (1–24 printable characters). Ring the
guild bell, accept the delivery and recruit Pip or Bea. Explore town or leave
for the crossing, then deliver the parcel or challenge the boss. Each ending
offers another journey with the same character.

Levels, XP, gold, equipment, unused repair kits and achievements carry over.
Health is restored and local tasks reset. From journey 2, a travel desk keeps
your companion and offers a direct route to the boss or optional stops.
You can change companion or replay the full introduction instead.
Skipped events grant no rewards.

## Controls

Enter a displayed number to act. Used one-time options disappear without
renumbering the remaining choices.

| Command | Purpose |
| --- | --- |
| `status`, `bag`, `quests`, `journal`, `achievements` | Inspect your character. |
| `hall` | View the ending collection and achievement records. |
| `hints` | Reveal optional clues for undiscovered endings; also works in the main menu. |
| `travel` | Return to express-route choices outside battles and endings. |
| `back` or Enter | Redisplay the current choices; does **not** undo an action. |
| `save`, `load` | Reload the latest automatic snapshot, not an earlier checkpoint. |
| `help` | Show command help. |
| `menu`, `quit` | Return to the main menu or exit. |

Information commands do not spend a combat turn. Pip's spell transforms the
enemy **and your parcel** into bread; Bea can counterattack and block once per
fight. Combat option **5. Concede defeat** allows failure endings even at high
levels. From journey 2, merchants offer 5-gold wagers: victory pays 10 gold total;
defeat, concession or retreat forfeits the stake. Pip's spell is banned in wagers.

## Saves and collection

New characters **autosave every decision**, including combat and ending rewards.
Loading cannot undo a wager or duplicate a reward. Save data and the Hall of Fame
are stored together in `saves/journeys.sqlite3`, excluded from Git.

Main menu: **New game**, **Continue game**, **Hall of Fame**, **Manage saves**,
**Quit**. Manage saves can archive a character and restore it if the name is
available. Archived characters retain their honour records.

The hall shows collection progress out of ten endings. Undiscovered names stay
hidden until earned; `hints` is optional. Detailed records identify the character,
save ID, first-earned UTC time, journey, level and repeat count.

Back up the entire `saves/` directory while the game is closed. Older replay saves
remain supported but initially use manual saving; see
[save compatibility](docs/save-compatibility.md) for those exceptions.

## Verify

```sh
uv run python -m unittest discover -s tests -v
uvx ruff check .
uvx ruff format --check .
```

[GitHub Actions](https://github.com/frandebill-FDB/hero-on-probation/actions/workflows/test.yml)
checks installation, tests, module launch and code style on Ubuntu 24.04 with
Python 3.10 and 3.12. Test saves use temporary directories.

## Code and documentation

The current game separates state and rules (`journey.py`), terminal interaction
(`journey_cli.py`), SQLite persistence (`journey_store.py`), collection presentation
(`collection.py`) and the main menu (`menu.py`). The other modules preserve
older story and replay-save behaviour. Tests cover both paths.

Public types can be imported without launching the game:

```python
from hero_on_probation import Journey

character = Journey(save_id="a" * 32, name="Mira")
print(character.status())
```

`Hero` is also exported for the older story model.

- [Current rules and rewards](docs/progression.md)
- [Ending guide — spoilers](docs/endings.md)
- [Save compatibility](docs/save-compatibility.md)
- [Submission checklist and verification evidence](docs/submission-checklist.md)
- [Development log](docs/development-log.md) and [original feedback](docs/feedback.md)
- [Archived combat proposal](docs/archive/combat-design.md) — historical, not current rules

The scope is deliberately small: no character classes, skill tree, multiplayer
or cloud sync. The three job templates repeat; fixed enemy stats let experienced
characters become overpowered. Manual save-file tampering is outside the reward
protections.
