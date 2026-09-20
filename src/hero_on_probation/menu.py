"""Character creation and save management before entering the story."""

from uuid import uuid4

from hero_on_probation import saves
from hero_on_probation.models import Hero
from hero_on_probation.session import Session, validate_replay


def new_character_name() -> str | None:
    """Ask for a unique name; duplicate names must not overwrite a character."""
    existing = {saved.name.casefold() for saved in saves.list_saves()}
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


def select_save() -> saves.SavedGame | None:
    """Display character identities instead of asking users for file paths."""
    choices = saves.list_saves()
    if not choices:
        print("No character saves yet. Create a character or import old progress.")
        return None
    for number, saved in enumerate(choices, 1):
        print(f"{number}. {saved.name} | Saved decisions: {len(saved.choices)}")
    while True:
        answer = input("Select a character (0 to cancel): ").strip()
        if answer == "0":
            return None
        if answer in [str(n) for n in range(1, len(choices) + 1)]:
            return choices[int(answer) - 1]
        print("Enter one of the displayed numbers, or 0.")


def start_menu() -> Session | None:
    """Create, resume, import or delete a character without advancing the story."""
    while True:
        print("\nHERO ON PROBATION | Character menu")
        print("1. Create a character")
        print("2. Load a character's save")
        print("3. Delete a character's save")
        print("4. Import the old version-3 save")
        print("5. Quit")
        action = input("> ").strip().lower()
        try:
            if action in ("5", "quit"):
                return None
            if action in ("1", "4"):
                choices = saves.legacy_choices() if action == "4" else []
                validate_replay(choices)
                name = new_character_name()
                if name is None:
                    continue
                saved = saves.SavedGame(uuid4().hex, name, choices)
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
                    Hero(name=name), choices if action == "4" else None, saved.save_id
                )
            if action in ("2", "3"):
                saved = select_save()
                if saved is None:
                    continue
                if action == "2":
                    validate_replay(saved.choices)
                    print(f"Loading {saved.name}...")
                    return Session(Hero(name=saved.name), saved.choices, saved.save_id)
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
            print("Enter a number from 1 to 5.")
        except (OSError, ValueError) as error:
            print(f"Cannot complete request: {error}")
