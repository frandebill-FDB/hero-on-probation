"""Consumed choices disappear without renumbering or changing saved progress."""

import copy
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hero_on_probation import journey_store as store
from hero_on_probation import saves
from hero_on_probation.journey import Journey
from hero_on_probation.journey_cli import run


class AvailableOptionsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        replacement = patch.object(saves, "SAVE_DIR", Path(directory.name))
        replacement.start()
        self.addCleanup(replacement.stop)
        capture = redirect_stdout(StringIO())
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)

    def make(self, stage="certificate", gold=20, run_number=1):
        state = store.create("Mira")
        state.stage, state.gold, state.run = stage, gold, run_number
        return store.commit(state)

    def act(self, state, action):
        updated = copy.deepcopy(state)
        updated.act(action)
        return store.commit(updated)

    def test_certificate_purchase_disappears_after_success_and_after_load(self):
        state = self.act(self.make(), 1)
        self.assertEqual(state.gold, 17)
        self.assertEqual(dict(state.available_options()), {2: "Go to the boss's door."})
        loaded = store.load(state.save_id)
        self.assertEqual(loaded.available_options(), state.available_options())
        self.assertEqual(len(loaded.view()[1]), 1)

    def test_failed_purchase_stays_available_and_does_not_mark_as_used(self):
        state = self.make(gold=2)
        before = state.available_options()
        state = self.act(state, 1)
        self.assertEqual(state.available_options(), before)
        self.assertNotIn("certificate", state.flags)
        self.assertEqual(state.gold, 2)

    def test_owned_equipment_disappears_but_repair_kits_remain_repeatable(self):
        state = self.make("shop")
        state = self.act(state, 1)
        self.assertEqual(set(dict(state.available_options())), {2, 3, 4})
        state = self.act(state, 2)
        self.assertEqual(set(dict(state.available_options())), {3, 4})
        state = self.act(state, 3)
        state = self.act(state, 3)
        self.assertEqual(state.inventory["Repair Kit"], 2)
        self.assertEqual(state.gold, 8)
        state = self.act(state, 4)
        self.assertEqual(state.stage, "town")

    def test_certificate_and_wager_both_hide_with_exit_number_unchanged(self):
        state = self.make(run_number=2)
        state.companion = "Pip"
        state = self.act(state, 1)
        self.assertEqual(set(dict(state.available_options())), {2, 3})
        state = self.act(state, 3)
        state = self.act(state, 4)
        self.assertEqual(set(dict(state.available_options())), {2})
        state = self.act(state, 2)
        self.assertEqual(state.stage, "castle")
        self.assertEqual(state.gold, 12)

    def test_completed_quests_hide_their_town_entries_and_reward_choices(self):
        state = self.make("town")
        state = self.act(state, 2)
        state = self.act(state, 1)
        self.assertNotIn(2, dict(state.available_options()))
        state = self.act(state, 3)
        state = self.act(state, 1)
        self.assertEqual(set(dict(state.available_options())), {1, 4})
        # Older snapshots inside a completed quest remain safe and have an exit.
        for stage in ("rats", "ghost"):
            state.stage = stage
            self.assertEqual(dict(state.available_options()), {3: "Return to town."})
            self.assertIn("complete", state.view()[0])

    def test_used_bea_skill_hides_without_renumbering_retreat_or_spending_turns(self):
        state = self.make("bridge")
        state.companion = "Bea"
        state = self.act(state, 3)
        state = self.act(state, 3)
        self.assertEqual(set(dict(state.available_options())), {1, 2, 4, 5})
        loaded = store.load(state.save_id)
        before = loaded.data()
        with self.assertRaises(ValueError):
            loaded.act(3)
        self.assertEqual(loaded.data(), before)
        loaded = self.act(loaded, 4)
        self.assertEqual(loaded.stage, "bridge")

    def test_next_journey_restores_per_journey_choices_not_owned_equipment(self):
        state = self.make("shop", run_number=2)
        state = self.act(state, 1)
        state.flags.extend(
            ["certificate", "wager:shop", "wager:certificate", "rats", "ghost"]
        )
        state.finish("DELIVERY COMPLETE")
        state.next_run()
        state.stage = "shop"
        self.assertEqual(set(dict(state.available_options())), {2, 3, 4, 5})
        state.stage = "certificate"
        self.assertEqual(set(dict(state.available_options())), {1, 2, 3})
        state.stage = "town"
        self.assertEqual(set(dict(state.available_options())), {1, 2, 3, 4})

    def test_cli_rejects_hidden_number_without_spending_or_mutating_state(self):
        state = self.act(self.make(), 1)
        before = state.data()
        output = StringIO()
        with (
            patch("builtins.input", side_effect=["1", "bag", "back", "load", "quit"]),
            redirect_stdout(output),
        ):
            run(state)
        self.assertNotIn("Buy a certificate", output.getvalue())
        self.assertIn("2. Go to the boss's door.", output.getvalue())
        self.assertIn("Choose a displayed number", output.getvalue())
        self.assertEqual(store.load(state.save_id).data(), before)

    def test_cli_accepts_stable_number_larger_than_visible_option_count(self):
        state = self.act(self.make(), 1)
        with patch("builtins.input", side_effect=["2", "quit"]):
            run(state)
        loaded = store.load(state.save_id)
        self.assertEqual((loaded.stage, loaded.gold), ("castle", 17))

    def test_dynamic_options_do_not_change_snapshot_schema_or_state(self):
        state = self.act(self.make(), 1)
        before = state.data()
        for _ in range(5):
            state.view()
            state.available_options()
        self.assertEqual(state.data(), before)
        self.assertEqual(
            Journey.from_data(before).available_options(), state.available_options()
        )
