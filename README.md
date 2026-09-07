# Hero on Probation

A short original English-language comic fantasy adventure. Return the Demon
King's frying pan, recruit a questionable companion, and obtain dinner.

## Run

Requires Python 3.10+ and uv:

```sh
uv sync
uv run -m hero_on_probation
```

For editable installation: `uv pip install -e .` after creating an environment.
Enter a displayed number to choose, or `quit` to exit. Invalid input is retried.
At any choice (and after the ending), use `status`, `bag`, `quests`, or `journal`.
The inventory tracks quantities, equipped items, the quest pan and its condition.
Turning your wooden sword into bread removes it from inventory; an equipped
Iron Sword stays equipped.

Use `save` to replace the local slot `saves/adventure.json`, and `load` to resume.
Version-two saves store decisions and replay them from a fresh character, so
rewards are not added twice. Replay text is hidden: loading resumes at the saved
choice, or displays the completed adventure's status and achievement.
Save files are excluded from Git. Progress is not saved automatically.
Version-one saves are rejected because the new town changes choice order.
Existing files are not altered by loading. Saving replaces the selected slot.

## Prototype scope

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
The initial guild choices all lead to the pan delivery; bridge choices change
gold and the pan's condition, which determine the ending. The duel is a single
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

`models.py` stores the player's state. `game.py` contains the scene functions
and input handling. This is an initial learning prototype, not the final
course submission. `town.py` holds optional errands and purchases. Tests cover
single-payment rewards, spending, equipment effects and save replay.
Future milestones include richer character models,
expanded side quests and documented public GitHub development history.
