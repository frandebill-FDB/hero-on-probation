"""State that persists between scenes during one playthrough."""

from dataclasses import dataclass, field


@dataclass
class Hero:
    """The player's possessions and decisions."""

    gold: int = 3
    companion: str = ""
    pan: str = "intact"
    helped_slime: bool = False
    equipment: dict[str, str] = field(
        default_factory=lambda: {"Weapon": "Wooden Sword", "Armour": "Borrowed Coat"}
    )
    inventory: dict[str, int] = field(
        default_factory=lambda: {"Wooden Sword": 1, "Borrowed Coat": 1}
    )
    quests: dict[str, str] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    name: str = "Hero"
