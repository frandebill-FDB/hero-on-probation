"""Fast replay, voluntary defeats and spoiler-safe collection records."""

import copy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import journey_store as store
from hero_on_probation import menu, saves
from hero_on_probation.collection import HINTS, show_collection
from hero_on_probation.journey import ENDINGS, Journey
from hero_on_probation.journey_cli import run


class CollectionPlayTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        replacement = patch.object(saves, "SAVE_DIR", Path(directory.name))
        replacement.start()
        self.addCleanup(replacement.stop)
        capture = redirect_stdout(StringIO())
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)

    def act(self, state, *choices):
        for choice in choices:
            candidate = copy.deepcopy(state)
            candidate.act(choice)
            state = store.commit(candidate)
        return state

    def second_journey(self):
        state = store.create("Mira")
        # Play the real first journey, including the bread-boss jackpot.
        return self.act(state, 3, 4, 1, 4, 2, 2, 2, 2, 3, 1)

    def test_express_retains_companion_and_skips_without_granting_rewards(self):
        state = self.second_journey()
        self.assertEqual(
            (state.run, state.stage, state.companion), (2, "dispatch", "Pip")
        )
        before = (state.gold, state.xp, state.level, copy.deepcopy(state.achievements))
        state = self.act(state, 1)
        self.assertEqual(state.stage, "castle")
        self.assertEqual(
            (state.gold, state.xp, state.level, state.achievements), before
        )
        self.assertEqual(state.quests, {"Delivery": "Active"})
        self.assertEqual(state.rewards, [])
        self.assertNotIn("Rat Recommendation", state.inventory)
        self.assertNotIn("Ghost Reference", state.inventory)

    def test_change_companion_then_express_delivery(self):
        state = self.act(self.second_journey(), 5)
        self.assertEqual(store.load(state.save_id).stage, "travel_companion")
        state = self.act(store.load(state.save_id), 2, 1, 1)
        self.assertEqual((state.companion, state.ending), ("Bea", "DELIVERY COMPLETE"))

    def test_full_route_and_refusal_remain_available(self):
        state = self.act(self.second_journey(), 6)
        self.assertEqual((state.stage, state.companion), ("guild", ""))
        state = self.act(state, 3, 5)
        self.assertEqual(state.ending, "CLOCKED OUT")
        state = self.act(state, 1)
        self.assertEqual((state.run, state.stage), (2, "dispatch"))
        self.assertEqual(set(dict(state.available_options())), {5, 6})
        state = self.act(state, 5, 1, 1)
        self.assertEqual(state.stage, "castle")

    def test_route_destinations_are_available_without_restarting_intro(self):
        original = self.second_journey()
        for choice, stage in (
            (1, "castle"),
            (2, "town"),
            (3, "bridge"),
            (4, "certificate"),
        ):
            state = copy.deepcopy(original)
            state.act(choice)
            self.assertEqual(state.stage, stage)
            state.travel()
            self.assertEqual(state.stage, "dispatch")
            self.assertNotIn(6, dict(state.available_options()))
            with self.assertRaises(ValueError):
                state.act(6)

    def test_revisiting_town_does_not_reset_rewards_or_owned_items(self):
        state = self.act(self.second_journey(), 2, 2, 1, 3, 1)
        state.travel()
        state = store.commit(state)
        gold = state.gold
        state = self.act(state, 2)
        self.assertEqual(set(dict(state.available_options())), {1, 4})
        self.assertEqual(state.gold, gold)
        self.assertIn("Ghost Reference", state.inventory)

    def test_earned_ghost_bonus_pays_once_across_both_routes(self):
        state = self.act(self.second_journey(), 2, 3, 1)
        before = state.gold
        state.travel()
        state = self.act(store.commit(state), 1)
        self.assertEqual(state.gold, before + 2)
        state.travel()
        state = self.act(store.commit(state), 4, 2)
        self.assertEqual(state.gold, before + 2)

    def test_travel_cannot_escape_fights_or_reopen_endings(self):
        state = self.act(self.second_journey(), 1, 2, 2)
        for expected in ("battle", "ending"):
            before = state.data()
            with self.assertRaises(ValueError):
                state.travel()
            self.assertEqual(state.data(), before)
            self.assertEqual(state.stage, expected)
            if expected == "battle":
                state = self.act(state, 5)

    def test_first_journey_has_no_express_escape(self):
        state = store.create("First")
        with self.assertRaises(ValueError):
            state.travel()
        state = self.act(state, 3, 5, 1)
        self.assertEqual((state.run, state.stage), (1, "guild"))

    def test_old_snapshot_fields_and_new_route_survive_loading(self):
        old = store.create("Old")
        self.assertEqual(Journey.from_data(old.data()).stage, "guild")
        state = self.second_journey()
        self.assertEqual(set(old.data()), set(state.data()))
        self.assertEqual(store.load(state.save_id).data(), state.data())

    def test_high_level_concession_unlocks_both_failure_endings(self):
        for kind, ending in (("bridge", "TOLL TAKEN"), ("boss", "BOSS DEFEAT")):
            state = store.create(kind)
            state.level, state.hp, state.companion = 50, 404, "Pip"
            state.begin_battle(kind)
            state = store.commit(state)
            state = self.act(state, 5)
            self.assertEqual((state.ending, state.hp), (ending, 0))
            self.assertNotIn("battle:" + kind, state.rewards)
            self.assertEqual(state.gold, 3)
            self.assertEqual(state.xp, 110)  # Defeat + first ending, not victory XP.
            saved = store.load(state.save_id)
            self.assertEqual(saved.data(), state.data())
            saved.finish(ending)
            self.assertEqual(saved.data(), state.data())

    def test_merchant_concession_forfeits_stake_without_any_reward(self):
        for merchant in ("shop", "certificate"):
            state = store.create(merchant)
            state.run, state.gold, state.companion = 2, 10, "Pip"
            state.wager(merchant)
            state = self.act(store.commit(state), 5)
            self.assertEqual(
                (state.stage, state.gold, state.hp), (merchant, 5, state.max_hp)
            )
            self.assertEqual((state.xp, state.achievements, state.rewards), (0, {}, []))
            self.assertIn("wager:" + merchant, state.flags)
            state.wager(merchant)
            self.assertEqual(state.gold, 5)

    def test_retreat_remains_distinct_from_concession(self):
        state = self.act(self.second_journey(), 1, 2, 2, 4)
        self.assertEqual(state.ending, "TACTICAL RETREAT")
        self.assertGreater(state.hp, 0)

    def test_collection_counts_unique_endings_not_bonus_achievements(self):
        output = StringIO()
        with redirect_stdout(output):
            show_collection(["DELIVERY HERO", "DELIVERY HERO", "BREAD OVER BRAWN"])
        text = output.getvalue()
        self.assertIn("1/10", text)
        self.assertIn("DELIVERY COMPLETE", text)
        self.assertNotIn("THE FINAL LOAF", text)
        self.assertEqual(text.count("???"), 9)

    def test_hints_are_opt_in_and_do_not_reveal_hidden_titles(self):
        self.assertEqual(set(HINTS), set(ENDINGS))
        normal, hinted = StringIO(), StringIO()
        with redirect_stdout(normal):
            show_collection([])
        with redirect_stdout(hinted):
            show_collection([], show_hints=True)
        self.assertNotIn("Hint:", normal.getvalue())
        self.assertEqual(hinted.getvalue().count("Hint:"), 10)
        self.assertNotIn("THE FINAL LOAF", hinted.getvalue())
        self.assertIn("0/10", hinted.getvalue())

    def test_full_collection_has_no_locked_rows_and_no_extra_ending(self):
        output = StringIO()
        with redirect_stdout(output):
            show_collection([value[0] for value in ENDINGS.values()], True)
        self.assertIn("10/10", output.getvalue())
        self.assertNotIn("???", output.getvalue())
        self.assertNotIn("Hint:", output.getvalue())

    def test_hall_keeps_character_identity_time_and_archived_records(self):
        state = self.second_journey()
        second = store.create("Ada")
        second.finish("THE FINAL LOAF")
        store.commit(second)
        store.archive(state.save_id)
        before = store.honours()
        output = StringIO()
        with redirect_stdout(output):
            store.show_honours()
        text = output.getvalue()
        self.assertIn("1/10", text)
        self.assertIn(state.save_id, text)
        self.assertIn("Mira", text)
        self.assertIn("Ada", text)
        self.assertIn("save deleted; record retained", text)
        self.assertIn(state.achievements["BREAD OF THE REALM"]["first_at"], text)
        self.assertEqual(store.honours(), before)

    def test_main_menu_and_in_game_hints_do_not_change_progress(self):
        state = self.second_journey()
        before = state.data()
        with patch("builtins.input", side_effect=["hints", "5"]):
            self.assertIsNone(menu.start_menu())
        with patch("builtins.input", side_effect=["hall", "hints", "quit"]):
            run(state)
        self.assertEqual(store.load(state.save_id).data(), before)

    def test_cli_travel_and_concession_persist_across_restart(self):
        state = self.second_journey()
        with patch("builtins.input", side_effect=["1", "travel", "3", "3", "quit"]):
            run(state)
        saved = store.load(state.save_id)
        self.assertEqual(saved.battle["kind"], "bridge")
        with patch("builtins.input", side_effect=["travel", "5", "load", "quit"]):
            run(saved)
        final = store.load(state.save_id)
        self.assertEqual(final.ending, "TOLL TAKEN")
        self.assertEqual(final.achievements["SPOON-FED DEFEAT"]["count"], 1)

    def test_actual_module_express_second_ending_and_collection(self):
        commands = "\n".join(
            [
                "1",
                "CLI",
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
                "1",
                "2",
                "2",
                "5",
                "menu",
                "3",
                "hints",
                "5",
                "",
            ]
        )
        result = subprocess.run(
            [sys.executable, "-m", "hero_on_probation"],
            input=commands,
            text=True,
            capture_output=True,
            cwd=saves.SAVE_DIR,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in (
            "ENDING: THE FINAL LOAF",
            "ENDING: BOSS DEFEAT",
            "Travel desk",
            "Ending collection: 2/10",
            "Hint:",
        ):
            self.assertIn(expected, result.stdout)
        self.assertNotIn("Could not complete action", result.stdout)
        self.assertNotIn("Choose a displayed number", result.stdout)

    def test_parcel_wording_handles_all_jobs_without_changing_state(self):
        for run_number in (1, 2, 3):
            state = Journey("a" * 32, "Mira", run=run_number, stage="dispatch")
            before = state.data()
            prompt, _ = state.view()
            self.assertIn(f"deliver {state.job[1]}'s {state.job[2]}", prompt)
            self.assertNotIn("wants one", prompt)
            self.assertEqual(state.data(), before)
            state.stage = "parcel"
            before = state.data()
            output = StringIO()
            with redirect_stdout(output):
                state.act(1)
            self.assertIn(f"Contents: {state.job[2]}.", output.getvalue())
            self.assertEqual(state.data(), before)
