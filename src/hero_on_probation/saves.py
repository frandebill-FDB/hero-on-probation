"""Named character saves, legacy import and recoverable deletion."""

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

SAVE_DIR = Path("saves")
SAVE_VERSION = 5
CURRENT_RULES = 2


def character_name(value: str) -> str:
    """Allow short display names, never using them as filesystem paths."""
    if not isinstance(value, str) or not value.isprintable():
        raise ValueError("Use a printable character name.")
    value = value.strip()
    if not 1 <= len(value) <= 24:
        raise ValueError("Use a name between 1 and 24 characters.")
    return value


def checked_choices(value: object) -> list[int]:
    """Validate the JSON shape before the story validates its branching path."""
    if not isinstance(value, list) or not all(
        type(n) is int and 1 <= n <= 5 for n in value
    ):
        raise ValueError("Invalid saved decisions")
    return list(value)


def save_path(save_id: str) -> Path:
    """Resolve only generated IDs under the local save directory."""
    if not isinstance(save_id, str) or not re.fullmatch(r"[0-9a-f]{32}", save_id):
        raise ValueError("Invalid save ID")
    path = SAVE_DIR / f"{save_id}.json"
    if path.is_symlink():
        raise ValueError("Linked save files are not supported.")
    return path


@dataclass
class SavedGame:
    """A character identity plus deterministic story decisions."""

    save_id: str
    name: str
    choices: list[int]
    rules_version: int = CURRENT_RULES


def read_save(save_id: str) -> SavedGame:
    """Read character saves; version-four files retain the original story rules."""
    data = json.loads(save_path(save_id).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") not in (4, SAVE_VERSION):
        raise ValueError("This character requires a version-4 or version-5 save.")
    rules = 1 if data["version"] == 4 else data.get("rules_version")
    if type(rules) is not int or rules not in (1, CURRENT_RULES):
        raise ValueError("Unsupported story rules version.")
    profile = data.get("character")
    if not isinstance(profile, dict) or profile.get("id") != save_id:
        raise ValueError("Save identity does not match its filename.")
    return SavedGame(
        save_id,
        character_name(profile.get("name")),
        checked_choices(data.get("choices")),
        rules,
    )


def write_save(saved: SavedGame) -> Path:
    """Atomically replace one character's slot, not other characters' saves."""
    path = save_path(saved.save_id)
    if type(saved.rules_version) is not int or saved.rules_version not in (
        1,
        CURRENT_RULES,
    ):
        raise ValueError("Unsupported story rules version.")
    data = {
        "version": SAVE_VERSION,
        "character": {"id": saved.save_id, "name": character_name(saved.name)},
        "choices": checked_choices(saved.choices),
        "rules_version": saved.rules_version,
    }
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=SAVE_DIR, suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump(data, output, ensure_ascii=False)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return path


def list_saves() -> list[SavedGame]:
    """List named saves; report unreadable files without blocking other slots."""
    found = []
    for path in sorted(SAVE_DIR.glob("*.json")):
        if not re.fullmatch(r"[0-9a-f]{32}", path.stem):
            continue
        try:
            found.append(read_save(path.stem))
        except (OSError, ValueError) as error:
            print(f"Cannot read save {path.name}: {error}")
    return sorted(found, key=lambda saved: (saved.name.casefold(), saved.save_id))


def archive_save(save_id: str) -> Path:
    """Move just the selected save out of the active list for manual recovery."""
    source = save_path(save_id)
    if not source.is_file():
        raise ValueError("That save no longer exists.")
    deleted = SAVE_DIR / "deleted"
    if deleted.is_symlink():
        raise ValueError("Linked deletion folders are not supported.")
    deleted.mkdir(parents=True, exist_ok=True)
    destination = deleted / f"{save_id}-{uuid4().hex}.json"
    source.rename(destination)
    return destination


def legacy_choices() -> list[int]:
    """Read the old unnamed version-three slot, leaving the source untouched."""
    path = SAVE_DIR / "adventure-v3.json"
    if path.is_symlink():
        raise ValueError("Linked save files are not supported.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 3:
        raise ValueError("Only version-3 progress can be imported here.")
    return checked_choices(data.get("choices"))
