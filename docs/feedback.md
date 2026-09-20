# Playtesting feedback

I keep my original feedback here so that later development notes can be traced
back to the problem or design request. Quotes preserve my wording; the English
summaries describe the requested outcome, not additional requirements.

This record was started on 2026-09-20. FB-001 and FB-002 were entered
retrospectively from earlier project messages; their linked implementation dates
do not imply these notes were written at that time. Earlier discussions are
summarised separately in [the development log](development-log.md).

For future entries I will keep the original feedback, recording date, requested
outcome, implementation reference, verification and any remaining questions.
Implementation and passing tests do not automatically mean the experience has
been accepted after playtesting. I will record further feedback rather than
overwrite the original observation.

## FB-001 — Discover the opening through interaction

Recorded: 2026-09-20, retrospective entry.

**My original feedback:**

> 我感觉有些开场介绍完全是阅读，没有互动慢慢认知的情况

**Requested outcome:** I wanted to learn about the world and companions through
actions, rather than only reading an introduction.

**Implementation:** [3ed6e8b](https://github.com/frandebill-FDB/hero-on-probation/commit/3ed6e8b),
2026-09-19. Optional counter exploration, parcel questions and companion encounters.

**Verification/status:** Implemented; 15 local tests passed at that revision.
Further feedback about clarity and pacing remains open.

## FB-002 — Refuse the first job for a speedrun ending

Recorded: 2026-09-20, retrospective entry.

**My original feedback:**

> 我觉得第一关可以再加入一个拒绝接受任务的选项，直接通过的速通结局

**Requested outcome:** I wanted refusal to be a real choice with its own short,
funny ending.

**Implementation:** [c5735c3](https://github.com/frandebill-FDB/hero-on-probation/commit/c5735c3),
2026-09-19. Option 5 leads to CLOCKED OUT and the ANY% HERO achievement.

**Verification/status:** Implemented; 18 local tests passed at that revision.
Final playtesting acceptance of the ending is not recorded yet.

## FB-003 — Create a character and manage that character's save

Recorded: 2026-09-20.

**My original feedback:**

> 现在我发现了问题，这个游戏没有创建角色的功能，存档功能就很无语，应该要有对应的玩家创建角色，并且还要有删除存档的功能

**Requested outcome:** I wanted character creation, saved progress associated
with the correct character, and an option to delete unwanted saves.

**Implementation:** [6b5b1d8](https://github.com/frandebill-FDB/hero-on-probation/commit/6b5b1d8),
2026-09-20. Named characters have independent slots. The start menu supports
creation, selection, confirmed recoverable deletion and version-three import.
The in-game `menu` command returns to character selection. The current scope is
naming, not a class or attribute system; later progress still needs manual saving.

**Verification/status:** Implemented; 37 local tests and Ruff checks passed.
The [Ubuntu CI run](https://github.com/frandebill-FDB/hero-on-probation/actions/runs/35508428305)
for this revision also passed. A separate temporary-directory CLI check covered
two characters, save/load, cancelling deletion and recoverable deletion.
My own playtesting acceptance of this update is still pending.

**Follow-up:** FB-004 records a subsequent usability problem: saving was available
mid-story, but that availability was not clear from the choice interface.

## FB-004 — Make mid-story saving visible and keep the early ending a surprise

Recorded: 2026-09-20.

**My original feedback:**

> 现在有一个路径问题，存档功能似乎设定在了故事结尾，这毫无意义，然后一个速通结局选项应该作为彩蛋而给直白告诉结果

**Requested outcome:** I wanted saving to be useful during the story, not seem
limited to the end. I also wanted the refusal ending to be an Easter egg rather
than have its outcome announced in the option text.

**Diagnosis:** The existing choice handler already accepted `save` and `load`
at every story prompt. The problem was discoverability: a mid-story menu did
not show those commands, while the ending explicitly displayed them.

**Implementation:** The commit titled
`Expose mid-story save controls and hide refusal spoilers` adds a compact command
bar beneath each choice, explains end-result saving separately, and replaces the
refusal label with an ordinary line of dialogue without the ending warning.
The choices, ending trigger and version-four save format remain unchanged.

**Verification/status:** 41 local tests and Ruff checks passed. New checks cover
command visibility, saving without advancing the story, resuming at the shop
after quitting and relaunching, and withholding the Easter egg result until the
choice is made. Further playtesting feedback remains open.

## FB-005 — No real combat system

Recorded: 2026-09-20.

**My original feedback:**

> 然后整个游戏没有战斗系统

**Observation:** I noticed that the game does not provide an actual combat system.

**Code review:** The bridge duel is a single-choice story event. It checks the
equipped item and changes the pan or gold, but there are no player/enemy health
values, combat turns, enemy actions or damage calculations. Equipment currently
affects story outcomes rather than combat statistics.

**Design proposal, not yet implemented:** Upgrade the existing bridge encounter
to a short optional turn-based fight with visible health, weapon and shield
effects, a companion action and retreat. Keep the existing non-combat crossing
routes. Before changing the decision sequence, determine how to preserve or
version existing replay saves, and define victory, defeat and retreat outcomes.

**Status:** Open. This entry records the missing feature and a proposal; no
combat implementation or combat test result is being claimed.

## FB-006 — Let Pip turn an enemy into bread to bypass combat

Recorded: 2026-09-20.

**My original feedback:**

> 我觉得你的处事规则就很好，我建议的是弄一个邪修，那个能把任何物品变成面包的伙伴能把敌人变成面包来逃课

**Requested outcome:** I liked the proposed initial combat rules and wanted an
unconventional shortcut: Pip should be able to turn the enemy into bread and
bypass the normal fight.

**Working design:** Keep the proposed short, deterministic turn-based encounter.
Pip's companion action transforms the bridge slime and ends combat immediately,
without an enemy counterattack. It does not require reducing the enemy to low
health first. The pre-action menu does not label this an instant-win shortcut.
The initial proposal left the quest pan unchanged. That part was superseded by
FB-007 below, which explicitly adds the pan's transformation as the drawback.

**Status:** Design recorded, not yet implemented or tested. The exact action
wording, achievement and aftermath are proposals in
[the combat design](combat-design.md), not completed features.

**Follow-up to FB-005:** The normal combat rules and this shortcut will be
implemented in small steps, with replay-save compatibility handled before the
new fight is connected to the existing story.

## FB-007 — Bread magic also transforms the quest pan

Recorded: 2026-09-20.

**My original feedback:**

> 可以把任务锅也变成面包，算是负面效果

**Requested outcome:** I wanted a drawback for Pip's combat shortcut: the quest
pan should also turn into bread when the enemy does.

**Updated design:** The spell ends the fight immediately but sets the pan to
`bread`. The player continues the story and, on delivery, reaches the existing
ACCIDENTAL CATERING ending. Repair kits cannot undo this transformation. The
current bread ending still pays five gold, so the cost is losing the intact-pan
outcome, not an additional financial penalty. No other equipment is transformed.

**Status:** Recorded in the combat design; not implemented or tested yet. This
refines FB-006 rather than replacing its original quoted request.

## FB-008 — Pip can turn the final boss into bread

Recorded: 2026-09-20.

**My original feedback:**

> 最后带上Pip的情况下 坚持和恶龙战斗可以把boss也变成面包

**Requested outcome:** I wanted the bread-magic shortcut to work at the final
boss too, when Pip accompanies the hero and the player insists on fighting.

**Design implications:** This adds a final confrontation beyond the currently
implemented delivery scene. The option should not disclose its bread outcome
before the player discovers it. The exact battle trigger, aftermath and
achievement are still to be designed.

**Open question:** The current destination character is the Demon King, whereas
this feedback names a dragon. Whether the dragon replaces the Demon King, is the
Demon King's form, or is a separate character is not yet decided.

**Status:** Design request recorded. No final-boss fight or transformation has
been implemented. This extends the combat proposal and does not silently replace
the existing delivery endings.
