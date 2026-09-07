"""Commands and deterministic replay saves for the short adventure."""

import json
from pathlib import Path

from hero_on_probation.models import Hero

SAVE_PATH = Path("saves/adventure.json")


class Restart(Exception):
    """Restart the adventure using a validated sequence of past decisions."""

    def __init__(self, decisions: list[int]):
        self.decisions = decisions


class Session:
    """Save choices and reconstruct state without duplicating rewards."""

    def __init__(self, hero: Hero, replay: list[int] | None = None):
        self.hero = hero
        self.history: list[int] = []
        self.replay = list(replay or [])
        self.validating = False
        self.restoring = replay is not None

    def command(self, text: str) -> bool:
        """Handle informational commands without advancing the story."""
        hero = self.hero
        if text == "status":
            print(f"Gold: {hero.gold} | Companion: {hero.companion or 'None'}")
            for slot, item in hero.equipment.items():
                print(f"{slot}: {item}")
        elif text == "bag":
            for item, count in hero.inventory.items():
                print(f"{item} x{count}")
            if "Demon King's Pan" in hero.inventory:
                print(f"Pan condition: {hero.pan}")
        elif text == "quests":
            print(
                "\n".join(f"[{state}] {name}" for name, state in hero.quests.items())
                or "No quests yet."
            )
        elif text == "journal":
            print("\n".join(hero.journal) or "Your adventure has just begun.")
        elif text == "achievements":
            print("\n".join(hero.achievements) or "No achievements yet. Dinner awaits.")
        elif text == "help":
            print("Enter a number to act. Other commands do not advance the story:")
            print("status / bag: gold, companion, equipment and possessions")
            print("quests / journal / achievements: your progress and rewards")
            print("save / load: replace or restore the single save slot")
            print("quit: exit without saving automatically")
        elif text == "save":
            SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            temporary = SAVE_PATH.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({"version": 2, "choices": self.history}), encoding="utf-8"
            )
            temporary.replace(SAVE_PATH)
            print(f"Saved at this choice to {SAVE_PATH} (replaces the previous slot).")
        elif text == "load":
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") != 2:
                raise ValueError(
                    "This chapter requires a version-2 save. Older saves cannot be replayed safely."
                )
            choices = data.get("choices")
            if not isinstance(choices, list) or not all(
                type(n) is int and 1 <= n <= 5 for n in choices
            ):
                raise ValueError("Invalid saved decisions")
            # Validate the entire path before discarding the current session.
            validate_replay(choices)
            raise Restart(choices)
        else:
            return False
        return True


def validate_replay(choices: list[int]) -> None:
    """Replay the actual branching story on a temporary hero without input."""
    from contextlib import redirect_stdout
    from io import StringIO
    from hero_on_probation import game
    from hero_on_probation.town import explore_town

    previous = game.session
    trial = Session(Hero(), choices)
    trial.validating = True
    game.session = trial
    try:
        with redirect_stdout(StringIO()):
            try:
                game.guild(trial.hero)
                explore_town(trial.hero, game.choose)
                game.bridge(trial.hero)
                game.arrival(trial.hero)
            except game.ReplayComplete:
                pass
        if trial.replay:
            raise ValueError("Save contains choices after the ending")
    finally:
        game.session = previous
