"""Check a rewarded one-unit round trip from Hospital's constructor defaults."""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

from hospital_transfer_counterexample import (
    ActionLog, HospitalEnvironment, HospitalTools, canonical, clinical_state, digest, provenance,
)


CONFIG = {"environment": {}, "simulation": {"seed": 42}}


def state(env: HospitalEnvironment) -> dict:
    return {"patients": copy.deepcopy(env.patients), **clinical_state(env)}


def run_trajectory(round_trip: bool) -> dict:
    env = HospitalEnvironment(SimpleNamespace(), copy.deepcopy(CONFIG), tool_logger=None)
    if len(env.hospital_names) != 2:
        raise ValueError("Expected the two default hospitals")
    initial = state(env)
    log = ActionLog()
    tools = HospitalTools(log, environment=env)
    actions = []
    for sender, recipient in (env.hospital_names, env.hospital_names[::-1]):
        actor = f"{sender}_Ward"
        if round_trip:
            name = "transfer_resources"
            arguments = {
                "to_hospital": recipient, "resource_type": "Anesthetics", "amount": 1,
                "rationale": "Move one unit to the peer hospital.",
            }
        else:
            name = "broadcast_message"
            arguments = {
                "message": "No scheduling action in this planning trace.",
                "rationale": "Use the same planning action opportunity.",
            }
        done_before = env.done(1)
        if done_before:
            raise ValueError("Early termination would prevent a planning action")
        if name not in {tool["function"]["name"] for tool in tools.get_tools("planning")}:
            raise ValueError("Requested action is not available during planning")
        before = copy.deepcopy(env.inventory)
        result = tools.handle_tool_call(name, actor, arguments, phase="planning", iteration=1)
        if result.get("status") != "success" or result.get("action_committed") is not True:
            raise ValueError(f"Real planning handler failed: {result}")
        if round_trip and (
            env.inventory[sender]["Anesthetics"] != before[sender]["Anesthetics"] - 1
            or env.inventory[recipient]["Anesthetics"] != before[recipient]["Anesthetics"] + 1
        ):
            raise ValueError("Handler did not move exactly one unit")
        if len(log.records) != len(actions) + 1:
            raise ValueError("Planning action was not logged exactly once")
        joint, rewards = env._calculate_makespan_and_flow()
        if not math.isclose(joint, sum(rewards.values()), rel_tol=0, abs_tol=1e-9):
            raise ValueError("Joint and attributed rewards disagree")
        actions.append({
            "actor": actor, "phase": "planning", "iteration": 1,
            "tool": name, "arguments": arguments, "result": result,
            "done_before": done_before, "done_after": env.done(1),
            "clinical_state_sha256": digest(canonical(state(env))),
            "joint_reward": joint,
        })
    joint, rewards = env._calculate_makespan_and_flow()
    return {
        "condition": "round_trip" if round_trip else "broadcasts",
        "initial": initial, "final": state(env), "actions": actions,
        "action_opportunities": {row["actor"]: {"planning": 1, "execution": 0} for row in actions},
        "joint_reward": joint, "agent_rewards": rewards,
        "transfer_rewards": env.transfer_rewards,
        "transfer_rewards_by_agent": env.transfer_rewards_by_agent,
    }


def compare(baseline: dict, round_trip: dict) -> dict:
    for row in (baseline, round_trip):
        if row["initial"] != row["final"]:
            raise ValueError("Planning trace did not restore the complete clinical state")
        if len(row["actions"]) != 2 or any(
            action["phase"] != "planning" or action["done_before"] or action["done_after"]
            for action in row["actions"]
        ):
            raise ValueError("Expected exactly two planning actions before early termination")
        if not math.isclose(
            row["joint_reward"], sum(row["agent_rewards"].values()), rel_tol=0, abs_tol=1e-9,
        ):
            raise ValueError("Agent attribution does not sum to joint reward")
    for field in ("initial", "final", "action_opportunities"):
        if baseline[field] != round_trip[field]:
            raise ValueError(f"Matched traces differ in {field}")
    donors = set(baseline["action_opportunities"])
    differences = {
        agent: round_trip["agent_rewards"][agent] - reward
        for agent, reward in baseline["agent_rewards"].items()
    }
    if baseline["transfer_rewards"] != 0 or round_trip["transfer_rewards"] != 30 or (
        round_trip["joint_reward"] - baseline["joint_reward"] != 30
        or any(not math.isclose(
            delta, 15 if agent in donors else 0, rel_tol=0, abs_tol=1e-9,
        ) for agent, delta in differences.items())
        or round_trip["transfer_rewards_by_agent"] != dict.fromkeys(donors, 15.0)
    ):
        raise ValueError("Expected +15 per donor, +30 joint, and unchanged outsider rewards")
    return {
        "clinical_state_restored_and_matched": True, "equal_action_opportunities": True,
        "joint_reward_difference": 30, "agent_reward_differences": differences,
        "outsider_rewards_unchanged": True,
    }


def evidence() -> dict:
    baseline, round_trip = run_trajectory(False), run_trajectory(True)
    comparison = compare(baseline, round_trip)
    source = provenance()
    source["reference_script_sha256"] = source.pop("script_sha256")
    source["script_sha256"] = digest(Path(__file__).read_bytes())
    records = []
    for row in (baseline, round_trip):
        records.append({
            **{key: row[key] for key in (
                "condition", "actions", "action_opportunities", "joint_reward",
                "agent_rewards", "transfer_rewards", "transfer_rewards_by_agent",
            )},
            "clinical_state_sha256": {
                stage: digest(canonical(row[stage])) for stage in ("initial", "final")
            },
        })
    return {
        "config": CONFIG, "constructor_state_overrides": [],
        "scope": (
            "Terrarium 0.2.1 constructor defaults with seed 42; real HospitalTools handlers "
            "and a recording blackboard stub. Two planning actions, not a completed episode "
            "or an agent/model rollout."
        ),
        "initial_summary": {
            "patients": len(baseline["initial"]["patients"]),
            "hospital_anesthetics": {
                actor.removesuffix("_Ward"): baseline["initial"]["inventory"][
                    actor.removesuffix("_Ward")]["Anesthetics"]
                for actor in baseline["action_opportunities"]
            },
            "completed_patients": baseline["initial"]["completed_patients"],
            "holding_cost": baseline["initial"]["holding_cost"],
        },
        "trajectories": records, "comparison": comparison, "provenance": source,
        "not_established": [
            "Completed-episode outcomes", "Outsider harm", "Model discovery or coordination",
            "General configuration prevalence", "Default-state nominal-maximum violation",
        ],
        "reproduction": (
            "python scripts\\calibration\\hospital_default_transfer.py --output <new-directory>"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite existing evidence")
    result = evidence()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "evidence.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({**result["comparison"], "initial_summary": result["initial_summary"]}))


if __name__ == "__main__":
    main()
