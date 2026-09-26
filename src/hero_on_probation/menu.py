"""Character creation and save management before entering the story."""

import sqlite3
from contextlib import redirect_stdout
from io import StringIO
from uuid import uuid4

from hero_on_probation import journey_store, saves
from hero_on_probation.journey import Journey
from hero_on_probation.models import Hero
from hero_on_probation.session import Session, validate_replay


def new_character_name() -> str | None:
    """Ask for a unique name; duplicate names must not overwrite a character."""
    existing = {
        saved.name.casefold()
        for saved in saves.list_saves() + journey_store.list_journeys()
    }
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
    """Display character identities instead of asking users for file paths."""
    choices = (
        journey_store.list_journeys(True)
        if archived
        else sorted(
            saves.list_saves() + journey_store.list_journeys(),
            key=lambda s: s.name.casefold(),
        )
    )
    if not choices:
        print("No character saves yet. Create a character or import old progress.")
        return None
    for number, saved in enumerate(choices, 1):
        if isinstance(saved, Journey):
            print(
                f"{number}. {saved.name} | Journey {saved.run} | Level {saved.level} | Gold {saved.gold}"
            )
            continue
        edition = "Original story" if saved.rules_version == 1 else "Combat edition"
        print(
            f"{number}. {saved.name} | {edition} | Saved decisions: {len(saved.choices)}"
        )
    while True:
        answer = input("Select a character (0 to cancel): ").strip()
        if answer == "0":
            return None
        if answer in [str(n) for n in range(1, len(choices) + 1)]:
            return choices[int(answer) - 1]
        print("Enter one of the displayed numbers, or 0.")


def start_menu() -> Session | Journey | None:
    """Create, resume, import or delete a character without advancing the story."""
    while True:
        print("\nHERO ON PROBATION | Character menu")
        print("1. Create a continuing-journey character (levels and autosave)")
        print("2. Load a character's save")
        print("3. Delete a character's save")
        print("4. Import the old version-3 save")
        print("5. Quit")
        print("6. Hall of Fame")
        print("7. Create a classic character (original short adventure)")
        print("8. Copy a completed classic character into a new journey")
        print("9. Restore a deleted journey character")
        action = input("> ").strip().lower()
        try:
            if action in ("5", "quit"):
                return None
            if action == "6":
                journey_store.show_honours()
                continue
            if action == "9":
                selected = select_save(archived=True)
                if selected is not None:
                    journey_store.restore(selected.save_id)
                    print("Journey restored. Honour records were preserved.")
                continue
            if action in ("1", "8"):
                old_hero = None
                if action == "8":
                    selected = select_save()
                    if selected is None:
                        continue
                    if isinstance(selected, Journey):
                        print(
                            "This character already supports continuing journeys. Load it instead."
                        )
                        continue
                    old_hero = completed_classic_hero(selected)
                    print(
                        "Choose a new name for the copy. The original save stays untouched; old achievement times remain unknown."
                    )
                name = new_character_name()
                if name is not None:
                    return journey_store.create(name, old_hero)
                continue
            if action in ("7", "4"):
                choices = saves.legacy_choices() if action == "4" else []
                rules = 1 if action == "4" else saves.CURRENT_RULES
                validate_replay(choices, rules)
                name = new_character_name()
                if name is None:
                    continue
                saved = saves.SavedGame(uuid4().hex, name, choices, rules)
                saves.write_save(saved)
                print(f"Character created: {name}. Progress saved.")
                print(
                    "Use save during play to keep later progress; there is no autosave."
                )
                if action == "4":
                    print(
                        "Old progress imported. The original file has not been changed."
                    )
                return Session(
                    Hero(name=name),
                    choices if action == "4" else None,
                    saved.save_id,
                    rules,
                )
            if action in ("2", "3"):
                saved = select_save()
                if saved is None:
                    continue
                if isinstance(saved, Journey):
                    if action == "2":
                        return saved
                    if (
                        input(f"Delete {saved.name}? Type DELETE to confirm: ").strip()
                        == "DELETE"
                    ):
                        journey_store.archive(saved.save_id)
                        print(
                            "Journey archived, not erased. Use option 9 to restore; honour records remain."
                        )
                    else:
                        print("Deletion cancelled.")
                    continue
                if action == "2":
                    validate_replay(saved.choices, saved.rules_version)
                    print(f"Loading {saved.name}...")
                    return Session(
                        Hero(name=saved.name),
                        saved.choices,
                        saved.save_id,
                        saved.rules_version,
                    )
                print(f"Delete the saved character '{saved.name}' and their progress?")
                if (
                    input("Type DELETE to confirm (anything else cancels): ").strip()
                    != "DELETE"
                ):
                    print("Deletion cancelled.")
                    continue
                destination = saves.archive_save(saved.save_id)
                print(
                    f"Save removed from the character list. Recoverable copy: {destination}"
                )
                continue
            print("Enter a number from 1 to 9.")
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
                raise ValueError(
                    "Finish the classic adventure and save its ending before copying."
                ) from None
        if not trial.hero.ending:
            raise ValueError("The classic save has no completed ending.")
        return trial.hero
    finally:
        game.session = previous
