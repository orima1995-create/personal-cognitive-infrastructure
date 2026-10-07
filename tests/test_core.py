import tempfile
import unittest
from pathlib import Path

from pci.core import (ContractError, audit_store, confirm, empty_store,
                      get_entry, init_store, is_learnable, load_store,
                      observe, parse_impacts, propose, reject, save_store)


class ContractTests(unittest.TestCase):
    def proposal(self, store):
        return propose(
            store, seed="psychoacoustics", hook="Why is a mosquito so loud?",
            ruler="See sound through perception", bridge="alarm sound to hearing",
            unexpected=True, relevant=True,
            expected_impact={"RICHNESS": "HIGH"})

    def test_closed_loop_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pci.json"
            init_store(path)
            store = load_store(path)
            entry = self.proposal(store)
            self.assertEqual(entry["motivation"], {"joy": None, "must": None})
            confirm(store, entry["id"], joy=True, must=False)
            observe(store, entry["id"], experience="noticed another alarm",
                    observed_impact={"TRANSFER": "HIGH"})
            self.assertTrue(is_learnable(entry))
            save_store(path, store)
            retrieved = get_entry(load_store(path), entry["id"])
            self.assertEqual(retrieved["expected_impact"], {"RICHNESS": "HIGH"})
            self.assertEqual(retrieved["observed_impact"], {"TRANSFER": "HIGH"})

    def test_ai_cannot_claim_human_motivation(self):
        store = empty_store()
        entry = self.proposal(store)
        entry["motivation"] = {"joy": True, "must": False}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ContractError, "cannot claim"):
                save_store(Path(directory) / "pci.json", store)

    def test_confirmation_requires_explicit_motivation(self):
        store = empty_store()
        entry = self.proposal(store)
        with self.assertRaisesRegex(ContractError, "explicitly record"):
            confirm(store, entry["id"], joy=False, must=False)

    def test_cannot_skip_confirmation(self):
        store = empty_store()
        entry = self.proposal(store)
        with self.assertRaisesRegex(ContractError, "invalid transition"):
            observe(store, entry["id"], experience="did it",
                    observed_impact={"FEEL": "HIGH"})

    def test_must_only_is_not_learnable(self):
        store = empty_store()
        entry = self.proposal(store)
        confirm(store, entry["id"], joy=False, must=True)
        observe(store, entry["id"], experience="could not stop reading",
                observed_impact={"GROW": "HIGH"})
        self.assertFalse(is_learnable(entry))

    def test_rejection_is_terminal_and_preserves_no_motivation_claim(self):
        store = empty_store()
        entry = self.proposal(store)
        reject(store, entry["id"], note="not interesting")
        self.assertEqual(entry["status"], "USER_REJECTED")
        self.assertEqual(entry["motivation"], {"joy": None, "must": None})
        self.assertFalse(is_learnable(entry))
        with self.assertRaises(ContractError):
            confirm(store, entry["id"], joy=True, must=False)

    def test_serendipity_requires_unexpected_and_relevant(self):
        with self.assertRaisesRegex(ContractError, "serendipity"):
            propose(empty_store(), seed="x", hook="one hook", ruler="lens",
                    bridge="known to unknown", unexpected=True, relevant=False,
                    expected_impact={})

    def test_impact_axes_are_separate_closed_and_unique(self):
        self.assertEqual(parse_impacts(["feel=high", "ease=low"]),
                         {"FEEL": "HIGH", "EASE": "LOW"})
        with self.assertRaises(ContractError):
            parse_impacts(["QOL=HIGH"])
        with self.assertRaisesRegex(ContractError, "duplicate"):
            parse_impacts(["FEEL=LOW", "FEEL=HIGH"])

    def test_hook_must_be_one_string(self):
        store = empty_store()
        entry = self.proposal(store)
        entry["hook"] = ["one", "two"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ContractError, "one non-empty hook"):
                save_store(Path(directory) / "pci.json", store)

    def test_unknown_fields_and_bad_timestamps_are_rejected(self):
        store = empty_store()
        entry = self.proposal(store)
        entry["aggregate_score"] = 99
        with self.assertRaisesRegex(ContractError, "unknown fields"):
            audit_store(store)
        del entry["aggregate_score"]
        entry["updated_at"] = "yesterday"
        with self.assertRaisesRegex(ContractError, "ISO-8601"):
            audit_store(store)

    def test_audit_reports_counts_without_qol_score(self):
        store = empty_store()
        accepted = self.proposal(store)
        confirm(store, accepted["id"], joy=True, must=False)
        rejected = self.proposal(store)
        reject(store, rejected["id"])
        report = audit_store(store)
        self.assertTrue(report["valid"])
        self.assertEqual(report["status_counts"]["USER_REJECTED"], 1)
        self.assertIsNone(report["aggregate_qol_score"])


if __name__ == "__main__":
    unittest.main()
