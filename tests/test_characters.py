"""Character selection, per-character persistence and safe deletion tests."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import game, journey_store, menu, saves, session
from hero_on_probation.models import Hero


class CharacterTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        replacement = patch.object(saves, "SAVE_DIR", self.root)
        replacement.start()
        self.addCleanup(replacement.stop)

    def run_menu(self, commands):
        output = StringIO()
        with patch("builtins.input", side_effect=commands), redirect_stdout(output):
            game.main()
        return output.getvalue()

    def seed(self, name="Ada", choices=None, save_id=None):
        saved = saves.SavedGame(save_id or "a" * 32, name, choices or [])
        saves.write_save(saved)
        return saved

    def test_create_character_shows_name_and_saves_starting_progress(self):
        text = self.run_menu(["1", "  Mira  ", "status", "quit"])
        slots = journey_store.list_journeys()
        self.assertEqual(len(slots), 1)
        self.assertEqual((slots[0].name, slots[0].stage), ("Mira", "guild"))
        self.assertIn("Hero: Mira", text)

    def test_blank_long_and_control_character_names_are_retried(self):
        self.run_menu(["1", "", " ", "x" * 25, "\x1b[2J", "Éva", "quit"])
        self.assertEqual(
            [saved.name for saved in journey_store.list_journeys()], ["Éva"]
        )

    def test_names_cannot_escape_the_save_directory(self):
        self.run_menu(["1", "../../example", "quit"])
        slot = journey_store.list_journeys()[0]
        self.assertEqual(slot.name, "../../example")
        self.assertEqual(saves.save_path(slot.save_id).parent, self.root)
        self.assertRegex(slot.save_id, r"^[0-9a-f]{32}$")

    def test_duplicate_name_is_rejected_without_overwriting_existing_slot(self):
        original = self.seed(choices=[3, 5])
        before = saves.save_path(original.save_id).read_bytes()
        text = self.run_menu(["1", " ada ", "Mira", "quit"])
        self.assertIn("already has a save", text)
        self.assertEqual(saves.save_path(original.save_id).read_bytes(), before)
        self.assertEqual(len(menu.active_saves()), 2)

    def test_creation_cancel_and_eof_do_not_create_a_character(self):
        self.run_menu(["1", "0", "5"])
        self.run_menu(["1", EOFError()])
        self.assertEqual(menu.active_saves(), [])

    def test_two_characters_keep_separate_progress_and_identity(self):
        self.run_menu(
            [
                "1",
                "Ada",
                "3",
                "5",
                "menu",
                "1",
                "Mira",
                "3",
                "4",
                "2",
                "menu",
                "2",
                "1",
                "quit",
            ]
        )
        ada, mira = journey_store.list_journeys()
        self.assertEqual((ada.name, ada.ending), ("Ada", "CLOCKED OUT"))
        self.assertEqual(
            (mira.name, mira.stage, mira.companion), ("Mira", "town", "Bea")
        )
        self.assertNotEqual(ada.save_id, mira.save_id)
        self.assertEqual(ada.gold, 3)

    def test_in_game_load_restores_only_current_older_character(self):
        other = self.seed("Other", [3, 5])
        current = self.seed("Mira", [], "b" * 32)
        self.run_menu(["2", "1", "3", "save", "1", "load", "quit"])
        self.assertEqual(game.session.hero.name, current.name)
        self.assertEqual(game.session.history, [3])
        self.assertEqual(saves.read_save(other.save_id).choices, [3, 5])

    def test_mid_story_older_save_survives_quitting_and_loading_from_main_menu(self):
        slot = self.seed("Mira")
        self.run_menu(["2", "1", "3", "4", "3", "1", "1", "save", "quit"])
        slot = saves.read_save(slot.save_id)
        self.assertEqual(slot.choices, [3, 4, 3, 1, 1])
        text = self.run_menu(["2", "1", "quit"])
        self.assertEqual(game.session.history, slot.choices)
        self.assertEqual(game.session.hero.name, "Mira")
        self.assertEqual(game.session.hero.companion, "Pip")
        self.assertIn("Iron Sword: 5 gold", text)
        self.assertNotIn("You wake up at a counter", text)
        self.assertNotIn("ENDING:", text)

    def test_return_to_menu_does_not_autosave_older_unfinished_adventure(self):
        self.seed()
        self.run_menu(["2", "1", "3", "5", "menu", "2", "1", "quit"])
        self.assertEqual(game.session.hero.name, "Ada")
        self.assertEqual(game.session.history, [])
        self.assertEqual(game.session.hero.achievements, [])

    def test_delete_requires_confirmation_and_preserves_other_characters(self):
        ada = self.seed(choices=[3, 5])
        other = self.seed("Mira", [3], "b" * 32)
        original = saves.save_path(ada.save_id).read_bytes()
        text = self.run_menu(["4", "1", "1", "no", "0", "5"])
        self.assertIn("Deletion cancelled", text)
        self.assertEqual(saves.save_path(ada.save_id).read_bytes(), original)
        text = self.run_menu(["4", "1", "1", "DELETE", "0", "5"])
        self.assertIn("Recoverable copy:", text)
        self.assertFalse(saves.save_path(ada.save_id).exists())
        self.assertEqual([s.save_id for s in saves.list_saves()], [other.save_id])
        archived = list((self.root / "deleted").glob("*.json"))
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0].read_bytes(), original)

    def test_delete_selection_cancel_or_interrupted_confirmation_keeps_save(self):
        original = self.seed()
        self.run_menu(["4", "1", "0", "0", "5"])
        self.run_menu(["4", "1", "1", KeyboardInterrupt()])
        self.assertTrue(saves.save_path(original.save_id).exists())

    def test_empty_menu_and_invalid_selections_are_handled(self):
        text = self.run_menu(["hello", "2", "4", "1", "0", "5"])
        self.assertIn("Enter a number", text)
        self.assertIn("No character saves yet", text)
        self.seed()
        text = self.run_menu(["2", "abc", "99", "0", "5"])
        self.assertIn("Enter one of the displayed numbers", text)

    def test_import_version_three_save_preserves_progress_and_source(self):
        source = self.root / "adventure-v3.json"
        source.write_text(json.dumps({"version": 3, "choices": [3, 4, 3, 1]}))
        before = source.read_bytes()
        text = self.run_menu(["4", "3", "Legacy Hero", "quit"])
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(game.session.history, [3, 4, 3, 1])
        self.assertEqual(game.session.hero.name, "Legacy Hero")
        self.assertEqual(game.session.hero.companion, "Pip")
        self.assertIn("Visit the equipment shop", text)
        self.assertNotIn("You wake up at a counter", text)
        self.assertEqual(saves.list_saves()[0].choices, [3, 4, 3, 1])

    def test_import_completed_ending_preserves_achievement_without_rewards(self):
        source = self.root / "adventure-v3.json"
        source.write_text(json.dumps({"version": 3, "choices": [3, 5]}))
        self.run_menu(["4", "3", "Retired Hero", "load", "quit"])
        state = journey_store.list_journeys()[0]
        self.assertEqual(state.gold, 3)
        self.assertEqual(list(state.achievements), ["ANY% HERO"])

    def test_bad_legacy_import_leaves_files_unchanged(self):
        source = self.root / "adventure-v3.json"
        for data in (
            {"version": 2, "choices": []},
            {"version": 3, "choices": [3, 5, 1]},
        ):
            with self.subTest(data=data):
                source.write_text(json.dumps(data))
                before = source.read_bytes()
                text = self.run_menu(["4", "3", "0", "5"])
                self.assertIn("Cannot complete request", text)
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(saves.list_saves(), [])

    def test_missing_legacy_and_corrupt_character_save_do_not_crash_menu(self):
        saves.save_path("b" * 32).write_text("not json")
        valid = self.seed()
        text = self.run_menu(["4", "3", "0", "2", "1", "quit"])
        self.assertIn("Cannot complete request", text)
        self.assertIn("Cannot read save", text)
        self.assertEqual(game.session.save_id, valid.save_id)

    def test_invalid_replay_does_not_replace_live_session(self):
        saved = self.seed(choices=[3, 5, 1])
        current = session.Session(Hero(name="Ada", gold=42), save_id=saved.save_id)
        game.session = current
        with self.assertRaises(ValueError):
            current.command("load")
        self.assertIs(game.session, current)
        self.assertEqual(current.hero.gold, 42)

    def test_identity_mismatch_and_unsafe_ids_are_rejected(self):
        saved = self.seed()
        path = saves.save_path(saved.save_id)
        data = json.loads(path.read_text())
        data["character"]["id"] = "b" * 32
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "identity"):
            saves.read_save(saved.save_id)
        for bad_id in ("../outside", "", "A" * 32):
            with self.assertRaises(ValueError):
                saves.archive_save(bad_id)

    def test_invalid_decision_types_are_rejected(self):
        for choices in ([True], [0], [6], ["1"], None, {}):
            with self.subTest(choices=choices), self.assertRaises(ValueError):
                saves.checked_choices(choices)

    def test_failed_atomic_save_keeps_previous_contents(self):
        saved = self.seed(choices=[3])
        path = saves.save_path(saved.save_id)
        before = path.read_bytes()
        saved.choices = [3, 5]
        with patch.object(Path, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                saves.write_save(saved)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(self.root.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
