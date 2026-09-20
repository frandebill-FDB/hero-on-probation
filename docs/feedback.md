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
