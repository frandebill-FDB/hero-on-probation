# Hero on Probation

A short original English-language comic fantasy adventure. Return the Demon
King's frying pan, recruit a questionable companion, and obtain dinner.

## Run

Requires Python 3.10+ and uv:

```sh
uv sync
uv run -m hero_on_probation
```

From the project root, the grading installation and launch commands are:

```sh
uv venv
uv pip install -e .
uv run -m hero_on_probation
```

All commands work in a text terminal; no GUI, network service or external data
is needed during play. Run commands from the project root so saves use the
same location each time.
Enter a displayed number to choose, or `quit` to exit. Invalid input is retried.
At any choice (and after the ending), use `status`, `bag`, `quests`, or `journal`.
The inventory tracks quantities, equipped items, the quest pan and its condition.
Turning your wooden sword into bread removes it from inventory; an equipped
Iron Sword stays equipped.

Use `save` to replace the local slot `saves/adventure-v3.json`, and `load` to resume.
Version-three saves store decisions and replay them from a fresh character, so
rewards are not added twice. Replay text is hidden: loading resumes at the saved
choice, or displays the completed adventure's status and achievement.
Save files are excluded from Git. Progress is not saved automatically.
Older saves are rejected because the interactive opening changes choice order.
The original `saves/adventure.json` is left untouched; play version-two saves
with the preserved `v0.1.0` release of the game.
Existing files are not altered by loading. Saving replaces the selected slot.

## Game scope

Keep the adventure short: one pan delivery, one optional town hub, two brief
side errands, one bridge encounter and three endings. Do not add more locations
or a long combat grind. Aim for short dialogue beats followed by a decision;
humour should come from choices and their consequences.

Each ending unlocks a different achievement:

| Ending | Achievement |
| --- | --- |
| Delivery Complete | DELIVERY HERO — defeated the shipping estimate |
| Dish Duty | LORD OF THE RINSE — came for gold, stayed for grease |
| Accidental Catering | BREADWINNER — delivered edible cookware |

Use `achievements` to review the current playthrough's unlocks. They are restored
with a saved playthrough, not collected globally across separate new games.

The guild, an explorable town, the bridge and the castle; two companions,
three endings and optional kindness callbacks.
At the guild, optionally inspect your contract and pockets, ask about the parcel,
and meet the companions before recruiting one. Ring the bell, accept the parcel,
then choose a companion to advance. Questions can be skipped or revisited;
repeating them grants no extra items or money. The delivery remains the main job.
Bridge choices change gold and the pan's condition; the pan's condition at delivery
determines the ending. The duel is a single
choice encounter, not a full combat system. Equipment has specific story effects
rather than numeric combat statistics:

- Iron Sword (5 gold): unlocks a clean victory in the bridge duel.
- Pot Lid (3 gold): blocks the spoon without damaging the quest pan.
- Repair Kit (2 gold): automatically repairs a dented pan before delivery.

Visit town locations in any order and return as often as needed before leaving.
The rats' moving dispute pays 2 or 4 gold and gives a reference that waives the
toll. The warehouse ghost pays 3 gold and provides a castle reference worth
2 gold on arrival. Both quests can be deferred; rewards are granted once only.
Pip and Bea produce different ghost-quest dialogue and items.

## Verify

```sh
uv run python -m unittest discover -s tests -v
```

## Code and limitations

- `models.py`: the Hero data class with gold, inventory, equipment and progress.
- `game.py`: numbered input, main scenes and ending achievements.
- `town.py`: optional errands and purchases.
- `session.py`: information commands, validated JSON saves and replay.
- `tests/test_adventure.py`: rewards, purchases, endings and save regression tests.

The game deliberately uses a short, deterministic choice-based duel rather than
a full combat engine. Achievements belong to one playthrough. There is one save
slot and no autosave. Story changes can require a new save version, because
saves replay decisions rather than storing a snapshot of the call stack.

The public API exposes `Hero`, for example:

```python
from hero_on_probation import Hero

hero = Hero()
print(hero.gold)
```

Development provenance is documented in [the development log](docs/development-log.md).
Outstanding release checks are in [the submission checklist](docs/submission-checklist.md).
