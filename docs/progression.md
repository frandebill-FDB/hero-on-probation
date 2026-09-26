# Continuing journeys — implemented design, 2026-09-24

## Confirmed choices

I chose to let a sufficiently strong character defeat the boss through normal
combat, retain levels, gold and equipment between journeys, and prohibit Pip's
bread magic in merchant wagers. The implementation keeps each journey short,
using three rotating jobs rather than adding a large map or skill tree.

The main menu has one New game entry and one Continue game entry. Older unfinished
saves retain their current scenes and can continue into the growth system at
the ending using `next`. Completed older saves upgrade on loading, keeping the
same name and ID and preserving the original JSON as a hidden recovery backup.

## Growth and rewards

Characters start at level 1, 12 HP and 3 gold. XP required for each next level is
100 times the current level. Each level adds 8 maximum HP, 4 attack and 2 defence.
Levelling adds the extra HP capacity to a surviving hero; it does not resurrect
a defeated hero. Starting another journey restores full HP.

| Event | Repeatable reward per journey | First-achievement bonus per character |
| --- | --- | --- |
| Bridge victory, ordinary or bread | 30 XP | Bread shortcut: 100 XP |
| Merchant wager victory | 30 XP and 10 gold payout after a 5-gold stake | HOSTILE NEGOTIATION: 100 XP |
| Boss victory, ordinary or bread | 150 XP | Ordinary: 100 XP; bread: 1,000 XP |
| Intact or bread delivery ending | 80 XP and 5 gold | 100 XP for each distinct ending |
| Damaged delivery ending | 40 XP, no delivery pay | 100 XP |
| Boss victory ending | 80 XP; ordinary victory also gives 8 gold | Included in the boss row above |
| Bridge defeat, boss defeat, boss retreat | 10 XP, no delivery pay | 100 XP for each distinct ending |
| Guild refusal | 0 task XP, no gold | 20 XP once |
| Bribed victory | No task/battle XP or gold reward | 100 XP once |

Battle and ending XP are separate events: a bread boss victory awards 150 + 80
normal XP, plus the 1,000 first-time achievement bonus. Achievements have stable
IDs across task variants. Repeating the same ending on a later journey can earn
normal XP, but not another first-time bonus. Repeated refusal stays on the same
journey number and gives no further XP. After a non-refusal outcome (including
failure), the next journey increments the number and enables second-journey rules.

Each merchant and battle event can pay only once in a journey. Every decision
is automatically saved, so reopening or loading the same character restores the
settled result instead of replaying a payout. This is not a tamper-proof online
economy; manually replacing the database with a backup is out of scope.

## Task rotation and retained state

1. The Pan Returns — Demon King — frying pan — Probation Square / Bridge Slime.
2. Curtain Call — Count Snooze — blackout curtains — Midnight Market / Toll Bat.
3. Notice Period — The Lich Manager — resignation form — Overtime Plaza / Union Skeleton.

Jobs repeat in that order. The same scene and choice structure handles each.
The current stage, enemies, combat turn and companion action availability are
saved as data; loading does not rerun previous scenes.

Retain: identity, level, XP, gold, equipment, owned gear, unused repair kits,
achievement records and ending journal. Reset: companion selection, current
parcel, quests, local references/certificates, wager participation and run rewards.

## Battle balance

Wooden Sword base damage is 3, Iron Sword 5, and no weapon 1; add level bonuses.
Pot Lid gives 1 defence and protects a parcel when defending. Defending adds 4
protection for that turn. Bea gives one counterattack (+2 damage) and full enemy
turn block per battle. Pip instantly transforms both opponent and task parcel.
A repair kit fixes damage but not bread. Retreat from the crossing keeps damage
and returns to its menu; retreat from the boss is a terminal outcome.

Continuing bosses have 120/130/140 HP, 18/19/20 attack and 8 defence across the
three variants. These fixed values deliberately replace the classic 9999/999/99
balance **only in continuing mode**. A level-1 hero loses without the shortcut;
a tested level-8 hero can defeat the first boss with normal attacks. Bosses do
not scale to the player's level, allowing growth to matter. The classic boss
remains unbeatable by ordinary classic equipment.

## Wagers and bribery

Both shop NPCs offer wagers from journey 2: equipment shopkeeper and certificate
clerk. The stake and no-magic rule are shown before selection. The chosen stake
is 5 gold: win pays 10 total (net +5); defeat or retreat pays nothing (net -5).
The stake is committed before the first combat action. Insufficient funds reject
the wager without consuming the merchant's once-per-journey opportunity.

Pip's action is visibly unavailable in these fights and cannot change enemy HP,
the parcel or the turn. Bea can act normally. The merchant restores the hero's
HP after the wager and keeps the shop open. No permanent NPC death is modelled.

The boss's staged defeat costs 12/14/16 gold according to the job variant, from
journey 2 onward. The option shows the price. Payment produces PAID PERFORMANCE
and PAY-TO-WIN HERO, but no genuine boss XP, task XP, delivery pay or victory gold.
Insufficient funds leave the character at the boss menu without a deduction.

## Storage and Hall of Fame

The standard-library SQLite database `saves/journeys.sqlite3` contains character
snapshots and per-character achievements. Each numbered transition runs on an
in-memory copy. Its new snapshot and honour rows commit in one transaction;
write failure preserves the previous snapshot. Revision checks reject writes
from stale windows. Information commands perform no transition or payout.

Achievements store their description, actual first-earned timezone-aware UTC
timestamp, character ID/name (via the character table), first journey/level,
last journey and repeat count. The primary key is character ID plus achievement
name. A repeat on the same journey does not add another count. Records remain
after a character is archived, clearly marked as a deleted save. Manage saves →
Restore restores that character if its name is not already in use.

Older-save upgrading replays a completed save without writes or prompts, keeps
money and gear under the same character identity at level 1, and imports achievements without retroactive
XP. Unknown historical timestamps and original levels are explicitly shown as
unknown, not replaced with the import time. The source JSON is left untouched.
Its ID is marked by the database entry, so the backup is not listed again, even
if the upgraded character is deleted. A repeated upgrade loads the existing
progress instead of resetting it or issuing rewards again.

The player's next playtest is still needed to judge pacing and reward balance.

## Small interface improvement — consumed choices

Menus filter out completed one-time actions using existing flags and inventory,
without changing the save format. Certificate purchases, already-owned unique
equipment, completed errand entries, spent merchant wagers and used companion
skills disappear. Repair kits remain repeatable, and navigation stays available.
A failed purchase does not consume its option. A banned Pip action is still
labelled unavailable in wagers; it is a rule restriction, not a consumed skill.

Choice numbers remain stable when a row disappears. For example, after buying a
certificate the exit still reads `2. Go to the boss's door.` Both rendering and
input validation use the same available-action list. Entering a removed number
does not spend gold, take a turn or write a new autosave. Per-journey choices
return next journey; owned permanent equipment stays hidden. Existing snapshot
saves immediately use these rules when loaded. Older replay-story compatibility
keeps its historical numbered decisions unchanged.
