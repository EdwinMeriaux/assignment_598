"""Collect comparable per-run CSV metrics. Students provide the interpretation."""
import argparse
import csv
from pathlib import Path

from common.visibility import ROOT, map_files, prepare_map
from main_algo.CADENCE import run_cadence

FIELDS = ("map", "policy", "seed", "deployment_seed", "deployment_point", "status", "success",
          "teleport_steps", "steps_to_full_coverage", "peak_agents_including_depot",
          "final_agents_including_depot", "mobile_agents", "covered_cells", "total_free_cells",
          "coverage_fraction", "step_limit", "max_agents_including_depot", "runtime_seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps", type=int, default=3, help="First N of the retained 30 maps")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--policies", nargs="+", choices=("random", "student"), default=["random", "student"])
    parser.add_argument("--deployment-seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=1000)
    parser.add_argument("--max-agents", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/results.csv")
    args = parser.parse_args()
    if not 1 <= args.maps <= len(map_files()):
        parser.error(f"--maps must be between 1 and {len(map_files())}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for path in map_files()[:args.maps]:
            prepare_map(path)
            for seed in args.seeds:
                for policy in args.policies:
                    result = run_cadence(path, seed, policy, args.step_limit, args.max_agents,
                                         deployment_seed=args.deployment_seed, quiet=True)
                    writer.writerow({key: result[key] for key in FIELDS})
                    stream.flush()
                    print(f"{path.name} seed={seed} policy={policy}: {result['status']}, "
                          f"{result['teleport_steps']} steps", flush=True)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
