import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "calibration"))

from hospital_transfer_counterexample import compare, recorded_trajectory, run_trajectory


class HospitalTransferCounterexampleTests(unittest.TestCase):
    def test_redundant_round_trip_rewards_with_equal_clinical_state(self):
        baseline, exchange = run_trajectory(False), run_trajectory(True)
        result = compare(baseline, exchange)
        self.assertEqual(result["joint_reward_difference"], 600)
        self.assertEqual(result["agent_reward_differences"]["A_Ward"], 300)
        self.assertEqual(result["agent_reward_differences"]["B_Ward"], 300)
        self.assertTrue(result["outsider_rewards_unchanged"])
        self.assertGreater(exchange["joint_reward"], exchange["compute_max_joint_reward"])
        self.assertEqual(exchange["final"]["completed_flow_times"], {
            "Patient_A": 25, "Patient_B": 25,
        })
        self.assertEqual(exchange["final"]["holding_cost"], 400)

    def test_phase_trace_and_early_termination(self):
        for exchange in (False, True):
            trajectory = run_trajectory(exchange)
            trace = trajectory["trace"]
            self.assertEqual([row["phase"] for row in trace],
                             ["planning", "planning", "execution", "execution"])
            self.assertEqual([row["done_before"] for row in trace], [False] * 4)
            self.assertEqual([row["done_after"] for row in trace], [False, False, False, True])
            planning_tool = "transfer_resources" if exchange else "broadcast_message"
            self.assertEqual([row["tool"] for row in trace],
                             [planning_tool, planning_tool, "schedule_patient", "schedule_patient"])
            self.assertEqual(len(trajectory["blackboard_action_log"]), 4)
            self.assertEqual(trajectory["initial"], trajectory["after_planning"])
            for row in trace:
                self.assertEqual(row["joint_reward"], sum(row["agent_rewards"].values()))

    def test_comparison_rejects_clinical_or_outsider_changes(self):
        baseline, exchange = run_trajectory(False), run_trajectory(True)
        changed = copy.deepcopy(exchange)
        changed["final"]["inventory"]["A"]["Anesthetics"] -= 1
        with self.assertRaisesRegex(ValueError, "final"):
            compare(baseline, changed)
        changed = copy.deepcopy(exchange)
        changed["agent_rewards"]["A_Triage"] += 1
        with self.assertRaisesRegex(ValueError, "outsider"):
            compare(baseline, changed)

    def test_recorded_trajectories_reproduce(self):
        root = Path(__file__).resolve().parents[1] / "evidence" / "hospital-transfer-counterexample"
        evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evidence["trajectories"]), 2)
        for recorded, exchange in zip(evidence["trajectories"], (False, True), strict=True):
            self.assertEqual(recorded_trajectory(run_trajectory(exchange)), recorded)


if __name__ == "__main__":
    unittest.main()
