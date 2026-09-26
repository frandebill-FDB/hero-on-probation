"""A complete short adventure using numbered choices."""

import sqlite3
import sys
from contextlib import redirect_stdout

from hero_on_probation import combat, journey_store, saves
from hero_on_probation.journey import Journey
from hero_on_probation.journey_cli import run as run_journey
from hero_on_probation.menu import start_menu
from hero_on_probation.models import Hero
from hero_on_probation.session import Restart, Session
from hero_on_probation.town import explore_town


class ReplayComplete(Exception):
    """A validation replay has reached its saved decision."""


class ReturnToMenu(Exception):
    """Leave the current in-memory adventure without writing a save."""


session: Session


class ReplayOutput:
    """Discard old story output while restoring saved choices."""

    def __init__(self, output):
        self.output = output

    def write(self, text):
        if not session.restoring:
            self.output.write(text)
        return len(text)

    def flush(self):
        self.output.flush()


def show_choice(prompt: str, options: list[str]) -> None:
    """Redisplay the current decision without running scene or battle logic."""
    print(
        f"\n[Hero: {session.hero.name} | Gold: {session.hero.gold} | "
        f"HP: {session.hero.hp}/{session.hero.max_hp} | Companion: {session.hero.companion or 'Solo'}]"
    )
    print(prompt)
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")
    print(
        "Commands: save (save here) | load | status | bag | help | back | menu | quit"
    )
    print("Enter a number to act; back or Enter redisplays this choice (no undo).")


def choose(prompt: str, options: list[str]) -> int:
    """Keep asking until the player selects a numbered option."""
    if session.replay:
        answer = session.replay.pop(0)
        if not 1 <= answer <= len(options):
            raise ValueError("Saved choice is not available in this scene")
        session.history.append(answer)
        return answer
    if session.validating:
        raise ReplayComplete
    session.restoring = False
    show_choice(prompt, options)
    while True:
        answer = input("> ").strip()
        if answer.lower() == "quit":
            raise EOFError
        if answer.lower() == "menu":
            raise ReturnToMenu
        if answer.lower() in ("", "back"):
            show_choice(prompt, options)
            continue
        try:
            if session.command(answer.lower()):
                print("\nBack to your current choice. No action taken.")
                show_choice(prompt, options)
                continue
        except (OSError, ValueError) as error:
            print(f"Cannot complete command: {error}")
            continue
        if answer in [str(number) for number in range(1, len(options) + 1)]:
            session.history.append(int(answer))
            return int(answer)
        print(
            f"Enter a number from 1 to {len(options)}, or use back / save / load / help / menu / quit."
        )


def guild(hero: Hero) -> bool:
    """Return whether the player accepts the delivery and recruits a companion."""
    print("\nHERO ON PROBATION")
    print(f"Hero registration: {hero.name}. Job title: temporary hero.")
    print('You wake up at a counter. Your sleeve is stamped "TEMPORARY".')
    seen: set[int] = set()
    while True:
        action = choose(
            "Explore the counter, or ring the bell to begin work:",
            ["Read your contract.", "Check your pockets.", "Ring the service bell."],
        )
        if action == 3:
            break
        if action in seen:
            print("Nothing has changed. The bell is still waiting.")
            continue
        seen.add(action)
        if action == 1:
            print(
                "JOB: HERO (TEMPORARY). Lunch: not included. Destiny: non-refundable."
            )
            hero.journal.append("Read the contract: temporary hero, no lunch included.")
        else:
            print(f"You count {hero.gold} gold. Counting again will not earn interest.")
            print(
                "A wooden sword hangs at your belt. Type bag or status to inspect it."
            )
            hero.journal.append("Checked existing coins and equipment. No pay yet.")

    print('A receptionist pushes a box towards you. "One delivery. Five gold."')
    seen.clear()
    while True:
        action = choose(
            "Ask about the parcel, accept the delivery, or decline:",
            [
                "What am I delivering?",
                "Who is it for?",
                "What if it gets damaged?",
                "Take the parcel and accept the job.",
                "No thanks. I'm taking the day off.",
            ],
        )
        if action == 4:
            break
        if action == 5:
            refusal_ending(hero)
            return False
        if action in seen:
            print('Receptionist: "Same answer. Still five gold."')
            continue
        seen.add(action)
        answers = {
            1: 'Inside is a frying pan. "Please do not test it on my desk."',
            2: 'The label says DEMON KING. "Home delivery. No boss fight required."',
            3: '"Bring it back intact for five gold. Dent it, and you wash his dishes."',
        }
        print(answers[action])
        hero.journal.append(f"Delivery question: {answers[action]}")

    print(
        "Job accepted: deliver the Demon King's pan before dinner, intact, for 5 gold."
    )
    hero.inventory["Demon King's Pan"] = 1
    hero.quests["Return the pan"] = "Active"
    hero.journal.append("Accepted the pan delivery. Received the quest pan.")
    meet_companions(hero)
    return True


def unlock_achievement(hero: Hero, name: str, description: str) -> None:
    """Record an ending achievement once and display its punchline."""
    if name not in hero.achievements:
        hero.achievements.append(name)
        hero.journal.append(f"Achievement unlocked: {name}.")
    print(f"\n*** ACHIEVEMENT UNLOCKED: {name} ***")
    print(description)


def refusal_ending(hero: Hero) -> None:
    """Finish before accepting the parcel, without delivery rewards or items."""
    print('You: "No, thanks. I am taking the day off."')
    print('Receptionist: "You have been here for twelve seconds."')
    print('You: "And already I need a break."')
    print("You leave the box on the counter and walk out. Nobody stops you.")
    print("\nENDING: CLOCKED OUT")
    hero.ending = "CLOCKED OUT"
    hero.journal.append(
        "Declined the delivery. Ending: CLOCKED OUT. No pay, no dishes."
    )
    unlock_achievement(
        hero,
        "ANY% HERO",
        "You skipped the quest, the boss and the unpaid lunch break.",
    )
    print(f"Gold: {hero.gold} | Companion: None | Completed quests: 0")
    print("Pan: not your problem. Probation: someone else's problem.")


def meet_companions(hero: Hero) -> None:
    """Let players discover each companion's joke before choosing."""
    print("Two volunteers wait by the exit: Pip holds a wand. Bea checks the exits.")
    seen: set[int] = set()
    while True:
        action = choose(
            "Meet the volunteers, or choose someone now:",
            [
                "Ask Pip for a magic demonstration.",
                "Ask Bea about her last battle.",
                "Choose a companion and leave the guild.",
            ],
        )
        if action == 3:
            break
        if action in seen:
            print("You have heard their pitch. Neither has improved it.")
            continue
        seen.add(action)
        if action == 1:
            print(
                'Pip turns a pencil into a baguette. Receptionist: "Third one today."'
            )
            print('Pip: "Objects into bread. Easy! Turning them back? Still learning."')
            hero.journal.append("Met Pip: turns objects into bread, not back again.")
        else:
            print('Bea: "Everyone escaped safely." You: "And the enemy?"')
            print('Bea: "Also safe. I find exits, not unnecessary fights."')
            hero.journal.append("Met Bea: prefers safe routes to fighting.")
    partner = choose(
        "Choose a companion:",
        [
            "Recruit Pip, the wizard.",
            "Recruit Bea, the knight.",
        ],
    )
    hero.companion = "Pip" if partner == 1 else "Bea"
    hero.journal.append(f"Recruited {hero.companion}.")


def bridge(hero: Hero) -> bool:
    """Resolve the toll through payment, help, force, or a companion."""
    print("\nA slime blocks the bridge. It is wearing a tiny official badge.")
    print('Slime: "Two gold. Swimming is free. So are complaints."')
    options = [
        "Pay two gold.",
        "Ask whether the slime needs help.",
        "Demand a heroic duel.",
        f"Ask {hero.companion} for a solution.",
    ]
    if "Rat Recommendation" in hero.inventory:
        options.append("Show the rats' recommendation. Free passage.")
    while True:
        action = choose("How will you cross?", options)
        if action == 3 and session.rules_version >= 2:
            result = combat.fight(hero, combat.slime(), choose)
            if result == "retreat":
                print(
                    "You step back from the bridge. The slime offers a customer survey."
                )
                continue
            if result == "defeat":
                hero.quests["Bridge duel"] = "Failed"
                finish_combat_ending(hero, "TOLL TAKEN")
                return False
            hero.quests["Bridge duel"] = "Done"
            if result == "bread":
                unlock_achievement(
                    hero,
                    "BREAD OVER BRAWN",
                    "You solved a combat encounter with a bakery.",
                )
                print(
                    'The bun squeaks, "The toll still applies!" It cannot hold its spoon.'
                )
            else:
                print('Slime: "You win. Please rate your violence five stars."')
            print("You cross without paying. The castle is just ahead.")
            return True
        if action != 1 or hero.gold >= 2:
            break
        print(
            "Not enough gold. Helping, fighting or asking your companion costs nothing."
        )
    if action == 1:
        hero.gold -= 2
        hero.inventory["Toll Receipt"] = 1
        hero.journal.append("Paid bridge toll: -2 gold.")
        print("The slime prints a receipt larger than itself. You cross.")
    elif action == 2:
        hero.helped_slime = True
        hero.quests["Help the bridge slime"] = "Done"
        hero.inventory["Slime Thank-you Note"] = 1
        hero.journal.append(
            "Helped the slime. Earned free passage and a thank-you note."
        )
        print("You move its toll sign into the shade. It was slowly drying out.")
        print('Slime: "Free crossing. Please do not mention my moisture problem."')
    elif action == 3:
        print("The slime produces a regulation duelling spoon.")
        moves = [
            "Block with the frying pan.",
            "Retreat with dignity and pay the toll.",
        ]
        if hero.equipment.get("Weapon") == "Iron Sword":
            moves.append("Disarm the slime with your Iron Sword.")
        while True:
            move = choose("The spoon approaches. Slowly.", moves)
            if move != 2 or hero.gold >= 2:
                break
            print("You cannot afford the toll. Try another move.")
        if move == 1:
            if hero.equipment.get("Shield") == "Pot Lid":
                hero.journal.append("Pot Lid blocked the spoon. Quest pan protected.")
                print(
                    "CLANG. Your pot lid wins a cooking-related duel. The pan is safe."
                )
            else:
                hero.pan = "dented"
                hero.journal.append("Blocked the spoon. The quest pan is now dented.")
                print(
                    "CLANG. The pan dents. The slime declares you too expensive to fight."
                )
        elif move == 2:
            hero.gold -= 2
            hero.inventory["Toll Receipt"] = 1
            hero.journal.append("Retreated and paid toll: -2 gold.")
            print("Your dignity crosses first. You follow with the receipt.")
        else:
            hero.journal.append(
                "Iron Sword disarmed the slime. Free passage; pan intact."
            )
            print('Slime: "That is a very persuasive upgrade. Please cross."')
    elif action == 5:
        hero.journal.append("Rat Recommendation waived the bridge toll.")
        print('Slime: "A union reference! Why did you not say so?"')
    elif hero.companion == "Pip":
        print('Pip: "I can make bread. The spell needs an object."')
        material = choose("Offer an object:", ["Your wooden sword.", "The frying pan."])
        if material == 1:
            hero.inventory.pop("Wooden Sword")
            if hero.equipment["Weapon"] == "Wooden Sword":
                hero.equipment["Weapon"] = "None"
            hero.journal.append(
                "Sword became bread and was spent on the toll. Weapon lost."
            )
            print("Your sword becomes a baguette. Its combat rating improves.")
            print("The slime accepts the baguette as payment.")
        else:
            hero.pan = "bread"
            hero.journal.append(
                "Quest pan transformed into bread. Handle paid the toll."
            )
            print("The pan becomes bread. Pip pays the toll with its handle.")
    else:
        hero.journal.append("Bea found a free route through shallow water.")
        print('Bea: "The water is ankle-deep. I checked while you were talking."')
        print("You walk around the bridge. Bea remains undefeated.")
    return True


def finish_combat_ending(hero: Hero, ending: str) -> None:
    """Settle a terminal battle outcome once, without delivery payment."""
    outcomes = {
        "TOLL TAKEN": (
            "SPOON-FED DEFEAT",
            "You lost to cutlery. The guild has requested its sword back.",
            "The slime puts you in the recovery position and prints a defeat receipt.",
        ),
        "BOSS DEFEAT": (
            "ONE-HIT INTERN",
            "Your sword dealt zero damage. Your confidence took 999.",
            'The dragon flicks you onto the welcome mat. "Delivery attempted," he writes.',
        ),
        "TACTICAL RETREAT": (
            "CAREER PRESERVATION",
            "You chose a long life over a very short boss fight.",
            "Your feet resign before your mouth can explain. Bea would approve.",
        ),
        "THE FINAL LOAF": (
            "BREAD OF THE REALM",
            "You defeated the final boss. The kingdom now has a crust problem.",
            'Pip: "I promised to handle the final course." You: "You said boss."',
        ),
    }
    achievement, description, scene = outcomes[ending]
    hero.ending = ending
    failed = ending in ("TOLL TAKEN", "BOSS DEFEAT")
    hero.quests["Return the pan"] = "Failed" if failed else "Cancelled"
    hero.journal.append(f"Ending: {ending}. Delivery reward: 0 gold.")
    print(scene)
    if ending == "THE FINAL LOAF":
        print("The enormous dragon loaf still wears an apron. The pan is bread too.")
        print('Dragon loaf: "Do NOT serve me with soup."')
        print("Dinner: enormous. Payment: pending. Nobody can sign the receipt.")
    elif failed:
        print(
            "You are unconscious, not deleted. Your saved progress is still available."
        )
    else:
        print("Dinner: missed. Survival: achieved. The pan is still your problem.")
    print(f"\nENDING: {ending}")
    unlock_achievement(hero, achievement, description)
    print(f"Hero: {hero.name} | HP: {hero.hp}/{hero.max_hp} | Gold: {hero.gold}")
    print(
        f"Companion: {hero.companion or 'None'} | Pan: {hero.pan} | Delivery reward: 0 gold"
    )


def challenge_boss(hero: Hero) -> bool:
    """Offer two opportunities to deliver peacefully before a terminal fight."""
    decision = choose(
        "The dragon sets the table. What do you do?",
        ["Hand over the pan and stay for dinner.", "Ask for a proper boss fight."],
    )
    if decision == 1:
        return False
    print('Demon King: "I have 9999 HP and a casserole in the oven. Choose carefully."')
    decision = choose(
        "He puts down his oven gloves.",
        ["Maybe dinner first. Return the pan.", "I insist. Draw your weapon."],
    )
    if decision == 1:
        return False
    hero.quests["Challenge the Demon King"] = "Active"
    result = combat.fight(hero, combat.demon_king(), choose)
    if result == "bread":
        hero.quests["Challenge the Demon King"] = "Done"
        finish_combat_ending(hero, "THE FINAL LOAF")
    elif result == "retreat":
        hero.quests["Challenge the Demon King"] = "Abandoned"
        finish_combat_ending(hero, "TACTICAL RETREAT")
    elif result == "defeat":
        hero.quests["Challenge the Demon King"] = "Failed"
        finish_combat_ending(hero, "BOSS DEFEAT")
    else:
        raise RuntimeError("The Demon King's armour must prevent ordinary victory.")
    return True


def arrival(hero: Hero) -> None:
    """Offer a purchase and deliver an ending based on earlier actions."""
    if hero.pan == "dented" and hero.inventory.get("Repair Kit", 0):
        hero.inventory["Repair Kit"] -= 1
        if not hero.inventory["Repair Kit"]:
            del hero.inventory["Repair Kit"]
        hero.pan = "intact"
        hero.journal.append("Used one Repair Kit before delivery. Pan restored.")
        print("You repair the pan. The instructions say: HIT IT FROM THE OTHER SIDE.")
    print("\nOutside the castle, a machine sells hero certificates for three gold.")
    if hero.gold >= 3:
        purchase = choose(
            "Would you like one?",
            [
                "Buy a certificate. It has a shiny border.",
                "Keep the money.",
            ],
        )
        if purchase == 1:
            hero.gold -= 3
            hero.inventory["Hero Certificate"] = 1
            hero.journal.append("Bought hero certificate: -3 gold.")
            print("The certificate reads: PARTICIPATED.")
    else:
        print("You cannot afford official recognition. You approach the door.")
    print("\nA dragon in an apron opens the castle door. This is the Demon King.")
    print('Demon King: "Finally. My pan."')
    print('You: "Are we going to fight?"')
    print('Demon King: "Have you eaten? No? Then you are not ready for a boss fight."')
    if "Ghost Reference" in hero.inventory:
        hero.gold += 2
        hero.journal.append("Ghost Reference earned a castle signing bonus: +2 gold.")
        print('King: "Our warehouse ghost recommended you. Two gold signing bonus."')
    if "Bread Resignation" in hero.inventory:
        print('King: "An edible resignation? Finally, paperwork I can stomach."')
    if session.rules_version >= 2 and challenge_boss(hero):
        return
    if hero.pan == "dented":
        ending = "DISH DUTY"
        print(
            "He examines the dent. You agree to wash dishes instead of collecting pay."
        )
        print("Dinner is included. Unfortunately, so are twelve enormous soup pots.")
    elif hero.pan == "bread":
        ending = "ACCIDENTAL CATERING"
        print('He tears off a piece. "A bread bowl with ambition. I like it."')
        hero.gold += 5
        print("You receive five gold and a seat at the table. Pip takes full credit.")
    else:
        ending = "DELIVERY COMPLETE"
        if hero.gold == 0 and hero.helped_slime:
            print("The bridge slime arrives with groceries and buys you a starter.")
            print('Slime: "Consider this a moisture-related thank-you."')
        hero.gold += 5
        print("You receive five gold. The Demon King sets an extra place for dinner.")
    print(f"\nENDING: {ending}")
    hero.ending = ending
    achievements = {
        "DELIVERY COMPLETE": (
            "DELIVERY HERO",
            "You defeated the shipping estimate. The Demon King remains undefeated.",
        ),
        "DISH DUTY": (
            "LORD OF THE RINSE",
            "You came for gold. You stayed for grease.",
        ),
        "ACCIDENTAL CATERING": (
            "BREADWINNER",
            "You brought home the bread. It used to be cookware.",
        ),
    }
    achievement, description = achievements[ending]
    unlock_achievement(hero, achievement, description)
    hero.inventory.pop("Demon King's Pan", None)
    hero.quests["Return the pan"] = "Done"
    hero.journal.append(
        f"Returned the pan. Ending: {ending}. Reward: {0 if hero.pan == 'dented' else 5} gold."
    )
    print(f"Companion: {hero.companion} | Pan: {hero.pan} | Gold: {hero.gold}")
    completed = sum(state == "Done" for state in hero.quests.values())
    print(f"Completed quests: {completed} | Weapon: {hero.equipment['Weapon']}")
    print("Dinner: obtained. Probation: extended.")


def play_adventure(hero: Hero) -> None:
    """Run the same story path for live play and save validation."""
    if guild(hero):
        explore_town(hero, choose)
        if bridge(hero):
            arrival(hero)


def run_session(initial: Session) -> bool:
    """Play a selected character; return True to reopen character selection."""
    global session
    session = initial
    print(
        "Use numbers, or status / bag / quests / journal / achievements / save / load / menu / quit."
    )
    print(f"Playing as {session.hero.name}. Saving affects only this character.")
    if session.rules_version == 1:
        print("Your older save's current story and choices are preserved.")
        print(
            "After the ending, use next to continue this character's journey with levels."
        )
    print("Use save before menu or quit to keep your latest progress.")
    while True:
        try:
            with redirect_stdout(ReplayOutput(sys.stdout)):
                play_adventure(session.hero)
            if session.restoring:
                session.restoring = False
                print("Completed adventure restored.")
                session.command("status")
                session.command("achievements")
            print("Adventure complete. Saving now records this ending.")
            print("Use load to restore your last save, or menu to select a character.")
            ending_commands = "Commands: status | bag | quests | journal | achievements | save | load | back | next | menu | quit"
            print(ending_commands)
            print(
                "next: continue this character into a new journey, keeping possessions and achievements."
            )
            while True:
                command = input("> ").strip().lower()
                if command == "quit":
                    raise EOFError
                if command == "menu":
                    raise ReturnToMenu
                if command in ("", "back"):
                    print(
                        "Adventure complete. Use load for your last save, or menu for character selection."
                    )
                    print(ending_commands)
                    continue
                try:
                    if command == "next":
                        saved = saves.SavedGame(
                            session.save_id,
                            session.hero.name,
                            session.history,
                            session.rules_version,
                        )
                        return run_journey(journey_store.upgrade(saved, session.hero))
                    if session.command(command):
                        print(ending_commands)
                    else:
                        print(
                            "Use status, bag, quests, journal, achievements, save, load, menu or quit."
                        )
                except (OSError, ValueError, sqlite3.Error) as error:
                    print(f"Cannot complete command: {error}")
        except Restart as restart:
            session = restart.session
            print("Save loaded. Returning to your decision...")
        except ReturnToMenu:
            print("Returning to character selection. Unsaved progress is not kept.")
            return True
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Only progress saved with save will be kept.")
            return False


def main() -> None:
    """Select a named character before entering or restoring the adventure."""
    try:
        while True:
            selected = start_menu()
            if selected is None:
                print("Goodbye!")
                return
            if not (
                run_journey(selected)
                if isinstance(selected, Journey)
                else run_session(selected)
            ):
                return
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye! No additional progress was saved.")
