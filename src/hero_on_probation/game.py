"""A complete short adventure using numbered choices."""

import sys
from contextlib import redirect_stdout

from hero_on_probation.models import Hero
from hero_on_probation.session import Restart, Session
from hero_on_probation.town import explore_town


class ReplayComplete(Exception):
    """A validation replay has reached its saved decision."""


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
    print(
        f"\n[Gold: {session.hero.gold} | Companion: {session.hero.companion or 'Solo'}]"
    )
    print(prompt)
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")
    while True:
        answer = input("> ").strip()
        if answer.lower() == "quit":
            raise EOFError
        try:
            if session.command(answer.lower()):
                continue
        except (OSError, ValueError) as error:
            print(f"Cannot complete command: {error}")
            continue
        if answer in [str(number) for number in range(1, len(options) + 1)]:
            session.history.append(int(answer))
            return int(answer)
        print(f"Enter a number from 1 to {len(options)}, or quit.")


def guild(hero: Hero) -> bool:
    """Return whether the player accepts the delivery and recruits a companion."""
    print("\nHERO ON PROBATION")
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
                "Decline the job and leave. (End adventure.)",
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


def bridge(hero: Hero) -> None:
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
    print('\nThe Demon King opens the door wearing an apron. "Finally. My pan."')
    print('You: "Are we going to fight?"')
    print('Demon King: "Have you eaten? No? Then you are not ready for a boss fight."')
    if "Ghost Reference" in hero.inventory:
        hero.gold += 2
        hero.journal.append("Ghost Reference earned a castle signing bonus: +2 gold.")
        print('King: "Our warehouse ghost recommended you. Two gold signing bonus."')
    if "Bread Resignation" in hero.inventory:
        print('King: "An edible resignation? Finally, paperwork I can stomach."')
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
        bridge(hero)
        arrival(hero)


def main() -> None:
    """Play one adventure; allow graceful exit at any choice."""
    global session
    print(
        "Use numbers, or status / bag / quests / journal / achievements / save / load / quit."
    )
    print("One save slot: saves/adventure-v3.json. Saving replaces that slot.")
    replay = None
    while True:
        hero = Hero()
        session = Session(hero, replay)
        try:
            with redirect_stdout(ReplayOutput(sys.stdout)):
                play_adventure(hero)
            if session.restoring:
                session.restoring = False
                print("Completed adventure restored.")
                session.command("status")
                session.command("achievements")
            print(
                "Review status, bag, quests, journal or achievements; save, load or quit."
            )
            while True:
                command = input("> ").strip().lower()
                if command == "quit":
                    raise EOFError
                try:
                    if not session.command(command):
                        print(
                            "Use status, bag, quests, journal, achievements, save, load or quit."
                        )
                except (OSError, ValueError) as error:
                    print(f"Cannot complete command: {error}")
        except Restart as restart:
            replay = restart.decisions
            print("Save loaded. Returning to your decision...")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Only progress saved with save will be kept.")
            return
