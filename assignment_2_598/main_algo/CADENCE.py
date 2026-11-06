"""CADENCE teaching variant: teleport ONE NEW agent to a seen valid corner.

Student edit point: main_algo/corner_selection.py::choose_corner.
One step is one deployment, not a physical movement time step. Existing agents
stay fixed. No deallocation, neural networks, or motion planner are included.
"""
import argparse
import json
from pathlib import Path
import random
import sys
import time
from types import MappingProxyType

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.visibility import ROOT, Sensor, map_files
from common.visuals import draw_frame, save_frames
from main_algo.corner_selection import Observation, choose_corner, random_corner


def make_observation(sensor, positions, step):
    seen, walls, candidates, distances = sensor.observe(positions)
    observation = Observation(sensor.width, sensor.height, step, positions[0],
                              tuple(positions), frozenset(seen), frozenset(walls),
                              MappingProxyType(distances))
    return observation, candidates


def run_cadence(map_path, seed=0, policy="random", step_limit=1000,
                max_agents=1000, deployment_point=None, deployment_seed=0,
                output=None, quiet=False, selector=None):
    """Run a seeded policy. Agent counts INCLUDE the fixed deployment point.

    Separate deployment and action seeds hold the start fixed across policies.
    The optional selector is useful for programmatic experiments and tests.
    Invalid policy outputs raise ValueError before any deployment occurs.
    """
    if step_limit < 0 or max_agents < 1:
        raise ValueError("step_limit must be nonnegative; max_agents must be at least 1.")
    if policy not in ("random", "student"):
        raise ValueError("policy must be 'random' or 'student'")
    sensor = Sensor(map_path)
    start = time.perf_counter()
    try:
        if deployment_point is None:
            deployment_point = random.Random(deployment_seed).choice(sorted(sensor.free))
        deployment_point = tuple(deployment_point)
        if deployment_point not in sensor.free:
            raise ValueError(f"Deployment point {deployment_point} is not free space.")
        positions = [deployment_point]
        rng = random.Random(seed)
        selection = selector if selector is not None else (random_corner if policy == "random" else choose_corner)
        trace, frames, step = [], [], 0
        observation, candidates = make_observation(sensor, positions, step)
        while True:
            covered = len(observation.observed_free) == len(sensor.free)
            if covered:
                status = "covered"
                break
            if step >= step_limit:
                status = "step_limit"
                break
            if len(positions) >= max_agents:
                status = "agent_limit"
                break
            if not candidates:
                status = "no_eligible_corners"
                break
            # The sole policy call: inputs contain only current observations.
            selected = selection(candidates, observation, rng)
            if not isinstance(selected, tuple) or selected not in candidates:
                raise ValueError(f"Policy returned {selected!r}; return a tuple from {candidates!r}.")
            if output is not None:
                frames.append(draw_frame(observation, candidates, selected))
            before = observation
            # Add a NEW stationary agent. Older agents never move or disappear.
            positions.append(selected)
            step += 1
            observation, next_candidates = make_observation(sensor, positions, step)
            if not before.observed_free <= observation.observed_free:
                raise RuntimeError("Previously observed coverage was lost.")
            # Endpoint LOS check. This does not simulate a path or continuous time.
            new_visible = sensor.visible_from(selected)
            if not any(p in new_visible and selected in sensor.visible_from(p) for p in positions[:-1]):
                raise RuntimeError("New agent is disconnected at its teleport endpoint.")
            trace.append({"step": step, "candidates_before": candidates, "selected": selected,
                          "known_depot_distance": before.distances[selected],
                          "observed_cells_before": len(before.observed_free),
                          "observed_cells_after": len(observation.observed_free),
                          "new_cells": len(observation.observed_free - before.observed_free),
                          "candidates_after": next_candidates, "agents_including_depot": len(positions)})
            if not quiet:
                print(f"Step {step:3d}: {len(candidates):2d} candidates -> {selected}; "
                      f"+{trace[-1]['new_cells']} cells; {len(positions)} agents", flush=True)
            candidates = next_candidates
        result = {"map": Path(map_path).name, "policy": policy, "seed": seed,
                  "deployment_seed": deployment_seed, "deployment_point": deployment_point,
                  "status": status, "success": covered, "teleport_steps": step,
                  "steps_to_full_coverage": step if covered else None,
                  "peak_agents_including_depot": len(positions),
                  "final_agents_including_depot": len(positions),
                  "mobile_agents": len(positions)-1, "covered_cells": len(observation.observed_free),
                  "total_free_cells": len(sensor.free), "coverage_fraction": len(observation.observed_free)/len(sensor.free),
                  "step_limit": step_limit, "max_agents_including_depot": max_agents,
                  "agent_positions": positions, "trace": trace,
                  "runtime_seconds": time.perf_counter()-start}
        if output is not None:
            output = Path(output)
            frames.append(draw_frame(observation, candidates))
            save_frames(frames, output)
            (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        if not quiet:
            print(f"{status}: {len(observation.observed_free)}/{len(sensor.free)} free cells; "
                  f"{step} teleport steps; {len(positions)} agents including depot.")
        return result
    finally:
        sensor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=map_files()[0])
    parser.add_argument("--policy", choices=("random", "student"), default="random")
    parser.add_argument("--seed", type=int, default=0, help="Corner-selection seed")
    parser.add_argument("--deployment-seed", type=int, default=0, help="Independent start-position seed")
    parser.add_argument("--deployment", nargs=2, type=int, metavar=("X", "Y"))
    parser.add_argument("--step-limit", type=int, default=1000)
    parser.add_argument("--max-agents", type=int, default=1000, help="Includes the fixed depot")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/latest")
    args = parser.parse_args()
    try:
        result = run_cadence(args.map, args.seed, args.policy, args.step_limit,
                             args.max_agents, args.deployment, args.deployment_seed, args.output)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(f"Trace and images: {args.output.resolve()}")
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
