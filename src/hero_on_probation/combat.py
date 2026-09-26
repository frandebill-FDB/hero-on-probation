"""Short deterministic battles; choices can be replayed without random rolls."""

from collections.abc import Callable
from dataclasses import dataclass, field

from hero_on_probation.models import Hero

Choose = Callable[[str, list[str]], int]


@dataclass
class Enemy:
    """Health and attack rules for one encounter."""

    name: str
    max_hp: int
    attack: int
    heavy_attack: int
    armour: int = 0
    hp: int = field(init=False)

    def __post_init__(self):
        self.hp = self.max_hp


def slime() -> Enemy:
    return Enemy("Bridge Slime", 12, 2, 5)


def demon_king() -> Enemy:
    """No available weapon penetrates this armour; magic changes the rules."""
    return Enemy("Demon King", 9999, 999, 999, 99)


def weapon_damage(hero: Hero) -> int:
    return {"Wooden Sword": 3, "Iron Sword": 5}.get(hero.equipment.get("Weapon"), 1)


def take_damage(hp: int, damage: int) -> int:
    """Never heal through negative damage or leave negative HP."""
    return max(0, hp - max(0, damage))


def fight(hero: Hero, enemy: Enemy, choose: Choose) -> str:
    """Return victory, defeat, retreat or bread; never pay rewards here."""
    turn = 1
    companion_used = False
    while hero.hp > 0 and enemy.hp > 0:
        incoming = enemy.attack if turn % 2 else enemy.heavy_attack
        action = choose(
            f"ROUND {turn} | {hero.name}: {hero.hp}/{hero.max_hp} HP | "
            f"{enemy.name}: {enemy.hp}/{enemy.max_hp} HP\n"
            f"Enemy defence: {enemy.armour}. Next attack: {incoming} damage.",
            [
                f"Attack with {hero.equipment.get('Weapon', 'bare hands')}.",
                "Defend. Use your shield, or risk the quest pan.",
                f"Ask {hero.companion or 'your companion'} for help."
                + (" (Already used.)" if companion_used else ""),
                "Retreat.",
            ],
        )
        guard = 0
        skip_enemy = False
        if action == 4:
            hero.journal.append(f"Retreated from {enemy.name} on round {turn}.")
            return "retreat"
        if action == 3:
            if companion_used or hero.companion not in ("Pip", "Bea"):
                print("No companion action available. Choose another move.")
                continue
            companion_used = True
            if hero.companion == "Pip":
                enemy.hp = 0
                hero.pan = "bread"
                print(
                    f"Pip waves his wand. {enemy.name} becomes a very surprised loaf."
                )
                print(
                    'Your pan smells freshly baked. Pip: "Good news: no fight. '
                    'Bad news: no frying."'
                )
                hero.journal.append(
                    f"Pip transformed {enemy.name} and the quest pan into bread."
                )
                return "bread"
            print(
                'Bea: "One rescue per battle. Union rules." She parries and counters.'
            )
            damage = max(0, weapon_damage(hero) + 2 - enemy.armour)
            enemy.hp = take_damage(enemy.hp, damage)
            skip_enemy = True
            print(f"Bea deals {damage} damage and blocks this enemy turn.")
        elif action == 2:
            guard = 4
            if hero.equipment.get("Shield") == "Pot Lid":
                print("You raise the pot lid. Finally, cookware with a combat licence.")
            elif hero.pan == "intact":
                hero.pan = "dented"
                hero.journal.append("Defended with the quest pan. It is now dented.")
                print("You raise the pan. Its resale value ducks instead.")
            else:
                print("You brace behind the pan. Culinary standards remain low.")
        else:
            damage = max(0, weapon_damage(hero) - enemy.armour)
            enemy.hp = take_damage(enemy.hp, damage)
            print(f"You deal {damage} damage.")
            if damage == 0:
                print("Your weapon makes a polite noise. The armour ignores it.")
        if enemy.hp == 0:
            hero.journal.append(f"Defeated {enemy.name} in {turn} rounds.")
            return "victory"
        if not skip_enemy:
            shield = 1 if hero.equipment.get("Shield") == "Pot Lid" else 0
            damage = max(0, incoming - guard - shield)
            hero.hp = take_damage(hero.hp, damage)
            print(
                f"{enemy.name} deals {damage} damage. Your HP: {hero.hp}/{hero.max_hp}."
            )
        turn += 1
    if hero.hp <= 0:
        hero.journal.append(f"Lost the fight against {enemy.name}.")
        return "defeat"
    return "victory"
