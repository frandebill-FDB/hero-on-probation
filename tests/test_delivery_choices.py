"""Owned equipment must not lock a persistent character out of delivery endings."""

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
from hero_on_probation import saves
from hero_on_probation.journey_cli import run


class DeliveryChoiceTests(unittest.TestCase):
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

    def damaged_delivery(self, name="Mira", kits=2):
        state = store.create(name)
        state.stage, state.parcel = "castle", "damaged"
        if kits:
            state.inventory["Repair Kit"] = kits
        return store.commit(state)

    def test_same_character_can_collect_damaged_delivery_after_buying_shield(self):
        state = store.create("Collector")
        # Earn money, buy a shield and kit, then complete an intact first delivery.
        state = self.act(state, 3, 4, 2, 2, 1, 1, 2, 3, 4, 4, 2, 2, 1)
        self.assertEqual(state.ending, "DELIVERY COMPLETE")
        save_id = state.save_id
        state = self.act(state, 1, 3)  # Next journey, directly to the crossing.
        with patch("builtins.input", side_effect=["shield", "quit"]):
            run(state)
        state = store.load(save_id)
        self.assertNotIn("Shield", state.equipment)
        self.assertEqual(state.inventory["Pot Lid"], 1)
        state = self.act(state, 3, 2, 4, 2, 2, 1)  # Defend, retreat, deliver.
        self.assertEqual(state.stage, "repair")
        state = self.act(store.load(save_id), 2)
        self.assertEqual(state.ending, "DISH DUTY")
        self.assertEqual(state.inventory["Repair Kit"], 1)
        self.assertIn("DELIVERY HERO", state.achievements)
        self.assertIn("LORD OF THE RINSE", state.achievements)
        self.assertEqual(len(store.list_journeys()), 1)
        state = self.act(state, 1)
        self.assertNotIn("Shield", state.equipment)
        with patch("builtins.input", side_effect=["shield", "quit"]):
            run(state)
        self.assertEqual(store.load(save_id).equipment["Shield"], "Pot Lid")

    def test_shield_toggle_keeps_items_money_and_progress(self):
        state = store.create("Shield")
        state.inventory["Pot Lid"] = 1
        before = state.data()
        state.toggle_shield()
        self.assertEqual(state.defence, 1)
        state.toggle_shield()
        self.assertEqual(state.data(), before)
        self.assertEqual(state.defence, 0)

    def test_shield_requires_ownership_and_cannot_change_during_combat_or_ending(self):
        state = store.create("Restrictions")
        before = state.data()
        with self.assertRaises(ValueError):
            state.toggle_shield()
        self.assertEqual(state.data(), before)
        state.inventory["Pot Lid"] = 1
        state.companion = "Bea"
        state.begin_battle("bridge")
        for stage in ("battle", "ending"):
            if stage == "ending":
                state.finish("TOLL TAKEN")
            before = state.data()
            with self.assertRaises(ValueError):
                state.toggle_shield()
            self.assertEqual(state.data(), before)

    def test_failed_shield_save_does_not_change_live_or_saved_state(self):
        state = store.create("Atomic")
        state.inventory["Pot Lid"] = 1
        state = store.commit(state)
        before = state.data()
        with (
            patch("builtins.input", side_effect=["shield", "quit"]),
            patch.object(store, "commit", side_effect=ValueError("Write failed")),
        ):
            run(state)
        self.assertEqual(state.data(), before)
        self.assertEqual(store.load(state.save_id).data(), before)

    def test_repair_prompt_is_saved_without_spending_or_awarding_anything(self):
        state = self.damaged_delivery()
        gold = state.gold
        state = self.act(state, 1)
        self.assertEqual(state.stage, "repair")
        self.assertEqual((state.gold, state.xp, state.ending), (gold, 0, ""))
        self.assertEqual(state.inventory["Repair Kit"], 2)
        loaded = store.load(state.save_id)
        self.assertEqual(loaded.data(), state.data())
        self.assertEqual(set(dict(loaded.available_options())), {1, 2})
        with patch("builtins.input", side_effect=["bag", "back", "load", "quit"]):
            run(loaded)
        self.assertEqual(store.load(state.save_id).data(), state.data())

    def test_accepting_repair_consumes_one_kit_and_pays_only_once(self):
        state = self.act(self.damaged_delivery(), 1)
        before_gold = state.gold
        with patch("builtins.input", side_effect=["1", "load", "quit"]):
            run(state)
        saved = store.load(state.save_id)
        self.assertEqual((saved.ending, saved.parcel), ("DELIVERY COMPLETE", "intact"))
        self.assertEqual(saved.inventory["Repair Kit"], 1)
        self.assertEqual(saved.gold, before_gold + 5)
        self.assertEqual(saved.achievements["DELIVERY HERO"]["count"], 1)

    def test_declining_repair_keeps_every_kit_and_gives_damaged_ending(self):
        state = self.damaged_delivery()
        before_gold = state.gold
        state = self.act(state, 1, 2)
        self.assertEqual((state.ending, state.parcel), ("DISH DUTY", "damaged"))
        self.assertEqual(state.inventory["Repair Kit"], 2)
        self.assertEqual(state.gold, before_gold)
        self.assertEqual(store.load(state.save_id).data(), state.data())

    def test_no_unnecessary_repair_prompt_for_other_deliveries(self):
        for parcel, kits, ending in (
            ("intact", 2, "DELIVERY COMPLETE"),
            ("bread", 2, "ACCIDENTAL CATERING"),
            ("damaged", 0, "DISH DUTY"),
        ):
            state = self.damaged_delivery(parcel, kits)
            state.parcel = parcel
            state = self.act(store.commit(state), 1)
            self.assertEqual(state.ending, ending)
            self.assertEqual(state.inventory.get("Repair Kit", 0), kits)

    def test_choosing_dinner_instead_of_boss_fight_also_offers_repairs(self):
        state = self.act(self.damaged_delivery(), 2, 1)
        self.assertEqual(state.stage, "repair")
        self.assertIsNone(state.battle)
        state = self.act(state, 2)
        self.assertEqual(state.ending, "DISH DUTY")

    def test_module_can_collect_both_deliveries_with_one_equipped_character(self):
        choices = [
            "1",
            "CLI Collector",
            3,
            4,
            2,
            2,
            1,
            1,
            2,
            3,
            4,
            4,
            2,
            2,
            1,
            1,
            3,
            "shield",
            3,
            2,
            4,
            2,
            2,
            1,
            2,
            "menu",
            3,
            5,
        ]
        result = subprocess.run(
            [sys.executable, "-m", "hero_on_probation"],
            input="\n".join(map(str, choices)) + "\n",
            text=True,
            capture_output=True,
            cwd=saves.SAVE_DIR,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in (
            "ENDING: DELIVERY COMPLETE",
            "Pot Lid stowed",
            "Keep the kit and deliver the parcel as it is.",
            "ENDING: DISH DUTY",
            "Ending collection: 2/10",
        ):
            self.assertIn(expected, result.stdout)
        self.assertNotIn("Could not complete action", result.stdout)
        self.assertNotIn("Choose a displayed number", result.stdout)
