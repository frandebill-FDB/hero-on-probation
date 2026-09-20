"""Commands and deterministic replay saves for the short adventure."""

from uuid import uuid4

from hero_on_probation import saves
from hero_on_probation.models import Hero


class Restart(Exception):
    """Restart the adventure using a validated sequence of past decisions."""

    def __init__(self, restored: "Session"):
        self.session = restored


class Session:
    """Save choices and reconstruct state without duplicating rewards."""

    def __init__(
        self, hero: Hero, replay: list[int] | None = None, save_id: str | None = None
    ):
        self.hero = hero
        self.save_id = save_id or uuid4().hex
        self.history: list[int] = []
        self.replay = list(replay or [])
        self.validating = False
        self.restoring = replay is not None

    def command(self, text: str) -> bool:
        """Handle informational commands without advancing the story."""
        hero = self.hero
        if text == "status":
            print(
                f"Hero: {hero.name} | Gold: {hero.gold} | Companion: {hero.companion or 'None'}"
            )
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
            print("save / load: replace or restore only this character's slot")
            print("menu: return to character selection without saving")
            print("quit: exit without saving automatically")
        elif text == "save":
            path = saves.write_save(
                saves.SavedGame(self.save_id, hero.name, self.history)
            )
            print(
                f"Saved {hero.name} at this choice to {path} (replaces this character's slot)."
            )
        elif text == "load":
            saved = saves.read_save(self.save_id)
            # Validate the entire path before discarding the current session.
            validate_replay(saved.choices)
            raise Restart(Session(Hero(name=saved.name), saved.choices, saved.save_id))
        else:
            return False
        return True


def validate_replay(choices: list[int]) -> None:
    """Replay the actual branching story on a temporary hero without input."""
    from contextlib import redirect_stdout
    from io import StringIO

    from hero_on_probation import game

    previous = getattr(game, "session", None)
    trial = Session(Hero(), choices)
    trial.validating = True
    game.session = trial
    try:
        with redirect_stdout(StringIO()):
            try:
                game.play_adventure(trial.hero)
            except game.ReplayComplete:
                pass
        if trial.replay:
            raise ValueError("Save contains choices after the ending")
    finally:
        game.session = previous
