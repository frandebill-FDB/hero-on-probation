# Hero on Probation

A short English-language comic fantasy RPG about questionable heroes and
ordinary deliveries. Keep the same character across brief journeys, grow stronger,
and build a record in the Hall of Fame.

## Install and run

Requires Python 3.10+ and uv. No GUI, network service, external dataset or
third-party runtime dependency is needed during play.

```sh
uv sync
uv run -m hero_on_probation
```

The course's installation and launch commands also work:

```sh
uv venv
uv pip install -e .
uv run -m hero_on_probation
```

Run from the same project directory each time: local saves live under `saves/`.

## Start here

Choose **1. Create a continuing-journey character**. Names are 1–24 printable
characters; duplicate active names are rejected without case sensitivity.
Everyone starts at level 1 with 12 HP, 3 gold and the same equipment.

Ring the guild bell, accept the delivery and recruit Pip or Bea. Explore town
or go straight to the crossing, then deliver the parcel or challenge the boss.
The numbered ending menu offers another journey with the same character.
Levels, XP, money, equipment, unused repair kits and achievements carry over.
Health is restored; task items and local quest progress reset. Choose a companion
again on each journey.

Three short jobs rotate through the same structure: return a frying pan to the
Demon King, bring blackout curtains to Count Snooze, and deliver a resignation
form to the Lich Manager. There is no expanding world map or random grinding.

Type a displayed number to act. Other commands:

- `status`, `bag`, `quests`, `journal`, `achievements`: inspect your character.
- `hall`: show achievement records across journey characters.
- `back` or Enter: redisplay the current options, **not undo** a decision.
- `save` / `load`: reload the latest automatic snapshot.
- `menu` / `quit`: return to character selection or exit.

Information commands redisplay the current choices and never spend a battle turn.

## Saving: continuing journeys versus classic characters

**Continuing journeys autosave every numbered decision**, including purchases,
wager stakes, battle turns, XP and final outcomes. `load` restores the latest
snapshot; it is not a pre-battle checkpoint and cannot undo a losing wager.
Enemy health, round number and used companion actions survive exit/relaunch.
Progress and Hall of Fame updates commit in one SQLite transaction in
`saves/journeys.sqlite3`. A failed write keeps the previously saved state.
Concurrent stale windows cannot overwrite a newer revision.

**Classic characters** retain their original manual-save, decision-replay rules.
`save` keeps a checkpoint; `load` restores it. Their version-4/5 JSON files remain
supported and are not silently converted. Imported version-3 saves keep the
original non-turn-based story. Version-2 saves require the preserved `v0.1.0` game.

The main menu includes:

1. Create a continuing-journey character.
2. Load an active character (journey or classic).
3. Delete a character after typing `DELETE`.
4. Import an old unnamed version-3 classic save.
5. Quit.
6. Hall of Fame.
7. Create a classic combat-edition character.
8. Copy a **completed, saved** classic character into a new journey character.
9. Restore a deleted journey character.

Option 8 asks for a new unique name and preserves the original file. Money,
equipment, unused repair kits and achievements carry over. There is no invented
retroactive XP; old achievement times and original levels are reported unknown.
An unfinished classic adventure must be completed and saved before copying.

Deletion is recoverable. Journey characters are archived inside the database;
option 9 restores them if the name is available. Their Hall of Fame entries
remain visible and labelled as deleted. Classic JSON saves move to
`saves/deleted/`; restore a copy manually to `saves/<character.id>.json` without
overwriting an existing slot. All saves and the local hall are excluded from Git.

Back up the `saves/` directory while the game is closed to move your progress.

## Growth, combat and second journeys

XP to the next level is `100 × current level`. Each level adds 8 maximum HP,
4 attack and 2 defence. Weapons add their base damage (wood 3, iron 5), and a
Pot Lid adds 1 defence. Defending adds 4 protection for that turn. Damage never
goes below zero. Repair kits fix damaged parcels but cannot reverse bread magic.

A bridge or merchant victory gives 30 XP. Real boss victory gives 150 XP.
Delivery endings give task XP, and first-time achievements add bonuses.
Bea counters and blocks once per battle. Pip turns an enemy **and the parcel**
into bread. Ordinary attacks can defeat a boss after sufficient growth.

From journey 2, both the equipment shopkeeper and certificate clerk offer an
optional 5-gold wager: win receives 10 gold total; defeat or retreat loses the
stake. Each merchant accepts one wager per journey. Pip's bread spell is banned;
Bea is allowed. Afterwards health is restored and the shop stays open.
A displayed-price boss bribe is also available from journey 2.

<details>
<summary>Ending and reward spoilers</summary>

The journey edition has ten endings: the eight classic combat outcomes plus
**HONEST VICTORY** / EARNED THE HARD WAY and **PAID PERFORMANCE** / PAY-TO-WIN HERO.
First unlocking **BREAD OF THE REALM** gives 1,000 bonus XP. Later journeys can
earn normal battle/task XP again, but never repeat that first-unlock jackpot.
Repeated refusal gives no extra XP and does not advance the journey number.
Bribery pays no delivery gold or boss XP; its first achievement gives 100 XP.

Journey bosses use 120–140 HP, 18–20 attack and 8 defence, fixed by the rotating
job rather than scaling to the player's level. The classic 9999-HP boss remains
unchanged in classic saves. The growth edition is deliberately rebalanced so
low-level heroes lose while experienced characters can win through normal combat.

Full rules: [progression](docs/progression.md) and [ending reference](docs/endings.md).

</details>

## Hall of Fame

Main-menu option 6 shows each journey character's achievement, first-earned UTC
timestamp, full save ID, character name, first-earned journey/level and count.
Repeating an achievement keeps its original timestamp. Different characters
have separate records. Deleted characters remain identified in the hall.
Classic achievements enter the hall when copied via option 8, with unknown
historical timestamps explicitly marked. These are local records, not online rankings.

## Verify

```sh
uv run python -m unittest discover -s tests -v
```

GitHub Actions is configured for Ubuntu 24.04 with Python 3.10 and 3.12.
A configured workflow is not proof that a particular unpushed revision passed.

## Code structure and limitations

- `journey.py`: serializable state, growth, scenes and turn-based transitions.
- `journey_store.py`: SQLite transactions, optimistic revisions, archive/restore and honours.
- `journey_cli.py`: input, information views and automatic persistence.
- `menu.py`: shared character selection and safe classic-to-journey copying.
- `models.py`, `game.py`, `town.py`, `combat.py`, `session.py`, `saves.py`:
  preserved classic story and replay-save compatibility.
- `tests/`: legacy regressions, combat and endings, navigation, journeys and storage failures.

Public reusable types are available without starting the terminal interface:

```python
from hero_on_probation import Hero, Journey

character = Journey(save_id="a" * 32, name="Mira")
print(character.status())
```

This is a small local single-player game: no classes, skill tree, multiplayer,
cloud sync, global anti-cheat or unlimited new story content. The same three job
templates repeat. File backup manipulation is outside its reward protections.
The initial balance and dialogue still need player feedback.

See the [development log](docs/development-log.md),
[original feedback](docs/feedback.md) and [submission checklist](docs/submission-checklist.md).
