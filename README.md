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

Choose **1. New game**. Names are 1–24 printable
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
Completed one-time actions disappear: purchased certificates, owned unique gear,
finished errands, used merchant wagers and spent companion skills. Repeatable
repair-kit purchases, navigation and information commands remain. Remaining
choices keep their original numbers; a missing number is not reassigned to a
different action. Unaffordable purchases stay visible until actually completed.

## Saving and the main menu

**Continuing journeys autosave every numbered decision**, including purchases,
wager stakes, battle turns, XP and final outcomes. `load` restores the latest
snapshot; it is not a pre-battle checkpoint and cannot undo a losing wager.
Enemy health, round number and used companion actions survive exit/relaunch.
Progress and Hall of Fame updates commit in one SQLite transaction in
`saves/journeys.sqlite3`. A failed write keeps the previously saved state.
Concurrent stale windows cannot overwrite a newer revision.

**Older unfinished saves** resume at their original decisions. Until that older
adventure ends, they keep manual `save` / `load` checkpoints. At the ending,
`next` carries the same character into another journey with levels and autosave.
Loading an already completed older save performs this upgrade automatically,
reports the previous result, and starts the next journey. The old JSON remains
untouched as a backup. Version-2 saves require the preserved `v0.1.0` game.

The main menu includes:

1. **New game** — create a character with growth and automatic saving.
2. **Continue game** — select any active character; save compatibility is automatic.
3. **Hall of Fame** — achievements across characters.
4. **Manage saves** — delete, restore, or import an older save; 0 returns here.
5. Quit.

There is one new-game entry, not a choice of editions. Upgrading an older
character preserves its name, save ID, money, equipment, unused repair kits and
achievements. It starts at level 1 with no retroactive XP; historical achievement
times and levels remain unknown. A completed non-refusal advances to journey 2;
refusal starts journey 1 again. The source JSON is hidden from the active list
after upgrade, so it does not appear as a duplicate or reappear after deletion.
Importing an older unnamed file is available under Manage saves, not on the homepage.

Deletion is recoverable. Journey characters are archived inside the database;
Manage saves → Restore restores them if the name is available. Their Hall of Fame entries
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

Main-menu option 3 shows each character's recorded achievement, first-earned UTC
timestamp, full save ID, character name, first-earned journey/level and count.
Repeating an achievement keeps its original timestamp. Different characters
have separate records. Deleted characters remain identified in the hall.
Older achievements enter the hall when the completed character is upgraded, with unknown
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
- `menu.py`: one main menu, save management and automatic older-save upgrades.
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
