"""Portable shelves, offline generation, and simulator-only sensor access."""
import dbm.dumb
import hashlib
import json
import os
from pathlib import Path
import platform
import shelve
import stat
import subprocess
import tempfile

from PIL import Image

from .geometry import known_distances, line_clear, neighbors, valid_corners

ROOT = Path(__file__).resolve().parents[1]
WORLD_ROOT = ROOT / "worlds/divided_world_1"
FORMAT_VERSION = 1


def map_files(folder=WORLD_ROOT):
    return sorted(Path(folder).rglob("*.png"), key=lambda p: int(p.stem.split("_")[-1]))


def read_map(path):
    with Image.open(path) as image:
        image = image.convert("L")
        width, height = image.size
        values = list(image.tobytes())
    if any(v not in (0, 255) for v in values):
        raise ValueError("Maps must be binary PNGs: white free space, black walls.")
    free = {(i % width, i // width) for i, v in enumerate(values) if v == 255}
    if not free or len(known_distances(free, min(free))) != len(free):
        raise ValueError("The free space must be nonempty and four-neighbor connected.")
    if any(x in (0, width-1) or y in (0, height-1) for x, y in free):
        raise ValueError("The map must have a black outer border.")
    return free, width, height


def native_binary():
    machine = platform.machine().lower()
    machine = {"aarch64": "arm64", "amd64": "x86_64"}.get(machine, machine)
    suffix = ".exe" if platform.system() == "Windows" else ""
    return ROOT / "bin" / f"{platform.system().lower()}-{machine}" / f"cadence_visibility{suffix}"


def python_visibility(free, width, height):
    """Slower reference fallback with exactly the same LOS rule as Rust."""
    all_points = [(x, y) for y in range(height) for x in range(width)]
    points = sorted(free, key=lambda p: (p[1], p[0]))
    data = {str(p): [] for p in all_points}
    # Symmetry halves the work; keep row order identical to the Rust generator.
    for i, a in enumerate(points):
        for b in points[i:]:
            if line_clear(a, b, free) and line_clear(b, a, free):
                data[str(a)].append(b)
                if a != b:
                    data[str(b)].append(a)
    for p in points:
        data[str(p)].sort(key=lambda q: (q[1], q[0]))
    data["all"] = all_points
    data["blocked"] = [p for p in all_points if p not in free]
    return data


def open_shelf(path, flag="r"):
    # Explicit dumb-dbm + pickle protocol 4 avoids OS/Python-specific DB backends.
    return shelve.Shelf(dbm.dumb.open(str(path), flag), protocol=4)


def prepare_map(image_path, backend="auto", force=False):
    image_path = Path(image_path).resolve()
    shelf_path = image_path.with_suffix(".shelf")
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if not force and shelf_path.with_suffix(".shelf.dir").exists():
        with open_shelf(shelf_path) as shelf:
            meta = shelf.get("metadata", {})
            if meta.get("sha256") == digest and meta.get("format_version") == FORMAT_VERSION:
                return shelf_path, "cached"
    free, width, height = read_map(image_path)
    binary = native_binary()
    data, used = None, "python"
    if backend != "python" and binary.is_file():
        try:
            if os.name != "nt":
                binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
            with tempfile.TemporaryDirectory(prefix="cadence-") as folder:
                output = Path(folder) / "visibility.json"
                subprocess.run([str(binary), str(image_path), str(output)], check=True)
                data = json.loads(output.read_text())
            used = "native"
        except (OSError, subprocess.CalledProcessError) as error:
            if backend == "native":
                raise RuntimeError(f"Bundled executable failed: {error}") from error
            print(f"Native executable unavailable ({error}); using Python.", flush=True)
    elif backend == "native":
        raise FileNotFoundError(f"No bundled executable for this platform: {binary}")
    if data is None:
        print(f"Python visibility generation for {image_path.name} (may take a while)...", flush=True)
        data = python_visibility(free, width, height)
    data["metadata"] = {"format_version": FORMAT_VERSION, "sha256": digest,
                        "width": width, "height": height, "backend": used,
                        "corners": valid_corners(free, width, height)}
    with open_shelf(shelf_path, "n") as shelf:
        for key, value in data.items():
            shelf[key] = value
    # dumb-dbm may create a redundant index backup on close.
    shelf_path.with_suffix(".shelf.bak").unlink(missing_ok=True)
    return shelf_path, used


class Sensor:
    """Simulator internals. Never pass this object or its shelf to student code.

    The corner table implements the paper's blackbox alpha. Its hidden records
    are filtered by current observations before targets enter the policy context.
    """
    def __init__(self, image_path):
        self.image_path = Path(image_path).resolve()
        path = self.image_path.with_suffix(".shelf")
        try:
            self.shelf = open_shelf(path)
        except OSError as error:
            raise FileNotFoundError(f"Generate shelves first: python prepare.py --map '{self.image_path}'") from error
        try:
            meta = self.shelf["metadata"]
            if (meta["sha256"] != hashlib.sha256(self.image_path.read_bytes()).hexdigest()
                    or meta["format_version"] != FORMAT_VERSION):
                raise ValueError("Shelf is stale; run prepare.py --force.")
            self.width, self.height = meta["width"], meta["height"]
            self.blocked = {tuple(p) for p in self.shelf["blocked"]}
            self.free = {tuple(p) for p in self.shelf["all"]} - self.blocked
            self.corners = meta["corners"]
        except Exception:
            self.shelf.close()
            raise

    def close(self):
        self.shelf.close()

    def visible_from(self, position):
        return {tuple(p) for p in self.shelf[str(position)]}

    def observe(self, positions):
        seen = set().union(*(self.visible_from(p) for p in positions))
        walls = {q for p in seen for q in neighbors(p) if q in self.blocked}
        occupied = set(positions)
        # The supplied implementation filters valid targets by target visibility.
        # Requiring all neighboring cells visible is stricter and can deadlock.
        targets = {tuple(r["target"]) for r in self.corners
                   if tuple(r["target"]) in seen and tuple(r["target"]) not in occupied}
        distances = known_distances(seen, positions[0])
        return seen, walls, tuple(sorted(targets & distances.keys())), distances
