# Hero on Probation — Playtest Feedback and Idea Notes

This record tries to preserve how I expressed my ideas at the time, rather than rewriting every comment as a formal requirement. Not all feedback concerns bugs: some entries describe awkward experiences, while others are jokes or new mechanics I thought of along the way. Implementation notes appear separately below the feedback, so I can look back and understand why I changed the game.

FB-001 and FB-002 were documented retrospectively on September 20 from earlier conversations. That documentation date should not be treated as the date the ideas first appeared. Early combat proposals also retain their original wording. They were later implemented in the local version covered by FB-010, rather than remaining unfinished indefinitely. The test results below come from development records at the time; they do not indicate that tests were rerun to compile this document.

<a id="fb-001--discover-the-opening-through-interaction"></a>

## FB-001 | The opening should not be all reading

*Recorded retrospectively on September 20; corresponds to the September 19 commit `3ed6e8b`.*

> I feel that some of the opening introductions are entirely reading, without interaction that lets me gradually discover things.

I did not want the opening to feel like reading a manual. I wanted to inspect the contract, ask about the parcel and meet Pip and Bea before deciding whether to accept the job. These optional interactions were later added to the guild opening without forcing players to read everything. The corresponding version passed 15 local tests. Pacing and clarity could still benefit from further playtesting.

<a id="fb-002--refuse-the-first-job-for-a-speedrun-ending"></a>

## FB-002 | Refusing the job can count as a speedrun

*Recorded retrospectively on September 20; corresponds to the September 19 commit `c5735c3`.*

> I think the first stage could include an option to refuse the quest and immediately reach a speedrun ending.

After refusing to deliver the frying pan, the player leaves the guild and receives the `CLOCKED OUT` ending and `ANY% HERO` achievement. This route grants no pan or companion and retains the starting 3 gold. At the time, 18 local tests passed. FB-004 later adjusted the option's wording to avoid revealing the ending before the player selected it.

<a id="fb-003--create-a-character-and-manage-that-characters-save"></a>

## FB-003 | Saving feels strange without a character

*September 20; commit `6b5b1d8`.*

> I have noticed a problem: the game has no character creation, which makes the save feature rather frustrating. Players should be able to create a character with a corresponding save, and there should also be a way to delete saves.

This update introduced named characters with individual saves and the ability to import an old version-3 save. Deletion required confirmation, and deleted files could be recovered. Character creation was limited to choosing a name, without classes or an attribute system. At this stage, players still had to save subsequent progress manually after creating a character. The version passed 37 local tests, Ruff and Ubuntu CI. Additional checks in a temporary directory covered two characters, saving and loading, and deletion. Whether the system felt convenient still needed personal playtesting.

<a id="fb-004--make-mid-story-saving-visible-and-keep-the-early-ending-a-surprise"></a>

## FB-004 | Make saving visible during the story, and do not spoil the Easter egg

*September 20; implementation record: `Expose mid-story save controls and hide refusal spoilers`.*

> There is a problem with the flow: saving seems to be placed at the end of the story, which makes no sense. Also, the speedrun ending should be an Easter egg, rather than an option that plainly tells you the result.

Investigation showed that the code did not restrict saving to the ending. Instead, the story menus failed to display `save` and `load`. Command prompts were therefore added below story choices, with separate explanations of saving and loading at the ending screen. The refusal option was also changed to ordinary dialogue that did not reveal the ending in advance. The save format and option numbers remained unchanged. At the time, 41 local tests and Ruff checks passed.

<a id="fb-005--no-real-combat-system"></a>

## FB-005 | The game still has no real combat

*September 20; followed up in the local combat version covered by FB-010.*

> Also, the whole game has no combat system.

At the time, the supposed bridge duel was a single choice whose result depended on equipment. There were no actual hit points, turns or enemy actions. I wanted short turn-based combat while retaining a way to cross the bridge without fighting. This idea was not implemented when first proposed; the later local combat version added the bridge fight.

<a id="fb-006--let-pip-turn-an-enemy-into-bread-to-bypass-combat"></a>

## FB-006 | Let Pip turn enemies into bread to skip combat

*September 20; followed up in the local combat version covered by FB-010.*

> I like the rules you suggested. My idea is an unconventional shortcut: the companion who can turn anything into bread could turn enemies into bread to skip the fight.

Ordinary attacks are fine, but I prefer this kind of absurd shortcut. The later bridge fight allowed Pip to turn an enemy directly into bread, without first reducing its HP and without receiving a counterattack. The initial idea did not transform the pan; that side effect was added in the next entry.

<a id="fb-007--bread-magic-also-transforms-the-quest-pan"></a>

## FB-007 | The shortcut needs a side effect

*September 20; followed up in the local combat version covered by FB-010.*

> The quest's pan could also turn into bread as a negative side effect.

Skipping a fight should not be entirely free of consequences. When Pip casts the spell on an enemy, the quest pan also turns into bread. A repair kit cannot change it back, and continuing the delivery leads to `ACCIDENTAL CATERING`. The cost mainly affects the story's ending rather than deducting additional gold.

<a id="fb-008--pip-can-turn-the-final-boss-into-bread"></a>

## FB-008 | Even the boss cannot escape bread magic

*September 20; followed up in the local combat version covered by FB-010.*

> At the end, if Pip is with you and you insist on fighting the dragon, you should be able to turn the boss into bread too.

Bringing Pip to the castle and insisting on fighting the boss should give the player a chance to trigger the same ridiculous bread magic. I did not want the option to announce that it would immediately turn the boss into bread, because that would spoil the discovery. This ending was later added in the local combat version.

<a id="fb-009--the-demon-king-is-the-dragon"></a>

## FB-009 | The Demon King and the dragon are the same character

*September 20; confirmation of the character concept.*

> Keep the former.

The preceding discussion offered two options: make the existing Demon King a dragon, or keep the Demon King and add a separate dragon. I chose the former because I did not want to invent another character just to provide a boss fight. The Demon King at the castle subsequently became a dragon wearing an apron. This confirmation alone does not mean the boss fight had already been implemented at that point.

<a id="fb-010--complete-the-boss-fight-and-funny-failure-endings"></a>

## FB-010 | Complete the boss fight and funny failure endings

*September 21, recorded from an earlier implementation request; local combat version.*

> Please now complete all the content for insisting on fighting the boss. The boss should have enormous stats and be impossible to defeat except through the unconventional shortcut. Also add funny achievements and all the endings for losing.

The old boss fight followed this request with deliberately exaggerated stats: the dragon had 9999 HP, 999 attack and 99 defence. Ordinary combat could not win; Pip's bread spell was the only way. Both the bridge and castle gained actual combat, with distinct outcomes for defeat and retreat. The local combat version had eight endings at that stage. To avoid breaking existing saves, older characters retained their original story rules, while new characters used the combat version.

This implementation brought together the proposals in FB-005 through FB-009. Before the navigation fix below, 61 local tests passed. This entry does not mean the version had been uploaded to GitHub or passed remote CI at that time. Continuing-journey mode in FB-012 later changed the boss stats to allow high-level characters to win normally; the newer rules should not be read back into the old version.

<a id="fb-011--return-to-the-current-choices-after-checking-the-bag"></a>

## FB-011 | After checking the bag, it looks as though I cannot return

*September 21; local bug fix.*

> After checking the inventory, I found that I could not return to the previous step. This is a bug that needs fixing and recording in the log.

The screenshot showed that, after printing the inventory, only an empty input prompt remained. Pressing Enter asked for a number from 1 to 4, but the four choices were not listed again. The actual problem was that the menu was not redisplayed, rather than the story reaching a dead end.

After the fix, viewing the inventory or other information redisplayed the current choices. Pressing Enter or typing `back` did the same. These actions did not rerun the scene or change combat or shopping outcomes. Six regression tests were added, bringing the total to 67 passing local tests, with Ruff checks also passing. Further personal playtesting was still needed.

<a id="fb-012--persistent-growth-repeatable-jobs-and-a-hall-of-fame"></a>

## FB-012 | Keep levelling up after finishing, and challenge merchants to wager duels

*September 24; local implementation record: `Add continuing journeys, growth and character honours`.*

> I now want to adjust the overall game flow by adding a level system. Achievements from different endings should help the player level up after completing a run, and winning battles should also help them level up. Levelling up should increase the player's attributes. After finishing, the player should be able to continue the journey, keep their level and start a new quest. Change a few boss and stage names while keeping the same structure, so repeatedly playing with the same save improves the character's level and abilities. Defeating the boss through the Easter egg should give a huge level boost. Starting with the second journey, the player should be able to fight all shop NPCs, with a reward for winning and a penalty for losing, using gold as the stake. The second journey should also unlock bribing the boss with gold to pretend to lose. You can discuss more details with me. Finally, I want a Hall of Fame on the home screen showing unlocked achievements, when they were obtained, and which character from which save earned them.

After discussing the rules, my answer was:

> 1. Yes. 2. Keep everything. 3. Disable it.

This meant that high-level characters could beat the boss normally; levels, gold and equipment would be retained; and Pip's bread spell would be disabled in merchant wager duels. Continuing-journey mode accordingly added three rotating jobs, XP-based growth, ten endings, merchant wagers from the second journey onward, boss bribery and a Hall of Fame. The first bread-boss achievement grants 1000 XP, but repeating it does not award the first-time bonus again. Merchant wagers require a 5-gold stake, return 10 gold in total on a win, and forfeit the stake on defeat or retreat.

This update moved state and honour records into SQLite, with automatic saving at key actions to prevent reward farming through reloads. At the time, 100 local tests, Ruff and lockfile checks passed. Installation and a practical gameplay-flow check were completed in a temporary Python 3.12 environment. Remote CI and personal playtesting of the balance were still pending. The next feedback entry addresses the excessive number of menu entries for old and new modes.

<a id="fb-013--one-main-menu-not-two-versions-of-the-game"></a>

## FB-013 | The main menu should not look like two separate games

*September 24; local implementation record: `Unify main menu and upgrade older saves transparently`.*

> The new menu looks strange. It should be integrated instead of split into two.

The screenshot at the time showed nine main-menu options, with old characters, new characters, copying and importing all exposed at the top level. These were later unified into five entries: `New game`, `Continue game`, `Hall of Fame`, `Manage saves` and `Quit`. Older saves were upgraded automatically when loaded. Unfinished older adventures continued under their original rules, while completed ones could continue into another journey. Character identity, existing items and the original JSON backup were preserved, without inventing historical achievement dates.

At the time, 110 local tests and Ruff checks passed. The unified menu replaced the old character-copying workflow. Personal playtesting and remote CI for the new version still needed confirmation.

<a id="fb-014--hide-completed-one-time-choices"></a>

## FB-014 | Do not keep asking me to buy something I already bought

*September 24; local implementation record: `Hide consumed one-time choices in journey menus`.*

> Options like this should disappear once they have been used. This can be recorded in the log as a small improvement.

The issue arose because the certificate purchase option remained after buying it. Selecting it again only displayed “Already certified. Still temporary.” Purchased certificates and unique equipment, completed side quests, attempted wagers and consumed companion abilities were subsequently hidden automatically. Repeatable consumable purchases remained available. Hidden options did not cause the remaining numbers to change, avoiding accidental selections. Ten related tests were added, bringing the total to 120 passing local tests, with Ruff checks also passing. This was a small interface fix, not a new mechanic.

<a id="fb-015--collect-funny-endings-with-less-repetition"></a>

## FB-015 | I want to collect funny endings without following the same route every time

*September 26; local implementation record: `Streamline repeat journeys and add ending collection clues`.*

During this review, my original answers to three questions were:

> A relaxed little game about collecting funny endings.
>
> Yes.
>
> The repetitive flow.

These referred to the experience I wanted to create, whether I liked the huge XP reward for the first bread-boss victory, and what bothered me most about replaying. I then confirmed:

> Go ahead with what you suggested, and record these improvements in the log too.

Rather than weakening Pip's shortcut or adding another large system, the update added quick routes from the second journey onward, companion switching and an option to replay the full opening. The Hall of Fame displayed `?/10` ending collection progress, hidden names and optional clues. Combat gained a concede option so high-level characters could still obtain failure endings. Conceding a merchant wager still forfeited the stake, and skipped events did not award free rewards.

At the time, 139 local tests, Ruff and formatting checks passed. A temporary character completed the first bread-boss route, started a quick second journey and conceded the boss fight, displaying `2/10` collection progress. **I had not yet completed a personal playtest to confirm the changes, and this record did not confirm that the latest version had been uploaded to GitHub or passed remote CI.**

## What to record next

Continue recording issues found during actual playtests, especially quick second journeys, companion switching, conceding, ending clues, deletion and restoration, and upgrades of older saves. If the design changes later, add a new feedback entry and link to the earlier record rather than quietly altering what was originally said.
