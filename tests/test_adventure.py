"""Regression tests for rewards, purchases, equipment and save replay."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import game, saves, session
from hero_on_probation.models import Hero
from hero_on_probation.town import ghost, rats, shop


class AdventureTests(unittest.TestCase):
    def play_game(self):
        """Exercise the story with a selected character; menus have separate tests."""
        game.run_session(session.Session(Hero(name="Tester"), save_id="a" * 32))

    def test_declining_finishes_without_accepting_or_starting_later_scenes(self):
        for decisions in ([3, 5], [1, 2, 3, 1, 2, 3, 5]):
            with self.subTest(decisions=decisions):
                output = StringIO()
                with (
                    patch(
                        "builtins.input",
                        side_effect=[str(n) for n in decisions] + ["quit"],
                    ),
                    patch.object(game, "meet_companions") as companions,
                    patch.object(game, "explore_town") as town,
                    patch.object(game, "bridge") as bridge,
                    patch.object(game, "arrival") as arrival,
                    redirect_stdout(output),
                ):
                    self.play_game()
                for scene in (companions, town, bridge, arrival):
                    scene.assert_not_called()
                hero = game.session.hero
                self.assertEqual(hero.gold, 3)
                self.assertEqual(hero.companion, "")
                self.assertEqual(hero.inventory, Hero().inventory)
                self.assertEqual(hero.quests, {})
                self.assertEqual(hero.achievements, ["ANY% HERO"])
                self.assertIn("ENDING: CLOCKED OUT", output.getvalue())
                self.assertNotIn("Job accepted:", output.getvalue())

    def test_refusal_save_restores_once_and_keeps_review_commands(self):
        output = StringIO()
        commands = [
            "3",
            "5",
            "save",
            "load",
            "load",
            "status",
            "bag",
            "quests",
            "journal",
            "achievements",
            "quit",
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{'a' * 32}.json"
            with (
                patch.object(saves, "SAVE_DIR", Path(directory)),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(output),
            ):
                self.play_game()
            self.assertEqual(
                json.loads(path.read_text()),
                {
                    "version": 4,
                    "character": {"id": "a" * 32, "name": "Tester"},
                    "choices": [3, 5],
                },
            )
        self.assertEqual(game.session.hero.gold, 3)
        self.assertEqual(game.session.hero.achievements, ["ANY% HERO"])
        self.assertEqual(
            game.session.hero.journal.count("Achievement unlocked: ANY% HERO."), 1
        )
        text = output.getvalue()
        self.assertEqual(text.count("ENDING: CLOCKED OUT"), 1)
        self.assertEqual(text.count("Completed adventure restored."), 2)
        self.assertNotIn("Visit the equipment shop", text)

    def test_refusal_replay_rejects_decisions_after_ending(self):
        original = session.Session(Hero(gold=42))
        game.session = original
        session.validate_replay([3, 5])
        self.assertIs(game.session, original)
        with self.assertRaisesRegex(ValueError, "after the ending"):
            session.validate_replay([3, 5, 1])
        self.assertIs(game.session, original)
        self.assertEqual(original.hero.gold, 42)

    def test_new_opening_reaches_all_three_endings(self):
        for choices, achievement, gold in (
            ([3, 4, 3, 2, 4, 4, 2], "DELIVERY HERO", 8),
            ([3, 4, 3, 2, 4, 3, 1, 2], "LORD OF THE RINSE", 3),
            ([3, 4, 3, 1, 4, 4, 2, 2], "BREADWINNER", 8),
        ):
            with self.subTest(achievement=achievement):
                commands = [str(n) for n in choices] + ["quit"]
                with (
                    patch("builtins.input", side_effect=commands),
                    redirect_stdout(StringIO()),
                ):
                    self.play_game()
                self.assertEqual(game.session.hero.achievements, [achievement])
                self.assertEqual(game.session.hero.gold, gold)

    def test_loading_hides_previous_story_and_keeps_current_menu(self):
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(saves, "SAVE_DIR", Path(directory)),
                patch(
                    "builtins.input",
                    side_effect=["3", "4", "3", "2", "save", "load", "quit"],
                ),
                redirect_stdout(output),
            ):
                self.play_game()
        text = output.getvalue()
        self.assertEqual(text.count("You wake up at a counter."), 1)
        self.assertEqual(text.count("Visit the equipment shop."), 2)
        self.assertNotIn("Restored choice:", text)
        self.assertEqual(game.session.history, [3, 4, 3, 2])

    def test_opening_exploration_is_optional_and_rewards_are_not_repeated(self):
        for choices in (
            [3, 4, 3, 1],
            [1, 1, 2, 2, 3, 1, 1, 2, 3, 4, 1, 1, 2, 2, 3, 1],
        ):
            with self.subTest(choices=choices):
                hero = Hero()
                self.run_choices(hero, choices, lambda h, _: game.guild(h))
                self.assertEqual(hero.gold, 3)
                self.assertEqual(hero.companion, "Pip")
                self.assertEqual(hero.inventory["Demon King's Pan"], 1)
                self.assertNotIn("Bread Resignation", hero.inventory)
                self.assertEqual(hero.pan, "intact")
                self.assertEqual(hero.quests["Return the pan"], "Active")
                self.assertEqual(len(hero.journal), len(set(hero.journal)))

    def test_save_load_at_each_opening_stage(self):
        for decisions, menu in (
            ([1, 2], "Explore the counter"),
            ([3, 1, 2], "Ask about the parcel"),
            ([3, 4, 1, 2], "Meet the volunteers"),
            ([3, 4, 3], "Choose a companion:"),
        ):
            with self.subTest(decisions=decisions):
                output = StringIO()
                commands = [str(n) for n in decisions] + ["save", "load", "quit"]
                with tempfile.TemporaryDirectory() as directory:
                    with (
                        patch.object(saves, "SAVE_DIR", Path(directory)),
                        patch("builtins.input", side_effect=commands),
                        redirect_stdout(output),
                    ):
                        self.play_game()
                self.assertEqual(game.session.history, decisions)
                self.assertEqual(game.session.hero.gold, 3)
                restored = output.getvalue().split("Save loaded.", 1)[1]
                self.assertIn(menu, restored)
                self.assertNotIn("You wake up", restored)
                self.assertEqual(
                    len(game.session.hero.journal), len(set(game.session.hero.journal))
                )

    def test_older_save_is_rejected_without_changing_file_or_live_state(self):
        hero = Hero(gold=42)
        current = session.Session(hero)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{current.save_id}.json"
            old_save = json.dumps({"version": 2, "choices": [3, 1]})
            path.write_text(old_save, encoding="utf-8")
            with patch.object(saves, "SAVE_DIR", Path(directory)):
                with self.assertRaisesRegex(ValueError, "version-4"):
                    current.command("load")
            self.assertEqual(path.read_text(encoding="utf-8"), old_save)
        self.assertEqual(hero.gold, 42)
        self.assertEqual(current.history, [])

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
        session.validate_replay([3, 4, 3, 1, 2, 1, 3, 2, 4, 5, 2])
        self.assertIs(game.session, original)
        self.assertEqual(hero.gold, 42)
        with self.assertRaises(ValueError):
            session.validate_replay([3, 6])
        self.assertIs(game.session, original)

    def test_save_load_after_rewards_does_not_duplicate_them(self):
        commands = [str(n) for n in [3, 4, 3, 1, 2, 1, 3, 2, 4, 5, 2]]
        commands += ["save", "load", "quit"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{'a' * 32}.json"
            with (
                patch.object(saves, "SAVE_DIR", Path(directory)),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(StringIO()),
            ):
                self.play_game()
            self.assertEqual(game.session.hero.gold, 17)
            self.assertEqual(game.session.hero.achievements, ["DELIVERY HERO"])
            self.assertEqual(game.session.hero.quests["Return the pan"], "Done")
            self.assertEqual(json.loads(path.read_text())["version"], 4)

    def test_save_at_nested_shop_choice(self):
        commands = ["3", "4", "3", "2", "1", "save", "load", "quit"]
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(saves, "SAVE_DIR", Path(directory)),
                patch("builtins.input", side_effect=commands),
                redirect_stdout(StringIO()),
            ):
                self.play_game()
            self.assertEqual(game.session.history, [3, 4, 3, 2, 1])
            self.assertEqual(game.session.hero.gold, 3)


if __name__ == "__main__":
    unittest.main()
