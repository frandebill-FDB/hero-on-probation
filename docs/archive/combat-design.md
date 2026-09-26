# Combat design — historical proposal (2026-09-20)

This document preserves the pre-implementation discussion, not the current
feature status. The classic combat edition subsequently implemented these
encounters. The 2026-09-24 continuing-journey edition adds levelling, ordinary
boss victory, merchant wagers and bribery; its implemented rules and numbers
are documented in [progression.md](../progression.md). Statements below about
pending work describe the historical proposal only.

Status: design only, recorded on 2026-09-20. No combat system is implemented by
this document. Original feedback: [FB-005](../feedback.md#fb-005--no-real-combat-system)
and [FB-006](../feedback.md#fb-006--let-pip-turn-an-enemy-into-bread-to-bypass-combat),
with the drawback requested in [FB-007](../feedback.md#fb-007--bread-magic-also-transforms-the-quest-pan).

## Direction

I liked the proposed initial combat rules and wanted Pip's bread magic to allow
an unconventional way out of the fight. The normal encounter should remain
short and understandable, while a companion choice can produce an unexpected
comic result.

The working proposal is one optional turn-based fight at the bridge. Paying,
helping the slime and the other non-combat routes remain available. The initial
numbers proposed for playtesting are 12 HP for each side, 3 damage with a wooden
sword, 5 with an iron sword, and enemy attacks of 2 or 5 damage with a warning
before the heavy attack. These are starting values, not a tested balance result.

## Pip's shortcut

The player-facing action can simply read `Ask Pip for help.` It should not reveal
that it will end the fight. Choosing it during combat turns the slime into bread
and ends the encounter without a counterattack. No low-health condition or
random failure is planned for this shortcut.

Following the next piece of feedback, the spell transforms **both the enemy and
the quest pan**. The player escapes the normal fight but loses the intact-pan
delivery route: `hero.pan` becomes `bread`. HP, gold and other equipment do not
change as additional spell costs. A repair kit fixes dents, not a bread
transformation, so it cannot undo this consequence.

The adventure still continues towards the castle. Delivery of the bread pan
uses the existing `ACCIDENTAL CATERING` ending and `BREADWINNER` achievement.
Under the current story, that ending still awards five gold and dinner; this
drawback therefore changes the quest outcome rather than reducing the payment.
No extra gold penalty or new ending has been agreed. The existing non-combat
route that transforms the pan remains available too.

Possible aftermath, still a writing proposal:

> Pip waves his wand. The slime becomes a wobbling bun.
> The bun squeaks, "The toll still applies!"
> Your frying pan turns warm and smells suspiciously good.
> Pip: "Good news: no fight. Bad news: no frying."

A possible achievement is `BREAD OVER BRAWN`. It would be awarded once for this
battle outcome and restored once on load, independently of the main ending
achievement. The encounter should not grant repeatable gold or rewards.

## Implementation sequence

1. Model health and damage; test zero-health boundaries and ordinary attacks.
2. Add turn order, victory and defeat checks, then defence and equipment effects.
3. Add the Pip outcome, ensuring it exits before the enemy turn. Define Bea's
   distinct action, retreat and defeat consequences before wiring them in.
4. Connect the encounter to the bridge and test non-combat paths.
5. Handle old replay-save rules explicitly; do not interpret old duel decisions
   as new combat turns. Test mid-fight saving and each terminal battle outcome.
6. Playtest pacing, English wording and balance; record actual feedback.

## Checks needed for the shortcut

- Pip can transform an enemy at full or partial health.
- The encounter stops immediately, with no retaliation.
- The transformation sets the quest pan to `bread`, including if it was dented.
- HP, gold and unrelated inventory remain unchanged by the spell itself.
- Repair kits cannot reverse the transformation.
- No instant-win label or achievement title appears before the action is chosen.
- Saving before and after the action restores the correct result and does not
  duplicate achievements or rewards.
- Reaching the castle after this action produces the existing bread-pan ending
  and reward, not the intact-pan ending.

## Final-boss extension — the Demon King is a dragon

In [FB-008](../feedback.md#fb-008--pip-can-turn-the-final-boss-into-bread), I also
suggested that bringing Pip and insisting on fighting the final dragon/boss
could let me turn that boss into bread. This is an additional design request,
not an encounter already present in the game.

The intended condition is Pip's presence plus the player's decision to insist
on a final fight. The menu should preserve the surprise rather than advertise
an instant-win ending. The exact skill activation and resulting ending remain
to be specified. The bridge spell's pan-transformation drawback is retained;
its application at the final scene must account for whether the pan has already
been handed over.

In [FB-009](../feedback.md#fb-009--the-demon-king-is-the-dragon), I chose to make the
existing Demon King a dragon rather than add a separate dragon character.
He is still the owner of the frying pan and wears an apron when opening the
castle door. The current arrival text now establishes this identity.

The delivery remains the main task. A future option to insist on fighting will
lead to this same character's boss encounter, not an additional location or
unrelated quest. Bringing Pip will allow the proposed bread transformation.
The actual boss fight, non-Pip path, rewards, achievement and save compatibility
still need implementation. This story clarification does not add that fight yet.
