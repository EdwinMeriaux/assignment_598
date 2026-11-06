"""Generate portable visibility shelves. No Rust toolchain is required."""
import argparse
from pathlib import Path

from common.visibility import WORLD_ROOT, map_files, prepare_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, help="Process a single PNG instead of all 30 maps")
    parser.add_argument("--backend", choices=("auto", "native", "python"), default="auto")
    parser.add_argument("--limit", type=int, help="Process the first N maps in numeric dungeon order")
    parser.add_argument("--force", action="store_true", help="Rebuild existing shelves")
    args = parser.parse_args()
    paths = [args.map] if args.map else map_files(WORLD_ROOT)
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be positive")
        paths = paths[:args.limit]
    for i, path in enumerate(paths, 1):
        shelf, backend = prepare_map(path, args.backend, args.force)
        print(f"[{i}/{len(paths)}] {path.name}: {backend} -> {shelf.name}", flush=True)
    print("Ready. Run: python main_algo/CADENCE.py")


if __name__ == "__main__":
    main()
