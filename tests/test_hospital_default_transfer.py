import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "calibration"))

from hospital_default_transfer import compare, evidence, run_trajectory


class HospitalDefaultTransferTests(unittest.TestCase):
    def test_round_trip_restores_defaults_and_pays_only_donors(self):
        baseline, transfer = run_trajectory(False), run_trajectory(True)
        self.assertEqual(compare(baseline, transfer)["joint_reward_difference"], 30)
        self.assertEqual(len(baseline["initial"]["patients"]), 8)
        self.assertEqual(baseline["initial"]["completed_patients"], [])
        self.assertEqual(len(baseline["actions"]), 2)
        self.assertEqual([row["tool"] for row in transfer["actions"]],
                         ["transfer_resources", "transfer_resources"])
        self.assertEqual(baseline["final"], transfer["final"])

    def test_rejects_unreturned_stock_or_outsider_reward_changes(self):
        baseline, transfer = run_trajectory(False), run_trajectory(True)
        for clinical in (True, False):
            changed = copy.deepcopy(transfer)
            if clinical:
                changed["final"]["inventory"]["General_Hospital"]["Anesthetics"] -= 1
            else:
                changed["agent_rewards"]["General_Hospital_Triage"] += 1
                changed["agent_rewards"]["General_Hospital_Ward"] -= 1
            with self.assertRaises(ValueError):
                compare(baseline, changed)

    def test_saved_default_trace_replays_exactly(self):
        path = (Path(__file__).resolve().parents[1] / "evidence" /
                "hospital-default-transfer" / "evidence.json")
        self.assertEqual(evidence(), json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
