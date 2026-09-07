"""Regression tests for rewards, purchases, equipment and save replay."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import game, session
from hero_on_probation.models import Hero
from hero_on_probation.town import ghost, rats, shop


class AdventureTests(unittest.TestCase):
    def test_loading_hides_previous_story_and_keeps_current_menu(self):
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(session, "SAVE_PATH", Path(directory) / "save.json"),
                patch("builtins.input", side_effect=["3", "2", "save", "load", "quit"]),
                redirect_stdout(output),
            ):
                game.main()
        text = output.getvalue()
        self.assertEqual(text.count("Welcome, chosen hero!"), 1)
        self.assertEqual(text.count("Visit the equipment shop."), 2)
        self.assertNotIn("Restored choice:", text)
        self.assertEqual(game.session.history, [3, 2])

    def test_each_ending_unlocks_its_own_achievement(self):
        for pan, achievement in [
            ("intact", "DELIVERY HERO"),
            ("dented", "LORD OF THE RINSE"),
            ("bread", "BREADWINNER"),
        ]:
            with self.subTest(pan=pan):
                hero = Hero(gold=0, pan=pan)
                self.run_choices(hero, [], lambda h, _: game.arrival(h))
                self.assertEqual(hero.achievements, [achievement])
                self.assertIn(f"Achievement unlocked: {achievement}.", hero.journal)

    def run_choices(self, hero, choices, function):
        game.session = session.Session(hero, choices)
        game.session.validating = True
        with redirect_stdout(StringIO()):
            function(hero, game.choose)
        self.assertEqual(game.session.replay, [])

    def test_rat_rewards_are_once_only(self):
        hero = Hero()
        self.run_choices(hero, [1], rats)
        self.run_choices(hero, [], rats)
        self.assertEqual(hero.gold, 7)
        self.assertEqual(hero.inventory["Rat Recommendation"], 1)

    def test_ghost_can_be_deferred_and_completed(self):
        hero = Hero(companion="Pip")
        self.run_choices(hero, [3], ghost)
        self.assertEqual(hero.quests["Resignation from the afterlife"], "Active")
        self.run_choices(hero, [2], ghost)
        self.run_choices(hero, [], ghost)
        self.assertEqual(hero.gold, 6)
        self.assertIn("Bread Resignation", hero.inventory)

    def test_shop_rejects_unaffordable_and_duplicate_equipment(self):
        hero = Hero()
        self.run_choices(hero, [1, 2, 2, 4], shop)
        self.assertEqual(hero.gold, 0)
        self.assertNotIn("Iron Sword", hero.inventory)
        self.assertEqual(hero.inventory["Pot Lid"], 1)

    def test_sword_and_shield_protect_pan(self):
        for item, slot, move in [("Iron Sword", "Weapon", 3), ("Pot Lid", "Shield", 1)]:
            hero = Hero()
            hero.inventory[item] = 1
            hero.equipment[slot] = item
            self.run_choices(hero, [3, move], lambda h, _: game.bridge(h))
            self.assertEqual(hero.pan, "intact")

    def test_cannot_pay_negative_gold(self):
        hero = Hero(gold=0)
        self.run_choices(hero, [1, 3, 2, 1], lambda h, _: game.bridge(h))
        self.assertEqual(hero.gold, 0)
        self.assertEqual(hero.pan, "dented")

    def test_repair_is_consumed(self):
        hero = Hero(gold=0, pan="dented")
        hero.inventory.update({"Repair Kit": 1, "Demon King's Pan": 1})
        self.run_choices(hero, [], lambda h, _: game.arrival(h))
        self.assertEqual(hero.pan, "intact")
        self.assertEqual(hero.gold, 5)
        self.assertNotIn("Repair Kit", hero.inventory)
        self.assertNotIn("Demon King's Pan", hero.inventory)

    def test_replay_validation_preserves_live_state(self):
        hero = Hero(gold=42)
        original = session.Session(hero)
        game.session = original
        session.validate_replay([3, 1, 2, 1, 3, 2, 4, 5, 2])
        self.assertIs(game.session, original)
        self.assertEqual(hero.gold, 42)
        with self.assertRaises(ValueError):
            session.validate_replay([3, 5])
        self.assertIs(game.session, original)

    def test_save_load_after_rewards_does_not_duplicate_them(self):
        commands = ["3", "1", "2", "1", "3", "2", "4", "5", "2", "save", "load", "quit"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adventure.json"
            with (
                patch.object(session, "SAVE_PATH", path),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(StringIO()),
            ):
                game.main()
            self.assertEqual(game.session.hero.gold, 17)
            self.assertEqual(game.session.hero.achievements, ["DELIVERY HERO"])
            self.assertEqual(game.session.hero.quests["Return the pan"], "Done")
            self.assertEqual(json.loads(path.read_text())["version"], 2)

    def test_save_at_nested_shop_choice(self):
        commands = ["3", "2", "1", "save", "load", "quit"]
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(session, "SAVE_PATH", Path(directory) / "save.json"),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(StringIO()),
            ):
                game.main()
            self.assertEqual(game.session.history, [3, 2, 1])
            self.assertEqual(game.session.hero.gold, 3)


if __name__ == "__main__":
    unittest.main()
