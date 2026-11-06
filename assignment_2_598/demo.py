"""Prepare one map if needed, then run the teleporting random baseline."""
import argparse
from pathlib import Path

from common.visibility import ROOT, map_files, prepare_map
from main_algo.CADENCE import run_cadence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=map_files()[0])
    parser.add_argument("--policy", choices=("random", "student"), default="random")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=("auto", "native", "python"), default="auto")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/latest")
    args = parser.parse_args()
    prepare_map(args.map, args.backend)
    result = run_cadence(args.map, seed=args.seed, policy=args.policy, output=args.output)
    print(f"Trace and images: {args.output.resolve()}")
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
