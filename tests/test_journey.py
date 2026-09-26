"""Continuing journeys, persistence, reward boundaries and Hall of Fame."""

import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import game, menu, saves
from hero_on_probation import journey_store as store
from hero_on_probation.journey import ENDINGS, JOBS, Journey
from hero_on_probation.journey_cli import run


class JourneyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        replacement = patch.object(saves, "SAVE_DIR", self.root)
        replacement.start()
        self.addCleanup(replacement.stop)
        capture = redirect_stdout(StringIO())
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)

    def make(self, name="Mira"):
        return store.create(name)

    def act(self, state, *choices):
        for action in choices:
            candidate = copy.deepcopy(state)
            candidate.act(action)
            state = store.commit(candidate)
        return state

    def castle(self, state, companion=1):
        # Guild, accept, companion, skip town, help guard, approach door.
        return self.act(state, 3, 4, companion, 4, 2, 2)

    def test_new_menu_creates_journey_and_invalid_names_are_retried(self):
        with patch(
            "builtins.input",
            side_effect=["1", "", "x" * 25, "Mira", "status", "bag", "back", "quit"],
        ):
            game.main()
        states = store.list_journeys()
        self.assertEqual(len(states), 1)
        self.assertEqual(
            (states[0].name, states[0].stage, states[0].revision), ("Mira", "guild", 0)
        )

    def test_new_characters_are_isolated_and_names_are_case_insensitive(self):
        first, second = self.make(), self.make("Ada")
        first = self.act(first, 3)
        self.assertEqual(store.load(second.save_id).stage, "guild")
        with self.assertRaises(ValueError):
            self.make("mIRA")
        self.assertEqual(store.load(first.save_id).stage, "parcel")

    def test_legacy_and_journey_character_names_cannot_collide(self):
        saves.write_save(saves.SavedGame("a" * 32, "Old", []))
        with self.assertRaises(ValueError):
            self.make("old")
        self.make("New")
        with patch("builtins.input", side_effect=["NEW", "Different"]):
            self.assertEqual(menu.new_character_name(), "Different")

    def test_endings_have_distinct_achievements_and_first_bonus_once(self):
        for ending, (title, _, _) in ENDINGS.items():
            with self.subTest(ending=ending):
                state = Journey("a" * 32, "Test")
                state.finish(ending)
                before = state.data()
                state.finish(ending)
                self.assertEqual(state.data(), before)
                self.assertIn(title, state.achievements)
                self.assertEqual(state.stage, "ending")
        self.assertEqual(len({r[0] for r in ENDINGS.values()}), len(ENDINGS))

    def test_all_real_ending_routes_settle(self):
        routes = {
            "CLOCKED OUT": [3, 5],
            "DELIVERY COMPLETE": [3, 4, 2, 4, 2, 2, 1],
            "DISH DUTY": [3, 4, 2, 4, 3, 2, 4, 2, 2, 1],
            "ACCIDENTAL CATERING": [3, 4, 1, 4, 4, 2, 1],
            "TOLL TAKEN": [3, 4, 1, 4, 3, 2, 1, 1, 1],
            "BOSS DEFEAT": [3, 4, 2, 4, 2, 2, 2, 2, 1],
            "TACTICAL RETREAT": [3, 4, 2, 4, 2, 2, 2, 2, 4],
            "THE FINAL LOAF": [3, 4, 1, 4, 2, 2, 2, 2, 3],
        }
        for index, (ending, choices) in enumerate(routes.items()):
            with self.subTest(ending=ending):
                state = self.act(self.make(str(index)), *choices)
                self.assertEqual(state.ending, ending)
                self.assertEqual(store.load(state.save_id).data(), state.data())

    def test_next_journey_keeps_growth_money_gear_but_resets_tasks_and_health(self):
        state = self.make()
        state.inventory.update(
            {"Iron Sword": 1, "Pot Lid": 1, "Repair Kit": 2, "Ghost Reference": 1}
        )
        state.equipment.update({"Weapon": "Iron Sword", "Shield": "Pot Lid"})
        state.reward("test", 1000)
        state = store.commit(state)
        state = self.castle(state)
        state = self.act(state, 1)
        permanent = (
            state.level,
            state.xp,
            state.gold,
            dict(state.equipment),
            copy.deepcopy(state.achievements),
        )
        state = self.act(state, 1)
        self.assertEqual(
            (state.level, state.xp, state.gold, state.equipment, state.achievements),
            permanent,
        )
        self.assertEqual((state.run, state.stage, state.hp), (2, "guild", state.max_hp))
        self.assertNotIn("Ghost Reference", state.inventory)
        self.assertEqual(state.inventory["Repair Kit"], 2)
        self.assertEqual((state.quests, state.flags, state.rewards), ({}, [], []))
        self.assertEqual(state.job, JOBS[1])

    def test_jobs_cycle_without_resetting_progress(self):
        state = Journey("a" * 32, "Mira")
        for index in range(7):
            self.assertEqual(state.job, JOBS[index % 3])
            state.finish("DELIVERY COMPLETE")
            state.next_run()
        self.assertGreater(state.level, 1)

    def test_refusal_cannot_farm_xp_or_unlock_second_journey(self):
        state = self.act(self.make(), 3, 5)
        for _ in range(5):
            state = self.act(state, 1, 3, 5)
        self.assertEqual((state.level, state.xp, state.run), (1, 20, 1))
        self.assertEqual(state.achievements["ANY% HERO"]["count"], 1)

    def test_bread_boss_first_bonus_is_large_and_cannot_be_farmed_by_load(self):
        state = self.act(self.castle(self.make()), 2, 2, 3)
        self.assertEqual(state.level, 5)
        record = copy.deepcopy(state.achievements["BREAD OF THE REALM"])
        for _ in range(3):
            state = store.load(state.save_id)
            self.assertEqual(state.achievements["BREAD OF THE REALM"], record)
            self.assertEqual(state.level, 5)
        self.assertEqual(len(store.honours()), 1)
        state = self.act(state, 1)
        old_total = 50 * state.level * (state.level - 1) + state.xp
        state = self.act(self.castle(state), 2, 2, 3)
        total = 50 * state.level * (state.level - 1) + state.xp
        self.assertEqual(
            total - old_total, 230
        )  # 150 boss + 80 ending; not another 1000.
        self.assertEqual(state.achievements["BREAD OF THE REALM"]["count"], 2)
        self.assertEqual(
            state.achievements["BREAD OF THE REALM"]["first_at"], record["first_at"]
        )

    def test_level_one_loses_boss_but_level_eight_can_win_without_magic(self):
        low = self.act(self.castle(self.make("Low"), 2), 2, 2, 1)
        self.assertEqual((low.ending, low.hp), ("BOSS DEFEAT", 0))
        high = self.make("High")
        high.reward("training", 2800)
        high.hp = high.max_hp
        high = store.commit(high)
        high = self.act(self.castle(high, 2), 2, 2)
        for _ in range(20):
            if high.stage == "ending":
                break
            high = self.act(high, 1)
        self.assertEqual(high.ending, "HONEST VICTORY")
        self.assertIn("EARNED THE HARD WAY", high.achievements)
        self.assertEqual(high.gold, 11)

    def test_mid_battle_load_preserves_both_healths_turn_and_bea_usage(self):
        state = self.act(self.make(), 3, 4, 2, 4, 3, 3)
        loaded = store.load(state.save_id)
        self.assertEqual(loaded.battle, state.battle)
        self.assertEqual(loaded.battle["hp"], 7)
        self.assertEqual(loaded.battle["turn"], 2)
        with self.assertRaises(ValueError):
            self.act(loaded, 3)
        self.assertNotIn(3, dict(loaded.available_options()))
        self.assertEqual(state.battle, loaded.battle)
        self.assertEqual(state.hp, 12)

    def test_wager_is_locked_first_journey_then_stake_persists_and_pip_is_disabled(
        self,
    ):
        state = self.make()
        state.gold = 20
        state.stage = "shop"
        self.assertEqual(len(state.view()[1]), 4)
        state.wager("shop")
        self.assertEqual(state.gold, 20)
        state.run = 2
        state.companion = "Pip"
        state = store.commit(state)
        state = self.act(state, 5)
        self.assertEqual(state.gold, 15)
        loaded = store.load(state.save_id)
        state = self.act(loaded, 3)
        self.assertEqual(
            (state.gold, state.hp, state.battle), (15, loaded.hp, loaded.battle)
        )
        self.assertEqual(state.parcel, "intact")
        state = self.act(state, 4)
        self.assertEqual(
            (state.gold, state.stage, state.hp), (15, "shop", state.max_hp)
        )
        with self.assertRaises(ValueError):
            self.act(state, 5)
        self.assertNotIn(5, dict(state.available_options()))
        self.assertEqual((state.gold, state.stage), (15, "shop"))

    def test_both_merchants_award_exactly_one_payout_and_remain_open(self):
        for merchant, action in (("shop", 5), ("certificate", 3)):
            with self.subTest(merchant=merchant):
                state = self.make(merchant)
                state.run, state.stage, state.gold, state.companion = (
                    2,
                    merchant,
                    10,
                    "Bea",
                )
                state.reward("training", 2800)
                state = store.commit(state)
                state = self.act(state, action, 1)
                self.assertEqual((state.stage, state.gold), (merchant, 15))
                self.assertEqual(state.hp, state.max_hp)
                state = store.load(state.save_id)
                with self.assertRaises(ValueError):
                    self.act(state, action)
                self.assertNotIn(action, dict(state.available_options()))
                self.assertEqual(state.gold, 15)

    def test_losing_wager_costs_only_stake_and_does_not_end_adventure(self):
        state = self.make()
        state.run, state.stage, state.gold, state.companion = 2, "shop", 5, "Bea"
        state = store.commit(state)
        state = self.act(state, 5, 1, 1)
        self.assertEqual((state.gold, state.stage, state.hp), (0, "shop", 12))
        self.assertFalse(state.ending)
        self.assertFalse(state.achievements)
        self.assertEqual(state.xp, 0)

    def test_insufficient_gold_does_not_begin_wager_or_bribe(self):
        state = self.make()
        state.run, state.stage, state.companion = 2, "shop", "Pip"
        state = store.commit(state)
        state = self.act(state, 5)
        self.assertEqual((state.gold, state.stage, state.flags), (3, "shop", []))
        state.stage = "castle"
        state = store.commit(state)
        state = self.act(state, 3)
        self.assertEqual((state.gold, state.stage), (3, "castle"))

    def test_bribery_unlocks_second_journey_and_never_pays_delivery_or_boss_xp(self):
        state = self.castle(self.make())
        self.assertEqual(len(state.view()[1]), 2)
        state.run, state.gold = 2, 40
        state = store.commit(state)
        state = self.act(state, 3)
        self.assertEqual((state.ending, state.gold), ("PAID PERFORMANCE", 26))
        self.assertEqual((state.level, state.xp), (2, 0))  # First achievement only.
        self.assertNotIn("battle:boss", state.rewards)
        state = self.act(state, 1)
        state.stage, state.gold = "castle", 40
        state = store.commit(state)
        state = self.act(state, 3)
        self.assertEqual((state.level, state.xp, state.gold), (2, 0, 24))

    def test_failed_hero_stays_at_zero_until_starting_next_journey(self):
        state = self.act(self.castle(self.make(), 2), 2, 2, 1)
        self.assertEqual(state.hp, 0)
        self.assertGreater(state.level, 1)
        state = self.act(state, 1)
        self.assertEqual(state.hp, state.max_hp)

    def test_repair_kit_repairs_damage_but_cannot_reverse_bread(self):
        for parcel in ("damaged", "bread"):
            state = self.castle(self.make(parcel))
            state.parcel = parcel
            state.inventory["Repair Kit"] = 1
            state = store.commit(state)
            state = self.act(state, 1)
            if parcel == "bread":
                self.assertEqual(state.ending, "ACCIDENTAL CATERING")
                self.assertEqual(state.inventory["Repair Kit"], 1)
            else:
                self.assertEqual(state.ending, "DELIVERY COMPLETE")
                self.assertNotIn("Repair Kit", state.inventory)

    def test_hall_records_time_identity_and_survives_delete_restore(self):
        first = self.act(self.make("Ada"), 3, 5)
        self.act(self.make("Mira"), 3, 5)
        before = store.honours()
        self.assertEqual(len(before), 2)
        self.assertIsNotNone(before[0]["record"]["first_at"])
        store.archive(first.save_id)
        self.assertEqual(len(store.list_journeys()), 1)
        records = store.honours()
        archived = next(r for r in records if r["character_id"] == first.save_id)
        self.assertEqual(archived["deleted"], 1)
        self.assertEqual(archived["name"], "Ada")
        store.restore(first.save_id)
        self.assertEqual(len(store.list_journeys()), 2)
        self.assertEqual(store.honours(), before)

    def test_archive_rejects_stale_writer_and_restore_never_overwrites_same_name(self):
        state = self.make()
        store.archive(state.save_id)
        with self.assertRaises(ValueError):
            store.commit(state)
        self.make()
        with self.assertRaises(ValueError):
            store.restore(state.save_id)

    def test_concurrent_snapshots_cannot_overwrite_newer_rewards(self):
        state = self.make()
        stale = copy.deepcopy(state)
        state = self.act(state, 3, 5)
        with self.assertRaises(ValueError):
            store.commit(stale)
        self.assertEqual(store.load(state.save_id).data(), state.data())
        self.assertEqual(len(store.honours()), 1)

    def test_hall_write_failure_rolls_back_character_and_rewards_together(self):
        state = self.act(self.make(), 3)
        candidate = copy.deepcopy(state)
        candidate.act(5)
        with patch.object(
            store, "write_honours", side_effect=sqlite3.OperationalError("disk full")
        ):
            with self.assertRaises(sqlite3.Error):
                store.commit(candidate)
        self.assertEqual(store.load(state.save_id).data(), state.data())
        self.assertEqual(store.honours(), [])

    def test_bag_back_and_load_do_not_change_revision_or_repeat_rewards(self):
        state = self.act(self.make(), 3, 5)
        with patch(
            "builtins.input",
            side_effect=["bag", "back", "", "load", "save", "hall", "quit"],
        ):
            run(state)
        self.assertEqual(store.load(state.save_id).data(), state.data())
        self.assertEqual(len(store.honours()), 1)

    def test_menu_save_load_delete_restore_and_hall_integration(self):
        with patch(
            "builtins.input",
            side_effect=[
                "1",
                "Mira",
                "3",
                "5",
                "menu",
                "3",
                "2",
                "1",
                "menu",
                "4",
                "1",
                "1",
                "DELETE",
                "0",
                "3",
                "4",
                "2",
                "1",
                "0",
                "2",
                "1",
                "quit",
            ],
        ):
            game.main()
        state = store.list_journeys()[0]
        self.assertEqual(state.ending, "CLOCKED OUT")
        self.assertEqual(store.honours()[0]["deleted"], 0)

    def test_completed_classic_copy_preserves_equipment_money_source_and_unknown_dates(
        self,
    ):
        saved = saves.SavedGame("a" * 32, "Classic", [3, 5], 2)
        saves.write_save(saved)
        before = saves.save_path(saved.save_id).read_bytes()
        with patch("builtins.input", side_effect=["2", "1", "quit"]):
            game.main()
        state = store.list_journeys()[0]
        self.assertEqual((state.save_id, state.name), (saved.save_id, saved.name))
        self.assertEqual((state.gold, state.level, state.xp), (3, 1, 0))
        self.assertIsNone(state.achievements["ANY% HERO"]["first_at"])
        self.assertEqual(saves.save_path(saved.save_id).read_bytes(), before)
        self.assertIsNone(store.honours()[0]["record"]["first_at"])

    def test_unfinished_classic_copy_is_rejected_without_creating_new_save(self):
        saved = saves.SavedGame("a" * 32, "Classic", [3], 2)
        saves.write_save(saved)
        with self.assertRaises(ValueError):
            menu.completed_classic_hero(saved)
        self.assertEqual(store.list_journeys(), [])

    def test_corrupt_and_future_states_are_rejected_not_reset(self):
        state = self.make()
        for key, value in (
            ("gold", -1),
            ("level", True),
            ("hp", 99),
            ("stage", "nowhere"),
            ("inventory", []),
            ("xp", 100),
            ("battle", {}),
        ):
            with self.subTest(key=key):
                data = state.data()
                data[key] = value
                with self.assertRaises(ValueError):
                    Journey.from_data(data)
        with store.database() as db, db:
            db.execute("UPDATE characters SET version=999 WHERE id=?", (state.save_id,))
        with self.assertRaises(ValueError):
            store.load(state.save_id)
        self.assertEqual(store.list_journeys(), [])

    def test_database_identity_mismatch_is_rejected(self):
        state = self.make()
        data = state.data()
        data["save_id"] = "a" * 32
        with store.database() as db, db:
            db.execute(
                "UPDATE characters SET state=? WHERE id=?",
                (json.dumps(data), state.save_id),
            )
        with self.assertRaises(ValueError):
            store.load(state.save_id)

    def test_real_module_launch_can_finish_continue_reload_and_show_hall(self):
        commands = "\n".join(
            [
                "1",
                "CLI Hero",
                "3",
                "4",
                "1",
                "4",
                "2",
                "2",
                "2",
                "2",
                "3",
                "1",
                "menu",
                "3",
                "2",
                "1",
                "quit",
                "",
            ]
        )
        result = subprocess.run(
            [sys.executable, "-m", "hero_on_probation"],
            input=commands,
            text=True,
            capture_output=True,
            cwd=self.root,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in (
            "ENDING: THE FINAL LOAF",
            "LEVEL UP: 2 -> 5",
            "Curtain Call",
            "HALL OF FAME",
            "BREAD OF THE REALM",
            "Journey 2",
        ):
            self.assertIn(expected, result.stdout)
        self.assertNotIn("Could not complete action", result.stdout)
        self.assertNotIn("Choose a displayed number", result.stdout)
        with patch.object(saves, "SAVE_DIR", self.root / "saves"):
            saved = store.list_journeys()[0]
            self.assertEqual((saved.level, saved.run, saved.stage), (5, 2, "guild"))

    def test_readonly_rendering_and_information_do_not_grant_xp(self):
        state = self.act(self.make(), 3, 4, 1, 4, 3)
        before = state.data()
        for _ in range(10):
            state.view()
            state.status()
        self.assertEqual(state.data(), before)

    def test_side_quests_and_castle_bonus_cannot_repeat_within_journey(self):
        state = self.act(self.make(), 3, 4, 2, 2, 1)
        with self.assertRaises(ValueError):
            self.act(state, 2)
        state = self.act(state, 3, 1)
        with self.assertRaises(ValueError):
            self.act(state, 3)
        self.assertEqual(state.gold, 10)  # 3 initial + 4 rats + 3 ghost.
        state = self.act(state, 4, 2, 2)
        self.assertEqual(state.gold, 12)
        self.assertEqual(store.load(state.save_id).gold, 12)

    def test_imported_equipment_and_money_are_retained_without_old_quest_items(self):
        from hero_on_probation.models import Hero

        hero = Hero(gold=42, ending="DELIVERY COMPLETE")
        hero.inventory.update(
            {"Iron Sword": 1, "Pot Lid": 1, "Repair Kit": 2, "Ghost Reference": 1}
        )
        hero.equipment.update({"Weapon": "Iron Sword", "Shield": "Pot Lid"})
        state = store.create("Copy", hero)
        self.assertEqual((state.gold, state.inventory["Repair Kit"]), (42, 2))
        self.assertEqual(state.equipment, hero.equipment)
        self.assertNotIn("Ghost Reference", state.inventory)

    def test_failed_menu_creation_and_information_views_do_not_create_phantom_honours(
        self,
    ):
        with patch("builtins.input", side_effect=["1", "0", "3", "5"]):
            game.main()
        self.assertEqual(store.list_journeys(), [])
        self.assertEqual(store.honours(), [])


if __name__ == "__main__":
    unittest.main()
