"""Instructor utility: rebuild and bundle the visibility executable on this OS.

Students run prepare.py instead; this utility is never called automatically.
"""
import argparse
from pathlib import Path
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=ROOT / "target")
    args = parser.parse_args()
    target_dir = args.target_dir.resolve()
    subprocess.run(["cargo", "build", "--release", "--locked", "--target-dir", str(target_dir)],
                   cwd=ROOT, check=True)
    machine = platform.machine().lower()
    machine = {"aarch64": "arm64", "amd64": "x86_64"}.get(machine, machine)
    suffix = ".exe" if platform.system() == "Windows" else ""
    filename = "cadence_visibility" + suffix
    destination = ROOT / "bin" / f"{platform.system().lower()}-{machine}" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_dir / "release" / filename, destination)
    print(f"Bundled: {destination}")


if __name__ == "__main__":
    main()
