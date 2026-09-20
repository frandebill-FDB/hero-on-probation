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
Start by creating a named character or loading an existing character from the menu.
Character creation currently sets the hero's name, not a class or a stat build;
everyone starts with the same equipment and 3 gold. These are local characters,
not online accounts.

Enter a displayed number to choose, or `quit` to exit. Invalid input is retried.
At any choice (and after the ending), use `status`, `bag`, `quests`, or `journal`.
Every story choice displays a command bar. Type `save` at the same `>` prompt
to save **right there**, before picking the next story option; `load` returns to
that saved decision. These commands are available throughout the adventure,
including the guild, shop, side quests and bridge, not only after an ending.
The inventory tracks quantities, equipped items, the quest pan and its condition.
Turning your wooden sword into bread removes it from inventory; an equipped
Iron Sword stays equipped.

## Characters and saves

The opening menu offers:

1. **Create a character:** enter a printable name of 1-24 characters (0 cancels).
   Existing names are checked without case sensitivity to prevent accidental
   duplicates. A new character's starting progress is saved immediately.
2. **Load a character's save:** pick a name from the list to resume that character.
3. **Delete a character's save:** select a name, then type `DELETE` to confirm.
   Anything else cancels. The file is moved to `saves/deleted/`, not permanently
   erased, and disappears from the active character list. Other saves are untouched.
4. **Import the old version-3 save:** give the progress in `saves/adventure-v3.json`
   a new character name. The original file is preserved, and the imported game
   resumes at its saved choice or ending.
5. **Quit.**

During play, `save` replaces only the current character's slot and `load` restores
that same character. Use `menu` to change characters, create another or delete a
save. **Later progress is not autosaved:** use `save` before `menu` or `quit`.

Version-four files live at `saves/<generated-id>.json` and contain character
identity plus decisions. Names are never used as filenames. Loading replays the
decisions from a fresh hero with the saved name, without doubling rewards or
printing previous story text. Loading does not modify the file. Saves, including
deleted copies, are local and excluded from Git.

To recover a deleted save manually, first quit the game. The deletion message
shows the backup path; its JSON contains the original ID at `character.id`.
Copy that file back to `saves/<original-id>.json` without replacing an existing
file. Avoid restoring beside a newly created character with the same name.

Version-two `saves/adventure.json` files cannot be imported because the opening
changed; use the preserved `v0.1.0` game to play those files. They are left untouched.

## Game scope

Keep the adventure short: one pan delivery, one optional town hub, two brief
side errands, one bridge encounter, three delivery endings and one early exit ending.
Do not add more locations
or a long combat grind. Aim for short dialogue beats followed by a decision;
humour should come from choices and their consequences.

Each ending unlocks a different achievement. The option text does not announce
which choices end the adventure; discoveries are part of the joke.

<details>
<summary>Ending and achievement reference (spoilers)</summary>

| Ending | Achievement |
| --- | --- |
| Delivery Complete | DELIVERY HERO — defeated the shipping estimate |
| Dish Duty | LORD OF THE RINSE — came for gold, stayed for grease |
| Accidental Catering | BREADWINNER — delivered edible cookware |
| Clocked Out | ANY% HERO — skipped the quest and the unpaid lunch break |

</details>

Use `achievements` to review the current playthrough's unlocks. They are restored
with a saved playthrough, not collected globally across separate new games.

The guild, an explorable town, the bridge and the castle; two companions,
three delivery endings, an optional refusal ending and kindness callbacks.
At the guild, optionally inspect your contract and pockets, ask about the parcel,
and meet the companions before recruiting one. Ring the bell, accept the parcel,
then choose a companion to advance. Questions can be skipped or revisited;
repeating them grants no extra items or money. The delivery remains the main job.
Review commands and save/load still work after an ending. Saving then records
the completed result, not an earlier checkpoint. Use `load` for the last saved
decision or `menu` to select/create a different character.
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
- `menu.py`: character creation, selection, old-save import and deletion confirmation.
- `saves.py`: versioned character files, atomic writes and recoverable deletion.
- `tests/test_adventure.py`: rewards, purchases, endings and save regression tests.
- `tests/test_characters.py`: character identity, isolated saves, import and deletion.

The game deliberately uses a short, deterministic choice-based duel rather than
a full combat engine. Achievements belong to one character's playthrough. There
is one slot per character and no ongoing autosave. Story changes can require a new save version, because
saves replay decisions rather than storing a snapshot of the call stack.

The public API exposes `Hero`, for example:

```python
from hero_on_probation import Hero

hero = Hero(name="Mira")
print(hero.gold)
```

Design decisions and development notes are in [the development log](docs/development-log.md).
Original playtesting requests and follow-up status are in [the feedback record](docs/feedback.md).
Outstanding release checks are in [the submission checklist](docs/submission-checklist.md).
