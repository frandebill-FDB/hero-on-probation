# Combat design — working draft

Status: design only, recorded on 2026-09-20. No combat system is implemented by
this document. Original feedback: [FB-005](feedback.md#fb-005--no-real-combat-system)
and [FB-006](feedback.md#fb-006--let-pip-turn-an-enemy-into-bread-to-bypass-combat).

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

Only the enemy is transformed. The player's HP, gold and quest pan should not
change as an incidental effect of the transformation. The adventure continues
towards the castle; this is a battle outcome, not a replacement for a delivery
ending. The existing bread-pan ending remains a separate possibility on its
existing route.

Possible aftermath, still a writing proposal:

> Pip waves his wand. The slime becomes a wobbling bun.
> The bun squeaks, "The toll still applies!"
> It can no longer hold its spoon. You step around it.

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
- The transformation leaves the quest pan and unrelated inventory unchanged.
- No instant-win label or achievement title appears before the action is chosen.
- Saving before and after the action restores the correct result and does not
  duplicate achievements or rewards.
- The normal delivery ending still depends on the pan, not on the enemy's form.
