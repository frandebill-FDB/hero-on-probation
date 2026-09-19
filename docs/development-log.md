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
