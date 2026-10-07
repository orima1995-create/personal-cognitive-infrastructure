import tempfile
import unittest
from pathlib import Path

from pci.core import (ContractError, empty_store, get_entry, init_store,
                      is_learnable, load_store, parse_impacts, propose,
                      save_store, transition)


class ContractTests(unittest.TestCase):
    def proposal(self, store, *, joy=True, must=False):
        return propose(
            store, seed="psychoacoustics", hook="Why is a mosquito so loud?",
            ruler="See sound through perception", bridge="alarm sound to hearing",
            unexpected=True, relevant=True, joy=joy, must=must,
            expected_impact={"RICHNESS": "HIGH"},
        )

    def test_closed_loop_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pci.json"
            init_store(path)
            store = load_store(path)
            entry = self.proposal(store)
            self.assertFalse(is_learnable(entry))
            transition(store, entry["id"], "USER_CONFIRMED")
            transition(store, entry["id"], "OBSERVED",
                       experience="noticed frequency in another alarm",
                       observed_impact={"TRANSFER": "HIGH"})
            self.assertTrue(is_learnable(entry))
            save_store(path, store)
            retrieved = get_entry(load_store(path), entry["id"])
            self.assertEqual(retrieved["expected_impact"], {"RICHNESS": "HIGH"})
            self.assertEqual(retrieved["observed_impact"], {"TRANSFER": "HIGH"})

    def test_cannot_skip_confirmation(self):
        store = empty_store()
        entry = self.proposal(store)
        with self.assertRaisesRegex(ContractError, "invalid transition"):
            transition(store, entry["id"], "OBSERVED",
                       experience="did it", observed_impact={"FEEL": "HIGH"})

    def test_must_only_is_not_learnable(self):
        store = empty_store()
        entry = self.proposal(store, joy=False, must=True)
        transition(store, entry["id"], "USER_CONFIRMED")
        transition(store, entry["id"], "OBSERVED",
                   experience="could not stop reading",
                   observed_impact={"GROW": "HIGH"})
        self.assertFalse(is_learnable(entry))

    def test_serendipity_requires_unexpected_and_relevant(self):
        with self.assertRaisesRegex(ContractError, "serendipity"):
            propose(empty_store(), seed="x", hook="one hook", ruler="lens",
                    bridge="known to unknown", unexpected=True, relevant=False,
                    joy=True, must=False, expected_impact={})

    def test_impact_axes_are_separate_and_closed(self):
        self.assertEqual(parse_impacts(["feel=high", "ease=low"]),
                         {"FEEL": "HIGH", "EASE": "LOW"})
        with self.assertRaises(ContractError):
            parse_impacts(["QOL=HIGH"])

    def test_hook_must_be_one_string(self):
        store = empty_store()
        entry = self.proposal(store)
        entry["hook"] = ["one", "two"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ContractError, "one non-empty hook"):
                save_store(Path(directory) / "pci.json", store)


if __name__ == "__main__":
    unittest.main()
