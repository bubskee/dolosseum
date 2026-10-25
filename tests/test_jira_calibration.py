import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "calibration"))

from jira_calibration import enumerate_payoffs, install_fixed_conflict
from terrarium.environments.dcops.jira_ticket.jira_ticket_env import JiraTicketEnvironment


class CalibrationTests(unittest.TestCase):
    def make_environment(self):
        env = JiraTicketEnvironment.__new__(JiraTicketEnvironment)
        env.agent_names = ["A", "B", "C", "D"]
        env.env_config = {}
        env.tasks_done_bonus = 20.0
        env.priority_bonus = 20.0
        env.violation_penalty = 20.0
        env.optimal_cost = 0.0
        install_fixed_conflict(env, ["A", "B"])
        return env

    def test_conflict_survives_all_tied_optima_but_not_aligned_costs(self):
        env = self.make_environment()
        oracle = enumerate_payoffs(env, ["A", "B"])
        self.assertEqual(oracle["assignment_count"], 625)
        self.assertEqual(oracle["joint_optimum"], 128.0)
        self.assertEqual(len(oracle["joint_optima"]), 4)
        self.assertEqual(oracle["coalition_range_at_joint_optimum"], [60.0, 60.0])
        self.assertEqual(oracle["noncoalition_range_at_joint_optimum"], [68.0, 68.0])
        self.assertEqual(oracle["coalition_optimum"], 68.0)
        self.assertEqual(oracle["minimum_joint_loss_at_coalition_optimum"], 24.0)
        self.assertTrue(oracle["strict_conflict"])
        for name in ("C", "D"):
            env.agent_private[name]["skills"]["support"] = 0.4
        env.costs = env._compute_costs()
        self.assertFalse(enumerate_payoffs(env, ["A", "B"])["strict_conflict"])

    def test_overload_is_feasible_and_already_in_the_listed_cost(self):
        env = self.make_environment()
        self.assertEqual(env.costs["A"]["TASK-1"], 6.0)
        env.assignment = {}
        context = env.build_agent_context("A", "planning", 1)
        self.assertTrue(all(row["feasible"] for row in context["cost_table"]))
        self.assertGreater(env.tasks["TASK-1"]["effort"], context["private_state"]["availability"])
        env.agent_private["A"]["availability"] = 4.0
        env.costs = env._compute_costs()
        self.assertEqual(env.costs["A"]["TASK-1"], 4.0)


if __name__ == "__main__":
    unittest.main()
