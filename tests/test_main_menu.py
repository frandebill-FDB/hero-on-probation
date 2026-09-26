"""A single game entry point with transparent, non-destructive save upgrades."""

import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import game, journey_store, menu, saves
from hero_on_probation.journey import Journey
from hero_on_probation.session import Session


class MainMenuTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        replacement = patch.object(saves, "SAVE_DIR", Path(directory.name))
        replacement.start()
        self.addCleanup(replacement.stop)

    def seed(self, choices=None):
        saved = saves.SavedGame(
            "f" * 32, "Ada", [3, 5] if choices is None else choices, 2
        )
        saves.write_save(saved)
        return saved

    def play(self, commands):
        output = StringIO()
        with patch("builtins.input", side_effect=commands), redirect_stdout(output):
            game.main()
        return output.getvalue()

    def test_main_menu_has_five_options_and_no_version_selection(self):
        text = self.play(["5"])
        options = [line for line in text.splitlines() if line[:1].isdigit()]
        self.assertEqual(
            options,
            [
                "1. New game",
                "2. Continue game",
                "3. Hall of Fame",
                "4. Manage saves",
                "5. Quit",
            ],
        )
        for hidden in (
            "classic",
            "continuing-journey",
            "version-3",
            "Copy a",
            "Delete",
            "Restore",
        ):
            self.assertNotIn(hidden, text)

    def test_one_continue_entry_can_load_new_or_unfinished_old_character(self):
        saved = self.seed([3])
        new = journey_store.create("Bea")
        with redirect_stdout(StringIO()):
            self.assertIsInstance(menu.resume_character(saved), Session)
            self.assertIsInstance(menu.resume_character(new), Journey)
        self.assertEqual(len(menu.active_saves()), 2)

    def test_completed_old_save_is_upgraded_once_with_same_name_and_id(self):
        saved = self.seed()
        before = saves.save_path(saved.save_id).read_bytes()
        self.play(["2", "1", "menu", "2", "1", "quit"])
        listed = menu.active_saves()
        self.assertEqual(len(listed), 1)
        self.assertEqual(
            (listed[0].save_id, listed[0].name), (saved.save_id, saved.name)
        )
        self.assertEqual(saves.save_path(saved.save_id).read_bytes(), before)
        self.assertEqual(len(journey_store.honours()), 1)
        self.assertIsNone(journey_store.honours()[0]["record"]["first_at"])

    def test_old_character_can_finish_then_continue_without_renaming_or_resaving(self):
        saved = self.seed([3])
        before = saves.save_path(saved.save_id).read_bytes()
        self.play(["2", "1", "5", "next", "quit"])
        state = journey_store.load(saved.save_id)
        self.assertEqual((state.name, state.run, state.stage), ("Ada", 1, "guild"))
        self.assertIn("ANY% HERO", state.achievements)
        self.assertEqual(saves.save_path(saved.save_id).read_bytes(), before)

    def test_deleted_upgraded_character_does_not_reappear_from_backup(self):
        self.seed()
        self.play(["2", "1", "menu", "4", "1", "1", "DELETE", "0", "5"])
        self.assertEqual(menu.active_saves(), [])
        self.assertEqual(len(saves.list_saves()), 1)
        self.assertEqual(journey_store.honours()[0]["deleted"], 1)

    def test_restore_upgraded_character_ignores_its_own_json_backup(self):
        saved = self.seed()
        self.play(["2", "1", "menu", "4", "1", "1", "DELETE", "2", "1", "0", "5"])
        listed = menu.active_saves()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].save_id, saved.save_id)
        self.assertEqual(journey_store.honours()[0]["deleted"], 0)

    def test_upgrade_failure_does_not_hide_or_modify_old_save(self):
        saved = self.seed()
        before = saves.save_path(saved.save_id).read_bytes()
        with patch.object(
            journey_store,
            "write_honours",
            side_effect=sqlite3.OperationalError("disk full"),
        ):
            text = self.play(["2", "1", "5"])
        self.assertIn("Cannot complete request", text)
        self.assertEqual(journey_store.list_journeys(), [])
        self.assertEqual(len(menu.active_saves()), 1)
        self.assertEqual(saves.save_path(saved.save_id).read_bytes(), before)

    def test_repeated_upgrade_does_not_reset_progress(self):
        saved = self.seed()
        with redirect_stdout(StringIO()):
            state = menu.resume_character(saved)
            state.act(3)
            state = journey_store.commit(state)
            again = menu.resume_character(saved)
        self.assertEqual(again.data(), state.data())

    def test_manage_saves_back_returns_to_main_without_starting_game(self):
        text = self.play(["4", "0", "5"])
        self.assertEqual(text.count("HERO ON PROBATION | Main menu"), 2)
        self.assertNotIn("Guild desk", text)
        self.assertEqual(menu.active_saves(), [])

    def test_deleted_name_can_be_reused_but_restore_cannot_overwrite_it(self):
        self.seed()
        self.play(["2", "1", "menu", "4", "1", "1", "DELETE", "0", "1", "Ada", "quit"])
        listed = menu.active_saves()
        self.assertEqual(len(listed), 1)
        self.assertNotEqual(listed[0].save_id, "f" * 32)
        with self.assertRaises(ValueError):
            journey_store.restore("f" * 32)
