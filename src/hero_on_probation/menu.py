"""One player-facing menu; save-format compatibility is handled internally."""

import sqlite3
from contextlib import redirect_stdout
from io import StringIO
from uuid import uuid4

from hero_on_probation import journey_store, saves
from hero_on_probation.journey import Journey
from hero_on_probation.models import Hero
from hero_on_probation.session import Session, validate_replay


class IncompleteAdventure(ValueError):
    """An older save has a valid unfinished decision, not a completed result."""


def active_saves():
    """An upgraded character appears once; its JSON remains a recovery backup."""
    return sorted(
        journey_store.legacy_saves() + journey_store.list_journeys(),
        key=lambda saved: saved.name.casefold(),
    )


def new_character_name() -> str | None:
    existing = {saved.name.casefold() for saved in active_saves()}
    while True:
        raw = input("Character name (1-24 characters; 0 to cancel): ")
        if raw.strip() == "0":
            return None
        try:
            name = saves.character_name(raw)
            if name.casefold() in existing:
                raise ValueError(
                    "That name already has a save. Load it or choose another."
                )
            return name
        except ValueError as error:
            print(error)


def select_save(archived=False) -> saves.SavedGame | Journey | None:
    choices = journey_store.list_journeys(True) if archived else active_saves()
    if not choices:
        print(
            "No deleted character saves to restore."
            if archived
            else "No character saves yet. Start a new game."
        )
        return None
    for number, saved in enumerate(choices, 1):
        if isinstance(saved, Journey):
            detail = f"Journey {saved.run} | Level {saved.level} | Gold {saved.gold}"
        else:
            detail = "Saved adventure"
        print(f"{number}. {saved.name} | {detail}")
    while True:
        answer = input("Select a character (0 to cancel): ").strip()
        if answer == "0":
            return None
        if answer in [str(n) for n in range(1, len(choices) + 1)]:
            return choices[int(answer) - 1]
        print("Enter one of the displayed numbers, or 0.")


def resume_character(saved: saves.SavedGame | Journey) -> Session | Journey:
    if isinstance(saved, Journey):
        return saved
    try:
        hero = completed_classic_hero(saved)
    except IncompleteAdventure:
        print(f"Loading {saved.name} at the saved decision.")
        return Session(
            Hero(name=saved.name), saved.choices, saved.save_id, saved.rules_version
        )
    upgraded = journey_store.upgrade(saved, hero)
    print(f"Last ending: {hero.ending}. {saved.name} can now continue the journey.")
    print(
        "Your name, money, equipment and achievements are kept. The older save file remains as a backup."
    )
    return upgraded


def manage_saves() -> Session | Journey | None:
    while True:
        print("\nSAVE MANAGEMENT")
        print("1. Delete a character's save")
        print("2. Restore a deleted character")
        print("3. Import an older save")
        print("0. Back to main menu")
        action = input("> ").strip().lower()
        if action in ("0", "back", "menu"):
            return None
        if action == "quit":
            raise EOFError
        try:
            if action == "1":
                saved = select_save()
                if saved is None:
                    continue
                print(f"Delete '{saved.name}'? Other characters will not be affected.")
                if (
                    input("Type DELETE to confirm (anything else cancels): ").strip()
                    != "DELETE"
                ):
                    print("Deletion cancelled.")
                    continue
                if isinstance(saved, Journey):
                    journey_store.archive(saved.save_id)
                    print(
                        "Character archived, not erased. Use Restore here to recover it. Honour records remain."
                    )
                else:
                    destination = saves.archive_save(saved.save_id)
                    print(f"Recoverable copy: {destination}")
                continue
            if action == "2":
                saved = select_save(archived=True)
                if saved is not None:
                    journey_store.restore(saved.save_id)
                    print("Character restored. Honour records were preserved.")
                continue
            if action == "3":
                print(
                    "Importing saved progress from saves/adventure-v3.json. The original file is kept."
                )
                choices = saves.legacy_choices()
                validate_replay(choices, 1)
                name = new_character_name()
                if name is None:
                    continue
                saved = saves.SavedGame(uuid4().hex, name, choices, 1)
                saves.write_save(saved)
                print("Old progress imported. The original file has not been changed.")
                return resume_character(saved)
            print("Enter a number from 0 to 3.")
        except (OSError, ValueError, sqlite3.Error) as error:
            print(f"Cannot complete request: {error}")


def start_menu() -> Session | Journey | None:
    while True:
        print("\nHERO ON PROBATION | Main menu")
        print("1. New game")
        print("2. Continue game")
        print("3. Hall of Fame")
        print("4. Manage saves")
        print("5. Quit")
        action = input("> ").strip().lower()
        try:
            if action in ("5", "quit"):
                return None
            if action == "1":
                name = new_character_name()
                if name is not None:
                    return journey_store.create(name)
            elif action == "2":
                saved = select_save()
                if saved is not None:
                    return resume_character(saved)
            elif action == "3":
                journey_store.show_honours()
            elif action == "4":
                selected = manage_saves()
                if selected is not None:
                    return selected
            else:
                print("Enter a number from 1 to 5.")
        except (OSError, ValueError, sqlite3.Error) as error:
            print(f"Cannot complete request: {error}")


def completed_classic_hero(saved: saves.SavedGame) -> Hero:
    """Read a completed old adventure without writes, prompts or replay output."""
    from hero_on_probation import game

    validate_replay(saved.choices, saved.rules_version)
    previous = getattr(game, "session", None)
    trial = Session(
        Hero(name=saved.name), saved.choices, saved.save_id, saved.rules_version
    )
    trial.validating = True
    game.session = trial
    try:
        with redirect_stdout(StringIO()):
            try:
                game.play_adventure(trial.hero)
            except game.ReplayComplete:
                raise IncompleteAdventure(
                    "Finish the current adventure before continuing to the next journey."
                ) from None
        if not trial.hero.ending:
            raise IncompleteAdventure("The saved adventure is not finished.")
        return trial.hero
    finally:
        game.session = previous
