# Development log

I use this log to explain what I wanted from the game, what I noticed during
playtesting, and how the project changed in response. My original wording and
follow-up status are kept in [the feedback record](feedback.md). The early-development
section was added retrospectively on 2026-09-20 from project discussions and
the first code snapshot; its individual development dates are not confirmed.
The dated implementation entries refer to actual Git commits. Test results
describe the checks at those revisions, not a new test run for this document.

## Early development — retrospective notes

### Finding a topic I wanted to work on

I initially explored a study-planning tool, but I was more interested in a
text adventure because it gave me room to develop an original story. I tried
a last-train theme with a protagonist travelling home. After discussing the
story, I felt that the mystery was too conventional and that lengthy suspense
would be tiring to read in a terminal.

I wanted an English-language game that other students could understand. I
eventually chose short comic fantasy, inspired by the familiar hero-versus-Demon
King setup but with absurd everyday problems instead of a long heroic epic.
The resulting prototype, Hero on Probation, sends the hero to return a frying pan.

### Making the prototype feel like a game

I felt that the early experience was too sparse. I asked for more side stories
and a way to track gold, equipment and possessions. I also asked that the
adventure stay short and that each ending have its own achievement.

By the first Git snapshot, the game included two companions, a shop, the rats'
moving dispute, the warehouse ghost's resignation, a bridge encounter, inventory,
equipment, quests, a journal, save/load and three delivery endings. These features
are present in that snapshot, but separate implementation dates were not recorded.

## 2026-09-07 — First version-control snapshot

Commit: `3b58af3` — `Record playable RPG baseline`.

My project was already playable when this repository was created. This commit
preserves that prototype; it is not the start of development. Earlier design
discussions are summarised above, but there are no step-by-step Git snapshots
of that earlier work.

The baseline includes the short adventure, state tracking, replay-based saves,
three ending achievements, package configuration, a README and regression tests.

## 2026-09-07 — Preparing installation and verification

Commit: `1c52aaf` —
`Document submission workflow and configure Ubuntu verification`.

After reaching an ending, I asked whether the project was ready for submission
and what was still missing. The next changes addressed installation, documentation
and verification rather than adding more story.

The README was expanded with installation and launch commands, controls, saves,
code structure and limitations. A submission checklist and Ubuntu 24.04 GitHub
Actions workflow were added, with Python 3.10 and 3.12 checks. At this stage,
11 local tests and Ruff checks passed. The subsequent GitHub Actions run for
this revision also passed; that result does not cover later revisions.

## 2026-09-19 — Keeping a baseline and improving the opening

I wanted to preserve the first version before improving it gradually. The
`v0.1.0` tag was created on this date, pointing to the September 7 revision
`1c52aaf`. It remains available as a reference and for the original save format.

Commit: `3ed6e8b` —
`Make the guild opening discoverable through player choices`.

**What I noticed:** I did not understand all the options and endings. In
particular, the opening explained the setting and companions through reading
rather than letting me discover them through interaction.

**What I wanted:** A short opening where I could inspect things, ask questions
and meet the companions before choosing one, without making the story much longer.

**What changed:** The opening now offers contract and pocket inspection, questions
about the parcel, and short Pip/Bea encounters. Questions can be skipped or
revisited. Accepting the parcel always states the delivery goal and reward.
Repeated inspection gives no extra money, items or journal entries. The town,
bridge and three delivery endings were kept unchanged.

**Technical notes:** The new choice sequence requires version-three saves in
`saves/adventure-v3.json`. The previous file is left untouched, and version-two
saves can still be played using the preserved `v0.1.0` game.

**Verification:** 15 local tests passed, covering all three complete delivery
routes, optional/repeated exploration, saves at each opening stage and safe
rejection of older saves. Ruff lint and format checks passed. Remote CI for
this revision was not confirmed in this entry.

## 2026-09-19 — A refusal ending

Commit: `c5735c3` — `Add a refusal speedrun ending at the guild`.

**What I wanted:** At the first job offer, I wanted the option to refuse and
finish immediately with a funny speedrun ending, instead of always accepting
the delivery.

**What changed:** Option 5, "Decline the job and leave", now leads to
`CLOCKED OUT` and the `ANY% HERO` achievement. The hero keeps the initial
3 gold and leaves without accepting the quest, receiving the pan or recruiting
a companion. Review commands and save/load still work after the ending.

**Technical notes:** The guild reports whether the job was accepted, and both
live play and save validation use the same story runner. This prevents replay
from continuing into town after refusal. The new option is appended without
renumbering existing choices, so existing version-three saves remain compatible.

**Verification:** 18 local tests passed, including refusal before and after
exploration, unchanged resources, skipped later scenes, repeated load without
duplicate achievements, review commands and rejection of decisions after the
ending. The original delivery routes still pass, as do Ruff checks. Remote CI
for this revision was not confirmed in this entry.

## 2026-09-20 — Named characters and save management

Git record: `6b5b1d8` — `Add named characters and recoverable save management`.
Original feedback: [FB-003](feedback.md#fb-003--create-a-character-and-manage-that-characters-save).

**What I noticed:** The game had no character creation. The single unnamed save
did not feel connected to a player, and there was no way to delete a save in-game.

**What I wanted:** Create a character before playing, associate saved progress
with that character, and offer a way to delete unwanted saves.

**What changed:** A start menu now offers creation, loading, deletion and import
of old version-three progress. Each named character has a separate save, and the
name appears in story menus and status. Duplicate active names are rejected.
The `menu` command returns to character selection without saving new progress.
Creating a character writes a starting save; later progress still needs `save`.
Character creation is deliberately limited to naming, without adding classes,
stats or more story content in this iteration.

**Technical notes:** Version-four saves contain a generated ID, a display name
and replay choices. Display names are not file paths. Writes replace only the
current character's slot atomically. Import validates version-three progress
before creating a named copy and leaves the source file unchanged. Deletion
requires typing `DELETE` and moves the selected file to `saves/deleted/`, making
it recoverable without affecting other characters. Old version-two saves still
require the preserved initial game.

**Verification:** 37 local tests passed, including the original story regressions,
separate character progress, duplicate/invalid names, cancelled and confirmed
deletion, recovery-copy contents, save-write failure and old-save import. Ruff
lint and format checks passed. The CI module-entry smoke test now creates a
character, reaches an ending, saves and reloads. The subsequent
[Ubuntu CI run for this revision](https://github.com/frandebill-FDB/hero-on-probation/actions/runs/35508428305)
passed; that result does not cover future changes.
An actual module launch in an isolated temporary directory also exercised two
characters, a completed ending, save/load, cancelled deletion and confirmed
recoverable deletion. No existing player saves were used or changed by that check.

## 2026-09-20 — Mid-story save controls and a less obvious Easter egg

Git record: `Expose mid-story save controls and hide refusal spoilers`.
Original feedback: [FB-004](feedback.md#fb-004--make-mid-story-saving-visible-and-keep-the-early-ending-a-surprise).

**What I noticed:** The interface made it look as though saving was only
available at the end of the game. Also, the refusal option announced that it
would end the adventure, which spoiled the surprise I wanted from a speedrun
Easter egg.

**What changed:** Every story choice now displays a compact `save` / `load`
command bar. Saving was already supported at those prompts; the improvement
makes that existing behaviour visible. The ending separately explains that
saving there keeps the completed result, while loading returns to the last save.
The refusal option is now a normal line of dialogue without an ending label.
The README's ending reference is also collapsed behind a spoiler heading.

**Verification:** 41 local tests and Ruff checks passed. A new regression test
saves in the shop, exits, starts the menu again and restores the same character
at the same unfinished decision. Other new checks verify visible save controls
and that the early ending is not disclosed before selection. No story choice
numbers or save format changed. Remote CI for this revision is a separate check.

## Next steps

I have also identified the lack of a real combat system. The current bridge
duel is only a story choice; [FB-005](feedback.md#fb-005--no-real-combat-system)
records this open issue and a proposed small turn-based encounter. Its design,
save compatibility and implementation are still pending.
I liked the proposed initial rules and suggested that Pip could turn the enemy
into bread to bypass the fight. [FB-006](feedback.md#fb-006--let-pip-turn-an-enemy-into-bread-to-bypass-combat)
preserves that request, and [the combat design](combat-design.md) separates the
working rules from implementation and test results that are still pending.

I want to check whether the mid-story save controls are now clear and whether
the early ending feels like a discovery. Character switching, deletion and
old-save import remain part of further playtesting. I also want to work
through the character state, branching, save replay
and tests so that I can understand and explain the implementation. Further
changes should address specific playtesting feedback rather than just add length.

## Development tools and collaboration

I chose the direction and provided the design requests and playtesting feedback
described above. I used AI assistance to generate and revise code, prepare and
run automated tests, and help draft documentation. I have not kept a complete
record of working hours, so this log does not infer them retrospectively. The
course's rules on AI assistance still need to be confirmed before submission.
