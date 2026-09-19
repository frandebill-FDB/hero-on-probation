# Development record

## First version-control snapshot

The first commit records an already playable prototype developed with AI
assistance during an interactive learning session. It does not represent the
start of coding. Earlier development was not tracked in this repository;
no historical commits or working hours have been reconstructed.

The baseline includes a short story, two companions, optional town errands,
inventory and equipment, save replay, three endings and achievements.

## Submission preparation

After the baseline, documentation and Ubuntu CI configuration were added.
Local verification results and outstanding checks are recorded in
`submission-checklist.md`. Git commit timestamps record when changes were saved.

Record future work honestly: date, actual time spent, change, verification,
and the relevant commit. The student should review and understand generated
code and check the course's policy on AI assistance before submission.

## 2026-09-19 — Discoverable guild opening

- Feedback: the opening explained the setting and companions before the player
  could discover them through actions. Three advertised jobs led to the same
  delivery and suggested branches that did not exist.
- Change: replaced that menu with optional contract/pocket inspection, questions
  about the parcel, and short Pip/Bea encounters before recruitment. Players can
  skip questions. Accepting the job always states its destination, reward and
  goal, so skipping does not hide essential instructions.
- Scope: kept the town, bridge, rewards and three endings unchanged. Repeated
  inspections have short responses and do not duplicate coins, items or journal
  entries. Pip demonstrates on a pencil, not on the player's quest item.
- Save decision: numbered replay paths changed. New saves use version 3 and
  `saves/adventure-v3.json`; the old file is not overwritten. Older save versions
  are rejected with guidance to use the preserved `v0.1.0` baseline.
- Verification: 15 local unit tests passed, including all three complete ending
  routes, repeated/skipped exploration, saves at each opening stage and rejection
  of older saves without modifying them. Ruff lint and format checks passed.
  Remote CI for this change is not implied by local results.
- Authorship/time: AI-assisted implementation following student feedback. No
  student working hours were measured or inferred from this session.
- Next: student playtest of the new opening, especially clarity of English and
  whether optional questions feel useful. No further story expansion yet.
- Git record: the commit containing this entry is titled
  `Make the guild opening discoverable through player choices`.

## 2026-09-19 — Refuse the delivery: a short alternate ending

- Feedback: the student wanted the first job offer to include a real refusal,
  leading directly to a humorous speedrun ending instead of forcing acceptance.
- Change: appended option 5 at the parcel menu, explicitly marked as ending the
  adventure. Refusal unlocks `CLOCKED OUT` / `ANY% HERO`, preserves the initial
  3 gold and never awards the pan, accepts the quest or recruits a companion.
  The ending retains status, bag, quests, journal, achievements and save/load.
- Implementation: the guild reports whether the job was accepted. Live play and
  replay validation share a story runner so both stop at the early ending.
  Achievement recording is shared with the three unchanged delivery endings.
- Compatibility: retained save version 3 and its filename. Appending the option
  preserves all previous valid choice sequences. Replay rejects extra decisions
  after refusal and never proceeds into town.
- Verification: 18 local unit tests passed; new tests cover immediate refusal,
  refusal after exploration, unchanged resources, skipped later scenes, repeated
  load without duplicate achievements, review commands and invalid trailing
  decisions. Existing delivery-route and save tests still pass. Ruff lint and
  format checks passed. Remote CI is a separate check.
- Authorship/time: AI-assisted implementation of student feedback; student hours
  were not measured and are not inferred from this change.
- Next: student playtest of option 5 and the short ending's wording.
- Git record: `Add a refusal speedrun ending at the guild`.
