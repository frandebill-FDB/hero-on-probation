"""Optional town stories with one-time rewards and a repeatable shop."""

from collections.abc import Callable

from hero_on_probation.models import Hero

Choose = Callable[[str, list[str]], int]


def explore_town(hero: Hero, choose: Choose) -> None:
    """Allow errands in any order before leaving for the bridge."""
    while True:
        action = choose(
            f"PROBATION SQUARE | Gold: {hero.gold}",
            [
                "Visit the equipment shop.",
                "Visit the rats' moving office.",
                "Visit the haunted warehouse.",
                "Leave town for the bridge.",
            ],
        )
        if action == 1:
            shop(hero, choose)
        elif action == 2:
            rats(hero, choose)
        elif action == 3:
            ghost(hero, choose)
        else:
            hero.journal.append("Left town for the bridge.")
            return


def shop(hero: Hero, choose: Choose) -> None:
    """Buy useful goods; equipment purchases equip the new item."""
    goods = [("Iron Sword", 5), ("Pot Lid", 3), ("Repair Kit", 2)]
    while True:
        action = choose(
            f'Shopkeeper: "No refunds for destiny." | Gold: {hero.gold}',
            [
                "Iron Sword: 5 gold. Win the bridge duel without damaging the pan.",
                "Pot Lid: 3 gold. Protect the pan when blocking a spoon.",
                "Repair Kit: 2 gold. Fix a dent before delivery (automatic).",
                "Return to the square.",
            ],
        )
        if action == 4:
            return
        item, price = goods[action - 1]
        if item != "Repair Kit" and item in hero.inventory:
            print("You already own one. Even destiny does not need two.")
        elif hero.gold < price:
            print(f"You need {price} gold. You have {hero.gold}.")
        else:
            hero.gold -= price
            hero.inventory[item] = hero.inventory.get(item, 0) + 1
            if item == "Iron Sword":
                hero.equipment["Weapon"] = item
            elif item == "Pot Lid":
                hero.equipment["Shield"] = item
            hero.journal.append(f"Bought {item}: -{price} gold.")
            print(f"Received {item}. Gold remaining: {hero.gold}.")


def rats(hero: Hero, choose: Choose) -> None:
    """Resolve a labour dispute through negotiation or carrying boxes."""
    quest = "The rats' moving expenses"
    if hero.quests.get(quest) == "Done":
        print('Rat: "We have moved. This office is now a commemorative pile of boxes."')
        return
    hero.quests[quest] = "Active"
    print('A rat in a tie shows you the contract. "Remove rats. We removed ourselves."')
    answer = choose(
        "The guild refuses to pay. How can you help?",
        [
            "Read the contract to the receptionist. Slowly.",
            "Help carry the boxes instead.",
            "Come back later.",
        ],
    )
    if answer == 3:
        return
    reward = 4 if answer == 1 else 2
    hero.gold += reward
    hero.inventory["Rat Recommendation"] = 1
    hero.quests[quest] = "Done"
    hero.journal.append(
        f"Helped the moving rats: +{reward} gold and Rat Recommendation."
    )
    print('Rat: "You are unusually employable for a human."')
    print(f"Reward: {reward} gold. The recommendation can waive the bridge toll.")


def ghost(hero: Hero, choose: Choose) -> None:
    """A ghost cannot leave because their resignation is unsigned."""
    quest = "Resignation from the afterlife"
    if hero.quests.get(quest) == "Done":
        print("The warehouse is quiet. A note reads: GONE FISHING. FINALLY.")
        return
    hero.quests[quest] = "Active"
    print('Ghost: "I died thirty years ago. HR marked it as an extended lunch."')
    answer = choose(
        "Their resignation needs a witness.",
        [
            "Sign as a witness. You have technically seen a ghost.",
            f"Ask {hero.companion} to help.",
            "Come back later.",
        ],
    )
    if answer == 3:
        return
    if answer == 2 and hero.companion == "Pip":
        hero.inventory["Bread Resignation"] = 1
        print(
            "Pip turns the form into toast. HR accepts it as written notice with catering."
        )
    elif answer == 2:
        print('Bea: "I specialise in leaving. Your notice period ended in 1996."')
    else:
        print("You sign. The ghost immediately removes their employee badge.")
    hero.inventory["Ghost Reference"] = 1
    hero.gold += 3
    hero.quests[quest] = "Done"
    hero.journal.append("Freed the warehouse ghost: +3 gold and Ghost Reference.")
    print("Reward: 3 gold. The ghost recommends you for castle employment.")
