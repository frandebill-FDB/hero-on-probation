"""Information views return to the current decision without changing progress."""

import copy
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import combat, game, saves, session
from hero_on_probation.models import Hero
from hero_on_probation.town import shop


class NavigationTests(unittest.TestCase):
    def setUp(self):
        previous = getattr(game, "session", None)
        self.addCleanup(setattr, game, "session", previous)
        game.session = session.Session(Hero(name="Tester"))

    def test_information_commands_redisplay_the_same_choices_without_mutation(self):
        for command in ("bag", "status", "quests", "journal", "achievements", "help"):
            with self.subTest(command=command):
                game.session = session.Session(Hero(name="Tester"))
                before = copy.deepcopy(game.session.hero)
                output = StringIO()
                with (
                    patch("builtins.input", side_effect=[command, "2"]),
                    redirect_stdout(output),
                ):
                    self.assertEqual(game.choose("Current decision", ["One", "Two"]), 2)
                text = output.getvalue()
                self.assertEqual(text.count("Current decision"), 2)
                self.assertEqual(text.count("2. Two"), 2)
                self.assertIn("Back to your current choice. No action taken.", text)
                self.assertEqual(game.session.hero, before)
                self.assertEqual(game.session.history, [2])

    def test_bag_then_enter_or_back_does_not_produce_an_input_error(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=["bag", "", " BACK ", "1"]),
            redirect_stdout(output),
        ):
            game.choose("Current decision", ["Continue"])
        self.assertEqual(output.getvalue().count("Current decision"), 4)
        self.assertNotIn("Enter a number from", output.getvalue())
        self.assertEqual(game.session.history, [1])

    def test_inspection_during_battle_does_not_advance_turn_or_damage_anyone(self):
        hero = game.session.hero
        hero.companion = "Bea"
        enemy = combat.slime()
        output = StringIO()
        commands = ["3", "bag", "", "back", "4"]
        with patch("builtins.input", side_effect=commands), redirect_stdout(output):
            self.assertEqual(combat.fight(hero, enemy, game.choose), "retreat")
        self.assertEqual((hero.hp, enemy.hp), (12, 7))
        self.assertEqual(game.session.history, [3, 4])
        self.assertEqual(
            output.getvalue().count(
                "ROUND 2 | Tester: 12/12 HP | Bridge Slime: 7/12 HP"
            ),
            4,
        )
        self.assertEqual(output.getvalue().count("(Already used.)"), 4)
        self.assertNotIn("ROUND 3", output.getvalue())

    def test_shop_inspection_does_not_repeat_purchase_or_pollute_saved_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            game.session.hero.gold = 10
            with (
                patch.object(saves, "SAVE_DIR", Path(directory)),
                patch(
                    "builtins.input", side_effect=["1", "bag", "back", "", "save", "4"]
                ),
                redirect_stdout(StringIO()),
            ):
                shop(game.session.hero, game.choose)
                saved = saves.read_save(game.session.save_id)
            self.assertEqual(game.session.hero.gold, 5)
            self.assertEqual(game.session.hero.inventory["Iron Sword"], 1)
            self.assertEqual(saved.choices, [1])
            self.assertEqual(game.session.history, [1, 4])

    def test_replayed_choices_are_still_silent_and_do_not_wait_for_back(self):
        game.session = session.Session(Hero(), replay=[2])
        output = StringIO()
        with patch("builtins.input") as read, redirect_stdout(output):
            self.assertEqual(game.choose("Old decision", ["One", "Two"]), 2)
        read.assert_not_called()
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(game.session.history, [2])

    def test_ending_bag_and_back_redisplay_commands_without_repeating_rewards(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=["3", "5", "bag", "back", "", "quit"]),
            redirect_stdout(output),
        ):
            game.run_session(game.session)
        text = output.getvalue()
        self.assertEqual(text.count("ENDING: CLOCKED OUT"), 1)
        self.assertEqual(text.count("Commands: status | bag"), 4)
        self.assertEqual(game.session.hero.gold, 3)
        self.assertEqual(game.session.hero.achievements, ["ANY% HERO"])
        self.assertEqual(game.session.history, [3, 5])
