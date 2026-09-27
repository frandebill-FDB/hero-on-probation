# Hero on Probation — Development Log

This log records how I gradually shaped the game into something I wanted to play. Sometimes an idea came from a problem I encountered during a playtest; sometimes I simply thought of a funny ending. The original feedback and the follow-up work are recorded in the [playtest feedback log](feedback.md).

Some early work was documented retrospectively from project discussions, without precise development dates. The commit hashes below identify recorded Git revisions. Entries that only have a commit title and are marked as local should not be taken as evidence that they were uploaded. Test counts come from the records kept at each stage; I did not rerun the tests just to compile this log.

## Getting started: from a study tool to a frying pan (retrospective)

I initially considered making a study planner, but eventually found a text adventure more interesting: at least I could invent my own story. I also explored a mystery called “The Last Train,” in which the protagonist was travelling back to their hometown. The more I thought about it, though, the more familiar the premise felt. Reading long stretches of mystery prose in a terminal did not seem particularly relaxing either, so I changed direction.

I wanted to make a short, funny fantasy game in English that other students could understand. On the surface, it would be about a hero and a Demon King, but the actual quest would be returning someone's frying pan. That became **Hero on Probation**.

The early version was quite sparse. I wanted it to feel more like a game, not just a story with choices, so companions, gold, equipment and side quests were gradually added. I still wanted each adventure to stay short and each ending to have its own achievement. By the first Git snapshot, the game already included Pip and Bea, a shop, a rat relocation dispute, a warehouse ghost trying to resign, a bridge encounter, an inventory, a quest list, an in-game journal, saving and loading, and three delivery endings. These early features do not each have a separate Git date.

## September 7: preserve a playable version first

The first Git snapshot was created on this date (`3b58af3`, `Record playable RPG baseline`). This does not mean development started from scratch that day. The game already supported a complete short adventure, basic state tracking, choice-replay saves, three ending achievements, project configuration, a README and regression tests.

After reaching an ending, I started thinking about submission: could someone else install the game? Would it run on Ubuntu? Were the instructions clear? Instead of adding more story, the next work focused on installation and gameplay instructions, explanations of saving and the code structure, and a submission checklist. A GitHub Actions workflow was then added to check the game on Ubuntu 24.04 with Python 3.10 and 3.12.

This work corresponds to `1c52aaf` (`Document submission workflow and configure Ubuntu verification`). At the time, 11 local tests and Ruff checks passed, and GitHub Actions subsequently passed for that revision. These results apply to that version only; they do not mean every later update also passed CI.

## September 19: the opening should not read like a manual

I first tagged the baseline as `v0.1.0`, pointing to `1c52aaf`, so that later changes would not leave me without the original playable version.

When playing through the opening, I felt that the setting and companions were mostly introduced through exposition. The player had to read quite a lot before doing anything. I wanted players to discover the world through choices instead of hearing all the background at once. At the same time, this was a short game, so I did not want the opening to drag on.

The guild opening therefore gained options to read the contract, check the hero's pockets, ask about the parcel, and talk to Pip and Bea first. Players could still accept the job immediately or inspect things more than once. Repeated inspection did not generate extra gold or items. The town, bridge and original three delivery endings were unchanged.

This change is recorded in `3ed6e8b` (`Make the guild opening discoverable through player choices`, FB-001). Because the sequence of opening choices changed, saves moved to version 3, using `saves/adventure-v3.json`. Version-2 saves could still be played with `v0.1.0`. At the time, 15 local tests and Ruff checks passed; no confirmation of remote CI for that revision was recorded.

## September 19: what if I simply refuse to work?

Since the hero's job was only to deliver a frying pan, refusing the assignment and immediately clocking out felt right for this deliberately silly game. So an early-exit speedrun Easter egg was added.

At the guild, the player could refuse the job and receive the `CLOCKED OUT` ending and `ANY% HERO` achievement. The hero kept the starting 3 gold, never received the pan, never recruited a companion, and ended the adventure there. The new option was appended after the existing numbers to avoid changing earlier choice records. Save replay also had to recognise that the player had never accepted the job, rather than sending them on to the town.

The corresponding commit is `c5735c3` (`Add a refusal speedrun ending at the guild`, FB-002). At the time, 18 local tests and Ruff checks passed. Remote CI was not separately confirmed.

## September 20: without a character, whose progress am I saving?

As I kept playing, I noticed that the original system had only one anonymous save slot, with no character creation or save deletion. That felt awkward for an adventure with progression and equipment. I wanted to create a character first and give each character their own progress, rather than putting everything into one save.

This update added character naming and menu options to create, load and delete characters, as well as import an old version-3 save. Each character had a separate save, and duplicate names were rejected. Deletion required typing `DELETE`; deleted files were first moved to `saves/deleted/` so they could be recovered. I kept character creation to naming only, without adding classes or attribute allocation. Creating a character generated an initial save, but later progress still required a manual `save`.

The new save format was version 4. Display names were separated from internal IDs, and character names were not used directly to construct file paths. Old saves were validated before import, then copied rather than overwritten. This work corresponds to `6b5b1d8` (`Add named characters and recoverable save management`, FB-003). At the time, 37 local tests, Ruff and Ubuntu CI for that revision passed. Two-character handling, saving and loading, and recoverable deletion were also checked in a temporary directory without touching existing player saves.

## September 20: two small problems—one with usability, one with spoilers

After character saves were added, I noticed that the game appeared to allow saving only at an ending. That seemed strange: a text adventure would be inconvenient if saving midway were difficult. Investigation showed that `save` and `load` already worked during the story; the interface simply did not tell the player. This update did not rewrite the save system. Instead, it displayed the commands below each set of choices and separately explained the difference between saving and loading after an ending.

There was also a problem with the speedrun ending added the day before. I wanted refusing the job to be an unexpected Easter egg, but the option explicitly told the player it would end the game, giving away the joke. The option was changed to ordinary dialogue, and the README's ending descriptions were placed behind a spoiler warning.

This work was recorded as `Expose mid-story save controls and hide refusal spoilers` (FB-004). At the time, 41 local tests and Ruff checks passed. An additional check covered saving at the shop, quitting, and loading back into the same decision. Remote CI for that version was not confirmed.

## September 20–21: finally, combat—but I still want Pip to skip it

Another obvious issue emerged while playing: although the game had a bridge duel and equipment, it did not yet have actual turn-based combat. Making one choice and changing the outcome based on equipment did not quite feel like an RPG.

However, I did not want to turn it into a serious grinding game. Pip could already turn things into bread, so why not let him turn enemies into bread and bypass normal combat? I also added a drawback to this unconventional shortcut: the spell would turn the quest's frying pan into bread as well. Skipping the fight would be quick, but it would send the story towards another strange ending.

The final boss followed the same idea. Rather than adding a separate dragon, I made the existing Demon King a dragon wearing an apron. In the old combat version, the boss had 9999 HP and could not be beaten with ordinary attacks. Only bringing Pip allowed the player to turn it into bread. I also wanted defeat and retreat to lead to funny endings and achievements instead of just a Game Over screen.

The local combat version added a short, non-random bridge fight, followed by a choice between peaceful delivery and insisting on a duel at the castle. There were eight endings at that stage. To prevent the new rules from breaking old characters' choice records, version-5 saves recorded the story rules version. Existing characters kept the old rules, while new characters used the combat version. These ideas and their implementation correspond to FB-005 through FB-010.

**Status at the time: local version, not yet uploaded to GitHub.** Before the navigation fix below, 61 local tests passed.

## September 21: where did the choices go after checking my bag?

This was a bug encountered during an actual playtest. After I opened the inventory, the screen showed only an input prompt; the numbered choices were not displayed again. Pressing Enter produced a message asking me to enter a number from 1 to 4. The game was not actually stuck, but it looked as though there was no way back.

The fix addressed menu display rather than adding a way to undo story decisions. After viewing the inventory or other information, the current choices are shown again. Pressing Enter or typing `back` also redisplays the menu. Redisplaying it does not rerun the scene, so checking the bag cannot accidentally repeat a purchase, grant another reward, or give an enemy an extra attack.

This local fix corresponds to FB-011. Six regression tests were added, bringing the total to 67 passing local tests, with Ruff checks also passing. The save format and option numbers were unchanged. Another personal playtest was still needed; there was no upload or remote CI confirmation at that point.

## September 24: I want to keep using the same character after finishing

The original short adventure ended when the story was complete, but I had become attached to the equipment and gold I had collected. I wanted the same character to continue adventuring, level up through combat and ending achievements, and take on new jobs with similar structures but different names and situations. Finishing a run would then mean gradual character growth, not just starting over.

The idea became increasingly ridiculous: the first bread-boss victory would grant a huge amount of XP; the second journey would unlock wager duels with shop NPCs; and the player could even bribe the boss to pretend to lose. A Hall of Fame on the main menu would record which character earned each achievement and on which journey. After discussing and weighing these rules, I decided to retain levels, gold and equipment, allow high-level characters to beat the boss with ordinary attacks, and ban Pip's bread magic from merchant wager duels.


This changed the earlier rule that nobody except Pip could defeat the boss. In continuing-journey mode, bosses have fixed HP values in the 120–140 range, rather than the old mode's 9999 HP. A level-1 character still cannot win, but the level-8 character used in testing can win normally. The old combat values remain unchanged. Continuing journeys have three rotating jobs and ten endings. Unlocking the bread-boss achievement for the first time grants 1000 XP; earning it again does not repeat the first-time bonus.

Saving had to change too. After each decision, continuing journeys automatically save the current scene, combat and permanent progress. SQLite updates character data and honour records in the same transaction, preventing repeated rewards or wager farming through reloads. At that stage, old manual saves still worked, and a character who had completed an adventure could be copied into the new mode. Historical achievement dates that had never been recorded were marked as unknown rather than guessed.

This work corresponds to `Add continuing journeys, growth and character honours` (FB-012). At the time, 100 local tests, Ruff and lockfile checks passed. An editable installation and a practical two-journey flow check were completed in a temporary Python 3.12 environment. Updated Ubuntu CI was configured, but its remote result had not yet been confirmed. Whether the progression numbers were fun still needed further personal playtesting.

## September 24: the main menu should not make old and new versions look like separate games

To support older characters, the previous update had made the main menu longer and longer. It ended up with nine options, including separate creation paths for old and new modes, copying and importing. Having to choose between technical options before even playing did not feel right.

I decided to reduce the main menu to five basic entries: `New game`, `Continue game`, `Hall of Fame`, `Manage saves` and `Quit`. Save compatibility should be handled when loading, not by making players understand save versions first. An unfinished older adventure continues under its original rules, with `next` available after its ending. A completed older save is upgraded when loaded, while its original JSON is retained as a backup. Repeating an upgrade must not create another character or award rewards again. Deleted characters must not quietly reappear from their backups either.

This work corresponds to `Unify main menu and upgrade older saves transparently` (FB-013). At the time, 110 local tests and Ruff checks passed. Automated tests used fixtures rather than existing player saves. Further personal playtesting and remote CI were still pending. The unified menu also replaced the separate old-character copying entry from the previous update.

## September 24: stop offering things I have already bought

Another small but irritating playtest issue was that the certificate purchase option remained visible after buying it. Selecting it again only produced “Already certified. Still temporary.” Similar problems affected some completed side quests and one-use companion abilities.

I did not want to redesign the system just for this. I only wanted consumed one-time options to disappear automatically. Certificates, unique equipment, completed side quests, attempted wagers and used companion abilities are now hidden according to the saved state. Repeatable purchases, such as repair kits, remain available. Hiding an option does not renumber the others, so entering a familiar number cannot accidentally select something different.

This work corresponds to `Hide consumed one-time choices in journey menus` (FB-014). At the time, 120 local tests and Ruff checks passed. New tests covered obsolete option numbers, visibility after saving, and resets for a new journey. This was a local interface improvement that still needed playtesting and remote CI confirmation.

## September 26: I want to collect funny endings, not repeat the same journey

Looking back over the game, I realised that what I most wanted to preserve was the absurd feeling of turning the boss into bread with Pip for the first time and suddenly gaining a huge amount of XP. I wanted a relaxed game about collecting funny endings, not one that made players repeat the same guild and town sequence over and over just to reach the next joke.

This update therefore did not add another large system or weaken the bread spell. Instead, it tackled repeat play directly. From the second journey onward, a route menu retains the previous companion and allows direct travel to the boss, town, bridge or certificate merchant. Players can still change companions or replay the full opening. Skipped events do not award rewards for free, and returning to the route menu does not reset completed side quests or wagers.

The Hall of Fame now begins with collection progress across the ten endings. Unlocked endings show their names and jokes, while undiscovered ones appear as `???`, with optional clues available. Detailed character, save and achievement-time records remain accessible. Combat also gained an option to concede, allowing high-level characters to collect failure endings that would otherwise become difficult to reach. Conceding a merchant wager still forfeits the stake and does not grant a free reward.

This local implementation was recorded as `Streamline repeat journeys and add ending collection clues` (FB-015). At the time, 139 local tests, Ruff and formatting checks passed. A temporary character completed the bread-boss route, started a quick second journey, conceded the boss fight, and displayed `2/10` collection progress. **This does not mean I had personally confirmed that replay pacing felt right, nor that the latest version had been uploaded to GitHub or passed remote CI.**

## What I want to check next

In the next playtest, I want to focus on the quick second journey: changing companions, conceding and viewing ending clues. I want to see whether these changes actually reduce repetition without spoiling the jokes. Character switching, deletion and restoration, and automatic upgrades of older saves also need further personal checks.

Uploading the latest local version, Ubuntu CI and Moodle submission requirements still need confirmation. I also want to review how character state, branches, save replay and tests fit together, both for future maintenance and so I can explain the implementation clearly in a course presentation. Any later additions should ideally respond to specific playtest feedback, rather than adding features simply to make the project look bigger.

## About AI assistance

I completed the bulk of this game myself, from the story and gameplay to its main features and code implementation. AI mainly helped in two areas: setting up parts of the code framework early on, and assisting with debugging during development, such as investigating errors, checking logic or discussing possible fixes. The test results in this log are records of checks at the time; where I have not personally confirmed something through playtesting, I note that separately.
