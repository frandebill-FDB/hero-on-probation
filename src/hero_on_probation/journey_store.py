"""Atomic journey snapshots and Hall of Fame, using standard-library SQLite."""

import json
import sqlite3
from contextlib import contextmanager
from uuid import uuid4

from hero_on_probation import saves
from hero_on_probation.collection import show_collection
from hero_on_probation.journey import GEAR, Journey


@contextmanager
def database():
    saves.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = saves.SAVE_DIR / "journeys.sqlite3"
    if path.is_symlink() or saves.SAVE_DIR.is_symlink():
        raise ValueError("Linked journey storage is not supported.")
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL,
                revision INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
                version INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS active_name
                ON characters(name_key) WHERE deleted = 0;
            CREATE TABLE IF NOT EXISTS honours (
                character_id TEXT NOT NULL, title TEXT NOT NULL,
                record TEXT NOT NULL, PRIMARY KEY(character_id, title)
            );
        """)
        yield connection
    finally:
        connection.close()


def decode(row) -> Journey:
    if row is None:
        raise ValueError("Journey save not found.")
    if row["version"] != 1:
        raise ValueError("Unsupported journey save version.")
    state = Journey.from_data(json.loads(row["state"]))
    saves.save_path(state.save_id)
    saves.character_name(state.name)
    if (state.save_id, state.name, state.revision) != (
        row["id"],
        row["name"],
        row["revision"],
    ):
        raise ValueError("Journey identity or revision mismatch.")
    return state


def load(save_id: str) -> Journey:
    saves.save_path(save_id)
    with database() as db:
        return decode(
            db.execute(
                "SELECT * FROM characters WHERE id=? AND deleted=0", (save_id,)
            ).fetchone()
        )


def list_journeys(include_deleted=False) -> list[Journey]:
    if not (saves.SAVE_DIR / "journeys.sqlite3").exists():
        return []
    found = []
    with database() as db:
        rows = db.execute(
            "SELECT * FROM characters WHERE deleted=? ORDER BY name_key",
            (int(include_deleted),),
        ).fetchall()
        for row in rows:
            try:
                found.append(decode(row))
            except (ValueError, TypeError) as error:
                print(f"Cannot read journey {row['id']}: {error}")
    return found


def write_honours(db, state):
    for title, record in state.achievements.items():
        db.execute(
            "INSERT INTO honours VALUES (?, ?, ?) ON CONFLICT(character_id, title) DO UPDATE SET record=excluded.record",
            (state.save_id, title, json.dumps(record)),
        )


def legacy_saves():
    """Hide superseded JSON backups, including when their new character is deleted."""
    known = set()
    if (saves.SAVE_DIR / "journeys.sqlite3").exists():
        with database() as db:
            known = {row[0] for row in db.execute("SELECT id FROM characters")}
    return [saved for saved in saves.list_saves() if saved.save_id not in known]


def inherit_legacy(state, hero):
    """Keep verified possessions and mark unrecorded historical times as unknown."""
    if not hero.ending:
        raise ValueError("Finish the saved adventure before upgrading its character.")
    state.gold = hero.gold
    state.inventory = {k: v for k, v in hero.inventory.items() if k in GEAR}
    state.equipment = dict(hero.equipment)
    for title in hero.achievements:
        state.achievements[title] = {
            "description": "Imported achievement; original time and level unknown.",
            "first_at": None,
            "first_run": 1,
            "level": 1,
            "last_run": 1,
            "count": 1,
        }
    state.journal.append(
        "Previous ending: "
        + hero.ending
        + ". No retroactive XP or invented timestamps."
    )


def upgrade(saved: saves.SavedGame, hero) -> Journey:
    """Upgrade once with the same ID/name; leave the original JSON untouched."""
    saves.save_path(saved.save_id)
    name = saves.character_name(saved.name)
    if hero.name != name:
        raise ValueError("Character identity mismatch.")
    with database() as db:
        existing = db.execute(
            "SELECT * FROM characters WHERE id=?", (saved.save_id,)
        ).fetchone()
        if existing is not None:
            if existing["deleted"]:
                raise ValueError(
                    "This character was deleted. Restore it from Manage saves."
                )
            return decode(existing)
        state = Journey(saved.save_id, name)
        inherit_legacy(state, hero)
        state.run = 1 if hero.ending == "CLOCKED OUT" else 2
        Journey.from_data(state.data())
        try:
            with db:
                db.execute(
                    "INSERT INTO characters (id,name,name_key,revision,state) VALUES(?,?,?,?,?)",
                    (state.save_id, name, name.casefold(), 0, json.dumps(state.data())),
                )
                write_honours(db, state)
        except sqlite3.IntegrityError as error:
            raise ValueError(
                "Another active character uses that name. No progress was overwritten."
            ) from error
    return state


def create(name: str, legacy_hero=None) -> Journey:
    name = saves.character_name(name)
    if any(s.name.casefold() == name.casefold() for s in legacy_saves()):
        raise ValueError("That name already has a save.")
    state = Journey(uuid4().hex, name)
    if legacy_hero is not None:
        inherit_legacy(state, legacy_hero)
    Journey.from_data(state.data())
    with database() as db:
        try:
            with db:
                db.execute(
                    "INSERT INTO characters (id,name,name_key,revision,state) VALUES(?,?,?,?,?)",
                    (state.save_id, name, name.casefold(), 0, json.dumps(state.data())),
                )
                write_honours(db, state)
        except sqlite3.IntegrityError as error:
            raise ValueError("That name already has a save.") from error
    return state


def commit(state: Journey) -> Journey:
    """Commit a copied transition and its honours together, rejecting stale writers."""
    Journey.from_data(state.data())
    saves.save_path(state.save_id)
    saves.character_name(state.name)
    previous = state.revision
    payload = state.data()
    payload["revision"] += 1
    with database() as db, db:
        changed = db.execute(
            "UPDATE characters SET revision=?, state=? WHERE id=? AND revision=? AND name=? AND deleted=0",
            (previous + 1, json.dumps(payload), state.save_id, previous, state.name),
        ).rowcount
        if changed != 1:
            raise ValueError(
                "Save changed in another window or was deleted. Use load before continuing."
            )
        write_honours(db, state)
    state.revision = previous + 1
    return state


def archive(save_id: str):
    """Hide a journey without erasing its snapshot or honour records."""
    saves.save_path(save_id)
    with database() as db, db:
        if (
            db.execute(
                "UPDATE characters SET deleted=1 WHERE id=? AND deleted=0", (save_id,)
            ).rowcount
            != 1
        ):
            raise ValueError("Journey save not found.")


def restore(save_id: str):
    saves.save_path(save_id)
    with database() as db:
        row = db.execute(
            "SELECT * FROM characters WHERE id=? AND deleted=1", (save_id,)
        ).fetchone()
        state = decode(row)
        if any(s.name.casefold() == state.name.casefold() for s in legacy_saves()):
            raise ValueError("An active classic character has the same name.")
        try:
            with db:
                db.execute("UPDATE characters SET deleted=0 WHERE id=?", (save_id,))
        except sqlite3.IntegrityError as error:
            raise ValueError(
                "An active character has the same name. No save was overwritten."
            ) from error


def honours() -> list[dict]:
    if not (saves.SAVE_DIR / "journeys.sqlite3").exists():
        return []
    with database() as db:
        rows = db.execute(
            "SELECT h.*, c.name, c.deleted FROM honours h JOIN characters c ON c.id=h.character_id ORDER BY c.name_key, h.title"
        ).fetchall()
        return [dict(row, record=json.loads(row["record"])) for row in rows]


def show_honours(show_hints=False):
    print("\nHALL OF FAME | Local records across characters")
    records = honours()
    show_collection((row["title"] for row in records), show_hints)
    if not records:
        print("No achievements recorded yet. The trophy cleaner is on probation too.")
    for row in records:
        r = row["record"]
        when = r["first_at"] or "Unknown (imported from classic save)"
        status = " [save deleted; record retained]" if row["deleted"] else ""
        print(
            f"\n{row['title']} — {row['name']}{status}\nSave: {row['character_id']} | First earned: {when}"
        )
        origin = (
            f"Journey {r['first_run']} | Level {r['level']}"
            if r["first_at"]
            else "Original journey / level unknown"
        )
        print(f"{origin} | Count: {r['count']}\n{r['description']}")
