"""Battle rules, every ending, replay checkpoints and original-save compatibility."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import combat, game, journey_store, saves, session
from hero_on_probation.models import Hero


def opening(companion=1):
    return [3, 4, 3, companion, 4]


# All routes use ordinary starting resources and keep the certificate money.
ENDINGS = [
    ([3, 5], "CLOCKED OUT", "ANY% HERO", 3),
    (opening(2) + [2, 2, 1], "DELIVERY COMPLETE", "DELIVERY HERO", 8),
    (opening() + [3, 1, 2, 1, 1, 1, 2, 1], "DISH DUTY", "LORD OF THE RINSE", 3),
    (opening() + [3, 3, 2, 1], "ACCIDENTAL CATERING", "BREADWINNER", 8),
    (opening() + [3, 2, 1, 1, 1], "TOLL TAKEN", "SPOON-FED DEFEAT", 3),
    (opening() + [2, 2, 2, 2, 1], "BOSS DEFEAT", "ONE-HIT INTERN", 3),
    (opening(2) + [2, 2, 2, 2, 4], "TACTICAL RETREAT", "CAREER PRESERVATION", 3),
    (opening() + [2, 2, 2, 2, 3], "THE FINAL LOAF", "BREAD OF THE REALM", 3),
]


class CombatTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        replacement = patch.object(saves, "SAVE_DIR", self.root)
        replacement.start()
        self.addCleanup(replacement.stop)

    def play(self, decisions, extra=None):
        output = StringIO()
        commands = [str(n) for n in decisions] + (extra or ["quit"])
        with patch("builtins.input", side_effect=commands), redirect_stdout(output):
            game.run_session(session.Session(Hero(name="Tester"), save_id="c" * 32))
        return output.getvalue()

    def battle(self, hero, enemy, decisions):
        iterator = iter(decisions)
        with redirect_stdout(StringIO()):
            return combat.fight(hero, enemy, lambda *_: next(iterator))

    def test_health_boundaries(self):
        self.assertEqual(combat.take_damage(12, 3), 9)
        self.assertEqual(combat.take_damage(2, 999), 0)
        self.assertEqual(combat.take_damage(12, -4), 12)

    def test_normal_slime_fight_is_four_rounds_and_no_post_victory_attack(self):
        hero = Hero()
        enemy = combat.slime()
        self.assertEqual(self.battle(hero, enemy, [1, 1, 1, 1]), "victory")
        self.assertEqual(enemy.hp, 0)
        self.assertEqual(hero.hp, 3)

    def test_iron_sword_and_shield_improve_real_combat(self):
        hero = Hero()
        hero.equipment.update({"Weapon": "Iron Sword", "Shield": "Pot Lid"})
        self.assertEqual(self.battle(hero, combat.slime(), [1, 1, 1]), "victory")
        self.assertEqual(hero.hp, 7)

    def test_pan_defence_and_pot_lid_have_different_costs(self):
        for shield, expected_pan, expected_hp in [
            (False, "dented", 12),
            (True, "intact", 12),
        ]:
            with self.subTest(shield=shield):
                hero = Hero()
                if shield:
                    hero.equipment["Shield"] = "Pot Lid"
                self.assertEqual(self.battle(hero, combat.slime(), [2, 4]), "retreat")
                self.assertEqual((hero.pan, hero.hp), (expected_pan, expected_hp))

    def test_bea_skill_is_once_only_and_cannot_break_boss_armour(self):
        hero = Hero(companion="Bea")
        enemy = combat.demon_king()
        self.assertEqual(self.battle(hero, enemy, [3, 3, 1]), "defeat")
        self.assertEqual(enemy.hp, 9999)
        self.assertEqual(hero.hp, 0)

    def test_all_ordinary_boss_attacks_and_defences_cannot_win(self):
        for weapon in ("Wooden Sword", "Iron Sword", "None"):
            for shield in (False, True):
                for moves in ([1], [2], [3, 1], [3, 2]):
                    with self.subTest(weapon=weapon, shield=shield, moves=moves):
                        hero = Hero(companion="Bea")
                        hero.equipment["Weapon"] = weapon
                        if shield:
                            hero.equipment["Shield"] = "Pot Lid"
                        enemy = combat.demon_king()
                        self.assertEqual(self.battle(hero, enemy, moves), "defeat")
                        self.assertEqual((enemy.hp, hero.hp), (9999, 0))

    def test_pip_transforms_both_enemy_and_pan_without_retaliation_or_other_costs(self):
        for factory in (combat.slime, combat.demon_king):
            for pan in ("intact", "dented", "bread"):
                enemy = factory()
                with self.subTest(enemy=enemy.name, pan=pan):
                    hero = Hero(companion="Pip", pan=pan, hp=2)
                    hero.inventory.update({"Demon King's Pan": 1, "Repair Kit": 1})
                    original = dict(hero.inventory)
                    self.assertEqual(self.battle(hero, enemy, [3]), "bread")
                    self.assertEqual((hero.hp, hero.gold, hero.pan), (2, 3, "bread"))
                    self.assertEqual(hero.inventory, original)

    def test_all_eight_endings_and_achievements(self):
        for choices, ending, achievement, gold in ENDINGS:
            with self.subTest(ending=ending):
                text = self.play(choices)
                hero = game.session.hero
                self.assertEqual(hero.ending, ending)
                self.assertEqual(hero.gold, gold)
                self.assertIn(achievement, hero.achievements)
                self.assertIn(f"ENDING: {ending}", text)
                self.assertEqual(text.count("ENDING:"), 1)
                self.assertEqual(len(hero.achievements), len(set(hero.achievements)))

    def test_every_ending_survives_repeated_save_load_without_duplicate_rewards(self):
        for choices, ending, achievement, gold in ENDINGS:
            with self.subTest(ending=ending):
                self.play(choices, ["save", "load", "load", "quit"])
                hero = game.session.hero
                self.assertEqual(hero.ending, ending)
                self.assertEqual(hero.gold, gold)
                self.assertEqual(hero.achievements.count(achievement), 1)
                saved = saves.read_save("c" * 32)
                self.assertEqual(saved.rules_version, 2)
                self.assertEqual(saved.choices, choices)
                with self.assertRaisesRegex(ValueError, "after the ending"):
                    session.validate_replay(choices + [1])

    def test_mid_fight_reload_restores_round_enemy_hp_and_player_hp(self):
        decisions = opening(2) + [3, 1]
        text = self.play(decisions, ["save", "load", "quit"])
        self.assertEqual(game.session.hero.hp, 10)
        self.assertEqual(game.session.history, decisions)
        restored = text.split("Save loaded.", 1)[1]
        self.assertIn("ROUND 2 | Tester: 10/12 HP | Bridge Slime: 9/12 HP", restored)
        self.assertNotIn("You deal 3 damage", restored)

    def test_used_companion_skill_is_not_refreshed_by_loading(self):
        text = self.play(opening(2) + [3, 3], ["save", "load", "3", "quit"])
        self.assertEqual(game.session.hero.hp, 12)
        self.assertIn("No companion action available", text)
        self.assertEqual(text.count("Bea deals 5 damage"), 1)
        self.assertIn("Bridge Slime: 7/12 HP", text.split("Save loaded.", 1)[1])

    def test_save_before_boss_magic_can_resume_into_final_loaf(self):
        text = self.play(
            opening() + [2, 2, 2, 2], ["save", "load", "3", "save", "load", "quit"]
        )
        self.assertEqual(game.session.hero.ending, "THE FINAL LOAF")
        self.assertEqual(game.session.hero.pan, "bread")
        self.assertEqual(game.session.hero.hp, 12)
        self.assertEqual(text.count("becomes a very surprised loaf"), 1)

    def test_pip_can_use_magic_at_both_encounters_without_duplicate_achievements(self):
        self.play(opening() + [3, 3, 2, 2, 2, 3], ["save", "load", "quit"])
        self.assertEqual(game.session.hero.ending, "THE FINAL LOAF")
        self.assertEqual(
            game.session.hero.achievements, ["BREAD OVER BRAWN", "BREAD OF THE REALM"]
        )
        self.assertEqual(game.session.hero.gold, 3)

    def test_boss_prompt_shows_danger_but_does_not_reveal_magic_ending(self):
        text = self.play(opening() + [2, 2, 2, 2])
        self.assertIn("Demon King: 9999/9999 HP", text)
        self.assertIn("Enemy defence: 99. Next attack: 999 damage.", text)
        self.assertIn("Ask Pip for help.", text)
        self.assertNotIn("THE FINAL LOAF", text)
        self.assertNotIn("BREAD OF THE REALM", text)
        self.assertNotIn("instant win", text.lower())

    def test_backing_down_at_castle_still_allows_delivery(self):
        self.play(opening(2) + [2, 2, 2, 1])
        self.assertEqual(game.session.hero.ending, "DELIVERY COMPLETE")
        self.assertEqual(game.session.hero.hp, 12)

    def test_retreat_from_bridge_returns_to_other_crossing_options(self):
        self.play(opening(2) + [3, 4, 2, 2, 1])
        self.assertEqual(game.session.hero.ending, "DELIVERY COMPLETE")
        self.assertEqual(game.session.hero.gold, 8)

    def test_repair_kit_does_not_reverse_bread_spell(self):
        hero = Hero(companion="Pip", gold=0)
        hero.inventory["Repair Kit"] = 1
        self.battle(hero, combat.slime(), [3])
        game.session = session.Session(hero, [1])
        game.session.validating = True
        with redirect_stdout(StringIO()):
            game.arrival(hero)
        self.assertEqual(hero.ending, "ACCIDENTAL CATERING")
        self.assertEqual(hero.inventory["Repair Kit"], 1)

    def test_old_version_four_ending_loads_under_original_rules_and_stays_original(
        self,
    ):
        save_id = "d" * 32
        path = saves.save_path(save_id)
        # The last 2 is the certificate choice; old stories end without a boss menu.
        old_choices = opening(2) + [4, 2]
        path.write_text(
            json.dumps(
                {
                    "version": 4,
                    "character": {"id": save_id, "name": "Old Hero"},
                    "choices": old_choices,
                }
            )
        )
        before = path.read_bytes()
        saved = saves.read_save(save_id)
        self.assertEqual(saved.rules_version, 1)
        output = StringIO()
        with (
            patch("builtins.input", side_effect=["2", "1", "quit"]),
            redirect_stdout(output),
        ):
            game.main()
        upgraded = journey_store.load(save_id)
        self.assertEqual(
            (upgraded.name, upgraded.gold, upgraded.run), ("Old Hero", 8, 2)
        )
        self.assertIn("DELIVERY HERO", upgraded.achievements)
        self.assertEqual(path.read_bytes(), before)
        self.assertIn("Last ending: DELIVERY COMPLETE", output.getvalue())
        self.assertNotIn("The dragon sets the table", output.getvalue())
        self.assertEqual(saves.read_save(save_id).rules_version, 1)
        self.assertEqual(json.loads(path.read_text())["version"], 4)

    def test_unknown_rule_version_is_rejected(self):
        saved = saves.SavedGame("e" * 32, "Future", [], 999)
        with self.assertRaises(ValueError):
            saves.write_save(saved)


if __name__ == "__main__":
    unittest.main()
